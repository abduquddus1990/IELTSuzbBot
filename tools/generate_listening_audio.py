"""Generate Listening MP3 files from the scripts in `app/services/content/*_set*.py`.

Developer tool (not used at runtime). Requires `pip install edge-tts` and `ffmpeg` on PATH.

    python -m tools.generate_listening_audio                 # missing files only
    python -m tools.generate_listening_audio --force         # regenerate everything
    python -m tools.generate_listening_audio ielts_set1      # one set

To make synthetic speech sound like a studio recording, each speaker has its own neural voice,
speaking rate and pitch; turn-taking gaps vary like real conversation; and the finished track gets
a light room reverb, a very quiet noise floor (no "digital silence") and loudness normalisation.
Human recordings can replace any file later: keep the same name, e.g. `ielts_set1_part2.mp3`.
"""

from __future__ import annotations

import asyncio
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts

from app.services.content import cefr_set1, ielts_set1

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "webapp" / "audio"

SETS = {"ielts_set1": ielts_set1, "cefr_set1": cefr_set1}

# role -> (voice, rate, pitch). Dialogue speakers talk a little faster than the narrator.
VOICES: dict[str, tuple[str, str, str]] = {
    "NARRATOR": ("en-GB-ThomasNeural", "-6%", "-2Hz"),
    "MALE_GB": ("en-GB-RyanNeural", "+2%", "+0Hz"),
    "FEMALE_GB": ("en-GB-SoniaNeural", "+3%", "+2Hz"),
    "GUIDE_AU": ("en-AU-NatashaNeural", "+0%", "+0Hz"),
    "TUTOR": ("en-GB-LibbyNeural", "-2%", "-3Hz"),
    "MALE_IE": ("en-IE-ConnorNeural", "+4%", "+0Hz"),
    "FEMALE_IE": ("en-IE-EmilyNeural", "+4%", "+3Hz"),
    "LECTURER": ("en-US-AndrewMultilingualNeural", "-3%", "+0Hz"),
}
SAMPLE_RATE = "24000"

# Light room reverb + gentle band-limiting, then a quiet brown-noise floor, then broadcast loudness.
MASTER_FILTER = (
    "[0:a]aecho=0.8:0.6:18|37:0.10|0.06,highpass=f=70,lowpass=f=10500[v];"
    "[1:a]volume=0.5[n];"
    "[v][n]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
    "loudnorm=I=-18:TP=-2:LRA=11"
)


def _silence(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
         "-t", f"{seconds:.2f}", "-c:a", "pcm_s16le", str(path)],
        check=True,
    )


def _to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", SAMPLE_RATE, "-ac", "1",
         "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )


async def _tts_with_retry(text: str, role: str, dst: Path, attempts: int = 5) -> None:
    voice, rate, pitch = VOICES[role]
    for attempt in range(1, attempts + 1):
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(dst))
            return
        except Exception:
            if attempt == attempts:
                raise
            await asyncio.sleep(2 * attempt)


def _gap_after(role: str, next_role: str | None, rng: random.Random) -> float:
    """Natural turn-taking: quick replies in dialogue, longer breaths around the narrator."""
    if role == "NARRATOR" or next_role == "NARRATOR":
        return rng.uniform(0.9, 1.3)
    if next_role == role:  # same speaker continues (monologue paragraphs)
        return rng.uniform(0.45, 0.8)
    return rng.uniform(0.2, 0.55)


async def _render_part(set_id: str, part: dict, tmp: Path) -> Path:
    rng = random.Random(f"{set_id}-{part['number']}")  # reproducible output
    script = part["script"]
    pieces: list[Path] = []
    for idx, (role, text) in enumerate(script):
        wav = tmp / f"{set_id}_{part['number']}_{idx:03d}.wav"
        if role == "PAUSE":
            _silence(wav, float(text))
            pieces.append(wav)
            continue
        mp3 = wav.with_suffix(".mp3")
        await _tts_with_retry(text, role, mp3)
        _to_wav(mp3, wav)
        pieces.append(wav)
        next_role = next((r for r, _ in script[idx + 1:] if r != "PAUSE"), None)
        gap = tmp / f"gap_{set_id}_{part['number']}_{idx:03d}.wav"
        _silence(gap, _gap_after(role, next_role, rng))
        pieces.append(gap)

    concat_list = tmp / f"{set_id}_{part['number']}.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    out = OUT_DIR / f"{set_id}_part{part['number']}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.004:r={SAMPLE_RATE}",
         "-filter_complex", MASTER_FILTER,
         "-ac", "1", "-ar", "22050", "-b:a", "48k", str(out)],
        check=True,
    )
    return out


async def main(selected: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is required on PATH")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        for set_id in selected:
            for part in SETS[set_id].LISTENING_PARTS:
                existing = OUT_DIR / f"{set_id}_part{part['number']}.mp3"
                if existing.exists() and "--force" not in sys.argv:
                    continue
                out = await _render_part(set_id, part, tmp)
                print(f"{out.name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    asyncio.run(main([a for a in sys.argv[1:] if not a.startswith("--")] or list(SETS)))
