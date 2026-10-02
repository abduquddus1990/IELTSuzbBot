"""IELTS Academic practice test — Listening & Reading Set 1 (original content written for this platform).

`script` entries are (voice, text) pairs used by `tools/generate_listening_audio.py`; ("PAUSE", "20")
inserts silence. Scripts contain the answers, so they are server-only and stripped from client payloads.
"""

from __future__ import annotations

from app.services.content.builders import gap, group, item, lettered, mcq

# ---------------------------------------------------------------------------
# LISTENING
# ---------------------------------------------------------------------------

LISTENING_PARTS = [
    {
        "number": 1,
        "title": "Part 1 — Sports centre membership",
        "context": "You will hear a student talking to a receptionist at a university sports centre.",
        "groups": [
            group(
                "gap",
                "Complete the form below. Write ONE WORD AND/OR A NUMBER for each answer.",
                [
                    gap(1, "Name: Sarah ____"),
                    gap(2, "Mobile number: ____"),
                    gap(3, "Fitness course level: ____"),
                    gap(4, "Main facility (apart from the gym): ____"),
                    gap(5, "Monthly fee with student discount: £____"),
                    gap(6, "The fee includes free use of a personal ____"),
                    gap(7, "Before the first session: complete a short ____ questionnaire"),
                    gap(8, "Free induction workshop: every ____ evening"),
                    gap(9, "Meet the instructor beside the main ____ desk"),
                    gap(10, "Identification to bring: your ____"),
                ],
                title="RIVERSIDE UNIVERSITY SPORTS CENTRE — Membership Application",
            )
        ],
        "script": [
            ("NARRATOR", "IELTS Academic Listening practice test. Part one. You will hear a conversation between a student and a receptionist at a university sports centre. First, you have some time to look at questions one to ten."),
            ("PAUSE", "25"),
            ("NARRATOR", "Now listen carefully and answer questions one to ten."),
            ("MALE_GB", "Good morning, Riverside University Sports Centre. How can I help you?"),
            ("FEMALE_GB", "Hi. I'd like to join the centre, please. I'm a first-year student here."),
            ("MALE_GB", "Of course. I'll fill in the application form for you on the computer. Can I have your name first?"),
            ("FEMALE_GB", "Yes, it's Sarah Henderson."),
            ("MALE_GB", "Is that H, E, N, D, E, R, S, O, N?"),
            ("FEMALE_GB", "That's right."),
            ("MALE_GB", "And a mobile number we can contact you on?"),
            ("FEMALE_GB", "My old number ended in two oh one oh, but I changed it last week. The new one is oh seven eight nine four, three two one oh nine."),
            ("MALE_GB", "Oh seven eight nine four, three two one oh nine. Thanks. Now, our fitness courses run at three levels: beginner, intermediate and advanced. Which would suit you?"),
            ("FEMALE_GB", "Well, I did a beginners' course at school, and I was thinking of going straight to advanced, but my coach said that would be too much at first. So intermediate, please."),
            ("MALE_GB", "Intermediate. Fine. And apart from the gym, which facility do you think you'll use most? We have tennis courts, a climbing wall and a twenty-five metre pool."),
            ("FEMALE_GB", "I'd love to try the climbing wall one day, but at the moment it's mostly swimming for me. I go three times a week."),
            ("MALE_GB", "Swimming, then. Now, the fees. The standard monthly fee is fifty-five pounds, but with a student discount it comes down to forty-five pounds."),
            ("FEMALE_GB", "Forty-five pounds. That's reasonable. Does that include towels?"),
            ("MALE_GB", "I'm afraid towels are extra, but the fee does include free use of a personal locker, so you can leave your things here."),
            ("FEMALE_GB", "Oh, a locker is really useful."),
            ("MALE_GB", "Before your first session, you'll need to complete a short medical questionnaire. It's only a few questions about your health, and it takes about five minutes."),
            ("FEMALE_GB", "No problem. Is there any kind of introduction to the equipment?"),
            ("MALE_GB", "Yes, we run a free induction workshop. It used to be on Monday evenings, but since September it's every Tuesday evening at six o'clock."),
            ("FEMALE_GB", "Tuesday suits me fine. Where should I go?"),
            ("MALE_GB", "Don't go to the gym office upstairs. The instructor will meet you beside the main reception desk, just here by the entrance."),
            ("FEMALE_GB", "The reception desk. Got it. And do I need to bring anything with me?"),
            ("MALE_GB", "Just some identification. We can't accept a passport or a driving licence for membership, I'm afraid. It has to be your student card."),
            ("FEMALE_GB", "That's fine, I always carry it. Thank you so much."),
            ("NARRATOR", "That is the end of part one. You now have some time to check your answers."),
            ("PAUSE", "20"),
        ],
    },
    {
        "number": 2,
        "title": "Part 2 — Guided tour of the City Eco-Museum",
        "context": "You will hear a guide talking to visitors at the start of a museum tour.",
        "groups": [
            group(
                "mcq",
                "Choose the correct letter, A, B or C.",
                [
                    mcq(11, "Why was the City Eco-Museum originally founded in 1998?", [
                        "to replace the old municipal library",
                        "to preserve industrial heritage and promote renewable energy",
                        "to host international trade conferences",
                    ]),
                    mcq(12, "What is the most popular exhibition this season?", [
                        "Steam Engines of the 19th Century",
                        "the Arctic Photography Gallery",
                        "the Interactive Smart Cities Pavilion",
                    ]),
                    mcq(13, "What does the guide say about the museum café?", [
                        "It uses vegetables grown at the museum.",
                        "It is only open at weekends.",
                        "It offers discounts for groups.",
                    ]),
                    mcq(14, "Visitors who want to use the workshop room must", [
                        "pay an extra fee.",
                        "book at the information desk.",
                        "come with a teacher.",
                    ]),
                    mcq(15, "Photography is NOT allowed in", [
                        "the main hall.",
                        "the basement.",
                        "the temporary exhibition.",
                    ]),
                ],
            ),
            group(
                "matching",
                "What can visitors find in each area of the museum? Choose FIVE answers from the box and write the correct letter, A–G, next to Questions 16–20.",
                [
                    item(16, "Ground-floor hall"),
                    item(17, "Basement"),
                    item(18, "First-floor gallery"),
                    item(19, "Rooftop"),
                    item(20, "East wing"),
                ],
                box_title="Features",
                box=lettered([
                    "a model of a wind turbine",
                    "a gift shop",
                    "a small cinema",
                    "an original coal-mine tunnel",
                    "a children's play area",
                    "a giant water wheel",
                    "solar panels that visitors can control",
                ]),
            ),
        ],
        "script": [
            ("NARRATOR", "Part two. You will hear a guide talking to a group of visitors at the start of a tour of the City Eco-Museum. First, you have some time to look at questions eleven to fifteen."),
            ("PAUSE", "20"),
            ("NARRATOR", "Now listen carefully and answer questions eleven to fifteen."),
            ("GUIDE_AU", "Good morning, everyone, and welcome to the City Eco-Museum. Before we start the tour, let me tell you a little about the building. A lot of visitors assume the museum was opened to replace the old town library, which closed in the same year, nineteen ninety-eight. In fact, there's no connection. The museum was founded to preserve the area's industrial heritage, and at the same time to promote renewable energy for the future."),
            ("GUIDE_AU", "We have several exhibitions running at the moment. Our steam engine collection has always been a favourite, and last winter the Arctic photography gallery attracted enormous crowds. But this season, the one everybody is talking about is the new interactive Smart Cities Pavilion, so do leave plenty of time for that."),
            ("GUIDE_AU", "Now, a few practical points. The café on the ground floor is open every day, not just at weekends as it used to be. All the vegetables in the soups and salads come from our own garden at the back of the museum. Unfortunately, we can't offer discounts for groups in the café."),
            ("GUIDE_AU", "Some of you asked about the workshop room, where you can build simple solar circuits. It's completely free, and you don't need to be with a teacher, but space is limited, so you'll need to book a time at the information desk."),
            ("GUIDE_AU", "And finally, photography. You're welcome to take photos in the main hall and even down in the basement, but please don't take any pictures in the temporary exhibition, because the objects there are on loan from other museums."),
            ("NARRATOR", "Before you hear the rest of the talk, you have some time to look at questions sixteen to twenty."),
            ("PAUSE", "20"),
            ("NARRATOR", "Now listen and answer questions sixteen to twenty."),
            ("GUIDE_AU", "Let me quickly explain the layout. As you walk into the ground-floor hall, you can't miss the giant water wheel, which once powered the old textile mill. The gift shop used to be in the hall too, but it's moved outside next to the car park."),
            ("GUIDE_AU", "If you take the stairs down to the basement, you'll find something quite special: an original coal-mine tunnel, which we've restored so you can walk through it. There used to be a small cinema down there, but it closed last year."),
            ("GUIDE_AU", "Upstairs, in the first-floor gallery, there's a working model of a wind turbine. You can change the wind speed and watch how much electricity it produces."),
            ("GUIDE_AU", "On the rooftop you'll see our solar panels. There's a control screen where you can actually move the panels yourself to follow the sun."),
            ("GUIDE_AU", "And if you have children with you, head to the east wing, where there's a children's play area with energy games. Right, let's begin."),
            ("NARRATOR", "That is the end of part two. You now have some time to check your answers."),
            ("PAUSE", "15"),
        ],
    },
    {
        "number": 3,
        "title": "Part 3 — Tutorial on an urban microclimate project",
        "context": "You will hear two students, Tom and Maya, discussing their project with their tutor.",
        "groups": [
            group(
                "mcq",
                "Choose the correct letter, A, B or C.",
                [
                    mcq(21, "Why did Tom and Maya choose urban microclimates as their topic?", [
                        "They had studied it in a previous course.",
                        "Their tutor recommended it.",
                        "It is connected to their own city.",
                    ]),
                    mcq(22, "What problem did they have with their temperature data?", [
                        "Some sensors had been placed in direct sunlight.",
                        "There was no data for the winter months.",
                        "The readings were recorded in the wrong units.",
                    ]),
                    mcq(23, "The tutor says their literature review should", [
                        "include more recent studies.",
                        "discuss fewer studies in more depth.",
                        "be moved to the end of the report.",
                    ]),
                    mcq(24, "What surprised Maya about the park measurements?", [
                        "how much the noise level fell",
                        "how many people used the park",
                        "how far the cooling effect reached",
                    ]),
                    mcq(25, "What do they agree about the presentation?", [
                        "Tom will present the results.",
                        "They will use fewer slides.",
                        "They will practise in front of classmates.",
                    ]),
                ],
            ),
            group(
                "matching",
                "What do the students decide to do with each source? Choose FIVE answers from the box and write the correct letter, A–F, next to Questions 26–30.",
                [
                    item(26, "the council's traffic report"),
                    item(27, "the satellite images"),
                    item(28, "the residents' survey"),
                    item(29, "the weather station records"),
                    item(30, "their own photographs"),
                ],
                box_title="Decisions",
                box=lettered([
                    "put it in the appendix",
                    "use it to compare different years",
                    "check it with the tutor first",
                    "leave it out completely",
                    "use it on the title slide",
                    "combine it with their own measurements",
                ]),
            ),
        ],
        "script": [
            ("NARRATOR", "Part three. You will hear two students, Tom and Maya, discussing their geography project with their tutor, Dr Price. First, you have some time to look at questions twenty-one to twenty-five."),
            ("PAUSE", "20"),
            ("NARRATOR", "Now listen carefully and answer questions twenty-one to twenty-five."),
            ("TUTOR", "Come in, Tom, Maya. So, how is the microclimate project going? Remind me why you chose it. I think I'd suggested coastal erosion, hadn't I?"),
            ("MALE_IE", "You did, but neither of us had studied microclimates before, and we thought it would be more interesting to look at something happening in our own city. Maya noticed how much hotter the centre feels than her neighbourhood."),
            ("FEMALE_IE", "Exactly. It's our city, so we can collect the data ourselves."),
            ("TUTOR", "Good. And how did the data collection go?"),
            ("FEMALE_IE", "Mostly well. We have readings for the whole year, including winter, and everything's in degrees Celsius. The problem was that three of our sensors had been fixed to walls that get direct sunlight in the afternoon, so those readings were far too high."),
            ("TUTOR", "That happens a lot. Just explain it clearly in your methods section. Now, your literature review. You've included twenty-three studies, and many are very recent, which is good, but you only give each one a sentence. I'd rather you chose the six or seven most relevant and discussed them properly."),
            ("MALE_IE", "Fewer studies, in more depth. OK."),
            ("TUTOR", "What about the park measurements?"),
            ("FEMALE_IE", "That was the most interesting part. We expected the park to be cooler, and we expected it to be quieter, but what I didn't expect was that the cooling effect could still be measured three hundred metres away from the park, in the surrounding streets."),
            ("TUTOR", "That's a valuable finding. And the presentation?"),
            ("MALE_IE", "We were going to share it, but Maya's done most of the writing, so we've agreed I'll present the results section. We'll keep the twelve slides we have."),
            ("NARRATOR", "Before you hear the rest of the discussion, you have some time to look at questions twenty-six to thirty."),
            ("PAUSE", "20"),
            ("NARRATOR", "Now listen and answer questions twenty-six to thirty."),
            ("TUTOR", "Let's go through your other sources. The council's traffic report?"),
            ("MALE_IE", "We thought about putting it in the appendix, but honestly, it isn't really about temperature, so we'll leave it out completely."),
            ("TUTOR", "Fine. The satellite images?"),
            ("FEMALE_IE", "Those are great, because there are images from two thousand and five and from this year, so we'll use them to compare different years and show how the green spaces have shrunk."),
            ("TUTOR", "And the residents' survey?"),
            ("MALE_IE", "On its own it's just people's opinions, so we'll combine it with our own measurements and see if people's feelings match the real temperatures."),
            ("TUTOR", "Sensible. The weather station records?"),
            ("FEMALE_IE", "We weren't sure we're allowed to use them, because the station belongs to a private company. Could we check with you first, before we include them?"),
            ("TUTOR", "Yes, send me the details. And your photographs?"),
            ("MALE_IE", "Most aren't very scientific, but there's a nice one of the city centre at sunset. We'll use it on the title slide."),
            ("NARRATOR", "That is the end of part three. You now have some time to check your answers."),
            ("PAUSE", "15"),
        ],
    },
    {
        "number": 4,
        "title": "Part 4 — Lecture: architecture inspired by nature",
        "context": "You will hear a lecture about biomimicry in architecture.",
        "groups": [
            group(
                "gap",
                "Complete the notes below. Write ONE WORD ONLY for each answer.",
                [
                    gap(31, "Eastgate Centre, Harare: uses natural ____ instead of air conditioning"),
                    gap(32, "Its design copies the mounds built by ____"),
                    gap(33, "Self-repairing materials: bacteria inside ____ produce limestone that fills cracks"),
                    gap(34, "Leaf-inspired façades: panels turn to make the best use of ____"),
                    gap(35, "BIQ House, Hamburg: façade panels contain ____ that produce heat and biomass"),
                    gap(36, "Bones and spider silk: models for structures that absorb ____"),
                    gap(37, "This idea is already used in the cables of suspension ____"),
                    gap(38, "Main financial benefit: lower ____ costs over a building's life"),
                    gap(39, "Future buildings may contain smart ____ that work like nerves"),
                    gap(40, "Architects will make greater use of ____ materials"),
                ],
                title="Biomimicry in architecture",
            )
        ],
        "script": [
            ("NARRATOR", "Part four. You will hear a lecture about architecture inspired by nature. First, you have some time to look at questions thirty-one to forty."),
            ("PAUSE", "30"),
            ("NARRATOR", "Now listen carefully and answer questions thirty-one to forty."),
            ("LECTURER", "Good afternoon. Today I want to look at biomimicry, which means copying solutions from nature, and how architects are using it to design better buildings."),
            ("LECTURER", "Let's start with a famous example: the Eastgate Centre in Harare, Zimbabwe. It's a large office and shopping complex, but it has no conventional air conditioning. Instead, it relies on natural ventilation. Cool night air is drawn in at the bottom and warm air escapes through chimneys at the top. The architect, Mick Pearce, based this design on the mounds built by termites, which stay at a remarkably stable temperature even when it is very hot outside."),
            ("LECTURER", "My second example concerns materials. Cracks are the enemy of every building. Researchers in the Netherlands have developed a self-repairing concrete. It contains bacteria that remain inactive for years, but when water gets into a crack, they wake up and produce limestone, which gradually fills the gap."),
            ("LECTURER", "Plants have inspired architects too. Leaves constantly adjust their position, and some new office façades work in the same way: their panels rotate during the day to make the best use of sunlight, letting it in during winter and blocking it in summer."),
            ("LECTURER", "An even more unusual idea can be seen in the BIQ House in Hamburg. Its façade panels contain algae. The algae grow in water inside glass panels, producing heat for the building as well as biomass that can be turned into fuel."),
            ("LECTURER", "Engineers are also studying bones and spider silk, both of which are light but extremely strong. What interests them is how these natural structures absorb vibration without breaking. This principle has already been applied to the cables of some suspension bridges, which must cope with wind and heavy traffic."),
            ("LECTURER", "Why does all this matter? The construction costs of these buildings are not always lower. The real advantage is that maintenance costs over the life of the building are much lower, because the building looks after itself to some extent."),
            ("LECTURER", "Looking ahead, we may see buildings with smart sensors embedded in their walls, working rather like nerves in the body, detecting damage before humans notice it. And, following nature, where nothing is wasted, architects will make far greater use of recyclable materials. Next week, we'll look at some of the criticisms of biomimicry."),
            ("NARRATOR", "That is the end of the listening test. You now have two minutes to check your answers."),
            ("PAUSE", "10"),
        ],
    },
]

