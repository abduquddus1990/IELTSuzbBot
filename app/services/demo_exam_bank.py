"""Built-in Demo Exam Bank for IELTS Academic & Uzbekistan National CEFR (Multi-Level).

Provides two rich, realistic mock examinations out of the box so candidates and developers
can test the complete 4-skill flow (Listening, Reading, Writing, Speaking) in both the
Telegram Bot and the Telegram Mini App (WebApp) with $0 database setup required:

1. `IELTS-MOCK-01`:
   - Title: "IELTS Academic Official Format Mock #1"
   - Exam Type: "IELTS"
   - 40 Listening questions & answer key, 40 Academic Reading questions & passages,
     Academic Writing Task 1 & Task 2 prompts, Speaking Parts 1, 2, 3.

2. `CEFR-MOCK-01`:
   - Title: "O'zbekiston BBA Multi-Level (B1-C1) Mock #1"
   - Exam Type: "CEFR"
   - 40 Listening questions & answer key, 40 Reading questions & passages,
     Multi-Level Writing Task 1 (Letter) & Task 2 (Essay) prompts, Speaking Parts 1, 2, 3.

Includes `sanitize_test_for_client()` to deep-copy exam dictionaries and strip `answer_key`
fields before sending payloads to the frontend Mini App so answers cannot be inspected
in browser DevTools.
"""

from __future__ import annotations

import copy
import random
from typing import Any, Literal

ExamTypeLiteral = Literal["IELTS", "CEFR"]


def _build_ielts_listening_data() -> dict[str, Any]:
    """Construct 40-question IELTS Academic Listening mock data and answer key."""
    answer_key: dict[str, str] = {
        # Part 1: University Sports Club Registration (Form Completion)
        "1": "Henderson",
        "2": "0789432109",
        "3": "intermediate",
        "4": "swimming",
        "5": "45",
        "6": "locker",
        "7": "medical",
        "8": "Tuesday",
        "9": "reception",
        "10": "student card",
        # Part 2: City Eco-Museum Guided Tour (Multiple Choice & Map Matching)
        "11": "B",
        "12": "C",
        "13": "A",
        "14": "B",
        "15": "C",
        "16": "F",
        "17": "D",
        "18": "A",
        "19": "G",
        "20": "E",
        # Part 3: Academic Tutorial on Urban Microclimates (Multiple Choice & Matching)
        "21": "C",
        "22": "A",
        "23": "B",
        "24": "C",
        "25": "A",
        "26": "D",
        "27": "B",
        "28": "F",
        "29": "C",
        "30": "E",
        # Part 4: Lecture on Bio-Inspired Architecture (Note Completion)
        "31": "ventilation",
        "32": "termites",
        "33": "concrete",
        "34": "sunlight",
        "35": "algae",
        "36": "vibration",
        "37": "bridges",
        "38": "maintenance",
        "39": "sensors",
        "40": "recyclable",
    }

    featured_questions: list[dict[str, Any]] = [
        {
            "id": "1",
            "number": 1,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Applicant Surname: Sarah ________ (spell the surname mentioned in the recording).",
        },
        {
            "id": "2",
            "number": 2,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Contact mobile number: ________.",
        },
        {
            "id": "3",
            "number": 3,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Current fitness level selected: ________ course.",
        },
        {
            "id": "4",
            "number": 4,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Primary facility requested in addition to the gym: ________ pool.",
        },
        {
            "id": "5",
            "number": 5,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Monthly membership fee with university discount: £________.",
        },
        {
            "id": "6",
            "number": 6,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Annual fee includes free use of a personal ________.",
        },
        {
            "id": "7",
            "number": 7,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "New members must complete a short ________ questionnaire before their first session.",
        },
        {
            "id": "8",
            "number": 8,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Free induction workshop day: every ________ evening.",
        },
        {
            "id": "9",
            "number": 9,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Meet the instructor beside the main ________ desk.",
        },
        {
            "id": "10",
            "number": 10,
            "part": 1,
            "type": "fill_in_blank",
            "prompt": "Document required for identity verification: ________.",
        },
        {
            "id": "11",
            "number": 11,
            "part": 2,
            "type": "multiple_choice",
            "prompt": "Why was the City Eco-Museum originally founded in 1998?",
            "options": [
                "A) To replace the old municipal library",
                "B) To preserve industrial heritage and promote renewable energy",
                "C) To host international trade conferences",
            ],
        },
        {
            "id": "12",
            "number": 12,
            "part": 2,
            "type": "multiple_choice",
            "prompt": "What is the most popular new exhibition this season?",
            "options": [
                "A) Steam Engines of the 19th Century",
                "B) Arctic Photography Gallery",
                "C) Interactive Smart Cities Pavilion",
            ],
        },
    ]

    # Populate remaining questions 13..40 so the frontend can render all 40 inputs
    existing_ids = {q["id"] for q in featured_questions}
    for q_num in range(1, 41):
        q_id = str(q_num)
        if q_id in existing_ids:
            continue
        if q_num <= 20:
            featured_questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 2,
                    "type": "multiple_choice" if q_num <= 15 else "matching",
                    "prompt": f"Part 2 Question {q_num}: Select the correct option or map letter (A-G).",
                    "options": ["A", "B", "C", "D", "E", "F", "G"] if q_num > 15 else ["A", "B", "C"],
                }
            )
        elif q_num <= 30:
            featured_questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 3,
                    "type": "multiple_choice" if q_num <= 25 else "matching",
                    "prompt": f"Part 3 Question {q_num} (Urban Microclimates Tutorial): Choose the correct letter.",
                    "options": ["A", "B", "C"] if q_num <= 25 else ["A", "B", "C", "D", "E", "F"],
                }
            )
        else:
            featured_questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 4,
                    "type": "fill_in_blank",
                    "prompt": (
                        f"Part 4 Question {q_num} (Bio-Inspired Architecture): "
                        "Write ONE WORD ONLY from the lecture."
                    ),
                }
            )

    return {
        "audio_url": "/webapp/audio/ielts_mock_01_listening.wav",
        "duration_minutes": 30,
        "instructions": (
            "Listen to the 4 recorded sections and answer questions 1 to 40. "
            "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for completion items."
        ),
        "questions": featured_questions,
        "answer_key": answer_key,
    }


