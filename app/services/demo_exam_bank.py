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

from app.services.content import cefr_set1, ielts_set1
from app.services.content.builders import flatten_questions
from app.services.content.speaking_bank import build_speaking_data
from app.services.content.writing_charts import TASK1_CHARTS, TASK1_PROMPT_OVERRIDES, chart_to_text

ExamTypeLiteral = Literal["IELTS", "CEFR"]


def _listening_from_set(module: Any, set_id: str, duration: int, instructions: str) -> dict[str, Any]:
    parts = copy.deepcopy(module.LISTENING_PARTS)
    for part in parts:
        part["audio_url"] = f"/webapp/audio/{set_id}_part{part['number']}.mp3"
    return {
        "set_id": set_id,
        "duration_minutes": duration,
        "instructions": instructions,
        "parts": parts,
        "questions": flatten_questions(parts, "part"),
        "answer_key": dict(module.LISTENING_ANSWER_KEY),
    }


def _reading_from_set(module: Any, set_id: str, reading_module: str) -> dict[str, Any]:
    passages = copy.deepcopy(module.READING_PASSAGES)
    for passage in passages:
        passage["id"] = f"P{passage['number']}"
        passage["passage_number"] = passage["number"]
        passage["content"] = "\n\n".join(passage["paragraphs"])
    return {
        "set_id": set_id,
        "duration_minutes": 60,
        "module": reading_module,
        "passages": passages,
        "questions": flatten_questions(passages, "passage"),
        "answer_key": dict(module.READING_ANSWER_KEY),
    }


def _build_ielts_listening_data() -> dict[str, Any]:
    return _listening_from_set(
        ielts_set1, "ielts_set1", 30,
        "You will hear four recordings. Each recording is played ONCE. Answer questions 1–40.",
    )


def _build_ielts_reading_data() -> dict[str, Any]:
    return _reading_from_set(ielts_set1, "ielts_set1", "academic")


def _build_cefr_listening_data() -> dict[str, Any]:
    return _listening_from_set(
        cefr_set1, "cefr_set1", 35,
        "You will hear six parts. Each recording is played ONCE. Answer questions 1–40.",
    )


def _build_cefr_reading_data() -> dict[str, Any]:
    return _reading_from_set(cefr_set1, "cefr_set1", "cefr_multilevel")


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
                "Do you and your family recycle household items or save electricity at home?",
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


def _enrich_variants() -> None:
    """Attach Task 1 charts and the expanded speaking question bank to every variant."""
    for exam in DEMO_TESTS:
        vid = exam["id"]
        exam.setdefault("variant_number", 1)
        writing = exam["writing_data"]
        if vid in TASK1_PROMPT_OVERRIDES:
            writing["task_1_prompt"] = TASK1_PROMPT_OVERRIDES[vid]
        chart = TASK1_CHARTS.get(vid)
        if chart is not None:
            writing["task_1_chart_url"] = f"/api/v1/tests/{vid}/task1-chart.png"
            writing["task_1_chart_text"] = chart_to_text(chart)
        exam["speaking_data"] = build_speaking_data(vid, exam["variant_number"], exam["speaking_data"])


_enrich_variants()

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
            for part in section.get("parts") or []:
                if isinstance(part, dict):
                    part.pop("script", None)
            questions = section.get("questions")
            if isinstance(questions, list):
                for q in questions:
                    if isinstance(q, dict):
                        q.pop("answer_key", None)
                        q.pop("correct_answer", None)
                        q.pop("answer", None)

    sanitized.pop("answer_key", None)
    writing = sanitized.get("writing_data")
    if isinstance(writing, dict):
        writing.pop("task_1_chart_text", None)
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

