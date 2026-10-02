"""Speaking question bank: builds a realistic Part 1 (three topics, ~10 questions) and Part 3 (five
questions linked to the Part 2 cue card) for every variant."""

from __future__ import annotations

from typing import Any

INTRO_TOPICS: list[tuple[str, list[str]]] = [
    ("Your hometown", [
        "Where is your hometown?",
        "What do you like most about it?",
        "Has your hometown changed much since you were a child?",
        "Would you like to live there in the future?",
    ]),
    ("Your home", [
        "Do you live in a house or a flat?",
        "Which room do you spend the most time in?",
        "What would you like to change about your home?",
        "Do you plan to live there for a long time?",
    ]),
]

SHORT_TOPICS: list[tuple[str, list[str]]] = [
    ("Weather", ["What kind of weather do you like most?", "Does the weather affect your mood?", "Is the weather in your country changing?"]),
    ("Music", ["What kind of music do you listen to?", "Did you learn to play an instrument as a child?", "Do you prefer listening to music alone or with other people?"]),
    ("Mobile phones", ["How often do you use your phone each day?", "What do you mainly use it for?", "Could you live without a mobile phone for a week?"]),
    ("Friends", ["Do you prefer having many friends or a few close friends?", "How do you usually spend time with your friends?", "Have you kept in touch with your school friends?"]),
    ("Shopping", ["Do you enjoy shopping?", "Where do you usually buy clothes?", "Do you ever regret things you have bought?"]),
    ("Gifts", ["What was the last gift you gave someone?", "Do you prefer giving or receiving gifts?", "Is it common to give money as a gift in your country?"]),
    ("Walking", ["Do you walk a lot every day?", "Where do you like to go for a walk?", "Is your city a good place for walking?"]),
    ("Social media", ["Which social media apps do you use?", "How much time do you spend on social media?", "Do you think social media is good for young people?"]),
    ("Cooking", ["Can you cook?", "Who usually cooks in your family?", "What dish would you like to learn to cook?"]),
    ("Mornings", ["What time do you usually get up?", "What do you do first in the morning?", "Is your morning routine different at weekends?"]),
]

PART3_EXTRA: dict[str, list[str]] = {
    "IELTS-MOCK-01": ["Do you think older people find it harder to learn new technology? Why?", "Should children be taught how to solve problems rather than memorise facts?"],
    "IELTS-MOCK-02": ["Why do some people still prefer to drive even when public transport is available?", "How might the growth of cities affect the way people travel in the future?"],
    "IELTS-MOCK-03": ["Who should be more responsible for protecting the environment: individuals or governments?", "Do young people today care more about the environment than older generations?"],
    "IELTS-MOCK-04": ["Why do some people find it hard to change unhealthy habits?", "Should unhealthy food be taxed more heavily?"],
    "IELTS-MOCK-05": ["Should governments spend money on space exploration when there are problems on Earth?", "Why do fewer young people choose to study science in some countries?"],
    "IELTS-MOCK-06": ["Is it better to stay in one job for a long time or to change jobs often?", "How has the internet changed the way people look for work?"],
    "IELTS-MOCK-07": ["Should old buildings be preserved even when cities need space for new housing?", "How can technology help people learn about history?"],
    "IELTS-MOCK-08": ["Do people trust the news less than in the past? Why?", "Should parents limit the time children spend on screens?"],
    "IELTS-MOCK-09": ["Why do some people learn languages more easily than others?", "Is English becoming too dominant in the world?"],
    "IELTS-MOCK-10": ["How has the way people eat changed in your country in recent years?", "Should schools provide free healthy lunches for all children?"],
    "CEFR-MOCK-01": ["What can young people do to prepare for the job market while they are still studying?", "Is it better to work for a large company or a small one?"],
    "CEFR-MOCK-02": ["Should teachers be paid more than they are now?", "How will online learning change schools in the future?"],
    "CEFR-MOCK-03": ["What problems can too many tourists cause for a historic city?", "Why do people enjoy visiting other countries?"],
    "CEFR-MOCK-04": ["Why do some professional athletes earn so much money?", "Should physical education be compulsory at school?"],
    "CEFR-MOCK-05": ["Is it the responsibility of individuals or the government to keep cities clean?", "How can cities become better places to live?"],
    "CEFR-MOCK-06": ["Should children learn how to manage money at school?", "How has online shopping affected traditional shops?"],
    "CEFR-MOCK-07": ["Do exams really show what students know?", "What are the advantages of studying abroad?"],
    "CEFR-MOCK-08": ["Who should pay for new roads and public transport: governments or users?", "How will self-driving cars change our cities?"],
    "CEFR-MOCK-09": ["What qualities does a person need to start their own business?", "Why do many new businesses fail?"],
    "CEFR-MOCK-10": ["Should students be allowed to use AI tools to do their homework?", "Which jobs do you think will disappear because of technology?"],
}

# Part 1 questions that duplicate the intro topic are dropped.
_DUPLICATE_PREFIXES = ("tell me about your hometown", "where is your hometown")


def build_speaking_data(test_id: str, variant_number: int, base: dict[str, Any]) -> dict[str, Any]:
    """Return speaking data with `part_1_topics` (list of {topic, questions}) and expanded Part 3."""
    intro_title, intro_qs = INTRO_TOPICS[variant_number % len(INTRO_TOPICS)]
    extra_title, extra_qs = SHORT_TOPICS[(variant_number - 1) % len(SHORT_TOPICS)]
    variant_qs = [
        q for q in base.get("part_1_questions", [])
        if not q.lower().startswith(_DUPLICATE_PREFIXES)
    ]
    topics = [
        {"topic": intro_title, "questions": intro_qs},
        {"topic": "Topic 2", "questions": variant_qs},
        {"topic": extra_title, "questions": extra_qs},
    ]
    part_1 = [q for t in topics for q in t["questions"]]
    part_3 = list(base.get("part_3_questions", [])) + PART3_EXTRA.get(test_id, [])
    return {
        "part_1_topics": [t for t in topics if t["questions"]],
        "part_1_questions": part_1,
        "part_2_cue_card": base["part_2_cue_card"],
        "part_2_prep_seconds": 60,
        "part_2_speak_seconds": 120,
        "part_3_questions": part_3,
    }