def _build_ielts_reading_data() -> dict[str, Any]:
    """Construct 3 Academic Reading passages, 40 questions, and deterministic answer key."""
    answer_key: dict[str, str] = {
        # Passage 1: The Rise of Vertical Farming in Megacities (Q1 - Q13)
        "1": "TRUE",
        "2": "FALSE",
        "3": "NOT GIVEN",
        "4": "TRUE",
        "5": "FALSE",
        "6": "TRUE",
        "7": "nutrients",
        "8": "LED",
        "9": "pesticides",
        "10": "transport",
        "11": "pollination",
        "12": "B",
        "13": "C",
        # Passage 2: Cognitive Benefits of Multilingualism Across the Lifespan (Q14 - Q26)
        "14": "iv",
        "15": "ii",
        "16": "vi",
        "17": "i",
        "18": "v",
        "19": "A",
        "20": "C",
        "21": "B",
        "22": "D",
        "23": "executive",
        "24": "attention",
        "25": "dementia",
        "26": "plasticity",
        # Passage 3: Deep-Sea Hydrothermal Vents and the Origins of Life (Q27 - Q40)
        "27": "YES",
        "28": "NO",
        "29": "NOT GIVEN",
        "30": "YES",
        "31": "NO",
        "32": "C",
        "33": "A",
        "34": "D",
        "35": "B",
        "36": "chemosynthesis",
        "37": "alkaline",
        "38": "membranes",
        "39": "catalysts",
        "40": "A",
    }

    passages: list[dict[str, Any]] = [
        {
            "id": "P1",
            "passage_number": 1,
            "title": "Passage 1: The Rise of Vertical Farming in Megacities",
            "question_range": "1-13",
            "content": (
                "By 2050, nearly 70 percent of the global population is projected to reside in urban areas. "
                "Traditional horizontal agriculture faces mounting pressures from soil degradation, freshwater "
                "scarcity, and volatile weather patterns. Vertical farming—cultivating crops in vertically "
                "stacked layers inside controlled-environment buildings—offers a promising supplement to "
                "conventional farming.\n\n"
                "Instead of soil, most commercial vertical farms rely on hydroponic or aeroponic systems in "
                "which plant roots are misted or submerged in solutions rich in mineral nutrients. Because "
                "water is continuously recycled in closed-loop circuits, vertical farms consume up to 95 percent "
                "less water than open-field farms. Artificial LED arrays tuned to specific red and blue wavelengths "
                "drive photosynthesis year-round, eliminating dependence on seasonal sunlight.\n\n"
                "Furthermore, sealed indoor facilities prevent insect infestations, meaning crops can be grown "
                "entirely without chemical pesticides. Locating production inside metropolitan distribution hubs "
                "drastically reduces food transport miles and spoilage. However, high electricity demand and the "
                "need for manual or robotic pollination remain significant economic hurdles for staple calorie "
                "crops such as wheat and rice."
            ),
        },
        {
            "id": "P2",
            "passage_number": 2,
            "title": "Passage 2: Cognitive Benefits of Multilingualism Across the Lifespan",
            "question_range": "14-26",
            "content": (
                "For much of the early twentieth century, educators feared that exposing children to two "
                "languages simultaneously would cause linguistic confusion. Modern neuroimaging has overturned "
                "this view, demonstrating that managing multiple linguistic systems strengthens the brain's "
                "executive control network.\n\n"
                "Because both languages remain active in a bilingual speaker's mind even when only one is being "
                "used, the prefrontal cortex must constantly monitor context, select the target lexicon, and "
                "inhibit interference from the non-target language. This continuous mental workout enhances "
                "selective attention and task-switching efficiency.\n\n"
                "Longitudinal clinical studies further suggest that lifelong bilingualism builds cognitive "
                "reserve, delaying the behavioral onset of Alzheimer's disease and other forms of dementia by "
                "four to five years compared with monolingual peers, while promoting structural neuro-plasticity."
            ),
        },
        {
            "id": "P3",
            "passage_number": 3,
            "title": "Passage 3: Deep-Sea Hydrothermal Vents and the Origins of Life",
            "question_range": "27-40",
            "content": (
                "When oceanographers discovered hydrothermal vents along the Galápagos Rift in 1977, they were "
                "astonished to find thriving ecosystems in pitch darkness more than two kilometers below the "
                "ocean surface. Rather than relying on solar energy, microorganisms at these vents use "
                "chemosynthesis, oxidizing hydrogen sulfide and methane to fix carbon into organic molecules.\n\n"
                "Evolutionary biochemists now hypothesize that alkaline hydrothermal vents—such as the Lost City "
                "field—provided the ideal geochemical reactor for the emergence of life on early Earth. Porous "
                "mineral chimneys naturally create proton gradients across thin inorganic walls, mimicking "
                "modern cellular membranes, while iron-sulfur minerals act as primitive catalysts for "
                "prebiotic carbon fixation."
            ),
        },
    ]

    questions: list[dict[str, Any]] = [
        {
            "id": "1",
            "number": 1,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "Vertical farming uses up to 95% less water than conventional open-field farming.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "2",
            "number": 2,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "Vertical farms rely exclusively on natural sunlight reflected through glass mirrors.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "3",
            "number": 3,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "More than half of all supermarkets in Europe already sell vertically farmed produce.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "4",
            "number": 4,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "Growing staple crops like wheat indoors is currently limited by high energy costs.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "5",
            "number": 5,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "Hydroponic systems require heavier applications of chemical herbicides than soil farming.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "6",
            "number": 6,
            "passage": 1,
            "type": "true_false_not_given",
            "prompt": "Placing vertical farms inside cities lowers transportation distances.",
            "options": ["TRUE", "FALSE", "NOT GIVEN"],
        },
        {
            "id": "7",
            "number": 7,
            "passage": 1,
            "type": "fill_in_blank",
            "prompt": "Plant roots in hydroponic systems absorb dissolved mineral ________ from water.",
        },
        {
            "id": "8",
            "number": 8,
            "passage": 1,
            "type": "fill_in_blank",
            "prompt": "Specialized ________ lighting arrays provide wavelengths needed for photosynthesis.",
        },
        {
            "id": "9",
            "number": 9,
            "passage": 1,
            "type": "fill_in_blank",
            "prompt": "Because indoor environments are sealed from insects, chemical ________ are unnecessary.",
        },
        {
            "id": "10",
            "number": 10,
            "passage": 1,
            "type": "fill_in_blank",
            "prompt": "Urban cultivation cuts down on food ________ miles and post-harvest spoilage.",
        },
    ]

    existing_ids = {q["id"] for q in questions}
    for q_num in range(1, 41):
        q_id = str(q_num)
        if q_id in existing_ids:
            continue
        passage_idx = 1 if q_num <= 13 else (2 if q_num <= 26 else 3)
        expected_val = answer_key[q_id]
        if expected_val in {"TRUE", "FALSE", "NOT GIVEN"}:
            q_type = "true_false_not_given"
            opts = ["TRUE", "FALSE", "NOT GIVEN"]
        elif expected_val in {"YES", "NO"}:
            q_type = "yes_no_not_given"
            opts = ["YES", "NO", "NOT GIVEN"]
        elif expected_val in {"A", "B", "C", "D"}:
            q_type = "multiple_choice"
            opts = ["A", "B", "C", "D"]
        elif expected_val in {"i", "ii", "iii", "iv", "v", "vi"}:
            q_type = "matching_headings"
            opts = ["i", "ii", "iii", "iv", "v", "vi"]
        else:
            q_type = "fill_in_blank"
            opts = None

        q_entry: dict[str, Any] = {
            "id": q_id,
            "number": q_num,
            "passage": passage_idx,
            "type": q_type,
            "prompt": f"Passage {passage_idx} — Question {q_num}: Provide the correct response based on the text.",
        }
        if opts is not None:
            q_entry["options"] = opts
        questions.append(q_entry)

    return {
        "duration_minutes": 60,
        "module": "academic",
        "passages": passages,
        "questions": questions,
        "answer_key": answer_key,
    }


