"""Generate Listening MP3 files from the scripts in `app/services/content/*_set*.py`.

Developer tool (not used at runtime). Requires `pip install edge-tts` and `ffmpeg` on PATH.

    python -m tools.generate_listening_audio            # all sets
    python -m tools.generate_listening_audio ielts_set1 # one set
"""

from __future__ import annotations

import asyncio
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

VOICES = {
    "NARRATOR": "en-GB-ThomasNeural",
    "MALE_GB": "en-GB-RyanNeural",
    "FEMALE_GB": "en-GB-LibbyNeural",
    "GUIDE_AU": "en-AU-NatashaNeural",
    "TUTOR": "en-GB-SoniaNeural",
    "MALE_IE": "en-IE-ConnorNeural",
    "FEMALE_IE": "en-IE-EmilyNeural",
    "LECTURER": "en-US-AndrewNeural",
}
SAMPLE_RATE = "24000"
GAP_SECONDS = 0.6


def _silence(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
         "-t", str(seconds), "-c:a", "pcm_s16le", str(path)],
        check=True,
    )


def _to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", SAMPLE_RATE, "-ac", "1",
         "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )


async def _tts_with_retry(text: str, voice: str, dst: Path, attempts: int = 5) -> None:
    for attempt in range(1, attempts + 1):
        try:
            await edge_tts.Communicate(text, voice, rate="-5%").save(str(dst))
            return
        except Exception:
            if attempt == attempts:
                raise
            await asyncio.sleep(2 * attempt)


async def _render_part(set_id: str, part: dict, tmp: Path) -> Path:
    pieces: list[Path] = []
    gap = tmp / "gap.wav"
    if not gap.exists():
        _silence(gap, GAP_SECONDS)
    for idx, (voice, text) in enumerate(part["script"]):
        wav = tmp / f"{set_id}_{part['number']}_{idx:03d}.wav"
        if voice == "PAUSE":
            _silence(wav, float(text))
        else:
            mp3 = wav.with_suffix(".mp3")
            await _tts_with_retry(text, VOICES[voice], mp3)
            _to_wav(mp3, wav)
        pieces.extend([wav, gap])
    concat_list = tmp / f"{set_id}_{part['number']}.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    out = OUT_DIR / f"{set_id}_part{part['number']}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-ac", "1", "-ar", "22050", "-b:a", "40k", str(out)],
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