LISTENING_ANSWER_KEY = {
    "1": "Henderson", "2": "0789432109", "3": "intermediate", "4": "swimming", "5": "45",
    "6": "locker", "7": "medical", "8": "Tuesday", "9": "reception", "10": "student card/student ID card",
    "11": "B", "12": "C", "13": "A", "14": "B", "15": "C",
    "16": "F", "17": "D", "18": "A", "19": "G", "20": "E",
    "21": "C", "22": "A", "23": "B", "24": "C", "25": "A",
    "26": "D", "27": "B", "28": "F", "29": "C", "30": "E",
    "31": "ventilation", "32": "termites", "33": "concrete", "34": "sunlight", "35": "algae",
    "36": "vibration", "37": "bridges", "38": "maintenance", "39": "sensors", "40": "recyclable",
}

# ---------------------------------------------------------------------------
# READING
# ---------------------------------------------------------------------------

READING_PASSAGES = [
    {
        "number": 1,
        "title": "The Rise of Vertical Farming",
        "question_range": "1–13",
        "paragraphs": [
            "By 2050, nearly 70 percent of the world's population is expected to live in cities. Feeding them will be one of the great challenges of the century, because traditional agriculture is already under pressure from soil degradation, shortages of fresh water and increasingly unpredictable weather. One response that has attracted both investors and city planners is vertical farming: growing crops in stacked layers inside buildings where light, temperature and humidity are completely controlled.",
            "Most commercial vertical farms do not use soil at all. Instead they rely on hydroponic systems, in which plant roots hang in water, or aeroponic systems, in which the roots are sprayed with a fine mist. In both cases the water is enriched with the mineral nutrients that plants would normally take from the soil. Because the water circulates in closed loops and is recycled continuously, a vertical farm can use up to 95 percent less water than a field growing the same crop. For many engineers, this is the single most important argument in favour of the technology.",
            "Light is supplied not by the sun but by LED arrays. These lamps can be tuned to the red and blue wavelengths that plants use most efficiently for photosynthesis, so crops can grow all year round regardless of the season or the weather outside. Some early projects experimented with mirrors and glass roofs to bring in daylight, but almost all modern farms have abandoned this approach in favour of artificial lighting, which is easier to control.",
            "Because the growing rooms are sealed, insects cannot get in, and crops can be produced without chemical pesticides. Similarly, the absence of soil means that there are no weeds, so herbicides are unnecessary. Supporters also point to the advantages of location. A farm inside a city can be built close to supermarkets and restaurants, which dramatically reduces the transport miles that food travels and the amount of produce that spoils on the way.",
            "The technology does, however, have clear limits. Vertical farms consume large amounts of electricity, mainly for lighting and climate control, and in most countries this makes them expensive to run. Leafy greens, herbs and strawberries, which grow quickly and sell at high prices, are profitable. Staple crops such as wheat and rice are a different matter: they need far more space and light, and because there are no bees indoors, they would require manual or robotic pollination. At current energy prices, growing them indoors is not economically realistic.",
            "It would therefore be a mistake to imagine that skyscrapers full of crops will replace the world's farmland. A more realistic view is that vertical farming will become a valuable supplement to conventional agriculture, producing fresh, high-value food close to the people who eat it, while fields continue to supply the bulk of the world's calories.",
        ],
        "groups": [
            group(
                "tfng",
                "Do the following statements agree with the information given in the passage? Choose TRUE if the statement agrees with the information, FALSE if the statement contradicts the information, NOT GIVEN if there is no information on this.",
                [
                    item(1, "A vertical farm may use only about one twentieth of the water needed by a field growing the same crop."),
                    item(2, "Most modern vertical farms rely on natural sunlight reflected by mirrors."),
                    item(3, "More than half of European supermarkets already sell vertically farmed produce."),
                    item(4, "Growing staple crops such as wheat indoors is currently limited by energy costs."),
                    item(5, "Hydroponic farms need more herbicides than traditional soil farms."),
                    item(6, "Building farms inside cities reduces the distance food has to travel."),
                ],
            ),
            group(
                "gap",
                "Complete the notes below. Choose ONE WORD ONLY from the passage for each answer.",
                [
                    gap(7, "In hydroponic systems, water is enriched with mineral ____"),
                    gap(8, "Light comes from ____ arrays tuned to particular wavelengths"),
                    gap(9, "Sealed rooms keep insects out, so no chemical ____ are needed"),
                    gap(10, "City locations reduce food ____ miles and spoilage"),
                    gap(11, "Indoor wheat and rice would need manual or robotic ____"),
                ],
                title="How vertical farms work",
            ),
            group(
                "mcq",
                "Choose the correct letter, A, B, C or D.",
                [
                    mcq(12, "According to many engineers, the most important advantage of vertical farming is that", [
                        "buildings are cheap to construct.",
                        "water is recycled continuously.",
                        "crops grow faster than in fields.",
                        "the air in cities becomes cleaner.",
                    ]),
                    mcq(13, "What is the writer's overall view of vertical farming?", [
                        "It will soon replace traditional farming.",
                        "It is too expensive to be of any real use.",
                        "It is a valuable addition to conventional agriculture.",
                        "It is only suitable for wealthy countries.",
                    ]),
                ],
            ),
        ],
    },
    {
        "number": 2,
        "title": "The Bilingual Brain",
        "question_range": "14–26",
        "paragraphs": [
            "A  For much of the twentieth century, many teachers and doctors believed that exposing young children to two languages at once was harmful. Children raised bilingually, it was claimed, would become confused, mix up their vocabularies and fall behind their classmates. Parents of immigrant families were sometimes advised to speak only the majority language at home. Modern research has overturned this view almost entirely.",
            "B  Brain-imaging studies show that when bilingual people use one language, the other does not simply switch off. Both remain active, competing for attention. A bilingual speaker ordering coffee in English may still have the equivalent words in Spanish or Uzbek partially activated. To speak smoothly, the brain's prefrontal cortex must constantly monitor the situation, select the target language and suppress interference from the other one.",
            "C  This continuous mental exercise appears to strengthen what psychologists call the executive control network: the set of brain systems that manage attention, planning and switching between tasks. In laboratory tests, bilingual children and adults are often better at ignoring irrelevant information and at switching quickly from one rule to another. These are not abstract abilities; they are used every day, from driving in heavy traffic to working in a noisy office.",
            "D  Perhaps the most striking evidence comes from studies of older people. A team in Toronto examined the medical records of several hundred patients diagnosed with Alzheimer's disease. Those who had spoken two or more languages throughout their lives had developed symptoms, on average, four to five years later than those who spoke only one. Bilingualism did not prevent the disease, but it seemed to build up a cognitive reserve that allowed the brain to cope with damage for longer.",
            "E  Encouragingly, the benefits are not limited to those who grew up with two languages. Studies of university students and retired adults taking intensive language courses have found measurable changes in brain structure after only a few months of study. Fluency is not required for these changes to appear. The brain, it seems, retains its structural plasticity throughout life, and learning a language is one of the most effective ways to use it.",
        ],
        "groups": [
            group(
                "matching",
                "The passage has five paragraphs, A–E. Choose the correct heading for each paragraph from the list of headings below.",
                [
                    item(14, "Paragraph A"),
                    item(15, "Paragraph B"),
                    item(16, "Paragraph C"),
                    item(17, "Paragraph D"),
                    item(18, "Paragraph E"),
                ],
                box_title="List of Headings",
                box=lettered([
                    "Protection against decline in later life",
                    "A constant competition inside the mind",
                    "The economic value of speaking several languages",
                    "An outdated belief about children and two languages",
                    "It is never too late to start",
                    "Everyday mental skills that improve",
                    "Why some bilinguals forget their first language",
                ], roman=True),
            ),
            group(
                "mcq",
                "Choose the correct letter, A, B, C or D.",
                [
                    mcq(19, "In the twentieth century, many experts believed bilingual children would", [
                        "become confused between their languages.",
                        "learn to read earlier than other children.",
                        "lose interest in school.",
                        "speak both languages with an accent.",
                    ]),
                    mcq(20, "According to paragraph B, the prefrontal cortex", [
                        "is larger in bilingual people from birth.",
                        "stores the vocabulary of both languages.",
                        "selects one language and suppresses the other.",
                        "stops working when only one language is used.",
                    ]),
                    mcq(21, "The Toronto study found that bilingual patients", [
                        "recovered more quickly from surgery.",
                        "showed symptoms of dementia later than monolingual patients.",
                        "never developed Alzheimer's disease.",
                        "had larger vocabularies than other patients.",
                    ]),
                    mcq(22, "What is the main point of paragraph E?", [
                        "Children are the only group who benefit.",
                        "The benefits depend on becoming fully fluent.",
                        "Teaching methods matter more than age.",
                        "Even adults who start late can show changes in the brain.",
                    ]),
                ],
            ),
            group(
                "gap",
                "Complete the summary below. Choose ONE WORD ONLY from the passage for each answer.",
                [
                    gap(23, "Managing two languages strengthens the brain's ____ control network."),
                    gap(24, "As a result, bilinguals are often better at selective ____ and switching between tasks."),
                    gap(25, "Lifelong bilingualism may delay the symptoms of Alzheimer's and other forms of ____."),
                    gap(26, "Language learning at any age makes use of the brain's structural ____."),
                ],
                title="Summary",
            ),
        ],
    },
    {
        "number": 3,
        "title": "Life in the Dark: Hydrothermal Vents",
        "question_range": "27–40",
        "paragraphs": [
            "In 1977, scientists aboard the research submarine Alvin descended more than two kilometres to the floor of the Pacific Ocean near the Galápagos Islands. They were looking for hot springs on the sea floor, which geologists had predicted. What they found instead was something no one had predicted at all: thriving communities of giant tube worms, clams and crabs, living in complete darkness. It is hard to overstate how surprising this was. Biologists had assumed that the deep sea floor was almost empty, because all food chains were thought to depend, ultimately, on sunlight.",
            "The vent communities proved that assumption wrong. The bacteria at their base do not use light at all. Instead they obtain energy through chemosynthesis, oxidising chemicals such as hydrogen sulfide and methane that pour out of the vents, and using that energy to turn carbon dioxide into organic matter. The worms and clams, in turn, live off the bacteria. This is a food chain that would continue to function even if the sun disappeared.",
            "The first vents to be studied were so-called 'black smokers': chimneys that release water at temperatures of up to 400°C, extremely acidic and dark with dissolved metals. In 2000, however, researchers on an expedition investigating an underwater mountain in the Atlantic came across a very different kind of vent by accident. They named the field 'Lost City'. Its white towers, some as tall as a twenty-storey building, release water that is warm rather than scalding, and alkaline rather than acidic.",
            "For many scientists, Lost City changed the debate about the origin of life. The rock walls of alkaline vents are riddled with tiny pores, separated by thin mineral walls. Because the vent fluid is alkaline and the surrounding seawater was, on the early Earth, slightly acidic, a natural difference in the concentration of protons builds up across these walls. This matters because every living cell today powers itself in a remarkably similar way: by pumping protons across its membranes and using the resulting gradient to make energy. In this view, the mineral walls acted like the first cell membranes, while iron-sulfur minerals in the rock served as primitive catalysts, speeding up the reactions that turn carbon dioxide into the building blocks of life.",
            "In my view, this alkaline vent hypothesis is currently the most persuasive account we have of how life began. It explains why such a strange mechanism is shared by all living things, and it places the origin of life in an environment that we know existed on the early Earth. That is not to say the question is settled. Critics argue that in the open ocean, the key organic molecules would have been far too dilute to react with one another, unlike in the shallow, drying pools favoured by rival theories. And it should be said clearly that, despite many attempts, nobody has yet produced anything resembling a living cell under vent conditions in the laboratory.",
            "Whatever the final answer, the vents have already taught us something profound. If life can flourish in total darkness, powered by chemistry alone, then the icy moons of Jupiter and Saturn, which are thought to have oceans and perhaps vents of their own beneath their frozen surfaces, have become some of the most exciting places to search for life beyond the Earth.",
        ],
        "groups": [
            group(
                "ynng",
                "Do the following statements agree with the claims of the writer? Choose YES if the statement agrees with the claims of the writer, NO if the statement contradicts the claims of the writer, NOT GIVEN if it is impossible to say what the writer thinks about this.",
                [
                    item(27, "The discovery of animal communities at the vents in 1977 was unexpected."),
                    item(28, "The food chain at the vents depends ultimately on sunlight."),
                    item(29, "Vent communities contain a greater variety of species than coral reefs."),
                    item(30, "The alkaline vent hypothesis is the most convincing explanation currently available."),
                    item(31, "Scientists have already created simple living cells under vent conditions."),
                ],
            ),
            group(
                "mcq",
                "Choose the correct letter, A, B, C or D.",
                [
                    mcq(32, "Black smokers are different from the vents at Lost City because they", [
                        "are found in shallower water.",
                        "do not release any minerals.",
                        "are extremely hot and acidic.",
                        "remain active for a longer time.",
                    ]),
                    mcq(33, "The Lost City vent field was discovered", [
                        "by chance during an expedition with another purpose.",
                        "with the help of satellite data.",
                        "during the same expedition as the first vents.",
                        "by an unmanned underwater robot.",
                    ]),
                    mcq(34, "Why are proton gradients at alkaline vents considered important?", [
                        "They keep the vent water at a stable temperature.",
                        "They produce light that bacteria can use.",
                        "They attract bacteria from the open ocean.",
                        "They resemble the way all living cells produce energy.",
                    ]),
                    mcq(35, "Which criticism of the alkaline vent hypothesis does the writer mention?", [
                        "Such vents were too rare on the early Earth.",
                        "Organic molecules would have been too dilute in the open ocean.",
                        "The vents are too young to be relevant.",
                        "The water at the vents is too cold for chemical reactions.",
                    ]),
                ],
            ),
            group(
                "gap",
                "Complete the sentences below. Choose ONE WORD ONLY from the passage for each answer.",
                [
                    gap(36, "Bacteria at the vents make food through a process called ____."),
                    gap(37, "Unlike black smokers, the Lost City vents are ____."),
                    gap(38, "The thin mineral walls of the vents may have acted like the first cell ____."),
                    gap(39, "Iron-sulfur minerals may have served as primitive ____."),
                ],
            ),
            group(
                "mcq",
                "Choose the correct letter, A, B, C or D.",
                [
                    mcq(40, "Which is the most suitable title for the passage?", [
                        "The deep-sea cradle: rethinking where life began",
                        "How scientists explore the ocean floor",
                        "The dangers of mining hydrothermal vents",
                        "Why bacteria can survive extreme heat",
                    ]),
                ],
            ),
        ],
    },
]

READING_ANSWER_KEY = {
    "1": "TRUE", "2": "FALSE", "3": "NOT GIVEN", "4": "TRUE", "5": "FALSE", "6": "TRUE",
    "7": "nutrients", "8": "LED", "9": "pesticides", "10": "transport", "11": "pollination",
    "12": "B", "13": "C",
    "14": "iv", "15": "ii", "16": "vi", "17": "i", "18": "v",
    "19": "A", "20": "C", "21": "B", "22": "D",
    "23": "executive", "24": "attention", "25": "dementia", "26": "plasticity",
    "27": "YES", "28": "NO", "29": "NOT GIVEN", "30": "YES", "31": "NO",
    "32": "C", "33": "A", "34": "D", "35": "B",
    "36": "chemosynthesis", "37": "alkaline", "38": "membranes", "39": "catalysts", "40": "A",
}