def _build_cefr_listening_data() -> dict[str, Any]:
    """Construct 40-question Uzbekistan BBA Multi-Level (B1-C1) Listening data and answer key."""
    answer_key: dict[str, str] = {
        # Part 1 (Q1-Q8): Short Dialogues
        "1": "B",
        "2": "A",
        "3": "C",
        "4": "B",
        "5": "A",
        "6": "C",
        "7": "B",
        "8": "A",
        # Part 2 (Q9-Q14): Campus Announcement Completion
        "9": "library",
        "10": "Thursday",
        "11": "passport",
        "12": "15",
        "13": "certificate",
        "14": "auditorium",
        # Part 3 (Q15-Q20): Speaker Matching
        "15": "D",
        "16": "A",
        "17": "F",
        "18": "B",
        "19": "E",
        "20": "C",
        # Part 4 (Q21-Q25): Map Labeling
        "21": "G",
        "22": "C",
        "23": "A",
        "24": "E",
        "25": "B",
        # Part 5 (Q26-Q31): Radio Interview on Green Tourism in Uzbekistan
        "26": "B",
        "27": "C",
        "28": "A",
        "29": "B",
        "30": "C",
        "31": "A",
        # Part 6 (Q32-Q40): Academic Lecture Summary Completion
        "32": "solar",
        "33": "irrigation",
        "34": "sensors",
        "35": "cotton",
        "36": "efficiency",
        "37": "satellites",
        "38": "training",
        "39": "exports",
        "40": "sustainable",
    }

    questions: list[dict[str, Any]] = []
    for q_num in range(1, 41):
        q_id = str(q_num)
        ans = answer_key[q_id]
        if q_num <= 8:
            questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 1,
                    "type": "multiple_choice",
                    "prompt": f"Part 1 Dialogue {q_num}: Choose the best answer (A, B, or C).",
                    "options": ["A", "B", "C"],
                }
            )
        elif q_num <= 14:
            questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 2,
                    "type": "fill_in_blank",
                    "prompt": f"Part 2 Note {q_num}: Write ONE WORD OR A NUMBER from the announcement.",
                }
            )
        elif q_num <= 25:
            part_no = 3 if q_num <= 20 else 4
            questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": part_no,
                    "type": "matching",
                    "prompt": f"Part {part_no} Matching {q_num}: Match the item with the correct letter (A-G).",
                    "options": ["A", "B", "C", "D", "E", "F", "G"],
                }
            )
        elif q_num <= 31:
            questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 5,
                    "type": "multiple_choice",
                    "prompt": f"Part 5 Interview Question {q_num} (Eco-Tourism in Uzbekistan): Select A, B, or C.",
                    "options": ["A", "B", "C"],
                }
            )
        else:
            _ = ans
            questions.append(
                {
                    "id": q_id,
                    "number": q_num,
                    "part": 6,
                    "type": "fill_in_blank",
                    "prompt": f"Part 6 Lecture Summary {q_num}: Complete the gap with ONE WORD ONLY.",
                }
            )

    return {
        "audio_url": "/webapp/audio/cefr_mock_01_listening.wav",
        "duration_minutes": 35,
        "instructions": (
            "O'zbekiston BBA Multi-Level Listening bo'limi (6 qism, 40 ta savol). "
            "Har bir javobni diqqat bilan belgilang yoki yozing."
        ),
        "questions": questions,
        "answer_key": answer_key,
    }


def _build_cefr_reading_data() -> dict[str, Any]:
    """Construct 40-question Uzbekistan BBA Multi-Level (B1-C1) Reading data and answer key."""
    answer_key: dict[str, str] = {
        # Part 1 (Q1-Q6): Gap-fill short text (B1)
        "1": "community",
        "2": "volunteers",
        "3": "workshops",
        "4": "digital",
        "5": "schedule",
        "6": "certificates",
        # Part 2 (Q7-Q14): Matching notices/advertisements (B1+)
        "7": "C",
        "8": "A",
        "9": "F",
        "10": "B",
        "11": "E",
        "12": "D",
        "13": "G",
        "14": "H",
        # Part 3 (Q15-Q20): Heading Matching (B2)
        "15": "D",
        "16": "A",
        "17": "F",
        "18": "B",
        "19": "C",
        "20": "E",
        # Part 4 (Q21-Q29): Long Analytical Text Comprehension (B2+)
        "21": "B",
        "22": "C",
        "23": "A",
        "24": "D",
        "25": "TRUE",
        "26": "FALSE",
        "27": "NOT GIVEN",
        "28": "TRUE",
        "29": "FALSE",
        # Part 5 (Q30-Q40): C1 Academic Text Summary & Multiple Choice
        "30": "infrastructure",
        "31": "renewable",
        "32": "hydropower",
        "33": "grid",
        "34": "investment",
        "35": "emissions",
        "36": "B",
        "37": "A",
        "38": "C",
        "39": "D",
        "40": "B",
    }

    passages: list[dict[str, Any]] = [
        {
            "id": "CEFR-P1",
            "passage_number": 1,
            "title": "Parts 1-2: Youth Digital Literacy Centres in Tashkent & Samarkand (B1/B2)",
            "question_range": "1-14",
            "content": (
                "Across Uzbekistan, local mahalla youth centres have launched a new initiative to expand "
                "practical skills among high-school graduates. Supported by experienced industry volunteers, "
                "these centres organize weekend workshops focused on coding, graphic design, and digital "
                "entrepreneurship. Participants can choose a flexible evening schedule and receive official "
                "completion certificates after presenting their capstone team project."
            ),
        },
        {
            "id": "CEFR-P2",
            "passage_number": 2,
            "title": "Parts 3-4: Silk Road Logistics and Modern Rail Corridors (B2)",
            "question_range": "15-29",
            "content": (
                "As landlocked Central Asian economies deepen trade integration with both Europe and East Asia, "
                "modernizing rail and dry-port logistics has become a strategic priority. Electrified freight "
                "corridors and automated customs clearance terminals have shortened transit times by nearly "
                "forty percent over the past decade, while lowering carbon emissions per tonne-kilometer."
            ),
        },
        {
            "id": "CEFR-P3",
            "passage_number": 3,
            "title": "Part 5: Clean Energy Transition and Smart Grid Architecture (C1)",
            "question_range": "30-40",
            "content": (
                "Transitioning national electricity networks toward a high share of solar, wind, and modern "
                "hydropower requires far more than building generation plants. Utility operators must upgrade "
                "transmission infrastructure and deploy AI-assisted smart grid balancing systems capable of "
                "absorbing intermittent renewable supply. Sustained private investment and regional power-pool "
                "agreements are projected to cut greenhouse gas emissions substantially by 2035."
            ),
        },
    ]

    questions: list[dict[str, Any]] = []
    for q_num in range(1, 41):
        q_id = str(q_num)
        ans = answer_key[q_id]
        if ans in {"TRUE", "FALSE", "NOT GIVEN"}:
            q_type = "true_false_not_given"
            opts = ["TRUE", "FALSE", "NOT GIVEN"]
        elif len(ans) == 1 and ans.isupper():
            q_type = "multiple_choice" if ans in {"A", "B", "C", "D"} else "matching"
            opts = ["A", "B", "C", "D"] if q_type == "multiple_choice" else ["A", "B", "C", "D", "E", "F", "G", "H"]
        else:
            q_type = "fill_in_blank"
            opts = None

        q_item: dict[str, Any] = {
            "id": q_id,
            "number": q_num,
            "passage": 1 if q_num <= 14 else (2 if q_num <= 29 else 3),
            "type": q_type,
            "prompt": f"BBA Reading Question {q_num}: Enter or select the correct answer.",
        }
        if opts is not None:
            q_item["options"] = opts
        questions.append(q_item)

    return {
        "duration_minutes": 60,
        "module": "cefr_multilevel",
        "passages": passages,
        "questions": questions,
        "answer_key": answer_key,
    }


