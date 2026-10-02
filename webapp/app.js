/**
 * IELTS & CEFR Mock — computer-delivered exam client (Telegram Mini App + browser).
 *
 * Flow: home → (section intro → section) × N → scoring → results.
 * Sections: Listening (audio plays once, auto-advancing parts), Reading (split screen),
 * Writing (prompt/chart beside the answer box), Speaking (examiner asks one question at a
 * time; answers are recorded and transcribed per question).
 */
(function () {
  'use strict';

  const API = '/api/v1';
  const tg = window.Telegram && window.Telegram.WebApp;
  const IN_TELEGRAM = !!(tg && tg.initData);

  // ------------------------------------------------------------------ utils
  const $ = (sel, root = document) => root.querySelector(sel);
  const app = $('#app');

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function h(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === undefined || v === null || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : v);
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  function add(parent, ...nodes) {
    nodes.flat().forEach((n) => { if (n !== null && n !== undefined && n !== false) parent.append(n); });
    return parent;
  }

  function storage(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (_) {}
    return null;
  }

  function clientId() {
    let id = storage('mock_client_id');
    if (!id) {
      id = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2)).replace(/[^A-Za-z0-9_-]/g, '');
      storage('mock_client_id', id);
    }
    return id;
  }

  function headers() {
    const out = { 'Content-Type': 'application/json', 'X-Client-Id': clientId() };
    if (IN_TELEGRAM) out['X-Telegram-Init-Data'] = tg.initData;
    return out;
  }

  async function api(path, options = {}) {
    const res = await fetch(API + path, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try {
        const data = await res.json();
        if (typeof data.detail === 'string') detail = data.detail;
      } catch (_) {}
      const err = new Error(detail);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  let toastTimer = null;
  function toast(message, isError = false) {
    const t = $('#toast');
    t.textContent = message;
    t.classList.toggle('is-error', isError);
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, isError ? 7000 : 3500);
  }

  function confirmModal(title, text, okLabel = 'OK', showCancel = true) {
    return new Promise((resolve) => {
      $('#modal-title').textContent = title;
      $('#modal-text').textContent = text;
      $('#modal-ok').textContent = okLabel;
      $('#modal-cancel').hidden = !showCancel;
      $('#modal').hidden = false;
      const done = (val) => {
        $('#modal').hidden = true;
        $('#modal-ok').onclick = null;
        $('#modal-cancel').onclick = null;
        resolve(val);
      };
      $('#modal-ok').onclick = () => done(true);
      $('#modal-cancel').onclick = () => done(false);
    });
  }

  const fmt = (secs) => {
    const s = Math.max(0, Math.round(secs));
    return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  };
  const words = (text) => (String(text || '').trim() ? String(text).trim().split(/\s+/).length : 0);

  // ------------------------------------------------------------------ state
  const MODES = {
    full: { label: 'Full mock test', sub: 'Listening, Reading, Writing & Speaking • ~2 h 45 min • PDF report', sections: ['listening', 'reading', 'writing', 'speaking'], ai: true },
    listening: { label: 'Listening only', sub: 'Unlimited • instant score', sections: ['listening'], ai: false },
    reading: { label: 'Reading only', sub: 'Unlimited • 60 minutes', sections: ['reading'], ai: false },
    writing: { label: 'Writing only', sub: 'Task 1 + Task 2 • 60 min • AI feedback', sections: ['writing'], ai: true },
    speaking: { label: 'Speaking only', sub: 'Parts 1–3 with voice • AI feedback', sections: ['speaking'], ai: true },
  };
  const SECTION_INFO = {
    listening: { title: 'Listening', minutes: null, rules: ['You will hear each recording ONCE only.', 'The recording moves to the next part automatically.', 'Answer while you listen. You can move between parts using the bar at the bottom.', 'After the recording ends you have 2 minutes to check your answers.', 'Use headphones and check the volume before you start.'] },
    reading: { title: 'Reading', minutes: 60, rules: ['There are three reading texts and 40 questions.', 'The text is on the left and its questions are on the right.', 'Use the bar at the bottom to move between parts and questions.', 'Flag (⚑) questions you want to come back to.'] },
    writing: { title: 'Writing', minutes: 60, rules: ['There are two tasks. Spend about 20 minutes on Task 1 and 40 minutes on Task 2.', 'Type your answer, or upload a clear photo of your handwritten answer.', 'Task 2 is worth twice as much as Task 1.'] },
    speaking: { title: 'Speaking', minutes: null, rules: ['The examiner will ask you questions one at a time. Each question is read aloud.', 'Press the red button to start answering and press it again when you finish.', 'Part 2: you get 1 minute to prepare, then speak for up to 2 minutes.', 'You need a microphone. If it is not available you can type your answers.'] },
  };

  const S = {
    config: { daily_exam_limit: 2, ads: {} },
    quota: null,
    examType: 'IELTS',
    mode: 'full',
    name: '',
    lang: 'uz',
    test: null,
    sections: [],
    sectionIdx: 0,
    answers: { listening: {}, reading: {} },
    flags: { listening: new Set(), reading: new Set() },
    partIdx: 0,
    currentQ: null,
    writing: { task: 1, t1: '', t2: '', p1: null, p2: null },
    speaking: { queue: [], idx: 0, answers: [], pending: [], typed: false },
    inExam: false,
    timer: { id: null, end: 0, onEnd: null },
  };

  // ------------------------------------------------------------------ chrome
  function setChrome({ bar = false, nav = false, section = '', volume = false } = {}) {
    $('#exam-bar').hidden = !bar;
    $('#exam-nav').hidden = !nav;
    document.body.classList.toggle('has-bar', bar);
    document.body.classList.toggle('has-nav', nav);
    $('#bar-candidate').textContent = S.name;
    $('#bar-section').textContent = section;
    $('#volume-wrap').hidden = !volume;
    if (!nav) $('#exam-nav').innerHTML = '';
  }

  function startTimer(seconds, onEnd, label = 'minutes left') {
    stopTimer();
    S.timer.end = Date.now() + seconds * 1000;
    S.timer.onEnd = onEnd;
    $('#bar-timer-label').textContent = label;
    const tick = () => {
      const left = (S.timer.end - Date.now()) / 1000;
      const el = $('#bar-timer');
      el.textContent = fmt(left);
      el.classList.toggle('is-low', left < 300);
      if (left <= 0) {
        stopTimer();
        if (onEnd) onEnd();
      }
    };
    tick();
    S.timer.id = setInterval(tick, 500);
  }
  function stopTimer() {
    if (S.timer.id) clearInterval(S.timer.id);
    S.timer.id = null;
  }
  function showStaticTimer(text, label) {
    stopTimer();
    $('#bar-timer').textContent = text;
    $('#bar-timer').classList.remove('is-low');
    $('#bar-timer-label').textContent = label;
  }

  function setExamActive(active) {
    S.inExam = active;
    if (IN_TELEGRAM) {
      try { active ? tg.enableClosingConfirmation() : tg.disableClosingConfirmation(); } catch (_) {}
    }
  }
  window.addEventListener('beforeunload', (e) => {
    if (S.inExam) { e.preventDefault(); e.returnValue = ''; }
  });

  // ------------------------------------------------------------------ theme & telegram
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    storage('mock_theme', theme);
  }
  function initTelegram() {
    if (!tg) return;
    try {
      tg.ready();
      tg.expand();
      if (tg.isVersionAtLeast && tg.isVersionAtLeast('7.7') && tg.disableVerticalSwipes) tg.disableVerticalSwipes();
      const user = tg.initDataUnsafe && tg.initDataUnsafe.user;
      if (user && !storage('mock_name')) S.name = [user.first_name, user.last_name].filter(Boolean).join(' ');
      if (user && user.language_code && !storage('mock_lang')) S.lang = user.language_code.startsWith('ru') ? 'ru' : user.language_code.startsWith('en') ? 'en' : 'uz';
    } catch (_) {}
  }
  const isTelegramDesktop = () => IN_TELEGRAM && ['tdesktop', 'macos', 'web', 'weba', 'webk', 'unigram'].includes(tg.platform);
  function goFullscreen() {
    if (isTelegramDesktop() && tg.isVersionAtLeast && tg.isVersionAtLeast('8.0') && tg.requestFullscreen) {
      try { tg.requestFullscreen(); } catch (_) {}
    } else if (!IN_TELEGRAM && document.documentElement.requestFullscreen && window.matchMedia('(min-width: 900px)').matches) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  }
  function exitFullscreen() {
    if (IN_TELEGRAM && tg.isFullscreen && tg.exitFullscreen) { try { tg.exitFullscreen(); } catch (_) {} }
    else if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  }

  // ------------------------------------------------------------------ ads
  let adsenseLoaded = false;
  function adSlot() {
    const ads = S.config.ads || {};
    if (IN_TELEGRAM || !ads.adsense_client_id || !ads.adsense_slot_id) return null;
    if (!adsenseLoaded) {
      adsenseLoaded = true;
      const s = document.createElement('script');
      s.async = true;
      s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(ads.adsense_client_id)}`;
      s.crossOrigin = 'anonymous';
      document.head.append(s);
    }
    const ins = h('ins', { class: 'adsbygoogle', style: 'display:block', 'data-ad-client': ads.adsense_client_id, 'data-ad-slot': ads.adsense_slot_id, 'data-ad-format': 'auto', 'data-full-width-responsive': 'true' });
    setTimeout(() => { try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (_) {} }, 50);
    return h('div', { class: 'ad-slot' }, ins);
  }
  function showTelegramAd() {
    const blockId = (S.config.ads || {}).adsgram_block_id;
    if (!IN_TELEGRAM || !blockId) return Promise.resolve();
    return new Promise((resolve) => {
      const run = () => {
        try {
          window.Adsgram.init({ blockId }).show().then(resolve, resolve);
        } catch (_) { resolve(); }
      };
      if (window.Adsgram) return run();
      const s = document.createElement('script');
      s.src = 'https://sad.adsgram.ai/js/sad.min.js';
      s.onload = run;
      s.onerror = () => resolve();
      document.head.append(s);
    });
  }

  // ------------------------------------------------------------------ home
  async function loadQuota() {
    try { S.quota = await api('/quota'); } catch (_) { S.quota = null; }
  }

  function renderHome() {
    setExamActive(false);
    setChrome();
    stopAudio();
    exitFullscreen();
    app.innerHTML = '';

    const choice = (key, current, title, sub, onPick) =>
      h('button', { type: 'button', class: 'choice', 'aria-pressed': String(key === current), onclick: () => onPick(key) }, h('strong', {}, title), h('span', {}, sub));

    const examRow = h('div', { class: 'choice-row' },
      choice('IELTS', S.examType, 'IELTS Academic', 'Band 0–9 • computer-delivered format', (k) => { S.examType = k; renderHome(); }),
      choice('CEFR', S.examType, 'Multilevel (CEFR)', '0–75 scale • B1, B2, C1', (k) => { S.examType = k; renderHome(); }),
    );
    const modeRow = h('div', { class: 'choice-row' },
      Object.entries(MODES).map(([key, m]) => choice(key, S.mode, m.label, m.sub, (k) => { S.mode = k; renderHome(); })),
    );

    const nameInput = h('input', { class: 'input', id: 'cand-name', maxlength: '80', placeholder: 'e.g. Aziza Karimova', value: S.name, autocomplete: 'name', oninput: (e) => { S.name = e.target.value; } });
    const langSelect = h('select', { class: 'select', id: 'fb-lang', onchange: (e) => { S.lang = e.target.value; } },
      [['uz', 'Oʻzbekcha'], ['ru', 'Русский'], ['en', 'English']].map(([v, l]) => h('option', { value: v, selected: v === S.lang }, l)));

    const limit = S.config.daily_exam_limit;
    const quotaText = S.quota
      ? h('span', { class: 'quota' }, '🎟 AI-scored exams left today: ', h('b', {}, `${S.quota.remaining} / ${S.quota.limit}`))
      : h('span', { class: 'quota' }, `🎟 Free: ${limit} AI-scored exams per day`);

    const startBtn = h('button', { class: 'btn btn--primary btn--lg', type: 'button', onclick: () => startExam(nameInput.value, langSelect.value) }, 'Start test ▸');

    const tips = [];
    if (isTelegramDesktop() || (IN_TELEGRAM && window.innerWidth > 900)) {
      tips.push(h('div', { class: 'hint-box' }, '💻 On a computer the exam opens full screen. You can also use it in any browser: ',
        h('a', { href: location.origin + '/webapp/', target: '_blank', rel: 'noopener' }, location.host + '/webapp')));
    }
    if (!IN_TELEGRAM && S.config.bot_username) {
      tips.push(h('div', { class: 'notice' }, 'Prefer Telegram? Practise Writing & Speaking in our bot: ',
        h('a', { href: `https://t.me/${S.config.bot_username}`, target: '_blank', rel: 'noopener' }, '@' + S.config.bot_username)));
    }

    app.append(h('div', { class: 'home' },
      h('div', { class: 'hero' },
        h('span', { class: 'logo-dot' }, 'AI'),
        h('div', {},
          h('h1', {}, 'IELTS & CEFR Mock Test'),
          h('p', {}, 'Free practice in the real computer-delivered format, with instant AI feedback.')),
        h('button', { class: 'btn btn--ghost btn--sm', style: 'margin-left:auto', type: 'button', title: 'Light / dark', onclick: () => applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark') }, '◐')),
      h('div', { class: 'home-grid' },
        h('section', { class: 'card' }, h('p', { class: 'section-title' }, '1 · Exam'), examRow),
        h('section', { class: 'card' }, h('p', { class: 'section-title' }, '2 · Test'), modeRow),
        h('section', { class: 'card' },
          h('p', { class: 'section-title' }, '3 · Your details'),
          h('div', { class: 'form-row' },
            h('div', { class: 'field' }, h('label', { for: 'cand-name' }, 'Full name (for your report)'), nameInput),
            h('div', { class: 'field' }, h('label', { for: 'fb-lang' }, 'Feedback language'), langSelect))),
        tips,
        h('div', { class: 'start-row' }, quotaText, startBtn),
        adSlot() || '',
      ),
      h('p', { class: 'footer' }, 'Unofficial practice tool. Not affiliated with IELTS, Cambridge, IDP, the British Council or the Uzbekistan Knowledge Assessment Agency. Mustaqil AI baholash va tayyorgarlik vositasi.'),
    ));
  }

  async function startExam(name, lang) {
    S.name = String(name || '').trim();
    S.lang = lang;
    if (!S.name) {
      toast('Please enter your name first.', true);
      $('#cand-name').focus();
      return;
    }
    storage('mock_name', S.name);
    storage('mock_lang', S.lang);
    const mode = MODES[S.mode];
    if (mode.ai) {
      await loadQuota();
      if (S.quota && S.quota.remaining <= 0) {
        await confirmModal('Daily limit reached', `You can take ${S.quota.limit} AI-scored exams per day. Come back tomorrow!\nListening and Reading practice are still unlimited.`, 'OK', false);
        return;
      }
    }
    app.innerHTML = '<div class="loading"><div class="spinner"></div>Loading your test…</div>';
    try {
      S.test = await api(`/tests/${S.examType}-RANDOM`);
    } catch (err) {
      toast(`Could not load the test: ${err.message}`, true);
      renderHome();
      return;
    }
    Object.assign(S, {
      sections: mode.sections.slice(),
      sectionIdx: 0,
      answers: { listening: {}, reading: {} },
      flags: { listening: new Set(), reading: new Set() },
      writing: { task: 1, t1: '', t2: '', p1: null, p2: null },
      speaking: { queue: [], idx: 0, answers: [], pending: [], typed: false },
    });
    setExamActive(true);
    goFullscreen();
    renderSectionIntro();
  }

  // ------------------------------------------------------------------ section flow
  const currentSection = () => S.sections[S.sectionIdx];

  function renderSectionIntro() {
    const key = currentSection();
    const info = SECTION_INFO[key];
    setChrome({ bar: true, section: `${S.test.exam_type} · ${info.title}` });
    showStaticTimer(info.minutes ? `${info.minutes}:00` : '--:--', info.minutes ? 'minutes' : '');
    $('#btn-finish-section').hidden = true;
    app.innerHTML = '';
    const step = S.sections.length > 1 ? `Section ${S.sectionIdx + 1} of ${S.sections.length}` : 'Practice';
    app.append(h('div', { class: 'listen-start card' },
      h('p', { class: 'section-title' }, step),
      h('h2', {}, `${S.test.exam_type === 'IELTS' ? 'IELTS' : 'Multilevel'} ${info.title}`),
      info.minutes ? h('p', {}, `Time: ${info.minutes} minutes`) : null,
      h('ul', { style: 'text-align:left' }, info.rules.map((r) => h('li', {}, r))),
      h('button', { class: 'btn btn--primary btn--lg', type: 'button', onclick: () => startSection(key) }, `Start ${info.title} ▸`)));
  }

  function startSection(key) {
    $('#btn-finish-section').hidden = false;
    $('#btn-finish-section').onclick = () => finishSection(true);
    if (key === 'listening') return startListening();
    if (key === 'reading') return startReading();
    if (key === 'writing') return startWriting();
    if (key === 'speaking') return startSpeaking();
  }

  async function finishSection(ask) {
    const key = currentSection();
    if (ask) {
      const unanswered = key === 'listening' || key === 'reading' ? 40 - countAnswered(key) : 0;
      const msg = unanswered > 0 ? `You have ${unanswered} unanswered question(s).\nYou cannot return to this section.` : 'You cannot return to this section.';
      if (!(await confirmModal(`Finish ${SECTION_INFO[key].title}?`, msg, 'Finish section'))) return;
    }
    stopTimer();
    if (key === 'listening') stopAudio();
    if (key === 'writing') saveWritingFromDom();
    if (key === 'speaking') {
      stopRecording(true);
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      if (S.speaking.pending.length) app.innerHTML = '<div class="loading"><div class="spinner"></div>Processing your spoken answers…</div>';
      await Promise.all(S.speaking.pending);
      if (rec.stream) rec.stream.getTracks().forEach((t) => t.stop());
      rec.stream = null;
    }
    S.sectionIdx += 1;
    if (S.sectionIdx < S.sections.length) renderSectionIntro();
    else submitAll();
  }

  // ------------------------------------------------------------------ questions (shared L/R)
  function countAnswered(section) {
    return Object.values(S.answers[section]).filter((v) => String(v || '').trim()).length;
  }

  function sectionParts(section) {
    return section === 'listening' ? S.test.listening_data.parts : S.test.reading_data.passages;
  }

  function partNumbers(part) {
    return part.groups.flatMap((g) => g.questions.map((q) => q.number));
  }

  function setAnswer(section, number, value) {
    S.answers[section][String(number)] = value;
    S.currentQ = number;
    renderNav(section);
  }

  function renderQuestion(section, group, q) {
    const id = String(q.number);
    const value = S.answers[section][id] || '';
    const flagBtn = h('button', {
      class: 'flag', type: 'button', title: 'Flag for review', 'aria-pressed': String(S.flags[section].has(q.number)),
      onclick: (e) => {
        const f = S.flags[section];
        f.has(q.number) ? f.delete(q.number) : f.add(q.number);
        e.currentTarget.setAttribute('aria-pressed', String(f.has(q.number)));
        renderNav(section);
      },
    }, '⚑');

    const wrap = h('div', { class: 'q', id: `q-${section}-${id}` });
    const head = h('div', { class: 'q__head' }, h('span', { class: 'q__num' }, id));
    const text = h('div', { class: 'q__text' });

    if (group.kind === 'gap') {
      const pieces = String(q.prompt).split('____');
      const input = h('input', {
        class: 'gap-input', type: 'text', value, autocomplete: 'off', autocapitalize: 'off', spellcheck: 'false', 'aria-label': `Answer ${id}`,
        oninput: (e) => setAnswer(section, q.number, e.target.value),
        onfocus: () => { S.currentQ = q.number; renderNav(section); },
      });
      text.append(pieces[0] || '', input, pieces.slice(1).join(' ') || '');
      head.append(text, flagBtn);
      wrap.append(head);
      return wrap;
    }

    text.append(q.prompt);
    head.append(text, flagBtn);
    wrap.append(head);

    const options = q.options || group.box || [];
    if (group.kind === 'mcq') {
      const list = h('div', { class: 'options', role: 'radiogroup' });
      options.forEach((o) => list.append(h('button', {
        class: 'opt', type: 'button', role: 'radio', 'aria-pressed': String(value === o.value),
        onclick: () => { setAnswer(section, q.number, value === o.value ? '' : o.value); rerenderPart(section); },
      }, h('b', {}, o.value), h('span', {}, o.label))));
      wrap.append(list);
    } else {
      const list = h('div', { class: 'letters', role: 'radiogroup' });
      options.forEach((o) => list.append(h('button', {
        class: 'letter', type: 'button', role: 'radio', title: o.label || o.value, 'aria-pressed': String(value === o.value),
        onclick: () => { setAnswer(section, q.number, value === o.value ? '' : o.value); rerenderPart(section); },
      }, o.value)));
      wrap.append(list);
    }
    return wrap;
  }

  function renderGroup(section, group) {
    const node = h('div', { class: 'group' },
      h('p', { class: 'group__range' }, `Questions ${group.range}`),
      h('p', { class: 'group__instr' }, group.instructions));
    if (group.figure_svg) node.append(h('div', { class: 'figure', html: group.figure_svg }));
    const labelled = (group.box || []).some((o) => o.label && o.label !== o.value);
    if (group.box && labelled && !['tfng', 'ynng'].includes(group.kind)) {
      if (group.kind === 'gap') {
        node.append(h('div', { class: 'box' }, h('div', { class: 'box__title' }, group.box_title || 'Word box'),
          h('div', { class: 'word-bank' }, group.box.map((o) => h('span', {}, o.label)))));
      } else {
        node.append(h('div', { class: 'box' }, h('div', { class: 'box__title' }, group.box_title || 'Options'),
          h('ol', {}, group.box.map((o) => h('li', {}, h('b', {}, o.value), o.label)))));
      }
    }
    if (group.title) node.append(h('div', { class: 'group__title' }, group.title));
    group.questions.forEach((q) => node.append(renderQuestion(section, group, q)));
    return node;
  }

  function renderNav(section) {
    const nav = $('#exam-nav');
    nav.innerHTML = '';
    sectionParts(section).forEach((part, idx) => {
      const label = section === 'listening' ? `Part ${part.number}` : `Part ${part.number}`;
      const block = h('div', { class: `nav-part${idx === S.partIdx ? ' is-active' : ''}` }, h('span', { class: 'nav-part__label' }, label));
      partNumbers(part).forEach((n) => {
        const answered = String(S.answers[section][String(n)] || '').trim();
        const cls = ['qbtn', answered ? 'is-answered' : '', S.flags[section].has(n) ? 'is-flagged' : '', S.currentQ === n ? 'is-current' : ''].join(' ');
        block.append(h('button', { class: cls, type: 'button', onclick: () => goToQuestion(section, idx, n) }, n));
      });
      nav.append(block);
    });
    nav.append(h('div', { class: 'nav-arrows' },
      h('button', { class: 'btn btn--sm', type: 'button', onclick: () => stepQuestion(section, -1), 'aria-label': 'Previous question' }, '◀'),
      h('button', { class: 'btn btn--sm', type: 'button', onclick: () => stepQuestion(section, 1), 'aria-label': 'Next question' }, '▶')));
    $('#bar-section').textContent = `${S.test.exam_type} · ${SECTION_INFO[section].title} · ${countAnswered(section)}/40 answered`;
  }

  function stepQuestion(section, delta) {
    const target = Math.min(40, Math.max(1, (S.currentQ || 0) + delta));
    const partIdx = sectionParts(section).findIndex((p) => partNumbers(p).includes(target));
    goToQuestion(section, partIdx, target);
  }

  function goToQuestion(section, partIdx, number) {
    S.currentQ = number;
    if (partIdx !== S.partIdx) {
      S.partIdx = partIdx;
      renderPart(section);
    } else {
      renderNav(section);
    }
    const node = document.getElementById(`q-${section}-${number}`);
    if (node) {
      document.querySelectorAll('.q.is-current').forEach((n) => n.classList.remove('is-current'));
      node.classList.add('is-current');
      const split = node.closest('.split');
      if (split && window.innerWidth < 900) {
        split.dataset.mobile = 'right';
        syncMobileTabs(split);
      }
      node.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = node.querySelector('input');
      if (input) input.focus({ preventScroll: true });
    }
  }

  function rerenderPart(section) {
    // Keep scroll positions while re-rendering after an option click.
    const panes = [...document.querySelectorAll('.pane, .full-pane')].map((p) => p.scrollTop);
    renderPart(section);
    [...document.querySelectorAll('.pane, .full-pane')].forEach((p, i) => { p.scrollTop = panes[i] || 0; });
  }

  function renderPart(section) {
    if (section === 'listening') renderListeningPart();
    else renderReadingPart();
    renderNav(section);
  }

  // ------------------------------------------------------------------ listening
  const audio = $('#listening-audio');
  let listeningState = { playingIdx: -1, finished: false };

  function stopAudio() {
    audio.onended = null;
    audio.onerror = null;
    audio.ontimeupdate = null;
    audio.pause();
    audio.removeAttribute('src');
  }

  function startListening() {
    S.partIdx = 0;
    S.currentQ = 1;
    listeningState = { playingIdx: -1, finished: false };
    setChrome({ bar: true, nav: true, volume: true, section: `${S.test.exam_type} · Listening` });
    $('#volume').oninput = (e) => { audio.volume = Number(e.target.value); };
    audio.volume = Number($('#volume').value);
    showStaticTimer('▶', 'recording playing');
    renderPart('listening');
    playListeningPart(0);
  }

  function playListeningPart(idx) {
    const parts = S.test.listening_data.parts;
    if (idx >= parts.length) {
      listeningState.finished = true;
      listeningState.playingIdx = -1;
      renderListeningPart();
      toast('The recording has finished. You have 2 minutes to check your answers.');
      startTimer(120, () => finishSection(false), 'to check answers');
      return;
    }
    listeningState.playingIdx = idx;
    if (S.partIdx !== idx) {
      S.partIdx = idx;
      S.currentQ = partNumbers(parts[idx])[0];
      renderPart('listening');
      if (idx > 0) toast(`Part ${parts[idx].number} begins.`);
    } else {
      renderListeningPart();
    }
    audio.src = parts[idx].audio_url;
    audio.onended = () => playListeningPart(idx + 1);
    audio.onerror = () => showListeningError(idx);
    audio.ontimeupdate = () => {
      if (!audio.duration) return;
      $('#bar-timer').textContent = fmt(audio.duration - audio.currentTime);
      $('#bar-timer-label').textContent = `Part ${parts[idx].number} audio`;
    };
    audio.play().catch(() => showListeningError(idx));
  }

  function showListeningError(idx) {
    const resumeAt = audio.currentTime || 0;
    confirmModal('Audio problem', 'The recording could not be played (connection problem or the browser blocked it). Press Continue to resume from where it stopped.', 'Continue', false)
      .then(() => {
        audio.play().catch(() => {
          audio.src = S.test.listening_data.parts[idx].audio_url;
          audio.currentTime = resumeAt;
          audio.play().catch(() => showListeningError(idx));
        });
      });
  }

  function renderListeningPart() {
    const part = S.test.listening_data.parts[S.partIdx];
    const playing = listeningState.playingIdx;
    const status = listeningState.finished
      ? h('div', { class: 'listen-status' }, '✅ The recording has finished — check your answers.')
      : playing === S.partIdx
        ? h('div', { class: 'listen-status' }, h('span', { class: 'eq' }, h('i'), h('i'), h('i')), `Now playing: Part ${part.number}`)
        : h('div', { class: 'listen-status' }, `🔈 Now playing: Part ${S.test.listening_data.parts[playing]?.number ?? '–'} — you are viewing Part ${part.number}`);
    const groups = h('div', { class: 'groups-grid' }, part.groups.map((g) => renderGroup('listening', g)));
    app.innerHTML = '';
    app.append(h('div', { class: 'full-pane' }, h('div', { class: 'full-pane__inner', style: 'max-width:1200px' },
      status,
      h('div', { class: 'part-head' }, h('h2', {}, part.title), h('p', {}, part.context)),
      groups)));
  }

  // ------------------------------------------------------------------ reading
  function startReading() {
    S.partIdx = 0;
    S.currentQ = 1;
    setChrome({ bar: true, nav: true, section: `${S.test.exam_type} · Reading` });
    startTimer(60 * 60, () => { toast('Time is up for Reading.'); finishSection(false); });
    renderPart('reading');
  }

  function makeSplit(left, right, leftLabel, rightLabel) {
    const split = h('div', { class: 'split', 'data-mobile': 'left' });
    const saved = storage('mock_split');
    if (saved) split.style.setProperty('--left', saved);
    const tabs = h('div', { class: 'mobile-tabs' },
      h('button', { type: 'button', 'aria-pressed': 'true', onclick: () => { split.dataset.mobile = 'left'; syncMobileTabs(split); } }, leftLabel),
      h('button', { type: 'button', 'aria-pressed': 'false', onclick: () => { split.dataset.mobile = 'right'; syncMobileTabs(split); } }, rightLabel));
    const resizer = h('div', { class: 'resizer', role: 'separator', 'aria-label': 'Resize panels' });
    resizer.addEventListener('pointerdown', (e) => {
      resizer.setPointerCapture(e.pointerId);
      const move = (ev) => {
        const rect = split.getBoundingClientRect();
        const pct = Math.min(75, Math.max(25, ((ev.clientX - rect.left) / rect.width) * 100));
        split.style.setProperty('--left', `${pct}%`);
      };
      const up = () => {
        resizer.removeEventListener('pointermove', move);
        storage('mock_split', split.style.getPropertyValue('--left'));
      };
      resizer.addEventListener('pointermove', move);
      resizer.addEventListener('pointerup', up, { once: true });
    });
    split.append(h('div', { class: 'pane pane--left' }, left), resizer, h('div', { class: 'pane pane--right' }, right));
    split._tabs = tabs;
    return [tabs, split];
  }
  function syncMobileTabs(split) {
    const tabs = split._tabs || split.previousElementSibling;
    if (!tabs) return;
    const [a, b] = tabs.querySelectorAll('button');
    a.setAttribute('aria-pressed', String(split.dataset.mobile === 'left'));
    b.setAttribute('aria-pressed', String(split.dataset.mobile === 'right'));
  }

  function renderReadingPart() {
    const passage = S.test.reading_data.passages[S.partIdx];
    const size = Number(storage('mock_font') || 16);
    document.documentElement.style.setProperty('--reading-size', `${size}px`);
    const fontBtn = (delta, label) => h('button', {
      class: 'btn btn--sm', type: 'button', onclick: () => {
        const next = Math.min(22, Math.max(13, Number(storage('mock_font') || 16) + delta));
        storage('mock_font', String(next));
        document.documentElement.style.setProperty('--reading-size', `${next}px`);
      },
    }, label);
    const left = h('article', { class: 'passage' },
      h('div', { class: 'text-tools' }, fontBtn(-1, 'A−'), fontBtn(1, 'A+')),
      h('p', { class: 'section-title' }, `Reading Passage ${passage.number}`),
      h('h2', {}, passage.title),
      passage.paragraphs.map((p) => {
        const m = /^([A-J]|\d{1,2})\s{2,}(.*)$/s.exec(p);
        return m ? h('p', {}, h('b', {}, m[1] + '  '), m[2]) : h('p', {}, p);
      }));
    const right = h('div', {},
      h('div', { class: 'part-head' }, h('h2', {}, `Questions ${passage.question_range}`)),
      passage.groups.map((g) => renderGroup('reading', g)));
    const [tabs, split] = makeSplit(left, right, 'Text', `Questions ${passage.question_range}`);
    app.innerHTML = '';
    app.append(tabs, split);
  }

  // ------------------------------------------------------------------ writing
  function startWriting() {
    S.writing.task = 1;
    setChrome({ bar: true, nav: true, section: `${S.test.exam_type} · Writing` });
    startTimer(60 * 60, () => { toast('Time is up for Writing.'); finishSection(false); });
    renderWriting();
  }

  function saveWritingFromDom() {
    const ta = $('#essay');
    if (ta) S.writing[`t${S.writing.task}`] = ta.value;
  }

  function renderWritingNav() {
    const nav = $('#exam-nav');
    nav.innerHTML = '';
    [1, 2].forEach((n) => {
      const text = S.writing[`t${n}`];
      const done = words(text) > 0 || S.writing[`p${n}`];
      nav.append(h('div', { class: `nav-part${S.writing.task === n ? ' is-active' : ''}` },
        h('button', { class: `qbtn${done ? ' is-answered' : ''}${S.writing.task === n ? ' is-current' : ''}`, type: 'button', style: 'padding:0 14px', onclick: () => { saveWritingFromDom(); S.writing.task = n; renderWriting(); } },
          `Task ${n} · ${words(text)} words`)));
    });
  }

  function renderWriting() {
    const n = S.writing.task;
    const wd = S.test.writing_data;
    const min = n === 1 ? (wd.min_words_t1 || 150) : (wd.min_words_t2 || 250);
    const prompt = n === 1 ? wd.task_1_prompt : wd.task_2_prompt;

    const chart = n === 1 && wd.task_1_chart_url
      ? h('img', { class: 'chart-img', src: wd.task_1_chart_url, alt: 'Task 1 visual', onclick: (e) => e.currentTarget.classList.toggle('is-zoomed') })
      : null;
    const left = h('div', {},
      h('p', { class: 'section-title' }, `Writing Task ${n}`),
      h('p', { class: 'group__instr' }, n === 1 ? 'You should spend about 20 minutes on this task.' : 'You should spend about 40 minutes on this task.'),
      h('div', { class: 'task-prompt' }, prompt),
      chart,
      chart ? h('p', { class: 'notice' }, 'Tap the chart to enlarge it.') : null);

    const counter = h('span', { class: 'wordcount' });
    const updateCount = (value) => {
      const c = words(value);
      counter.textContent = `Words: ${c}`;
      counter.className = `wordcount ${c >= min ? 'is-ok' : 'is-low'}`;
    };
    const ta = h('textarea', {
      class: 'essay', id: 'essay', spellcheck: 'false', autocorrect: 'off', autocapitalize: 'sentences',
      placeholder: `Type your answer here (at least ${min} words)…`,
      oninput: (e) => { S.writing[`t${n}`] = e.target.value; updateCount(e.target.value); renderWritingNav(); },
    });
    ta.value = S.writing[`t${n}`];
    ta.addEventListener('blur', renderWritingNav);
    updateCount(ta.value);

    const photo = S.writing[`p${n}`];
    const fileInput = h('input', { type: 'file', accept: 'image/*', hidden: true, onchange: (e) => handlePhoto(n, e.target) });
    const photoRow = h('div', { class: 'row' },
      h('div', { class: 'row' },
        h('button', { class: 'btn btn--sm', type: 'button', onclick: () => fileInput.click() }, photo ? '📷 Replace photo' : '📷 Upload handwritten answer'),
        photo ? h('img', { class: 'photo-thumb', src: `data:image/jpeg;base64,${photo}`, alt: 'Uploaded answer' }) : null,
        photo ? h('button', { class: 'btn btn--sm btn--ghost', type: 'button', onclick: () => { S.writing[`p${n}`] = null; renderWriting(); } }, 'Remove') : null,
        fileInput),
      h('span', { class: 'notice' }, photo ? 'The photo is used if the text box is empty.' : `Minimum ${min} words`));
    const right = h('div', { class: 'writing-area' }, h('div', { class: 'row' }, h('strong', {}, `Your answer — Task ${n}`), counter), ta, photoRow);

    const [tabs, split] = makeSplit(left, right, `Task ${n}`, 'Answer');
    app.innerHTML = '';
    app.append(tabs, split);
    renderWritingNav();
  }

  function downscaleImage(dataUrl, maxSide = 1800) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/jpeg', 0.85));
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  function handlePhoto(n, input) {
    const file = input.files && input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (evt) => {
      const dataUrl = await downscaleImage(String(evt.target.result || ''));
      S.writing[`p${n}`] = dataUrl.split(',')[1];
      saveWritingFromDom();
      renderWriting();
      toast(`Photo for Task ${n} attached.`);
    };
    reader.readAsDataURL(file);
  }

  // ------------------------------------------------------------------ speaking
  const rec = { stream: null, ctx: null, source: null, proc: null, chunks: [], started: 0, timerId: null, active: false, onStop: null };

  function buildSpeakingQueue() {
    const sd = S.test.speaking_data;
    const queue = [];
    (sd.part_1_topics || [{ topic: '', questions: sd.part_1_questions }]).forEach((t) =>
      t.questions.forEach((q, i) => queue.push({ part: 1, text: q, topic: i === 0 ? t.topic : null })));
    queue.push({ part: 2, text: sd.part_2_cue_card });
    sd.part_3_questions.forEach((q) => queue.push({ part: 3, text: q }));
    return queue;
  }

  async function startSpeaking() {
    S.speaking.queue = buildSpeakingQueue();
    S.speaking.idx = 0;
    setChrome({ bar: true, section: `${S.test.exam_type} · Speaking` });
    showStaticTimer('00:00', 'answer time');
    try {
      rec.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      S.speaking.typed = false;
    } catch (_) {
      S.speaking.typed = true;
      await confirmModal('Microphone not available', 'We could not access your microphone, so you can type your answers instead. Your pronunciation cannot be assessed in this case.', 'Type answers', false);
    }
    renderSpeakingQuestion();
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-GB';
      u.rate = 0.95;
      const voice = window.speechSynthesis.getVoices().find((v) => /en-GB/i.test(v.lang)) || window.speechSynthesis.getVoices().find((v) => /^en/i.test(v.lang));
      if (voice) u.voice = voice;
      window.speechSynthesis.speak(u);
    } catch (_) {}
  }

  const MAX_ANSWER = { 1: 45, 2: 120, 3: 90 };

  function renderSpeakingQuestion() {
    const { queue, idx } = S.speaking;
    if (idx >= queue.length) return finishSpeaking();
    const item = queue[idx];
    const partStart = idx === 0 || queue[idx - 1].part !== item.part;
    const dots = h('div', { class: 'progress-dots' }, queue.map((_, i) => h('i', { class: i < idx ? 'done' : i === idx ? 'now' : '' })));
    const partTitle = { 1: 'Part 1 — Introduction and interview', 2: 'Part 2 — Individual long turn', 3: 'Part 3 — Two-way discussion' }[item.part];
    $('#bar-section').textContent = `${S.test.exam_type} · Speaking · ${partTitle.split(' — ')[0]}`;

    app.innerHTML = '';
    const body = h('div', { class: 'speak' }, dots, h('p', { class: 'section-title' }, partTitle));

    if (item.part === 2) {
      body.append(h('div', { class: 'cue-card' }, item.text));
      const notes = h('textarea', { class: 'textarea', rows: '4', placeholder: 'Make notes here during your preparation time (not marked).' });
      const area = h('div', { class: 'rec' });
      body.append(h('p', {}, 'You have one minute to prepare. You can make notes. Then talk for one to two minutes.'), notes, area);
      app.append(h('div', { class: 'full-pane' }, body));
      speak('Now, I am going to give you a topic and I would like you to talk about it for one to two minutes. You have one minute to think about what you are going to say.');
      let left = 60;
      const prepLabel = h('div', { class: 'rec__time' }, fmt(left));
      const skip = h('button', { class: 'btn btn--primary', type: 'button' }, 'I am ready — start speaking');
      area.append(h('div', {}, 'Preparation time'), prepLabel, skip);
      showStaticTimer(fmt(left), 'preparation');
      const id = setInterval(() => {
        left -= 1;
        prepLabel.textContent = fmt(left);
        $('#bar-timer').textContent = fmt(left);
        if (left <= 0) go();
      }, 1000);
      const go = () => {
        clearInterval(id);
        area.innerHTML = '';
        speak('All right. Remember you have one to two minutes for this. Please start speaking now.');
        renderAnswerControls(area, item, true);
      };
      skip.onclick = go;
      return;
    }

    if (partStart && item.part === 3) speak('We have been talking about a topic. Now I would like to ask you some more general questions related to it.');
    if (item.topic && item.part === 1 && idx > 0) speak(`Now let's talk about ${item.topic.toLowerCase()}.`);
    const bubble = h('div', { class: 'examiner' },
      h('div', { class: 'examiner__avatar', 'aria-hidden': 'true' }, '🧑‍🏫'),
      h('div', { class: 'examiner__bubble' }, item.topic ? h('div', { class: 'notice' }, `Topic: ${item.topic}`) : null, item.text));
    const area = h('div', { class: 'rec' });
    body.append(bubble, h('div', { style: 'text-align:right' }, h('button', { class: 'btn btn--sm btn--ghost', type: 'button', onclick: () => speak(item.text) }, '🔊 Repeat question')), area);
    app.append(h('div', { class: 'full-pane' }, body));
    setTimeout(() => speak(item.text), partStart ? 2500 : 300);
    renderAnswerControls(area, item, false);
  }

  function renderAnswerControls(area, item, autoStart) {
    if (S.speaking.typed) {
      const ta = h('textarea', { class: 'textarea', rows: '5', placeholder: 'Type what you would say…' });
      area.append(ta, h('button', { class: 'btn btn--primary', type: 'button', onclick: () => {
        const text = ta.value.trim();
        S.speaking.answers.push({ part: item.part, question: item.text, text, duration: Math.max(5, (words(text) / 130) * 60) });
        nextSpeakingQuestion();
      } }, 'Next question ▸'));
      return;
    }
    const time = h('div', { class: 'rec__time' }, '00:00');
    const meter = h('div', { class: 'meter' }, h('i'));
    const btn = h('button', { class: 'rec__btn', type: 'button', 'aria-label': 'Start recording' }, '🎤');
    const hint = h('div', { class: 'notice' }, 'Press to start your answer');
    area.append(btn, time, meter, hint);
    const stop = () => stopRecording(false);
    btn.onclick = () => {
      if (rec.active) return stop();
      startRecording(item, time, meter.firstChild);
      btn.classList.add('is-recording');
      btn.textContent = '■';
      btn.setAttribute('aria-label', 'Stop recording');
      hint.textContent = `Recording… press to finish (max ${fmt(MAX_ANSWER[item.part])})`;
    };
    if (autoStart) btn.click();
  }

  function startRecording(item, timeEl, meterEl) {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    rec.ctx = new AudioCtx();
    rec.source = rec.ctx.createMediaStreamSource(rec.stream);
    rec.proc = rec.ctx.createScriptProcessor(4096, 1, 1);
    rec.chunks = [];
    rec.proc.onaudioprocess = (e) => {
      const data = e.inputBuffer.getChannelData(0);
      rec.chunks.push(new Float32Array(data));
      let peak = 0;
      for (let i = 0; i < data.length; i += 64) peak = Math.max(peak, Math.abs(data[i]));
      meterEl.style.width = `${Math.min(100, peak * 160)}%`;
    };
    rec.source.connect(rec.proc);
    rec.proc.connect(rec.ctx.destination);
    rec.started = Date.now();
    rec.active = true;
    const max = MAX_ANSWER[item.part];
    rec.timerId = setInterval(() => {
      const secs = (Date.now() - rec.started) / 1000;
      timeEl.textContent = fmt(secs);
      $('#bar-timer').textContent = fmt(secs);
      if (secs >= max) stopRecording(false);
    }, 250);
    rec.onStop = (wavBlob, duration) => {
      const answer = { part: item.part, question: item.text, text: '', duration };
      S.speaking.answers.push(answer);
      S.speaking.pending.push(transcribe(wavBlob, duration, item.part).then((text) => { answer.text = text; }));
      nextSpeakingQuestion();
    };
  }

  function stopRecording(discard) {
    if (!rec.active) return;
    rec.active = false;
    clearInterval(rec.timerId);
    const duration = (Date.now() - rec.started) / 1000;
    const sampleRate = rec.ctx.sampleRate;
    try { rec.source.disconnect(); rec.proc.disconnect(); rec.ctx.close(); } catch (_) {}
    if (discard) return;
    const wav = encodeWav(rec.chunks, sampleRate, 16000);
    rec.chunks = [];
    if (rec.onStop) rec.onStop(wav, duration);
  }

  function encodeWav(chunks, inRate, outRate) {
    const length = chunks.reduce((n, c) => n + c.length, 0);
    const merged = new Float32Array(length);
    let offset = 0;
    chunks.forEach((c) => { merged.set(c, offset); offset += c.length; });
    const ratio = inRate / outRate;
    const outLen = Math.floor(length / ratio);
    const buffer = new ArrayBuffer(44 + outLen * 2);
    const view = new DataView(buffer);
    const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)); };
    writeStr(0, 'RIFF'); view.setUint32(4, 36 + outLen * 2, true); writeStr(8, 'WAVE'); writeStr(12, 'fmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, outRate, true); view.setUint32(28, outRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    writeStr(36, 'data'); view.setUint32(40, outLen * 2, true);
    for (let i = 0; i < outLen; i++) {
      const start = Math.floor(i * ratio);
      const end = Math.min(length, Math.floor((i + 1) * ratio));
      let sum = 0;
      for (let j = start; j < end; j++) sum += merged[j];
      const s = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)));
      view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([buffer], { type: 'audio/wav' });
  }

  function blobToBase64(blob) {
    return new Promise((resolve) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(',')[1]);
      r.readAsDataURL(blob);
    });
  }

  async function transcribe(blob, duration, part, attempt = 1) {
    try {
      const audioB64 = await blobToBase64(blob);
      const res = await api('/speaking/transcribe', {
        method: 'POST',
        body: JSON.stringify({ audio_base64: audioB64, filename: 'answer.wav', duration_seconds: duration, part_number: part }),
      });
      return res.transcript || '';
    } catch (err) {
      if (attempt < 3 && err.status !== 429) {
        await new Promise((r) => setTimeout(r, 1500 * attempt));
        return transcribe(blob, duration, part, attempt + 1);
      }
      toast(`One answer could not be processed: ${err.message}`, true);
      return '';
    }
  }

  function nextSpeakingQuestion() {
    S.speaking.idx += 1;
    showStaticTimer('00:00', 'answer time');
    setTimeout(renderSpeakingQuestion, 600);
  }

  async function finishSpeaking() {
    speak('Thank you. That is the end of the speaking test.');
    app.innerHTML = '<div class="loading"><div class="spinner"></div>Processing your spoken answers…</div>';
    finishSection(false);
  }

  function speakingPayload() {
    const out = {};
    [1, 2, 3].forEach((p) => {
      const items = S.speaking.answers.filter((a) => a.part === p);
      out[`part_${p}_text`] = items.map((a) => a.text).filter(Boolean).join(' ');
      out[`part_${p}_duration`] = Math.round(items.reduce((n, a) => n + a.duration, 0)) || null;
    });
    return out;
  }

  // ------------------------------------------------------------------ submit & results
  async function submitAll() {
    setExamActive(false);
    setChrome();
    exitFullscreen();
    app.innerHTML = '<div class="loading"><div class="spinner"></div><h3>Scoring your test…</h3><p class="notice">The AI examiner is reading your answers. This usually takes 10–40 seconds.</p></div>';
    const base = { test_id: S.test.id, exam_type: S.test.exam_type, feedback_language: S.lang };
    const writing = {
      task_1_text: S.writing.t1, task_2_text: S.writing.t2,
      task_1_image_base64: S.writing.t1.trim() ? null : S.writing.p1,
      task_2_image_base64: S.writing.t2.trim() ? null : S.writing.p2,
    };
    const mode = S.mode;
    const adPromise = MODES[mode].ai ? showTelegramAd() : Promise.resolve();
    try {
      let result;
      if (mode === 'full') {
        result = await api('/submissions/full-report', { method: 'POST', body: JSON.stringify({
          ...base, ...writing, ...speakingPayload(), candidate_name: S.name,
          listening_answers: S.answers.listening, reading_answers: S.answers.reading,
        }) });
      } else if (mode === 'listening' || mode === 'reading') {
        result = await api('/submissions/objective', { method: 'POST', body: JSON.stringify({ ...base, [`${mode}_answers`]: S.answers[mode] }) });
      } else if (mode === 'writing') {
        result = { writing: await api('/submissions/writing', { method: 'POST', body: JSON.stringify({ ...base, ...writing }) }) };
      } else {
        result = { speaking: await api('/submissions/speaking', { method: 'POST', body: JSON.stringify({ ...base, ...speakingPayload() }) }) };
      }
      await adPromise;
      renderResults(result);
    } catch (err) {
      const retry = await confirmModal('Scoring failed', `${err.message}\n\nYour answers are still here. Try again?`, 'Try again');
      if (retry) submitAll();
      else renderHome();
    }
  }

  const isIelts = () => S.test.exam_type === 'IELTS';
  const to75 = (band) => Math.round((Number(band) / 9) * 750) / 10;

  function scoreCard(label, big, small) {
    return h('div', { class: 'score-card' }, h('div', { class: 'lbl' }, label), h('div', { class: 'big' }, big), small ? h('div', { class: 'notice' }, small) : null);
  }

  function feedbackBlock(title, evaluation, criteria) {
    if (!evaluation) return null;
    const errs = evaluation.detailed_errors || [];
    const vocab = evaluation.band_booster_vocabulary || [];
    return h('section', { class: 'card', style: 'margin-top:16px' },
      h('h3', { style: 'margin-top:0' }, title),
      h('div', { class: 'criteria' }, criteria.map(([label, val]) => h('div', { class: 'crit' }, h('span', {}, label), h('b', {}, Number(val).toFixed(1))))),
      evaluation.fluency_feedback_uz ? h('p', {}, '🗣 ', evaluation.fluency_feedback_uz) : null,
      evaluation.pronunciation_feedback_uz ? h('p', {}, '🔊 ', evaluation.pronunciation_feedback_uz) : null,
      errs.length ? h('h4', {}, 'Mistakes to fix') : null,
      errs.map((e) => h('div', { class: 'err' }, h('s', {}, e.original), ' → ', h('span', { class: 'fix' }, e.correction), h('p', {}, e.explanation_uz))),
      vocab.length ? h('h4', {}, 'Vocabulary upgrades') : null,
      vocab.length ? h('div', { class: 'criteria' }, vocab.map((v) => h('div', { class: 'crit' }, h('span', {}, v.simple_used), h('b', {}, v.advanced_alternative)))) : null);
  }

  function reviewBlock(title, items) {
    if (!items || !items.length) return null;
    return h('details', { class: 'card', style: 'margin-top:16px' },
      h('summary', {}, `${title} — answer review`),
      h('div', { class: 'review-grid', style: 'margin-top:10px' }, items.map((r) => h('div', { class: `review-item ${r.is_correct ? 'ok' : 'bad'}` },
        h('b', {}, `${r.question_id}. `), r.is_correct ? '✓ ' : '✗ ', r.user_answer || '—', r.is_correct ? '' : h('div', {}, `Answer: ${String(r.correct_answer).split('/')[0]}`)))));
  }

  function writingCriteria(w) {
    const c = w.criteria_scores;
    return [[isIelts() ? 'Task Achievement / Response' : 'Task Achievement', c.task_achievement], ['Coherence & Cohesion', c.coherence_cohesion], ['Lexical Resource', c.lexical_resource], ['Grammar', c.grammatical_range_accuracy], ['Task 1', w.task_1_score], ['Task 2', w.task_2_score]];
  }
  function speakingCriteria(s) {
    const c = s.criteria_scores;
    return [['Fluency & Coherence', c.fluency_coherence], ['Lexical Resource', c.lexical_resource], ['Grammar', c.grammatical_range_accuracy], ['Pronunciation', c.pronunciation]];
  }

  function downloadPdf(url, reportId) {
    const abs = new URL(url, location.origin).toString();
    if (IN_TELEGRAM && tg.isVersionAtLeast && tg.isVersionAtLeast('8.0') && tg.downloadFile) {
      try { tg.downloadFile({ url: abs, file_name: `${reportId}.pdf` }); return; } catch (_) {}
    }
    if (IN_TELEGRAM && tg.openLink) { tg.openLink(abs); return; }
    window.open(abs, '_blank', 'noopener');
  }

  function renderResults(result) {
    loadQuota();
    app.innerHTML = '';
    const wrap = h('div', { class: 'results' },
      h('div', { class: 'hero' }, h('span', { class: 'logo-dot' }, 'AI'), h('div', {}, h('h1', {}, 'Your results'), h('p', {}, `${S.test.title} · ${S.name}`))));
    const hero = h('div', { class: 'score-hero' });
    wrap.append(hero);

    if (S.mode === 'full') {
      const sc = result.scores;
      if (isIelts()) hero.append(scoreCard('Overall band', Number(sc.overall_band).toFixed(1), `CEFR ${sc.cefr_level.replace('BELOW_B1', 'below B1')}`));
      else hero.append(scoreCard('Overall (0–75)', Number(sc.overall_score_75).toFixed(1), `Level ${sc.cefr_level.replace('BELOW_B1', 'below B1')}`));
      [['Listening', sc.listening_band, sc.listening_score_75, `${sc.listening_raw}/40`], ['Reading', sc.reading_band, sc.reading_score_75, `${sc.reading_raw}/40`], ['Writing', sc.writing_band, sc.writing_score_75], ['Speaking', sc.speaking_band, sc.speaking_score_75]]
        .forEach(([label, band, s75, raw]) => hero.append(scoreCard(label, isIelts() ? Number(band).toFixed(1) : Number(s75).toFixed(1), raw || (isIelts() ? '' : '/ 75'))));
      wrap.append(h('div', { class: 'row card' },
        h('div', {}, h('strong', {}, '📄 PDF report'), h('div', { class: 'notice' }, result.sent_to_telegram ? 'We also sent it to your chat with the bot.' : 'Download and keep your detailed report.')),
        h('button', { class: 'btn btn--primary', type: 'button', onclick: () => downloadPdf(result.download_url, result.report_id) }, 'Download PDF')));
      const rd = result.report_data || {};
      add(wrap, feedbackBlock('✍️ Writing feedback', rd.writing_evaluation, rd.writing_evaluation ? writingCriteria(rd.writing_evaluation) : []));
      add(wrap, feedbackBlock('🎙 Speaking feedback', rd.speaking_evaluation, rd.speaking_evaluation ? speakingCriteria(rd.speaking_evaluation) : []));
      const review = result.objective_review || {};
      add(wrap, reviewBlock('🎧 Listening', review.listening), reviewBlock('📖 Reading', review.reading));
    } else if (S.mode === 'listening' || S.mode === 'reading') {
      const r = result[S.mode];
      hero.append(
        scoreCard('Correct answers', `${r.correct_count}/40`),
        isIelts() ? scoreCard('Band', Number(r.band_score).toFixed(1)) : scoreCard('Score (0–75)', Number(r.cefr_standard_score).toFixed(1)),
        scoreCard('CEFR', String(r.cefr_level).replace('BELOW_B1', 'below B1')));
      add(wrap, reviewBlock(S.mode === 'listening' ? '🎧 Listening' : '📖 Reading', r.question_results));
    } else if (S.mode === 'writing') {
      const w = result.writing;
      hero.append(scoreCard('Writing', isIelts() ? Number(w.overall_writing_score).toFixed(1) : to75(w.overall_writing_score).toFixed(1), isIelts() ? 'band' : '/ 75'), scoreCard('CEFR', w.cefr_level.replace('BELOW_B1', 'below B1')));
      add(wrap, feedbackBlock('✍️ Writing feedback', w, writingCriteria(w)));
    } else {
      const s = result.speaking;
      hero.append(scoreCard('Speaking', isIelts() ? Number(s.overall_speaking_score).toFixed(1) : Number(s.standard_score_75).toFixed(1), isIelts() ? 'band' : '/ 75'), scoreCard('CEFR', s.cefr_level.replace('BELOW_B1', 'below B1')));
      add(wrap, feedbackBlock('🎙 Speaking feedback', s, speakingCriteria(s)));
    }

    add(wrap, adSlot());
    wrap.append(h('div', { class: 'start-row', style: 'margin-top:20px' },
      h('span', { class: 'notice' }, 'This is an unofficial AI estimate, not an official IELTS or CEFR result.'),
      h('button', { class: 'btn btn--primary', type: 'button', onclick: async () => { await loadQuota(); renderHome(); } }, 'Take another test')));
    app.append(wrap);
    window.scrollTo(0, 0);
  }

  // ------------------------------------------------------------------ boot
  async function boot() {
    applyTheme(storage('mock_theme') || ((tg && tg.colorScheme === 'dark') || window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
    S.name = storage('mock_name') || '';
    S.lang = storage('mock_lang') || 'uz';
    initTelegram();
    const params = new URLSearchParams(location.search);
    if (params.get('exam_type') === 'CEFR') S.examType = 'CEFR';
    if ('serviceWorker' in navigator && !IN_TELEGRAM) navigator.serviceWorker.register('sw.js').catch(() => {});
    renderHome();
    try { S.config = await api('/config'); } catch (_) {}
    await loadQuota();
    if (!S.inExam) renderHome();
  }

  document.addEventListener('DOMContentLoaded', boot);
})();
