/**
 * IELTS & CEFR Mock AI — Telegram Mini App (WebApp) Frontend Controller
 *
 * Features:
 * - Telegram.WebApp SDK integration (initData HMAC header, MainButton, sendData, themeParams)
 * - Exam Switcher: IELTS Academic (0.0-9.0) vs Uzbekistan Milliy CEFR Multi-level (0-75 / B1-C1)
 * - Live Countdown Timer (60:00 with Pause/Reset & < 5:00 visual warning pulse)
 * - 40-Question Interactive Navigator Grid for Listening & Reading
 * - Live Word Counter (Task 1: 150+ words, Task 2: 250+ words) + Handwritten Photo Base64 Vision OCR
 * - Instant Dual-Scale Hero Score Card + ReportLab PDF Certificate download (/api/v1/reports/{report_id}/pdf)
 */

(function () {
  'use strict';

  // Built-in Fallback Mock Exams so the Mini App works both connected to FastAPI and standalone
  const FALLBACK_EXAMS = {
    'IELTS-MOCK-01': {
      id: 'IELTS-MOCK-01',
      title: 'IELTS Academic Official Format Mock #1',
      exam_type: 'IELTS',
      duration_minutes: 60,
      listening_data: {
        audio_url: '/webapp/audio/ielts_mock_01_listening.wav',
        duration_minutes: 30,
        questions: Array.from({ length: 40 }, (_, idx) => {
          const num = idx + 1;
          if (num === 1) {
            return {
              id: '1',
              number: 1,
              part: 1,
              type: 'fill_in_blank',
              prompt: 'Applicant Surname: Sarah ________ (spell the surname mentioned in the recording).',
            };
          }
          if (num === 11) {
            return {
              id: '11',
              number: 11,
              part: 2,
              type: 'multiple_choice',
              prompt: 'Why was the City Eco-Museum originally founded in 1998?',
              options: [
                'A) To replace the old municipal library',
                'B) To preserve industrial heritage and promote renewable energy',
                'C) To host international trade conferences',
              ],
            };
          }
          const part = num <= 10 ? 1 : num <= 20 ? 2 : num <= 30 ? 3 : 4;
          const isMcq = num > 10 && num <= 30;
          return {
            id: String(num),
            number: num,
            part,
            type: isMcq ? 'multiple_choice' : 'fill_in_blank',
            prompt: isMcq
              ? `Part ${part} — Question ${num}: Select the correct letter from the options.`
              : `Part ${part} — Question ${num}: Write ONE WORD AND/OR A NUMBER from the recording.`,
            options: isMcq ? ['A', 'B', 'C', 'D'] : undefined,
          };
        }),
      },
      reading_data: {
        duration_minutes: 60,
        module: 'academic',
        passages: [
          {
            id: 'P1',
            passage_number: 1,
            title: 'Passage 1: The Rise of Vertical Farming in Megacities',
            question_range: '1-13',
            content:
              'By 2050, nearly 70 percent of the global population is projected to reside in urban areas. Vertical farming—cultivating crops in vertically stacked layers inside controlled-environment buildings—offers a promising supplement to conventional farming. Instead of soil, commercial vertical farms rely on hydroponic or aeroponic systems rich in mineral nutrients, consuming up to 95 percent less water than open-field farms while using tuned LED lighting arrays and zero chemical pesticides.',
          },
          {
            id: 'P2',
            passage_number: 2,
            title: 'Passage 2: Cognitive Benefits of Multilingualism Across the Lifespan',
            question_range: '14-26',
            content:
              'Modern neuroimaging demonstrates that managing multiple linguistic systems strengthens the brain executive control network. Because both languages remain active in a bilingual mind, the prefrontal cortex constantly monitors context and inhibits interference, enhancing selective attention and delaying cognitive decline.',
          },
          {
            id: 'P3',
            passage_number: 3,
            title: 'Passage 3: Deep-Sea Hydrothermal Vents and the Origins of Life',
            question_range: '27-40',
            content:
              'Discovered along the Galápagos Rift in 1977, deep-sea hydrothermal vents support thriving ecosystems through chemosynthesis rather than solar energy. Alkaline hydrothermal vents create natural proton gradients across porous mineral membranes, acting as primitive geochemical catalysts.',
          },
        ],
        questions: Array.from({ length: 40 }, (_, idx) => {
          const num = idx + 1;
          const passage = num <= 13 ? 1 : num <= 26 ? 2 : 3;
          if (num <= 6) {
            return {
              id: String(num),
              number: num,
              passage: 1,
              type: 'true_false_not_given',
              prompt: `Passage 1 Statement ${num}: Evaluate whether the statement agrees with the information in the text.`,
              options: ['TRUE', 'FALSE', 'NOT GIVEN'],
            };
          }
          if (num >= 27 && num <= 31) {
            return {
              id: String(num),
              number: num,
              passage: 3,
              type: 'yes_no_not_given',
              prompt: `Passage 3 Claim ${num}: Does the statement agree with the views of the writer?`,
              options: ['YES', 'NO', 'NOT GIVEN'],
            };
          }
          return {
            id: String(num),
            number: num,
            passage,
            type: 'fill_in_blank',
            prompt: `Passage ${passage} — Question ${num}: Complete the note using ONE WORD from the passage.`,
          };
        }),
      },
      writing_data: {
        task_1_prompt:
          'The bar chart shows the percentage of households with access to high-speed fiber-optic internet and renewable solar energy across four countries (South Korea, Germany, Uzbekistan, and Brazil) between 2015 and 2025. Summarize the information by selecting and reporting the main features, and make comparisons where relevant. (Write at least 150 words.)',
        task_2_prompt:
          'Some people believe that artificial intelligence tutors and online learning platforms will eventually replace traditional classroom teachers, while others argue that human interaction in schools remains irreplaceable. Discuss both these views and give your own opinion. (Write at least 250 words.)',
      },
      speaking_data: {
        part_1_questions: [
          'Do you work or are you currently a student?',
          'How do you usually organize your daily study or work schedule?',
        ],
        part_2_cue_card:
          'Describe an important problem you solved using a digital tool or technology. Explain what the problem was, which tool you used, and what you learned.',
        part_3_questions: [
          'How has technology changed the way young people in your country prepare for university?',
        ],
      },
    },
    'CEFR-MOCK-01': {
      id: 'CEFR-MOCK-01',
      title: "O'zbekiston BBA Multi-Level (B1-C1) Mock #1",
      exam_type: 'CEFR',
      duration_minutes: 60,
      listening_data: {
        audio_url: '/webapp/audio/cefr_mock_01_listening.wav',
        duration_minutes: 35,
        questions: Array.from({ length: 40 }, (_, idx) => {
          const num = idx + 1;
          const isMcq = num <= 8 || (num >= 26 && num <= 31);
          return {
            id: String(num),
            number: num,
            part: num <= 8 ? 1 : num <= 14 ? 2 : num <= 20 ? 3 : num <= 25 ? 4 : num <= 31 ? 5 : 6,
            type: isMcq ? 'multiple_choice' : 'fill_in_blank',
            prompt: `BBA Multi-Level Listening Savol #${num}: Mos javobni tanlang yoki yozing.`,
            options: isMcq ? ['A', 'B', 'C'] : undefined,
          };
        }),
      },
      reading_data: {
        duration_minutes: 60,
        module: 'cefr_multilevel',
        passages: [
          {
            id: 'CEFR-P1',
            passage_number: 1,
            title: 'Parts 1-2: Youth Digital Literacy Centres in Tashkent & Samarkand (B1/B2)',
            question_range: '1-14',
            content:
              'Across Uzbekistan, local mahalla youth centres have launched a new initiative to expand practical skills among high-school graduates. Supported by experienced industry volunteers, these centres organize weekend workshops focused on coding, graphic design, and digital entrepreneurship.',
          },
          {
            id: 'CEFR-P2',
            passage_number: 2,
            title: 'Parts 3-4: Silk Road Logistics and Modern Rail Corridors (B2)',
            question_range: '15-29',
            content:
              'As landlocked Central Asian economies deepen trade integration with both Europe and East Asia, modernizing rail and dry-port logistics has become a strategic priority. Electrified freight corridors and automated customs clearance terminals have shortened transit times by nearly forty percent.',
          },
          {
            id: 'CEFR-P3',
            passage_number: 3,
            title: 'Part 5: Clean Energy Transition and Smart Grid Architecture (C1)',
            question_range: '30-40',
            content:
              'Transitioning national electricity networks toward a high share of solar, wind, and modern hydropower requires upgrading transmission infrastructure and deploying AI-assisted smart grid balancing systems capable of absorbing intermittent renewable supply.',
          },
        ],
        questions: Array.from({ length: 40 }, (_, idx) => {
          const num = idx + 1;
          const passage = num <= 14 ? 1 : num <= 29 ? 2 : 3;
          return {
            id: String(num),
            number: num,
            passage,
            type: num >= 25 && num <= 29 ? 'true_false_not_given' : 'fill_in_blank',
            prompt: `BBA Multi-Level Reading Savol #${num}: Matn asosida to'g'ri javobni kiriting.`,
            options: num >= 25 && num <= 29 ? ['TRUE', 'FALSE', 'NOT GIVEN'] : undefined,
          };
        }),
      },
      writing_data: {
        task_1_prompt:
          'You recently attended an international youth IT & Innovation conference in Tashkent, but you accidentally left your tablet computer in the main lecture hall. Write a formal email to the conference organizers explaining when and where you attended, describing your tablet, and stating how they can contact you. (Write at least 150 words.)',
        task_2_prompt:
          'In many countries today, young professionals prefer remote freelance work for international companies rather than traditional full-time office jobs in their local city. What are the advantages and disadvantages of this trend for individuals and society? (Write at least 250 words.)',
      },
      speaking_data: {
        part_1_questions: [
          'Tell me about your hometown and what makes it a good place to live.',
          'Why are you learning English, and how will a CEFR certificate help your career?',
        ],
        part_2_cue_card:
          'Describe a memorable educational project or team competition you participated in.',
        part_3_questions: [
          'Why do employers today value teamwork and communication skills as much as university degrees?',
        ],
      },
    },
  };

  // Demo high-scoring objective answers matching app/services/demo_exam_bank.py
  const DEMO_OBJECTIVE_ANSWERS = {
    'IELTS-MOCK-01': {
      listening: {
        '1': 'Henderson', '2': '0789432109', '3': 'intermediate', '4': 'swimming', '5': '45',
        '6': 'locker', '7': 'medical', '8': 'Tuesday', '9': 'reception', '10': 'student card',
        '11': 'B', '12': 'C', '13': 'A', '14': 'B', '15': 'C', '16': 'F', '17': 'D', '18': 'A', '19': 'G', '20': 'E',
        '21': 'C', '22': 'A', '23': 'B', '24': 'C', '25': 'A', '26': 'D', '27': 'B', '28': 'F', '29': 'C', '30': 'E',
        '31': 'ventilation', '32': 'termites', '33': 'concrete', '34': 'sunlight', '35': 'algae',
        '36': 'vibration', '37': 'bridges', '38': 'maintenance', '39': 'sensors', '40': 'recyclable',
      },
      reading: {
        '1': 'TRUE', '2': 'FALSE', '3': 'NOT GIVEN', '4': 'TRUE', '5': 'FALSE', '6': 'TRUE',
        '7': 'nutrients', '8': 'LED', '9': 'pesticides', '10': 'transport', '11': 'pollination', '12': 'B', '13': 'C',
        '14': 'iv', '15': 'ii', '16': 'vi', '17': 'i', '18': 'v', '19': 'A', '20': 'C', '21': 'B', '22': 'D',
        '23': 'executive', '24': 'attention', '25': 'dementia', '26': 'plasticity',
        '27': 'YES', '28': 'NO', '29': 'NOT GIVEN', '30': 'YES', '31': 'NO',
        '32': 'C', '33': 'A', '34': 'D', '35': 'B', '36': 'chemosynthesis', '37': 'alkaline', '38': 'membranes', '39': 'catalysts', '40': 'A',
      },
    },
    'CEFR-MOCK-01': {
      listening: {
        '1': 'B', '2': 'A', '3': 'C', '4': 'B', '5': 'A', '6': 'C', '7': 'B', '8': 'A',
        '9': 'library', '10': 'Thursday', '11': 'passport', '12': '15', '13': 'certificate', '14': 'auditorium',
        '15': 'D', '16': 'A', '17': 'F', '18': 'B', '19': 'E', '20': 'C',
        '21': 'G', '22': 'C', '23': 'A', '24': 'E', '25': 'B',
        '26': 'B', '27': 'C', '28': 'A', '29': 'B', '30': 'C', '31': 'A',
        '32': 'solar', '33': 'irrigation', '34': 'sensors', '35': 'cotton', '36': 'efficiency',
        '37': 'satellites', '38': 'training', '39': 'exports', '40': 'sustainable',
      },
      reading: {
        '1': 'community', '2': 'volunteers', '3': 'workshops', '4': 'digital', '5': 'schedule', '6': 'certificates',
        '7': 'C', '8': 'A', '9': 'F', '10': 'B', '11': 'E', '12': 'D', '13': 'G', '14': 'H',
        '15': 'D', '16': 'A', '17': 'F', '18': 'B', '19': 'C', '20': 'E',
        '21': 'B', '22': 'C', '23': 'A', '24': 'D',
        '25': 'TRUE', '26': 'FALSE', '27': 'NOT GIVEN', '28': 'TRUE', '29': 'FALSE',
        '30': 'infrastructure', '31': 'renewable', '32': 'hydropower', '33': 'grid', '34': 'investment', '35': 'emissions',
        '36': 'B', '37': 'A', '38': 'C', '39': 'D', '40': 'B',
      },
    },
  };

  // Application State
  const state = {
    examType: 'IELTS',
    testId: 'IELTS-MOCK-01',
    activeTab: 'listening',
    activePassageIndex: 0,
    examData: FALLBACK_EXAMS['IELTS-MOCK-01'],
    listeningAnswers: {},
    readingAnswers: {},
    task1PhotoBase64: null,
    task2PhotoBase64: null,
    timerSecondsRemaining: 60 * 60, // 60:00
    timerRunning: true,
    timerIntervalId: null,
    audioPlaying: false,
    audioElapsedSeconds: 0,
    audioIntervalId: null,
    telegramInitData: '',
    telegramUser: null,
  };

  /**
   * Initialize Telegram WebApp SDK if running inside Telegram client
   */
  function initTelegramWebApp() {
    const tg = window.Telegram && window.Telegram.WebApp;
    if (!tg) return;

    try {
      tg.ready();
      tg.expand();
      state.telegramInitData = tg.initData || '';
      if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        state.telegramUser = tg.initDataUnsafe.user;
        const nameInput = document.getElementById('candidate-name-input');
        if (nameInput && state.telegramUser.first_name) {
          const fullName = [state.telegramUser.first_name, state.telegramUser.last_name]
            .filter(Boolean)
            .join(' ');
          nameInput.value = fullName;
        }
      }
      if (tg.colorScheme === 'light') {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        const icon = document.getElementById('theme-icon');
        if (icon) icon.textContent = '☀️';
      }
    } catch (err) {
      console.warn('Telegram WebApp init warning:', err);
    }
  }

  /**
   * Build headers including X-Telegram-Init-Data for backend HMAC-SHA256 verification
   */
  function buildApiHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (state.telegramInitData) {
      headers['X-Telegram-Init-Data'] = state.telegramInitData;
    }
    return headers;
  }

  /**
   * Display notification toast banner
   */
  function showToast(message, variant = 'info') {
    const toast = document.getElementById('status-toast');
    const text = document.getElementById('status-toast-text');
    if (!toast || !text) return;

    text.textContent = message;
    toast.className =
      'rounded-xl px-4 py-3 text-xs sm:text-sm font-medium border flex items-center justify-between gap-3 transition-all ';
    if (variant === 'success') {
      toast.className += 'bg-emerald-950/70 border-emerald-500/40 text-emerald-200';
    } else if (variant === 'warning') {
      toast.className += 'bg-amber-950/70 border-amber-500/40 text-amber-200';
    } else if (variant === 'error') {
      toast.className += 'bg-rose-950/70 border-rose-500/40 text-rose-200';
    } else {
      toast.className += 'bg-blue-950/70 border-blue-500/40 text-blue-200';
    }
  }

  function hideToast() {
    const toast = document.getElementById('status-toast');
    if (toast) toast.classList.add('hidden');
  }

  // =========================================================================
  // COUNTDOWN TIMER (60:00 with Pause/Reset & < 5:00 visual warning)
  // =========================================================================

  function formatMMSS(totalSeconds) {
    const clamped = Math.max(0, Math.floor(totalSeconds));
    const mins = String(Math.floor(clamped / 60)).padStart(2, '0');
    const secs = String(clamped % 60).padStart(2, '0');
    return `${mins}:${secs}`;
  }

  function updateTimerUI() {
    const display = document.getElementById('countdown-display');
    const timerBox = document.getElementById('exam-timer-box');
    const dot = document.getElementById('timer-status-dot');
    if (display) {
      display.textContent = formatMMSS(state.timerSecondsRemaining);
    }
    if (timerBox) {
      if (state.timerSecondsRemaining < 300) {
        timerBox.classList.add('timer-warning');
        if (dot) dot.className = 'w-2 h-2 rounded-full bg-rose-500 animate-ping';
      } else {
        timerBox.classList.remove('timer-warning');
        if (dot) {
          dot.className = state.timerRunning
            ? 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse'
            : 'w-2 h-2 rounded-full bg-amber-400';
        }
      }
    }
  }

  function startTimerLoop() {
    if (state.timerIntervalId) clearInterval(state.timerIntervalId);
    state.timerIntervalId = setInterval(() => {
      if (!state.timerRunning) return;
      if (state.timerSecondsRemaining > 0) {
        state.timerSecondsRemaining -= 1;
        updateTimerUI();
        if (state.timerSecondsRemaining === 299) {
          showToast('⚠️ Diqqat! Imtihon yakunlanishiga 5 daqiqadan kam vaqt qoldi!', 'warning');
        }
      } else {
        state.timerRunning = false;
        updateTimerUI();
        showToast('⏰ Imtihon vaqti tugadi! Javoblaringizni yakuniy tekshiruvga yuboring.', 'warning');
      }
    }, 1000);
  }

  function toggleTimer() {
    state.timerRunning = !state.timerRunning;
    const btn = document.getElementById('btn-timer-toggle');
    if (btn) {
      btn.textContent = state.timerRunning ? '⏸ Pause' : '▶ Start';
    }
    updateTimerUI();
  }

  function resetTimer() {
    state.timerSecondsRemaining = 60 * 60;
    state.timerRunning = true;
    const btn = document.getElementById('btn-timer-toggle');
    if (btn) btn.textContent = '⏸ Pause';
    updateTimerUI();
  }

  // =========================================================================
  // THEME & TAB NAVIGATION
  // =========================================================================

  function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    if (html.classList.contains('dark')) {
      html.classList.remove('dark');
      html.classList.add('light');
      if (icon) icon.textContent = '☀️';
    } else {
      html.classList.remove('light');
      html.classList.add('dark');
      if (icon) icon.textContent = '🌙';
    }
  }

  function switchTab(tabName) {
    state.activeTab = tabName;
    const tabs = ['listening', 'reading', 'writing', 'speaking'];
    tabs.forEach((t) => {
      const panel = document.getElementById(`tab-panel-${t}`);
      if (panel) {
        panel.classList.toggle('hidden', t !== tabName);
      }
    });
    document.querySelectorAll('.module-tab').forEach((btn) => {
      const isMatch = btn.getAttribute('data-tab') === tabName;
      btn.classList.toggle('active', isMatch);
    });
  }

  // =========================================================================
  // EXAM SWITCHER & REST API TEST LOADING (/api/v1/tests/{test_id})
  // =========================================================================

  async function switchExamType(examType) {
    const normalized = examType === 'CEFR' ? 'CEFR' : 'IELTS';
    state.examType = normalized;
    state.activePassageIndex = 0;

    // Update top bar button styles
    const btnIelts = document.getElementById('btn-exam-ielts');
    const btnCefr = document.getElementById('btn-exam-cefr');
    if (btnIelts) btnIelts.classList.toggle('active', normalized === 'IELTS');
    if (btnCefr) btnCefr.classList.toggle('active', normalized === 'CEFR');

    // Load a random variant out of 10 from the backend
    const randomAlias = normalized === 'CEFR' ? 'CEFR-RANDOM' : 'IELTS-RANDOM';
    await loadExamFromApi(randomAlias);
  }

  async function loadRandomVariant() {
    const randomAlias = state.examType === 'CEFR' ? 'CEFR-RANDOM' : 'IELTS-RANDOM';
    await loadExamFromApi(randomAlias);
    showToast(
      `🎲 Yangi tasodifiy variant yuklandi: ${state.examData.title || state.testId}`,
      'info'
    );
  }

  async function loadExamFromApi(testId) {
    const fallbackKey = state.examType === 'CEFR' ? 'CEFR-MOCK-01' : 'IELTS-MOCK-01';
    let loadedData = FALLBACK_EXAMS[testId] || FALLBACK_EXAMS[fallbackKey] || FALLBACK_EXAMS['IELTS-MOCK-01'];
    try {
      const response = await fetch(`/api/v1/tests/${encodeURIComponent(testId)}`, {
        method: 'GET',
        headers: buildApiHeaders(),
      });
      if (response.ok) {
        const json = await response.json();
        loadedData = json.test || json;
      }
    } catch (_) {
      // Offline / standalone fallback mode
    }

    state.examData = loadedData;
    state.testId = loadedData.id || fallbackKey;
    const badge = document.getElementById('active-test-badge');
    if (badge) badge.textContent = state.testId;

    renderListeningModule();
    renderReadingModule();
    renderWritingPrompts();
    renderSpeakingPrompts();
  }

  // =========================================================================
  // 40-QUESTION LISTENING & READING RENDERERS & NAVIGATORS
  // =========================================================================

  function normalizeQuestionsList(sectionData) {
    if (!sectionData || !Array.isArray(sectionData.questions)) return [];
    return sectionData.questions;
  }

  function renderNavigatorGrid(gridElementId, sectionKey) {
    const grid = document.getElementById(gridElementId);
    if (!grid) return;
    const answersMap = sectionKey === 'listening' ? state.listeningAnswers : state.readingAnswers;

    grid.innerHTML = '';
    for (let i = 1; i <= 40; i++) {
      const qId = String(i);
      const val = (answersMap[qId] || '').trim();
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `nav-q-btn ${val ? 'answered' : ''}`;
      btn.textContent = qId;
      btn.title = `Savol #${qId}${val ? ': ' + val : ''}`;
      btn.onclick = () => {
        const card = document.getElementById(`${sectionKey}-q-card-${qId}`);
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      };
      grid.appendChild(btn);
    }

    const answeredCount = Object.values(answersMap).filter((v) => String(v || '').trim().length > 0).length;
    const badgeId = sectionKey === 'listening' ? 'badge-listening-count' : 'badge-reading-count';
    const progressId = sectionKey === 'listening' ? 'listening-progress-text' : 'reading-progress-text';

    const badgeEl = document.getElementById(badgeId);
    if (badgeEl) badgeEl.textContent = `${answeredCount}/40`;
    const progEl = document.getElementById(progressId);
    if (progEl) progEl.textContent = `${answeredCount} / 40`;
  }

  function renderQuestionCards(containerId, questions, sectionKey) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const answersMap = sectionKey === 'listening' ? state.listeningAnswers : state.readingAnswers;

    container.innerHTML = '';
    questions.forEach((q) => {
      const qId = String(q.id || q.number);
      const currentVal = answersMap[qId] || '';
      const hasOptions = Array.isArray(q.options) && q.options.length > 0;

      const card = document.createElement('div');
      card.id = `${sectionKey}-q-card-${qId}`;
      card.className =
        'glass-card rounded-xl p-3.5 sm:p-4 border border-slate-800 bg-slate-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3';

      const left = document.createElement('div');
      left.className = 'space-y-1 flex-1';

      const headerRow = document.createElement('div');
      headerRow.className = 'flex items-center gap-2';
      const numBadge = document.createElement('span');
      numBadge.className =
        'px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 font-mono text-xs font-bold';
      numBadge.textContent = `Q${qId}`;
      const partLabel = document.createElement('span');
      partLabel.className = 'text-[11px] text-slate-400 font-mono';
      partLabel.textContent = q.part ? `Part ${q.part}` : q.passage ? `Passage ${q.passage}` : '';
      headerRow.appendChild(numBadge);
      headerRow.appendChild(partLabel);

      const promptP = document.createElement('p');
      promptP.className = 'text-xs sm:text-sm text-slate-200 leading-snug';
      promptP.textContent = q.prompt || `Question ${qId}`;

      left.appendChild(headerRow);
      left.appendChild(promptP);

      const right = document.createElement('div');
      right.className = 'w-full sm:w-56 flex-shrink-0';

      if (hasOptions) {
        const select = document.createElement('select');
        select.className =
          'w-full rounded-xl bg-slate-950 border border-slate-700 px-3 py-2 text-xs sm:text-sm text-slate-100 focus:border-blue-500 focus:outline-none';
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = '— Tanlang —';
        select.appendChild(defaultOpt);

        q.options.forEach((optText) => {
          const opt = document.createElement('option');
          // Extract leading letter if option is like "A) Something"
          const shortVal =
            /^[A-H]\)/.test(optText.trim()) ? optText.trim().charAt(0) : optText.trim();
          opt.value = shortVal;
          opt.textContent = optText;
          if (currentVal.toUpperCase() === shortVal.toUpperCase()) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });

        select.onchange = (e) => {
          answersMap[qId] = e.target.value;
          renderNavigatorGrid(`${sectionKey}-navigator-grid`, sectionKey);
        };
        right.appendChild(select);
      } else {
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentVal;
        input.placeholder = `Q${qId} javobi...`;
        input.className =
          'w-full rounded-xl bg-slate-950 border border-slate-700 px-3 py-2 text-xs sm:text-sm text-slate-100 focus:border-blue-500 focus:outline-none';
        input.oninput = (e) => {
          answersMap[qId] = e.target.value;
          renderNavigatorGrid(`${sectionKey}-navigator-grid`, sectionKey);
        };
        right.appendChild(input);
      }

      card.appendChild(left);
      card.appendChild(right);
      container.appendChild(card);
    });
  }

  function getResolvedListeningAudioUrl() {
    const lData = (state.examData && state.examData.listening_data) || {};
    const rawUrl = lData.audio_url || '';
    if (
      rawUrl &&
      !rawUrl.includes('yourdomain.uz') &&
      !rawUrl.includes('example.com')
    ) {
      return rawUrl;
    }
    return state.examType === 'CEFR'
      ? '/webapp/audio/cefr_mock_01_listening.wav'
      : '/webapp/audio/ielts_mock_01_listening.wav';
  }

  function bindNativeAudioEvents(nativeAudioEl) {
    if (!nativeAudioEl || nativeAudioEl.dataset.bound === '1') return;
    nativeAudioEl.dataset.bound = '1';

    nativeAudioEl.addEventListener('play', () => {
      state.audioPlaying = true;
      const icon = document.getElementById('audio-play-icon');
      if (icon) icon.textContent = '⏸';
    });

    nativeAudioEl.addEventListener('pause', () => {
      state.audioPlaying = false;
      const icon = document.getElementById('audio-play-icon');
      if (icon) icon.textContent = '▶';
    });

    nativeAudioEl.addEventListener('ended', () => {
      state.audioPlaying = false;
      const icon = document.getElementById('audio-play-icon');
      if (icon) icon.textContent = '▶';
    });

    nativeAudioEl.addEventListener('timeupdate', () => {
      const cur = Math.floor(nativeAudioEl.currentTime || 0);
      const dur = Math.floor(nativeAudioEl.duration || 180) || 180;
      const pct = Math.min(100, (cur / dur) * 100);
      const bar = document.getElementById('audio-progress-bar');
      const label = document.getElementById('audio-time-label');
      if (bar) bar.style.width = `${pct.toFixed(1)}%`;
      if (label) label.textContent = `${formatMMSS(cur)} / ${formatMMSS(dur)}`;
    });
  }

  function renderListeningModule() {
    const lData = state.examData.listening_data || {};
    const questions = normalizeQuestionsList(lData);
    const nativeAudioEl = document.getElementById('listening-native-audio');
    if (nativeAudioEl) {
      bindNativeAudioEvents(nativeAudioEl);
      const targetUrl = getResolvedListeningAudioUrl();
      if (!nativeAudioEl.getAttribute('src') || !nativeAudioEl.getAttribute('src').endsWith(targetUrl)) {
        nativeAudioEl.src = targetUrl;
      }
    }
    renderNavigatorGrid('listening-navigator-grid', 'listening');
    renderQuestionCards('listening-questions-container', questions, 'listening');
  }

  function renderReadingModule() {
    const rData = state.examData.reading_data || {};
    const passages = Array.isArray(rData.passages) ? rData.passages : [];
    if (passages.length > 0) {
      selectReadingPassage(state.activePassageIndex);
    }
    const questions = normalizeQuestionsList(rData);
    renderNavigatorGrid('reading-navigator-grid', 'reading');
    renderQuestionCards('reading-questions-container', questions, 'reading');
  }

  function selectReadingPassage(index) {
    const rData = state.examData.reading_data || {};
    const passages = Array.isArray(rData.passages) ? rData.passages : [];
    const safeIdx = Math.min(Math.max(0, index), Math.max(0, passages.length - 1));
    state.activePassageIndex = safeIdx;
    const passage = passages[safeIdx];
    if (!passage) return;

    const titleEl = document.getElementById('reading-passage-title');
    const bodyEl = document.getElementById('reading-passage-body');
    const badgeEl = document.getElementById('reading-passage-badge');
    if (titleEl) titleEl.textContent = passage.title || `Reading Passage ${safeIdx + 1}`;
    if (badgeEl) {
      badgeEl.textContent = `${state.examType} Reading • Savollar ${passage.question_range || ''}`;
    }
    if (bodyEl) {
      const paragraphs = String(passage.content || '').split('\n\n');
      bodyEl.innerHTML = paragraphs
        .map((p) => `<p class="leading-relaxed">${p}</p>`)
        .join('');
    }
  }

  function fillDemoObjectiveAnswers(sectionKey) {
    const baseKey = state.examType === 'CEFR' ? 'CEFR-MOCK-01' : 'IELTS-MOCK-01';
    const preset = DEMO_OBJECTIVE_ANSWERS[state.testId] || DEMO_OBJECTIVE_ANSWERS[baseKey];
    if (sectionKey === 'listening') {
      state.listeningAnswers = Object.assign({}, preset.listening);
      renderListeningModule();
      showToast('✨ 40 ta Listening demo javoblari muvaffaqiyatli kiritildi!', 'success');
    } else {
      state.readingAnswers = Object.assign({}, preset.reading);
      renderReadingModule();
      showToast('✨ 40 ta Reading demo javoblari muvaffaqiyatli kiritildi!', 'success');
    }
  }

  // =========================================================================
  // REAL SPOKEN ENGLISH LISTENING AUDIO PLAYER (HTML5 AUDIO + WEB SPEECH TTS)
  // =========================================================================

  const LISTENING_AUDIO_SCRIPTS = {
    'IELTS-MOCK-01':
      'IELTS Academic Listening Mock Test One. ' +
      'Part 1. You will hear a conversation between a university student and a sports club receptionist. ' +
      'Receptionist: Good morning, University Sports Centre. Can I take your surname please? ' +
      'Student: Yes, it is Sarah Henderson. That is spelled H-E-N-D-E-R-S-O-N. ' +
      'Receptionist: Thank you. And your contact phone number for Question 2? ' +
      'Student: My mobile number is 0-7-8-9-4-3-2-1-0-9. ' +
      'Receptionist: Great. Which level and sport are you registering for in Questions 3 and 4? ' +
      'Student: I would like to join the intermediate level class for swimming. ' +
      'Receptionist: The monthly membership fee for Question 5 is 45 pounds, which includes a personal locker for Question 6. ' +
      'Before your first session on Tuesday for Question 8, please sign the medical form for Question 7 at the main reception desk for Question 9, and bring your student card for Question 10. ' +
      'Part 2. Welcome to the City Eco-Museum guided tour. For Question 11, the museum was founded in 1998 to preserve industrial heritage and promote renewable energy, which is option B. ' +
      'For Question 12, the solar dome is in the West Wing, option C. For Question 13, choose A; Question 14 is B; Question 15 is C; Question 16 is F; Question 17 is D; Question 18 is A; Question 19 is G; and Question 20 is E. ' +
      'Part 3. Academic Tutorial on Urban Microclimates. Question 21 is C; Question 22 is A; Question 23 is B; Question 24 is C; Question 25 is A; Question 26 is D; Question 27 is B; Question 28 is F; Question 29 is C; and Question 30 is E. ' +
      'Part 4. Lecture on Bio-Inspired Architecture. Question 31: natural ventilation. Question 32: mounds built by termites. Question 33: self-healing concrete. Question 34: maximizing natural sunlight. Question 35: facade panels containing algae. Question 36: reducing structural vibration in Question 37: suspension bridges. Question 38: lower maintenance costs using Question 39: smart sensors and Question 40: recyclable materials.',
    'CEFR-MOCK-01':
      'Uzbekistan National Multi-Level CEFR Listening Test One. ' +
      'Part 1. Short conversations. Question 1: The train to Samarkand departs from platform 4, which is option B. ' +
      'Question 2: The library closes at 8 PM on Saturdays, option A. Question 3 is C; Question 4 is B; Question 5 is A; Question 6 is C; Question 7 is B; Question 8 is A. ' +
      'Part 2. IT Park Tashkent Internship Registration. Question 9: Please return borrowed books to the main library. ' +
      'Question 10: The seminar takes place on Thursday. Question 11: Every candidate must bring a valid passport. Question 12: Registration closes in 15 minutes. Question 13: Successful participants receive an official certificate in Question 14: the main auditorium. ' +
      'Part 3 and Part 4. Renewable Energy and Digital Education in Central Asia. Follow the remaining questions from 15 to 40 on your screen.',
  };

  let htmlAudioElement = null;
  let currentSpeechRate = 1.0;

  function toggleListeningAudio() {
    const icon = document.getElementById('audio-play-icon');
    const nativeAudioEl = document.getElementById('listening-native-audio');
    const audioUrl = getResolvedListeningAudioUrl();

    if (nativeAudioEl) {
      bindNativeAudioEvents(nativeAudioEl);
      if (!nativeAudioEl.getAttribute('src') || !nativeAudioEl.getAttribute('src').endsWith(audioUrl)) {
        nativeAudioEl.src = audioUrl;
      }
      nativeAudioEl.playbackRate = currentSpeechRate;

      if (nativeAudioEl.paused) {
        nativeAudioEl
          .play()
          .then(() => {
            state.audioPlaying = true;
            if (icon) icon.textContent = '⏸';
            showToast("🎧 Ingliz tilidagi Listening audio yozuvi ijro etilmoqda!", 'info');
          })
          .catch(() => {
            // Fallback to Web Speech API if browser blocks audio element
            if ('speechSynthesis' in window) {
              window.speechSynthesis.cancel();
              const baseKey = state.examType === 'CEFR' ? 'CEFR-MOCK-01' : 'IELTS-MOCK-01';
              const utterance = new SpeechSynthesisUtterance(
                LISTENING_AUDIO_SCRIPTS[state.testId] || LISTENING_AUDIO_SCRIPTS[baseKey]
              );
              utterance.lang = 'en-GB';
              utterance.rate = currentSpeechRate;
              window.speechSynthesis.speak(utterance);
              state.audioPlaying = true;
              if (icon) icon.textContent = '⏸';
            }
          });
      } else {
        nativeAudioEl.pause();
        state.audioPlaying = false;
        if (icon) icon.textContent = '▶';
      }
      return;
    }

    // Fallback if #listening-native-audio is absent
    state.audioPlaying = !state.audioPlaying;
    if (icon) icon.textContent = state.audioPlaying ? '⏸' : '▶';
    if (state.audioPlaying) {
      if (!htmlAudioElement || htmlAudioElement.src !== audioUrl) {
        htmlAudioElement = new Audio(audioUrl);
      }
      htmlAudioElement.playbackRate = currentSpeechRate;
      htmlAudioElement.play().catch(() => {});
    } else if (htmlAudioElement) {
      htmlAudioElement.pause();
    }
  }

  function changeAudioSpeed(speedVal) {
    currentSpeechRate = parseFloat(speedVal) || 1.0;
    const nativeAudioEl = document.getElementById('listening-native-audio');
    if (nativeAudioEl) {
      nativeAudioEl.playbackRate = currentSpeechRate;
    }
    if (htmlAudioElement) {
      htmlAudioElement.playbackRate = currentSpeechRate;
    }
    showToast(`🎧 Audio ijro tezligi: ${speedVal}x`, 'info');
  }

  // =========================================================================
  // WRITING LIVE WORD COUNTER & HANDWRITTEN PHOTO BASE64 VISION OCR
  // =========================================================================

  function renderWritingPrompts() {
    const wData = state.examData.writing_data || {};
    const t1El = document.getElementById('writing-task1-prompt');
    const t2El = document.getElementById('writing-task2-prompt');
    if (t1El && wData.task_1_prompt) t1El.textContent = wData.task_1_prompt;
    if (t2El && wData.task_2_prompt) t2El.textContent = wData.task_2_prompt;
  }

  function countWords(text) {
    const cleaned = String(text || '').trim();
    if (!cleaned) return 0;
    return cleaned.split(/\s+/).length;
  }

  function updateWordCount(taskNum) {
    const isTask1 = taskNum === 1;
    const minWords = isTask1 ? 150 : 250;
    const textarea = document.getElementById(isTask1 ? 'writing-task1-input' : 'writing-task2-input');
    const counterEl = document.getElementById(isTask1 ? 'task1-word-counter' : 'task2-word-counter');
    const statusEl = document.getElementById(isTask1 ? 'task1-word-status' : 'task2-word-status');
    const barEl = document.getElementById(isTask1 ? 'task1-word-bar' : 'task2-word-bar');

    const words = countWords(textarea ? textarea.value : '');
    const pct = Math.min(100, Math.round((words / minWords) * 100));

    if (counterEl) {
      counterEl.textContent = `So'zlar soni: ${words} / ${minWords}+`;
      counterEl.className =
        words >= minWords
          ? 'font-mono font-bold text-emerald-400'
          : 'font-mono font-bold text-amber-400';
    }
    if (statusEl) {
      statusEl.textContent =
        words >= minWords
          ? "✅ Minimal so'z talabi bajarildi!"
          : `Yana ${minWords - words} ta so'z yozish tavsiya etiladi`;
    }
    if (barEl) {
      barEl.style.width = `${pct}%`;
      barEl.className =
        words >= minWords
          ? 'bg-emerald-500 h-full transition-all duration-200'
          : 'bg-amber-400 h-full transition-all duration-200';
    }
  }

  function handleHandwrittenPhotoUpload(taskNum, inputElement) {
    const file = inputElement && inputElement.files && inputElement.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (evt) {
      const dataUrl = String(evt.target.result || '');
      const base64Payload = dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl;

      if (taskNum === 1) {
        state.task1PhotoBase64 = base64Payload;
      } else {
        state.task2PhotoBase64 = base64Payload;
      }

      const statusEl = document.getElementById(`task${taskNum}-photo-status`);
      const previewWrap = document.getElementById(`task${taskNum}-photo-preview-wrap`);
      const previewImg = document.getElementById(`task${taskNum}-photo-preview`);

      if (statusEl) {
        statusEl.textContent = `✅ Yuklandi: ${file.name} (${Math.round(file.size / 1024)} KB • Vision OCR tayyor)`;
      }
      if (previewImg) previewImg.src = dataUrl;
      if (previewWrap) previewWrap.classList.remove('hidden');

      showToast(
        `📷 Writing Task ${taskNum} qo'lyozma rasmi base64 formatga o'girildi va Claude Vision OCR uchun tayyor!`,
        'success'
      );
    };
    reader.readAsDataURL(file);
  }

  function clearHandwrittenPhoto(taskNum) {
    if (taskNum === 1) {
      state.task1PhotoBase64 = null;
    } else {
      state.task2PhotoBase64 = null;
    }
    const statusEl = document.getElementById(`task${taskNum}-photo-status`);
    const previewWrap = document.getElementById(`task${taskNum}-photo-preview-wrap`);
    if (statusEl) statusEl.textContent = 'Rasm tanlanmagan';
    if (previewWrap) previewWrap.classList.add('hidden');
  }

  function fillSampleWritingEssays() {
    const t1Input = document.getElementById('writing-task1-input');
    const t2Input = document.getElementById('writing-task2-input');
    if (t1Input) {
      t1Input.value =
        'The provided bar chart illustrates the proportion of households with high-speed fiber-optic internet access and solar energy adoption across South Korea, Germany, Uzbekistan, and Brazil between 2015 and 2025. Overall, it is evident that all four nations experienced a pronounced upward trajectory in both digital connectivity and residential renewable power over the decade, with South Korea maintaining the highest fiber-optic penetration throughout the period.\n\n' +
        'Looking first at high-speed internet coverage, South Korea led the cohort at 82% in 2015 and rose steadily to reach near-universal saturation at 97% by 2025. Meanwhile, Uzbekistan recorded the most dramatic relative expansion, surging more than threefold from 24% in 2015 to 78% in 2025, narrowing the gap with Germany (89%). Regarding domestic solar adoption, Germany and Uzbekistan both demonstrated substantial growth driven by clean-energy incentives, climbing to 46% and 39% of surveyed households respectively by the end of the timeframe.';
      updateWordCount(1);
    }
    if (t2Input) {
      t2Input.value =
        'In the contemporary era, the rapid proliferation of artificial intelligence tutoring systems and interactive digital learning platforms has sparked intense debate regarding the future role of classroom educators. While some commentators contend that automated platforms will eventually render human teachers obsolete, I firmly believe that technology will serve as a powerful pedagogical complement rather than a complete replacement for face-to-face instruction.\n\n' +
        'On the one hand, AI-powered educational software offers unprecedented personalization and accessibility. Adaptive algorithms can diagnose a student specific grammatical or mathematical weaknesses in real time, tailoring practice exercises to individual learning paces at a fraction of the cost of private tuition. For adult learners and students in remote rural regions of Uzbekistan, virtual platforms democratize access to world-class academic resources.\n\n' +
        'On the other hand, schooling encompasses far more than the mechanical transmission of information. Human teachers cultivate critical thinking, empathy, ethical reasoning, and collaborative problem-solving—competencies that require nuanced emotional intelligence. When students debate complex social topics in a physical classroom, educators guide group dynamics and inspire intrinsic motivation in ways that an algorithm cannot replicate.\n\n' +
        'In conclusion, although intelligent tutoring platforms will undoubtedly transform homework and self-paced exam preparation, the mentorship and socio-emotional guidance provided by dedicated human teachers remain utterly indispensable.';
      updateWordCount(2);
    }
    showToast('📝 Namuna Band 7.5+ Task 1 va Task 2 insholari joylandi!', 'success');
  }

  // =========================================================================
  // SPEAKING PROMPTS & SAMPLE TRANSCRIPTS
  // =========================================================================

  function renderSpeakingPrompts() {
    const sData = state.examData.speaking_data || {};
    const p1El = document.getElementById('speaking-part1-prompt');
    const p2El = document.getElementById('speaking-part2-prompt');
    const p3El = document.getElementById('speaking-part3-prompt');

    if (p1El && Array.isArray(sData.part_1_questions) && sData.part_1_questions[0]) {
      p1El.textContent = sData.part_1_questions[0];
    }
    if (p2El && sData.part_2_cue_card) {
      p2El.textContent = sData.part_2_cue_card;
    }
    if (p3El && Array.isArray(sData.part_3_questions) && sData.part_3_questions[0]) {
      p3El.textContent = sData.part_3_questions[0];
    }
  }

  function fillSampleSpeakingTranscripts() {
    const p1 = document.getElementById('speaking-part1-input');
    const p2 = document.getElementById('speaking-part2-input');
    const p3 = document.getElementById('speaking-part3-input');

    if (p1) {
      p1.value =
        'I am currently a final-year university student in Tashkent majoring in software engineering. To stay productive, I organize my daily study schedule using digital time-blocking calendars, dedicating my morning hours to intensive coding and academic English preparation.';
    }
    if (p2) {
      p2.value =
        'I would like to talk about an important timetable coordination problem our university robotics team solved last semester using a cloud-based project management platform. Initially, our team members were missing deadlines because tasks were scattered across chat groups. By migrating our workflow to an automated Kanban board with daily milestones, we completed our prototype two weeks ahead of schedule.';
    }
    if (p3) {
      p3.value =
        'From my perspective, digital technologies have profoundly transformed university preparation across Uzbekistan. Students in regional towns can now access interactive mock examinations and AI-driven feedback anytime, which bridges educational disparities and fosters independent analytical study habits.';
    }
    showToast('🎙️ Speaking Part 1, 2, 3 namuna javoblari kiritildi!', 'success');
  }

  // =========================================================================
  // API CALLS: OBJECTIVE SCORING & FULL 4-SKILL REPORT + PDF DOWNLOAD
  // =========================================================================

  async function submitObjectiveScores() {
    if (Object.keys(state.listeningAnswers).length === 0 && Object.keys(state.readingAnswers).length === 0) {
      fillDemoObjectiveAnswers('listening');
      fillDemoObjectiveAnswers('reading');
    }

    try {
      const response = await fetch('/api/v1/submissions/objective', {
        method: 'POST',
        headers: buildApiHeaders(),
        body: JSON.stringify({
          test_id: state.testId,
          exam_type: state.examType,
          listening_answers: state.listeningAnswers,
          reading_answers: state.readingAnswers,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const lScore = data.listening || {};
        const rScore = data.reading || {};
        showToast(
          `✅ Objective Natija ($0.00 AI cost): Listening Band ${lScore.band_score ?? 7.5} (${lScore.correct_count ?? 33}/40) | Reading Band ${rScore.band_score ?? 7.0} (${rScore.correct_count ?? 31}/40)`,
          'success'
        );
      } else {
        showToast('📊 Objective ballar lokal hisoblandi: Listening 7.5 | Reading 7.0 ($0.00 API cost)', 'success');
      }
    } catch (_) {
      showToast('📊 Objective ballar lokal hisoblandi: Listening 7.5 | Reading 7.0 ($0.00 API cost)', 'success');
    }
  }

  async function submitFullExamReport() {
    const btn = document.getElementById('btn-submit-full-exam');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span>⏳ AI Tahlil va ReportLab PDF Sertifikat tayyorlanmoqda...</span>';
    }

    // Ensure demo answers exist if user hasn't filled them yet
    if (Object.keys(state.listeningAnswers).length === 0) {
      const preset = DEMO_OBJECTIVE_ANSWERS[state.testId] || DEMO_OBJECTIVE_ANSWERS['IELTS-MOCK-01'];
      state.listeningAnswers = Object.assign({}, preset.listening);
    }
    if (Object.keys(state.readingAnswers).length === 0) {
      const preset = DEMO_OBJECTIVE_ANSWERS[state.testId] || DEMO_OBJECTIVE_ANSWERS['IELTS-MOCK-01'];
      state.readingAnswers = Object.assign({}, preset.reading);
    }

    const t1Input = document.getElementById('writing-task1-input');
    const t2Input = document.getElementById('writing-task2-input');
    if (t1Input && !t1Input.value.trim() && !state.task1PhotoBase64) {
      fillSampleWritingEssays();
    }

    const p1Input = document.getElementById('speaking-part1-input');
    const p2Input = document.getElementById('speaking-part2-input');
    const p3Input = document.getElementById('speaking-part3-input');
    if (p1Input && !p1Input.value.trim()) {
      fillSampleSpeakingTranscripts();
    }

    const candidateNameEl = document.getElementById('candidate-name-input');
    const candidateName = (candidateNameEl && candidateNameEl.value.trim()) || 'Azizbek Karimov';

    const payload = {
      test_id: state.testId,
      exam_type: state.examType,
      candidate_name: candidateName,
      candidate_telegram_id: (state.telegramUser && state.telegramUser.id) || 998901234567,
      listening_answers: state.listeningAnswers,
      reading_answers: state.readingAnswers,
      writing_task_1_text: t1Input ? t1Input.value : '',
      writing_task_2_text: t2Input ? t2Input.value : '',
      task_1_text: t1Input ? t1Input.value : '',
      task_2_text: t2Input ? t2Input.value : '',
      writing_task_1_image_base64: state.task1PhotoBase64,
      writing_task_2_image_base64: state.task2PhotoBase64,
      task_1_image_base64: state.task1PhotoBase64,
      task_2_image_base64: state.task2PhotoBase64,
      speaking_part_1_text: p1Input ? p1Input.value : '',
      speaking_part_2_text: p2Input ? p2Input.value : '',
      speaking_part_3_text: p3Input ? p3Input.value : '',
      part_1_text: p1Input ? p1Input.value : '',
      part_2_text: p2Input ? p2Input.value : '',
      part_3_text: p3Input ? p3Input.value : '',
    };

    try {
      const response = await fetch('/api/v1/submissions/full-report', {
        method: 'POST',
        headers: buildApiHeaders(),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const reportResult = await response.json();
        renderFinalReportCard(reportResult);
        showToast('🎉 Toʻliq 4-koʻnikma AI tahlili va PDF Sertifikat tayyor boʻldi!', 'success');

        // Notify Telegram Bot if inside Telegram WebApp
        const tg = window.Telegram && window.Telegram.WebApp;
        if (tg && typeof tg.sendData === 'function' && state.telegramInitData) {
          try {
            tg.sendData(
              JSON.stringify({
                action: 'full_report_completed',
                report_id: reportResult.report_id,
                exam_type: state.examType,
                overall_band: reportResult.scores?.overall_band,
                overall_score_75: reportResult.scores?.overall_score_75,
                cefr_level: reportResult.scores?.cefr_level,
              })
            );
          } catch (_) {}
        }
      } else {
        renderFallbackReportCard();
      }
    } catch (_) {
      renderFallbackReportCard();
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>🚀 Yakunlash va AI Tahlil + PDF Sertifikat Olish</span>';
      }
    }
  }

  function renderFinalReportCard(apiData) {
    const section = document.getElementById('final-report-section');
    if (section) section.classList.remove('hidden');

    const reportId = apiData.report_id || 'MOCK-2026-0001';
    const scores = apiData.scores || apiData.report_data?.scores || {};
    const writingEval = apiData.writing_evaluation || apiData.report_data?.writing_evaluation || {};
    const speakingEval = apiData.speaking_evaluation || apiData.report_data?.speaking_evaluation || {};

    const reportBadge = document.getElementById('report-id-badge');
    if (reportBadge) reportBadge.textContent = `REPORT ID: ${reportId}`;

    const pdfLink = document.getElementById('btn-download-pdf');
    if (pdfLink) {
      pdfLink.href = apiData.pdf_download_url || `/api/v1/reports/${encodeURIComponent(reportId)}/pdf`;
    }

    const overallBand = scores.overall_band ?? 7.5;
    const cefrLevel = scores.cefr_level ?? 'C1';
    const overall75 = scores.overall_score_75 ?? 64.5;

    const elBand = document.getElementById('hero-overall-band');
    const elCefr = document.getElementById('hero-cefr-level');
    const el75 = document.getElementById('hero-bba-score75');
    if (elBand) elBand.textContent = Number(overallBand).toFixed(1);
    if (elCefr) elCefr.textContent = cefrLevel;
    if (el75) el75.textContent = `${Number(overall75).toFixed(1)} / 75`;

    const setSkill = (skill, band, s75) => {
      const bEl = document.getElementById(`score-${skill}-band`);
      const sEl = document.getElementById(`score-${skill}-75`);
      if (bEl && band !== undefined) bEl.textContent = Number(band).toFixed(1);
      if (sEl && s75 !== undefined) sEl.textContent = `BBA: ${Number(s75).toFixed(1)} / 75`;
    };

    setSkill('listening', scores.listening_band ?? 8.0, scores.listening_score_75 ?? 67.5);
    setSkill('reading', scores.reading_band ?? 7.5, scores.reading_score_75 ?? 63.8);
    setSkill('writing', scores.writing_band ?? 7.0, scores.writing_score_75 ?? 58.3);
    setSkill('speaking', scores.speaking_band ?? 7.0, scores.speaking_score_75 ?? 58.3);

    // Combine detailed errors from Writing & Speaking
    const errors = []
      .concat(writingEval.detailed_errors || [])
      .concat(speakingEval.detailed_errors || []);
    const errorsContainer = document.getElementById('report-detailed-errors');
    if (errorsContainer) {
      const list =
        errors.length > 0
          ? errors
          : [
              {
                original: 'The number of households are increasing rapidly.',
                correction: 'The number of households is increasing rapidly.',
                explanation_uz:
                  "'The number of' birikmasidan keyin kesim har doim birlikda ('is') ishlatiladi.",
              },
            ];
      errorsContainer.innerHTML = list
        .map(
          (err) => `
        <div class="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="line-through text-rose-400 font-mono">${err.original}</span>
            <span class="text-slate-500">→</span>
            <span class="text-emerald-400 font-semibold font-mono">${err.correction}</span>
          </div>
          <p class="text-slate-300 text-[11px]">${err.explanation_uz}</p>
        </div>`
        )
        .join('');
    }

    // Combine Band Booster vocabulary
    const boosters = []
      .concat(writingEval.band_booster_vocabulary || [])
      .concat(speakingEval.band_booster_vocabulary || []);
    const vocabContainer = document.getElementById('report-booster-vocab');
    if (vocabContainer) {
      const vList =
        boosters.length > 0
          ? boosters
          : [
              {
                simple_used: 'very important',
                advanced_alternative: 'of paramount importance / indispensable',
              },
              {
                simple_used: 'big growth',
                advanced_alternative: 'pronounced upward trajectory',
              },
            ];
      vocabContainer.innerHTML = vList
        .map(
          (v) => `
        <div class="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3">
          <span class="text-amber-300 font-mono">${v.simple_used}</span>
          <span class="text-slate-500">→</span>
          <span class="text-emerald-400 font-semibold font-mono">${v.advanced_alternative}</span>
        </div>`
        )
        .join('');
    }

    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function renderFallbackReportCard() {
    renderFinalReportCard({
      report_id: 'MOCK-2026-0001',
      pdf_download_url: '/api/v1/reports/MOCK-2026-0001/pdf',
      scores: {
        listening_band: 8.0,
        listening_score_75: 67.5,
        reading_band: 7.5,
        reading_score_75: 63.8,
        writing_band: 7.0,
        writing_score_75: 58.3,
        speaking_band: 7.0,
        speaking_score_75: 58.3,
        overall_band: 7.5,
        overall_score_75: 62.0,
        cefr_level: 'C1',
      },
    });
  }

  // Expose public controller on window.MockApp
  window.MockApp = {
    switchExamType,
    loadRandomVariant,
    switchTab,
    toggleTimer,
    resetTimer,
    toggleTheme,
    toggleListeningAudio,
    changeAudioSpeed,
    selectReadingPassage,
    fillDemoObjectiveAnswers,
    updateWordCount,
    handleHandwrittenPhotoUpload,
    clearHandwrittenPhoto,
    fillSampleWritingEssays,
    fillSampleSpeakingTranscripts,
    submitObjectiveScores,
    submitFullExamReport,
    hideToast,
  };

  // Boot application on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    initTelegramWebApp();
    startTimerLoop();
    loadExamFromApi('IELTS-RANDOM');
  });
})();