DEMO_TESTS: list[dict[str, Any]] = [
    {
        "id": "IELTS-MOCK-01",
        "title": "IELTS Academic Official Format Mock #1",
        "exam_type": "IELTS",
        "duration_minutes": 165,
        "listening_data": _build_ielts_listening_data(),
        "reading_data": _build_ielts_reading_data(),
        "writing_data": {
            "task_1_prompt": (
                "The bar chart below shows the percentage of households with access to high-speed "
                "fiber-optic internet and renewable solar energy across four countries (South Korea, "
                "Germany, Uzbekistan, and Brazil) between 2015 and 2025. Summarize the information by "
                "selecting and reporting the main features, and make comparisons where relevant. "
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Some people believe that artificial intelligence tutors and online learning platforms "
                "will eventually replace traditional classroom teachers, while others argue that human "
                "interaction in schools remains irreplaceable. Discuss both these views and give your "
                "own opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Do you work or are you currently a student?",
                "How do you usually organize your daily study or work schedule?",
                "What kinds of technology do you use most frequently to learn new skills?",
            ],
            "part_2_cue_card": (
                "Describe an important problem you solved using a digital tool or technology.\n"
                "You should say:\n"
                "- what the problem was\n"
                "- which digital tool or resource you used\n"
                "- how long it took to solve the issue\n"
                "and explain what you learned from this experience."
            ),
            "part_3_questions": [
                "How has technology changed the way young people in your country prepare for university?",
                "Do you think reliance on artificial intelligence makes students less creative, or more productive?",
                "What steps should governments take to bridge the digital divide between urban and rural schools?",
            ],
        },
    },
    {
        "id": "CEFR-MOCK-01",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #1",
        "exam_type": "CEFR",
        "duration_minutes": 160,
        "listening_data": _build_cefr_listening_data(),
        "reading_data": _build_cefr_reading_data(),
        "writing_data": {
            "task_1_prompt": (
                "You recently attended an international youth IT & Innovation conference in Tashkent, "
                "but you accidentally left your tablet computer in the main lecture hall. Write a formal "
                "email to the conference organizers:\n"
                "- explaining when and where you attended the session\n"
                "- describing your tablet in detail\n"
                "- stating how they can contact you and return the device.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "In many countries today, young professionals prefer remote freelance work for international "
                "companies rather than traditional full-time office jobs in their local city. What are the "
                "advantages and disadvantages of this trend for individuals and society? Give reasons for "
                "your answer and include relevant examples. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Tell me about your hometown and what makes it a good place to live.",
                "How do people in your community usually spend their weekends?",
                "Why are you learning English, and how will a CEFR certificate help your career?",
            ],
            "part_2_cue_card": (
                "Describe a memorable educational project or team competition you participated in.\n"
                "You should talk about:\n"
                "- what the project or competition was about\n"
                "- who was on your team and what your specific role was\n"
                "- what challenges you faced along the way\n"
                "and explain why this experience was meaningful to you."
            ),
            "part_3_questions": [
                "Why do employers today value teamwork and communication skills as much as university degrees?",
                "Should universities focus more on practical internships or theoretical academic research?",
                "How will green energy and digital transformation reshape jobs in Uzbekistan over the next decade?",
            ],
        },
    },
]

# =====================================================================
# 10 TA TASODIFIY (RANDOM) SAVOLLAR VARIANTLARI BAZASI (IELTS & CEFR)
# =====================================================================

IELTS_RANDOM_PROMPT_POOL: list[dict[str, Any]] = [
    # Variant 1 (Canonical IELTS-MOCK-01)
    {
        "variant_id": "IELTS-MOCK-01",
        "title": "IELTS Academic Official Format Mock #1 (Digital & Bio-Tech)",
        "writing_data": DEMO_TESTS[0]["writing_data"],
        "speaking_data": DEMO_TESTS[0]["speaking_data"],
    },
    # Variant 2
    {
        "variant_id": "IELTS-MOCK-02",
        "title": "IELTS Academic Official Format Mock #2 (Global Urbanization & Transport)",
        "writing_data": {
            "task_1_prompt": (
                "The line graph below compares the average daily passenger numbers using metro systems, "
                "electric buses, and private cars in three major metropolitan areas (Tokyo, London, and "
                "Tashkent) between 2010 and 2025. Summarize the information by selecting and reporting "
                "the main features, and make comparisons where relevant. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Many cities around the world are investing heavily in high-speed public transport while "
                "restricting private cars in city centers. Do the advantages of this policy outweigh the "
                "disadvantages for commuters and local businesses? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "How do you usually travel to school or work every day?",
                "Is public transport convenient in your city or town?",
                "Would you prefer to travel by high-speed train or by airplane on a long trip?",
            ],
            "part_2_cue_card": (
                "Describe a memorable journey you took using public transport.\n"
                "You should say:\n"
                "- where you were traveling to and with whom\n"
                "- what kind of transport you used\n"
                "- what happened during the journey\n"
                "and explain why you remember this trip so well."
            ),
            "part_3_questions": [
                "How can governments encourage more car owners to switch to public transport?",
                "What impact does traffic congestion have on the economic productivity of large cities?",
                "How do you think urban transportation will look thirty years from now?",
            ],
        },
    },
    # Variant 3
    {
        "variant_id": "IELTS-MOCK-03",
        "title": "IELTS Academic Official Format Mock #3 (Clean Energy & Environment)",
        "writing_data": {
            "task_1_prompt": (
                "The pie charts below illustrate the proportion of electricity generated from five "
                "different sources (natural gas, hydro, solar, wind, and coal) in a Central Asian country "
                "in 2015 and projections for 2030. Summarize the information by selecting and reporting "
                "the main features, and make comparisons where relevant. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Some people think that protecting the environment va reducing plastic waste is the "
                "responsibility of international organizations and governments, while others believe "
                "individual citizens must lead the change. Discuss both views and give your opinion. "
                "(Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What is the weather like in your hometown during different seasons?",
                "Do you va your family recycle household items or save electricity at home?",
                "Do you enjoy spending time in nature parks or botanical gardens?",
            ],
            "part_2_cue_card": (
                "Describe an environmental project or clean-up initiative you heard about or joined.\n"
                "You should say:\n"
                "- what the initiative was and where it took place\n"
                "- how people participated in it\n"
                "- what positive results it achieved\n"
                "and explain why such environmental initiatives are important."
            ),
            "part_3_questions": [
                "Why is freshwater conservation becoming a critical issue in Central Asia and globally?",
                "Should companies that pollute the environment face heavier financial penalties?",
                "Can technological innovation alone solve global climate challenges without lifestyle changes?",
            ],
        },
    },
    # Variant 4
    {
        "variant_id": "IELTS-MOCK-04",
        "title": "IELTS Academic Official Format Mock #4 (Healthcare & Active Lifestyle)",
        "writing_data": {
            "task_1_prompt": (
                "The table below gives data on average weekly hours spent on physical exercise, "
                "screen-based leisure, and sleep across four age groups in 2024. Summarize the "
                "information by selecting and reporting the main features, and make comparisons "
                "where relevant. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Despite major advances in modern medicine, many people today suffer from stress and "
                "sedentary lifestyle diseases. What are the primary causes of this trend, and what "
                "measures can schools and employers take to address it? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What do you usually do to keep fit and healthy?",
                "Did you play any team sports when you were at primary or secondary school?",
                "How important is getting enough sleep for your daily concentration?",
            ],
            "part_2_cue_card": (
                "Describe a healthy habit or sport you would like to practice more regularly.\n"
                "You should say:\n"
                "- what the activity or habit is\n"
                "- how much time or equipment it requires\n"
                "- why you have not been able to do it every day\n"
                "and explain how it would improve your physical or mental well-being."
            ),
            "part_3_questions": [
                "Why do many working adults find it difficult to maintain a balanced work-life schedule?",
                "Should governments spend more public money on illness prevention rather than hospital treatment?",
                "How have fitness apps and wearable smartwatches influenced people's attitude toward health?",
            ],
        },
    },
    # Variant 5
    {
        "variant_id": "IELTS-MOCK-05",
        "title": "IELTS Academic Official Format Mock #5 (Space Exploration & Science)",
        "writing_data": {
            "task_1_prompt": (
                "The diagram below illustrates how a satellite-based agricultural monitoring system "
                "collects soil moisture data and transmits automated irrigation commands to farms. "
                "Summarize the information by selecting and reporting the main stages of the process. "
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Governments and private corporations spend billions of dollars on space exploration "
                "and satellite missions. Some argue this money should be spent solving urgent problems "
                "on Earth instead. To what extent do you agree or disagree? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Were you interested in science and astronomy when you were a child?",
                "Do you enjoy watching science documentaries or visiting science museums?",
                "Which scientific invention do you find most useful in your everyday life?",
            ],
            "part_2_cue_card": (
                "Describe a scientific discovery or invention that has positively changed the world.\n"
                "You should say:\n"
                "- what the discovery or invention is\n"
                "- how it works or how people use it\n"
                "- how life was different before it existed\n"
                "and explain why you consider it so significant."
            ),
            "part_3_questions": [
                "How can schools make STEM subjects (Science, Technology, Engineering, Math) more engaging?",
                "What ethical responsibilities do scientists have when developing powerful new technologies?",
                "Do you think international cooperation in scientific research is stronger today than in the past?",
            ],
        },
    },
    # Variant 6
    {
        "variant_id": "IELTS-MOCK-06",
        "title": "IELTS Academic Official Format Mock #6 (Global Economy & Youth Employment)",
        "writing_data": {
            "task_1_prompt": (
                "The bar chart below shows the percentage of university graduates employed in five "
                "sectors (IT, Education, Finance, Engineering, and Healthcare) in 2015 and 2025. "
                "Summarize the information by selecting and reporting the main features, and make "
                "comparisons where relevant. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "In the modern job market, many young people change careers several times rather than "
                "staying with a single employer for life. Is this a positive or negative development "
                "for workers and the economy? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What kind of job or profession would you like to have in the future?",
                "Do you prefer working independently or as part of a large team?",
                "What time of day do you feel most productive when studying?",
            ],
            "part_2_cue_card": (
                "Describe a person you know who is very successful and dedicated in their profession.\n"
                "You should say:\n"
                "- who this person is and how you know them\n"
                "- what their profession involves\n"
                "- what skills or qualities helped them succeed\n"
                "and explain how this person inspires you."
            ),
            "part_3_questions": [
                "Which skills will be most in demand for university graduates over the next ten years?",
                "Is a high salary the most important factor when choosing a career, or job satisfaction?",
                "How can governments support young entrepreneurs who want to launch small businesses?",
            ],
        },
    },
    # Variant 7
    {
        "variant_id": "IELTS-MOCK-07",
        "title": "IELTS Academic Official Format Mock #7 (Cultural Heritage & Architecture)",
        "writing_data": {
            "task_1_prompt": (
                "The maps below show the layout of a historic city square in 1995 and how it was "
                "redeveloped into a pedestrian cultural and tourism zone by 2025. Summarize the "
                "information by selecting and reporting the main changes. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "When expanding modern cities, some planners prioritize building glass skyscrapers and "
                "shopping malls, while others argue that preserving historic architecture is essential "
                "for national identity. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Are there many historical buildings or monuments in your city?",
                "Do you like visiting museums and art galleries when you travel?",
                "What traditional festival or holiday is most popular in your country?",
            ],
            "part_2_cue_card": (
                "Describe an impressive historical building or architectural landmark you have visited.\n"
                "You should say:\n"
                "- where the building is located\n"
                "- what it looks like inside and outside\n"
                "- what you learned about its history\n"
                "and explain how you felt when visiting this landmark."
            ),
            "part_3_questions": [
                "How does international tourism help preserve historic monuments, and how can it damage them?",
                "Should admission to national history museums be free for all students and citizens?",
                "Why is it important for younger generations to learn about their cultural heritage?",
            ],
        },
    },
    # Variant 8
    {
        "variant_id": "IELTS-MOCK-08",
        "title": "IELTS Academic Official Format Mock #8 (Media, Books & Information Age)",
        "writing_data": {
            "task_1_prompt": (
                "The chart below compares the number of printed books, e-books, and audiobooks borrowed "
                "or downloaded from public libraries between 2016 and 2025. Summarize the information by "
                "selecting and reporting the main features. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Nowadays, most people get their daily news from social media platforms rather than "
                "traditional newspapers or television broadcasts. Why is this happening, and is it a "
                "positive or negative trend for society? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What kinds of books or articles do you enjoy reading in your free time?",
                "Do you prefer reading printed paper books or reading on a screen?",
                "How do you usually stay informed about current events and news?",
            ],
            "part_2_cue_card": (
                "Describe a book or article you read recently that taught you something valuable.\n"
                "You should say:\n"
                "- what the title and main topic were\n"
                "- why you decided to read it\n"
                "- what key ideas stood out to you\n"
                "and explain why you would recommend it to others."
            ),
            "part_3_questions": [
                "Has the rise of short video platforms reduced people's ability to read long, complex books?",
                "How can students learn to distinguish reliable news sources from misinformation online?",
                "Will public libraries still be needed in the future when almost all books are digital?",
            ],
        },
    },
    # Variant 9
    {
        "variant_id": "IELTS-MOCK-09",
        "title": "IELTS Academic Official Format Mock #9 (Global Languages & Study Abroad)",
        "writing_data": {
            "task_1_prompt": (
                "The table below shows the number of international students enrolled in universities "
                "in four countries (the UK, Germany, South Korea, and Australia) in 2018 and 2025, "
                "along with average tuition costs. Summarize the main features. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Learning a foreign language at primary school is compulsory in many countries. Some "
                "educators believe children should master their native language first before starting "
                "a second language. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "How long have you been studying English, and what methods help you most?",
                "Have you ever spoken English with a tourist or international colleague?",
                "Which other foreign language would you like to learn in the future?",
            ],
            "part_2_cue_card": (
                "Describe an effective method or habit you used to improve your foreign language skills.\n"
                "You should say:\n"
                "- what the method or resource was\n"
                "- how often you practiced with it\n"
                "- what difficulties you overcame\n"
                "and explain how much it helped your confidence in speaking or writing."
            ),
            "part_3_questions": [
                "What are the main benefits and challenges of studying at a university abroad?",
                "Will automatic AI translation devices make learning foreign languages unnecessary one day?",
                "How does speaking more than one language broaden a person's worldview?",
            ],
        },
    },
    # Variant 10
    {
        "variant_id": "IELTS-MOCK-10",
        "title": "IELTS Academic Official Format Mock #10 (Smart Agriculture & Food Security)",
        "writing_data": {
            "task_1_prompt": (
                "The line graph and bar chart below illustrate annual wheat and fruit production yields "
                "per hectare alongside drip-irrigation adoption rates in Uzbekistan between 2015 and 2025. "
                "Summarize the information and make comparisons where relevant. (Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "As the global population grows, some experts argue that genetically modified crops and "
                "automated vertical farms are the only way to guarantee food security, while others favor "
                "traditional organic farming. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What is your favorite traditional dish from your country?",
                "Do you prefer cooking meals at home or eating out with friends?",
                "Do you usually buy fresh fruits and vegetables from local markets or supermarkets?",
            ],
            "part_2_cue_card": (
                "Describe a special meal or family gathering that you really enjoyed.\n"
                "You should say:\n"
                "- what the occasion was and where it was held\n"
                "- who attended the meal\n"
                "- what traditional dishes were prepared\n"
                "and explain why this gathering was memorable for you."
            ),
            "part_3_questions": [
                "Why are traditional family meals becoming less common in busy modern societies?",
                "How can schools teach children about healthy nutrition and reducing food waste?",
                "What role does modern technology play in helping farmers cope with drought and climate change?",
            ],
        },
    },
]

CEFR_RANDOM_PROMPT_POOL: list[dict[str, Any]] = [
    # Variant 1 (Canonical CEFR-MOCK-01)
    {
        "variant_id": "CEFR-MOCK-01",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #1 (IT Conference & Remote Work)",
        "writing_data": DEMO_TESTS[1]["writing_data"],
        "speaking_data": DEMO_TESTS[1]["speaking_data"],
    },
    # Variant 2
    {
        "variant_id": "CEFR-MOCK-02",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #2 (University Library & Higher Ed)",
        "writing_data": {
            "task_1_prompt": (
                "Your university library is planning to extend its opening hours and buy new digital "
                "resources. Write a formal letter to the Chief Librarian:\n"
                "- stating what you like about the current library facilities\n"
                "- suggesting specific e-books or study rooms that students need\n"
                "- explaining how extended evening hours will help students prepare for exams.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Some people believe that university education should be completely tuition-free for "
                "all students, while others argue that students should pay part of the cost or earn "
                "merit scholarships. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Where do you prefer to study when preparing for an important exam?",
                "What subject did you enjoy most at school, and why?",
                "How do you usually relax after a busy day of classes?",
            ],
            "part_2_cue_card": (
                "Describe a teacher or mentor who had a strong positive influence on your education.\n"
                "You should talk about:\n"
                "- who this teacher was and what subject they taught\n"
                "- what made their teaching style special\n"
                "- a specific lesson or piece of advice you remember\n"
                "and explain how they helped you grow as a student."
            ),
            "part_3_questions": [
                "What qualities make an outstanding teacher in the modern digital era?",
                "Should school curricula include practical financial literacy and coding for all pupils?",
                "How does lifelong learning benefit professionals throughout their careers?",
            ],
        },
    },
    # Variant 3
    {
        "variant_id": "CEFR-MOCK-03",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #3 (Eco-Tourism in Samarkand & Bukhara)",
        "writing_data": {
            "task_1_prompt": (
                "An international student group is visiting your city next month to learn about Uzbek "
                "culture and historic architecture. Write an email to the group coordinator:\n"
                "- welcoming them and recommending the best season/clothing\n"
                "- proposing a 2-day cultural itinerary\n"
                "- offering to guide them around the main historical sites.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Rapid growth in international tourism brings significant economic revenue to historic "
                "cities, but it can also put pressure on local infrastructure and traditions. Discuss "
                "the advantages and disadvantages of mass tourism and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Which historic city in Uzbekistan would you recommend to a foreign visitor?",
                "Do you prefer traveling with family, with friends, or alone?",
                "What kind of souvenirs do tourists usually buy in your region?",
            ],
            "part_2_cue_card": (
                "Describe a beautiful place in your country that you have visited or want to visit.\n"
                "You should talk about:\n"
                "- where this place is located\n"
                "- what natural or historical attractions it has\n"
                "- what activities visitors can do there\n"
                "and explain why this destination is special."
            ),
            "part_3_questions": [
                "How can local communities benefit directly from eco-tourism?",
                "What steps should authorities take to protect ancient Silk Road monuments for future generations?",
                "How has online travel booking changed the way people plan their holidays?",
            ],
        },
    },
    # Variant 4
    {
        "variant_id": "CEFR-MOCK-04",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #4 (Community Sports & Youth Wellness)",
        "writing_data": {
            "task_1_prompt": (
                "Your local mahalla council wants to build a new youth facility and is choosing between "
                "a sports complex and a digital co-working hub. Write a formal letter to the council:\n"
                "- stating which option you support or how both can be combined\n"
                "- explaining the benefits for teenagers and young adults in your neighborhood\n"
                "- suggesting how local volunteers can help maintain the center.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Many children today spend several hours a day playing video games on smartphones rather "
                "than playing outdoor sports with peers. Why is this happening, and how can parents and "
                "schools encourage a healthier balance? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What sports are most popular among young people in Uzbekistan?",
                "Do you prefer watching live sports events or playing sports yourself?",
                "How do you usually spend your summer holidays?",
            ],
            "part_2_cue_card": (
                "Describe an exciting sports match or competition you watched or took part in.\n"
                "You should talk about:\n"
                "- what sport it was and where it took place\n"
                "- who was competing\n"
                "- what the most thrilling moment of the event was\n"
                "and explain how you felt at the end of the competition."
            ),
            "part_3_questions": [
                "How does participating in team sports help children develop leadership and discipline?",
                "Should governments invest more in grassroots neighborhood sports fields or elite stadiums?",
                "Why have chess and intellectual games become so popular among youth in Uzbekistan?",
            ],
        },
    },
    # Variant 5
    {
        "variant_id": "CEFR-MOCK-05",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #5 (Green Cities & Tree Planting)",
        "writing_data": {
            "task_1_prompt": (
                "You want to organize a weekend tree-planting and park clean-up campaign around your "
                "school or university campus. Write a letter to the campus director:\n"
                "- explaining the purpose of the green initiative\n"
                "- describing when and where the tree planting will take place\n"
                "- requesting gardening tools and saplings for student volunteers.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Air quality and green parks are becoming major concerns in rapidly growing cities. "
                "What are the main causes of urban pollution, and what practical solutions can city "
                "authorities and citizens implement together? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Are there many green parks and trees near your home?",
                "What is your favorite season of the year, and why?",
                "How can families reduce water and electricity waste in their daily routines?",
            ],
            "part_2_cue_card": (
                "Describe a park, garden, or natural area where you enjoy relaxing.\n"
                "You should talk about:\n"
                "- where it is and how often you go there\n"
                "- what you usually do when you visit\n"
                "- what makes the atmosphere peaceful\n"
                "and explain why green spaces are vital in modern cities."
            ),
            "part_3_questions": [
                "How do nationwide tree-planting campaigns help combat dust storms and urban heat?",
                "Should schools include practical environmental projects in their curriculum?",
                "What incentives can encourage citizens to use solar panels and electric vehicles?",
            ],
        },
    },
    # Variant 6
    {
        "variant_id": "CEFR-MOCK-06",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #6 (E-Commerce & Digital Banking)",
        "writing_data": {
            "task_1_prompt": (
                "You ordered an electronic dictionary and study lamp from an online store, but the "
                "delivery arrived late and one item was damaged. Write a formal complaint email to "
                "Customer Service:\n"
                "- giving your order details and delivery date\n"
                "- describing the damage to the item\n"
                "- requesting an immediate replacement or full refund.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Online shopping and mobile payment apps have grown rapidly over the past five years. "
                "To what extent has this trend improved consumer convenience, and what risks does it "
                "create for small neighborhood shops and personal finances? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Do you prefer shopping in traditional markets or using online shopping apps?",
                "How do you usually plan your monthly pocket money or personal budget?",
                "Have you ever bought a book or course online?",
            ],
            "part_2_cue_card": (
                "Describe a useful product or piece of equipment you bought recently.\n"
                "You should talk about:\n"
                "- what you bought and where you found it\n"
                "- why you needed this item\n"
                "- how often you use it in your daily life\n"
                "and explain why you are satisfied with this purchase."
            ),
            "part_3_questions": [
                "Why do people sometimes buy things they do not really need when shopping online?",
                "How can young people protect themselves from online scams and digital fraud?",
                "Will cash completely disappear in the future in favor of digital cards and QR payments?",
            ],
        },
    },
    # Variant 7
    {
        "variant_id": "CEFR-MOCK-07",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #7 (International Scholarship Application)",
        "writing_data": {
            "task_1_prompt": (
                "You are applying for a summer English and Leadership exchange program at an "
                "international university. Write a formal motivation letter to the Admissions Committee:\n"
                "- introducing your academic background and achievements\n"
                "- explaining why you want to join this specific summer program\n"
                "- describing how you will share the knowledge gained with your peers back home.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Some educators argue that standardized exams are the fairest way to evaluate student "
                "achievement, while others believe continuous coursework and practical projects give a "
                "more accurate picture of ability. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "How do you usually prepare in the week before an important exam?",
                "Do you study better in the early morning or late in the evening?",
                "Who do you usually ask for advice when making an important educational decision?",
            ],
            "part_2_cue_card": (
                "Describe an academic goal or certificate you worked hard to achieve.\n"
                "You should talk about:\n"
                "- what the goal or exam was\n"
                "- how you organized your preparation schedule\n"
                "- what obstacles you had to overcome\n"
                "and explain how achieving this goal helped your future plans."
            ),
            "part_3_questions": [
                "How can students manage exam anxiety and stay motivated during long preparation periods?",
                "Why are international language certificates like IELTS and CEFR so valued by universities?",
                "Should schools reward students for individual competition or collaborative group success?",
            ],
        },
    },
    # Variant 8
    {
        "variant_id": "CEFR-MOCK-08",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #8 (Public Transport & Smart Roads)",
        "writing_data": {
            "task_1_prompt": (
                "The bus route connecting your residential district to the university campus has become "
                "overcrowded during morning rush hours. Write a formal letter to the City Transport Department:\n"
                "- describing the problem and which bus route is affected\n"
                "- explaining how delays affect students and workers\n"
                "- suggesting practical solutions such as adding express buses at peak times.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Building wider roads and highway flyovers is often seen as the solution to city traffic "
                "jams, whereas urban planners argue that expanding metro lines and bicycle lanes is far "
                "more effective. Discuss both views and give your opinion. (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "What is the most popular form of public transport in your city?",
                "Do you like listening to podcasts or audiobooks while commuting?",
                "Have you ever ridden a bicycle to school or around a park?",
            ],
            "part_2_cue_card": (
                "Describe a positive change or new infrastructure project built in your city recently.\n"
                "You should talk about:\n"
                "- what was built or modernized (e.g. a metro station, park, bridge, or campus)\n"
                "- how the area looked before the change\n"
                "- how local residents use the new facility today\n"
                "and explain why this development improved daily life."
            ),
            "part_3_questions": [
                "How does reliable public transport improve equal access to education and jobs?",
                "What safety measures are needed to make city streets safer for pedestrians and children?",
                "Should historic city centers be made completely car-free on weekends?",
            ],
        },
    },
    # Variant 9
    {
        "variant_id": "CEFR-MOCK-09",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #9 (Youth Entrepreneurship & Startups)",
        "writing_data": {
            "task_1_prompt": (
                "Your friend wants to open an educational book café and English speaking club for "
                "students in your town and asked for your advice. Write an email to your friend:\n"
                "- congratulating them on the idea\n"
                "- recommending a good location near schools or universities\n"
                "- suggesting weekend events that would attract young learners.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Today many teenagers and university students want to launch their own startups or "
                "digital projects while still studying. What are the benefits and drawbacks of combining "
                "academic studies with part-time work or entrepreneurship? (Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "Have you ever participated in an English speaking club or debate club?",
                "Do you prefer studying in a quiet room or in a lively café?",
                "What hobby or skill would you like to turn into a project one day?",
            ],
            "part_2_cue_card": (
                "Describe a small business, café, or educational center in your town that you admire.\n"
                "You should talk about:\n"
                "- what kind of services or products it offers\n"
                "- why customers or students enjoy going there\n"
                "- what makes it stand out from competitors\n"
                "and explain what you would do if you managed a similar project."
            ),
            "part_3_questions": [
                "Why is good customer service so important for the long-term success of any business?",
                "How have IT Parks and youth technoparks in Uzbekistan helped young programmers?",
                "Can entrepreneurship skills be taught in classrooms, or are they learned only through experience?",
            ],
        },
    },
    # Variant 10
    {
        "variant_id": "CEFR-MOCK-10",
        "title": "O'zbekiston BBA Multi-Level (B1-C1) Mock #10 (Artificial Intelligence & Future Skills)",
        "writing_data": {
            "task_1_prompt": (
                "Your school or university is organizing a 'Digital Skills & AI Literacy Week' for "
                "students. Write a letter to the organizing committee:\n"
                "- expressing your interest in volunteering at the event\n"
                "- proposing a practical workshop topic on using AI for language learning\n"
                "- explaining what equipment or room setup your workshop will need.\n"
                "(Write at least 150 words.)"
            ),
            "task_2_prompt": (
                "Artificial intelligence tools can now summarize books, write code, and translate "
                "languages in seconds. How should schools and universities adapt their teaching methods "
                "so that students develop genuine critical thinking rather than over-relying on AI? "
                "(Write at least 250 words.)"
            ),
            "min_words_t1": 150,
            "min_words_t2": 250,
        },
        "speaking_data": {
            "part_1_questions": [
                "How often do you use computers or mobile apps for your studies?",
                "What is the most useful mobile app on your phone right now?",
                "Do you prefer taking study notes by hand in a notebook or typing on a keyboard?",
            ],
            "part_2_cue_card": (
                "Describe a new skill (such as coding, public speaking, design, or a language) you learned recently.\n"
                "You should talk about:\n"
                "- what the skill is and why you decided to learn it\n"
                "- who or what helped you practice\n"
                "- what was the hardest part of learning it\n"
                "and explain how this skill will be useful in your future."
            ),
            "part_3_questions": [
                "Which human qualities—such as empathy, creativity, and ethics—can never be replaced by machines?",
                "How can parents guide children to use the internet productively for self-education?",
                "In what ways will artificial intelligence improve medical diagnostics and education in the next decade?",
            ],
        },
    },
]


def _build_all_random_variants() -> None:
    """Populate `DEMO_TESTS` with all 10 IELTS variants and all 10 CEFR variants (20 total)."""
    existing_ids = {exam["id"] for exam in DEMO_TESTS}
    base_ielts_listening = DEMO_TESTS[0]["listening_data"]
    base_ielts_reading = DEMO_TESTS[0]["reading_data"]
    base_cefr_listening = DEMO_TESTS[1]["listening_data"]
    base_cefr_reading = DEMO_TESTS[1]["reading_data"]

    for idx, item in enumerate(IELTS_RANDOM_PROMPT_POOL, start=1):
        vid = item["variant_id"]
        if vid in existing_ids:
            DEMO_TESTS[0]["variant_number"] = 1
            continue
        DEMO_TESTS.append(
            {
                "id": vid,
                "variant_number": idx,
                "title": item["title"],
                "exam_type": "IELTS",
                "duration_minutes": 165,
                "listening_data": copy.deepcopy(base_ielts_listening),
                "reading_data": copy.deepcopy(base_ielts_reading),
                "writing_data": copy.deepcopy(item["writing_data"]),
                "speaking_data": copy.deepcopy(item["speaking_data"]),
            }
        )

    for idx, item in enumerate(CEFR_RANDOM_PROMPT_POOL, start=1):
        vid = item["variant_id"]
        if vid in existing_ids:
            DEMO_TESTS[1]["variant_number"] = 1
            continue
        DEMO_TESTS.append(
            {
                "id": vid,
                "variant_number": idx,
                "title": item["title"],
                "exam_type": "CEFR",
                "duration_minutes": 160,
                "listening_data": copy.deepcopy(base_cefr_listening),
                "reading_data": copy.deepcopy(base_cefr_reading),
                "writing_data": copy.deepcopy(item["writing_data"]),
                "speaking_data": copy.deepcopy(item["speaking_data"]),
            }
        )


_build_all_random_variants()

DEMO_EXAM_BANK: dict[str, dict[str, Any]] = {exam["id"]: exam for exam in DEMO_TESTS}


def get_demo_tests(exam_type: str | None = None) -> list[dict[str, Any]]:
    """Return built-in demo mock exams (10 IELTS + 10 CEFR variants), optionally filtered by `exam_type`."""
    if exam_type is None or not str(exam_type).strip():
        return [copy.deepcopy(exam) for exam in DEMO_TESTS]

    normalized = str(exam_type).strip().upper()
    if normalized in {"MULTILEVEL", "MULTI-LEVEL", "MULTI_LEVEL", "BBA"}:
        normalized = "CEFR"
    elif normalized in {"IELTS_ACADEMIC", "IELTS_GENERAL"}:
        normalized = "IELTS"

    return [
        copy.deepcopy(exam)
        for exam in DEMO_TESTS
        if exam.get("exam_type", "").upper() == normalized
    ]


def get_random_demo_test(exam_type: str = "IELTS") -> dict[str, Any]:
    """Select and return 1 random mock exam variant out of the 10 variants for `exam_type`."""
    pool = get_demo_tests(exam_type=exam_type)
    if not pool:
        return copy.deepcopy(DEMO_EXAM_BANK["IELTS-MOCK-01"])
    return random.choice(pool)


def get_demo_test_by_id(test_id: str) -> dict[str, Any] | None:
    """Lookup a built-in demo mock exam by its ID (case-insensitive), random alias, or exam type shorthand."""
    if not test_id or not str(test_id).strip():
        return None

    cleaned = str(test_id).strip().upper()
    if cleaned in {"IELTS-RANDOM", "RANDOM-IELTS", "RANDOM"}:
        return get_random_demo_test("IELTS")
    if cleaned in {"CEFR-RANDOM", "RANDOM-CEFR", "BBA-RANDOM"}:
        return get_random_demo_test("CEFR")

    for exam in DEMO_TESTS:
        if exam["id"].upper() == cleaned:
            return copy.deepcopy(exam)

    # Convenience fallback if caller passes "IELTS" or "CEFR" as test_id
    if cleaned in {"IELTS", "IELTS_ACADEMIC"}:
        return copy.deepcopy(DEMO_EXAM_BANK["IELTS-MOCK-01"])
    if cleaned in {"CEFR", "BBA", "MULTILEVEL", "MULTI-LEVEL"}:
        return copy.deepcopy(DEMO_EXAM_BANK["CEFR-MOCK-01"])

    return None


def sanitize_test_for_client(test_dict: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy a mock test dictionary and strip `answer_key` from `listening_data` and `reading_data`.

    Prevents candidates from viewing correct answers in browser DevTools / Network Inspector
    when taking the exam inside the Telegram Mini App (WebApp).
    """
    sanitized = copy.deepcopy(test_dict)

    for section_key in ("listening_data", "reading_data"):
        section = sanitized.get(section_key)
        if isinstance(section, dict):
            section.pop("answer_key", None)
            questions = section.get("questions")
            if isinstance(questions, list):
                for q in questions:
                    if isinstance(q, dict):
                        q.pop("answer_key", None)
                        q.pop("correct_answer", None)
                        q.pop("answer", None)

    sanitized.pop("answer_key", None)
    return sanitized


__all__ = [
    "CEFR_RANDOM_PROMPT_POOL",
    "DEMO_EXAM_BANK",
    "DEMO_TESTS",
    "IELTS_RANDOM_PROMPT_POOL",
    "get_demo_test_by_id",
    "get_demo_tests",
    "get_random_demo_test",
    "sanitize_test_for_client",
]

