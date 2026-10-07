"""Uzbekistan Multilevel (CEFR B1–C1) practice test — Listening & Reading Set 1 (original content).

The structure follows the 6-part Listening / 5-part Reading layout used by this platform's 40-item
scoring. Scripts contain the answers and are server-only.
"""

from __future__ import annotations

from app.services.content.builders import gap, group, item, lettered, mcq

CAMPUS_MAP_SVG = """<svg viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Campus plan with buildings A to H" font-family="Arial, sans-serif" font-size="14">
<rect x="0" y="0" width="420" height="320" fill="#f8fafc" stroke="#94a3b8"/>
<rect x="190" y="70" width="40" height="250" fill="#e2e8f0"/>
<rect x="20" y="150" width="380" height="30" fill="#e2e8f0"/>
<circle cx="210" cy="165" r="22" fill="#bae6fd" stroke="#0284c7"/>
<text x="210" y="170" text-anchor="middle" font-size="10">Fountain</text>
<g fill="#ffffff" stroke="#334155" stroke-width="1.5">
<rect x="25" y="20" width="110" height="70"/><rect x="155" y="10" width="110" height="55"/><rect x="285" y="20" width="110" height="70"/>
<rect x="25" y="95" width="110" height="50"/><rect x="285" y="95" width="110" height="50"/>
<rect x="25" y="200" width="110" height="80"/><rect x="285" y="200" width="110" height="80"/>
<rect x="240" y="235" width="35" height="35"/>
</g>
<g font-weight="bold" font-size="20" text-anchor="middle" fill="#1e3a8a">
<text x="80" y="62">A</text><text x="210" y="45">D</text><text x="340" y="62">G</text>
<text x="80" y="127">C</text><text x="340" y="127">E</text>
<text x="80" y="247">B</text><text x="340" y="247">F</text><text x="257" y="259">H</text>
</g>
<text x="210" y="312" text-anchor="middle" font-size="12">▲ MAIN ENTRANCE</text>
</svg>"""

LISTENING_PARTS = [
    {
        "number": 1,
        "title": "Part 1 — Short conversations",
        "context": "You will hear eight short conversations. There is one question for each conversation.",
        "groups": [
            group(
                "mcq",
                "Listen and choose the correct answer, A, B or C.",
                [
                    mcq(1, "Where does the train to Samarkand leave from?", ["platform 2", "platform 4", "platform 6"]),
                    mcq(2, "When does the library close on Saturdays?", ["at 8 pm", "at 6 pm", "at 9 pm"]),
                    mcq(3, "What will the woman buy for her brother?", ["a book", "a shirt", "headphones"]),
                    mcq(4, "How will the man get to the airport?", ["by taxi", "by bus", "in his friend's car"]),
                    mcq(5, "Why is the woman calling the clinic?", ["to change the time of an appointment", "to cancel an appointment", "to ask about test results"]),
                    mcq(6, "What does the man think about the film?", ["It was too long.", "It was boring.", "The acting was excellent."]),
                    mcq(7, "How much does the student pay for the course?", ["300,000 som", "250,000 som", "200,000 som"]),
                    mcq(8, "What will the weather be like tomorrow morning?", ["rainy", "sunny", "windy and cold"]),
                ],
            )
        ],
        "script": [
            ("NARRATOR", "Multilevel Listening practice test. Part one. You will hear eight short conversations. For each one, choose the correct answer, A, B or C. You have some time to read the questions."),
            ("PAUSE", "20"),
            ("NARRATOR", "Question one."),
            ("FEMALE_GB", "Excuse me, is the Samarkand train leaving from platform two?"),
            ("MALE_GB", "Er, no, platform two is for the Bukhara train. Samarkand leaves from platform four. Platform six is closed today for repairs."),
            ("NARRATOR", "Question two."),
            ("MALE_IE", "Is the library open late on Saturday?"),
            ("FEMALE_IE", "On weekdays it closes at nine, but on Saturdays it closes at eight. It used to close at six, but they changed the times this year."),
            ("NARRATOR", "Question three."),
            ("MALE_GB", "Have you decided what to get your brother for his birthday? A book again?"),
            ("FEMALE_GB", "Oh, he never reads them! Hmm, I thought about a shirt, but I don't know his size. He's always listening to music, so I'll get him some headphones."),
            ("NARRATOR", "Question four."),
            ("FEMALE_IE", "Is your friend driving you to the airport tomorrow?"),
            ("MALE_IE", "Well, he offered, but his car's being repaired. A taxi is too expensive at that time, so I'll take the airport bus. It leaves from the city centre every half hour."),
            ("NARRATOR", "Question five."),
            ("FEMALE_GB", "Hello, I have an appointment with Doctor Karimova on Friday at ten. I don't want to cancel it, but could I come in the afternoon instead? I have an exam in the morning."),
            ("MALE_GB", "Let me see... yes, three o'clock is free."),
            ("NARRATOR", "Question six."),
            ("FEMALE_IE", "Did you enjoy the film? It was nearly three hours long!"),
            ("MALE_IE", "Honestly, I didn't even notice the time. The story was a bit slow at the start, but the acting was excellent, especially the main actress."),
            ("NARRATOR", "Question seven."),
            ("MALE_GB", "How much is the English course?"),
            ("FEMALE_GB", "It's normally three hundred thousand som a month, but students get a discount, so for you it's two hundred and fifty thousand."),
            ("NARRATOR", "Question eight."),
            ("MALE_IE", "Shall we go hiking tomorrow morning?"),
            ("FEMALE_IE", "The forecast says it'll rain in the morning, and it'll be sunny only in the afternoon. Let's leave after lunch."),
            ("NARRATOR", "That is the end of part one."),
            ("PAUSE", "10"),
        ],
    },
    {
        "number": 2,
        "title": "Part 2 — Announcement: summer internship programme",
        "context": "You will hear an announcement about a summer internship programme.",
        "groups": [
            group(
                "gap",
                "Complete the notes. Write ONE WORD OR A NUMBER for each answer.",
                [
                    gap(9, "Before registering, return all borrowed books to the ____"),
                    gap(10, "Information session: ____ at 3 pm"),
                    gap(11, "Bring a copy of your ____"),
                    gap(12, "Each interview lasts ____ minutes"),
                    gap(13, "Successful interns receive a ____"),
                    gap(14, "Final presentations take place in the main ____"),
                ],
                title="Summer Internship Programme",
            )
        ],
        "script": [
            ("NARRATOR", "Part two. You will hear an announcement about a summer internship programme. Complete the notes. You have some time to read the notes."),
            ("PAUSE", "20"),
            ("FEMALE_GB", "Good morning, students. This is an announcement about this year's summer internship programme at the IT Park. Registration opens next week, but please note: before you can register, you must return all borrowed books to the library. Students with overdue books will not be able to sign up."),
            ("FEMALE_GB", "We are holding an information session for all applicants. It was planned for Wednesday, but it has moved to Thursday at three p.m., in room two hundred and four."),
            ("FEMALE_GB", "When you register, please bring a copy of your passport. We don't need your student card or your diploma at this stage."),
            ("FEMALE_GB", "All applicants will have a short interview with a company representative. Each interview lasts fifteen minutes, so please arrive on time."),
            ("FEMALE_GB", "The internship is unpaid, but successful interns will receive a certificate that can be included in your CV."),
            ("FEMALE_GB", "At the end of the summer, interns will give final presentations about their projects. These will take place in the main auditorium, and families are welcome to attend."),
            ("NARRATOR", "That is the end of part two."),
            ("PAUSE", "10"),
        ],
    },
    {
        "number": 3,
        "title": "Part 3 — Six speakers: learning English",
        "context": "You will hear six people talking about how they learned English.",
        "groups": [
            group(
                "matching",
                "Match each speaker (15–20) to a statement (A–H). There are TWO extra statements you do not need.",
                [
                    item(15, "Speaker 1"),
                    item(16, "Speaker 2"),
                    item(17, "Speaker 3"),
                    item(18, "Speaker 4"),
                    item(19, "Speaker 5"),
                    item(20, "Speaker 6"),
                ],
                box_title="Statements",
                box=lettered([
                    "I improved most by watching TV series.",
                    "A teacher changed my attitude to the language.",
                    "I learned mainly through my job.",
                    "I only started learning as an adult.",
                    "Living abroad helped me most.",
                    "I practised by talking to people online.",
                    "Grammar was always the hardest part for me.",
                    "I failed an important exam the first time.",
                ]),
            )
        ],
        "script": [
            ("NARRATOR", "Part three. You will hear six people talking about how they learned English. Match each speaker to a statement. There are two extra statements. You have some time to read the statements."),
            ("PAUSE", "20"),
            ("NARRATOR", "Speaker one."),
            ("MALE_GB", "At school I studied German, so I didn't learn a single word of English until I was thirty-two, when my company started working with partners in Canada. It was hard at that age, but I passed B2 last year."),
            ("NARRATOR", "Speaker two."),
            ("FEMALE_IE", "Honestly, my classes didn't help much. What really worked was watching American and British TV series every evening, first with subtitles in Uzbek, then in English, and finally without any subtitles at all."),
            ("NARRATOR", "Speaker three."),
            ("MALE_IE", "I'm quite shy, so speaking in class was terrible for me. Then I found a language exchange website, and I started talking to people from all over the world every day on video calls. That's how I became fluent."),
            ("NARRATOR", "Speaker four."),
            ("FEMALE_GB", "I hated English at school. I thought it was boring, all grammar tables. Then in tenth grade we got a new teacher who brought songs and debates into the classroom, and suddenly I loved it. I'm an English teacher myself now."),
            ("NARRATOR", "Speaker five."),
            ("GUIDE_AU", "I studied for years at home, but I really improved when I spent two years working in Australia. You have to speak English all day, at the shops, at work, everywhere. Grammar was never really my problem, it was speaking quickly."),
            ("NARRATOR", "Speaker six."),
            ("MALE_GB", "I work as a hotel receptionist in Khiva, and almost all our guests are foreign. I never took a proper course; I just learned from dealing with guests every day. My first IELTS score wasn't great, but I'm happy with my second one."),
            ("NARRATOR", "That is the end of part three."),
            ("PAUSE", "10"),
        ],
    },
    {
        "number": 4,
        "title": "Part 4 — Campus plan",
        "context": "You will hear a student guide describing the campus to new students.",
        "groups": [
            group(
                "matching",
                "Label the plan. Write the correct letter, A–H, next to Questions 21–25.",
                [
                    item(21, "Library"),
                    item(22, "Cafeteria"),
                    item(23, "Sports hall"),
                    item(24, "Computer lab"),
                    item(25, "Car park"),
                ],
                box=lettered(["", "", "", "", "", "", "", ""]),
                figure_svg=CAMPUS_MAP_SVG,
            )
        ],
        "script": [
            ("NARRATOR", "Part four. You will hear a student guide describing the campus. Look at the plan and label the places. You have some time to look at the plan."),
            ("PAUSE", "20"),
            ("MALE_IE", "Hi everyone, welcome to the campus. We're standing at the main entrance, at the bottom of your plan. As you come in, the building immediately on your left is not a building at all: it's the car park, for staff and students with permits."),
            ("MALE_IE", "The small building just to the right of the path, between the entrance and the fountain, is the security office. The large building on the right, near the entrance, is the medical centre."),
            ("MALE_IE", "Now walk straight up the path to the fountain in the middle. On your left, you'll see the cafeteria, the building directly to the left of the fountain. Opposite the cafeteria, on the right of the fountain, is the computer lab, which is open twenty-four hours a day."),
            ("MALE_IE", "At the top of the path, straight ahead, is the main administration building. In the top left corner, behind the cafeteria, is the sports hall. And in the top right corner, behind the computer lab, is the library, which most of you will use a lot."),
            ("NARRATOR", "That is the end of part four."),
            ("PAUSE", "10"),
        ],
    },
    {
        "number": 5,
        "title": "Part 5 — Radio interview: green tourism",
        "context": "You will hear a radio interview with Dilnoza, who runs an eco-tourism company.",
        "groups": [
            group(
                "mcq",
                "Choose the correct answer, A, B or C.",
                [
                    mcq(26, "What does Dilnoza say about the number of eco-tourists?", ["It has fallen recently.", "It has doubled in five years.", "It has stayed the same."]),
                    mcq(27, "Why do most tourists choose homestays?", ["They are cheaper than hotels.", "They are more comfortable.", "Tourists want to experience local life."]),
                    mcq(28, "What is the main problem for the industry?", ["a lack of trained guides", "poor roads", "high prices"]),
                    mcq(29, "How do villages benefit from eco-tourism?", ["New schools have been built.", "The income stays in the local community.", "Young people have stopped moving to cities."]),
                    mcq(30, "What does Dilnoza recommend to visitors?", ["to travel only in summer", "to bring plenty of cash", "to stay for at least three days"]),
                    mcq(31, "What are her plans for next year?", ["to open a training centre for guides", "to write a travel book", "to expand her business abroad"]),
                ],
            )
        ],
        "script": [
            ("NARRATOR", "Part five. You will hear a radio interview with Dilnoza, who runs an eco-tourism company. Choose the correct answer. You have some time to read the questions."),
            ("PAUSE", "25"),
            ("MALE_GB", "Dilnoza, eco-tourism seems to be growing fast in Uzbekistan. Is that right?"),
            ("FEMALE_IE", "Oh, very fast. Five years ago we had around four thousand eco-tourists a year in our region. Now it's over eight thousand, so the number has doubled."),
            ("MALE_GB", "Many of your guests stay in village homes rather than hotels. Why is that?"),
            ("FEMALE_IE", "Well, people think it's about price, but homestays aren't much cheaper, and they're certainly not more comfortable! Our guests simply want to experience real local life: cooking plov with a family, helping in the garden."),
            ("MALE_GB", "What's the biggest challenge?"),
            ("FEMALE_IE", "The roads have improved a lot, and prices are reasonable. The real problem is that we don't have enough trained guides who speak foreign languages and know about nature."),
            ("MALE_GB", "And what do the villages get out of it?"),
            ("FEMALE_IE", "Most importantly, the money stays in the community. Families earn directly from guests. Unfortunately, young people are still moving to the cities, but perhaps that will change."),
            ("MALE_GB", "Any advice for visitors?"),
            ("FEMALE_IE", "Hmm. Spring and autumn are actually better than summer. Cards are accepted almost everywhere now. My main advice is: don't rush. Stay at least three days, so you really get to know the place."),
            ("MALE_GB", "And next year?"),
            ("FEMALE_IE", "I've been asked to write a book, and some people suggest expanding to Kazakhstan, but my priority is to open a training centre for young guides here."),
            ("NARRATOR", "That is the end of part five."),
            ("PAUSE", "10"),
        ],
    },
    {
        "number": 6,
        "title": "Part 6 — Lecture: smart farming in Central Asia",
        "context": "You will hear part of a lecture about technology in agriculture.",
        "groups": [
            group(
                "gap",
                "Complete the notes. Write ONE WORD ONLY for each answer.",
                [
                    gap(32, "Many farms now use ____ -powered water pumps"),
                    gap(33, "Drip ____ can cut water use by up to 40%"),
                    gap(34, "Soil ____ measure moisture and send data to phones"),
                    gap(35, "Traditional water-intensive crop: ____"),
                    gap(36, "Main aim: to improve water-use ____"),
                    gap(37, "Images from ____ help to monitor crop health"),
                    gap(38, "Biggest need for farmers: ____"),
                    gap(39, "Better quality fruit has increased ____"),
                    gap(40, "Long-term goal: to make farming ____"),
                ],
                title="Smart farming in Central Asia",
            )
        ],
        "script": [
            ("NARRATOR", "Part six. You will hear part of a lecture about smart farming. Complete the notes. You have some time to read the notes."),
            ("PAUSE", "25"),
            ("LECTURER", "Today I'd like to talk about how technology is changing agriculture in Central Asia, where water is the most precious resource."),
            ("LECTURER", "First, energy. Pumping water used to depend on diesel generators, which are expensive and polluting. Now many farms use solar-powered pumps, which cost almost nothing to run once they are installed."),
            ("LECTURER", "Second, the way water reaches the plants. Flooding whole fields wastes enormous amounts of water. Drip irrigation, where water goes directly to the roots through thin pipes, can cut water use by up to forty percent."),
            ("LECTURER", "Third, information. Cheap soil sensors now measure moisture in the ground and send the data to the farmer's phone, so they water only when it is really necessary."),
            ("LECTURER", "This matters because the region traditionally grew cotton, a crop which needs huge amounts of water. The main aim of all these technologies is to improve water-use efficiency, in other words, to grow more food with every litre."),
            ("LECTURER", "Some larger farms also use images from satellites to check crop health across thousands of hectares and to spot disease early."),
            ("LECTURER", "However, technology alone is not enough. When we surveyed farmers, they said money was a problem, but their biggest need was training: they want to learn how to use the new equipment properly."),
            ("LECTURER", "The results are already visible. Better quality fruit and vegetables have increased exports, especially to Russia and China. In the long term, the goal is to make farming in the region sustainable, so that future generations still have water."),
            ("NARRATOR", "That is the end of the listening test. You now have some time to check your answers."),
            ("PAUSE", "10"),
        ],
    },
]

LISTENING_ANSWER_KEY = {
    "1": "B", "2": "A", "3": "C", "4": "B", "5": "A", "6": "C", "7": "B", "8": "A",
    "9": "library", "10": "Thursday", "11": "passport", "12": "15/fifteen", "13": "certificate", "14": "auditorium",
    "15": "D", "16": "A", "17": "F", "18": "B", "19": "E", "20": "C",
    "21": "G", "22": "C", "23": "A", "24": "E", "25": "B",
    "26": "B", "27": "C", "28": "A", "29": "B", "30": "C", "31": "A",
    "32": "solar", "33": "irrigation", "34": "sensors", "35": "cotton", "36": "efficiency",
    "37": "satellites", "38": "training", "39": "exports", "40": "sustainable",
}

READING_PASSAGES = [
    {
        "number": 1,
        "title": "Part 1 — New skills for young people",
        "question_range": "1–6",
        "paragraphs": [
            "NEW SKILLS FOR YOUNG PEOPLE",
            "This autumn, youth centres across Tashkent and Samarkand are opening their doors to school leavers who want to learn practical skills. The project is run by the local (1) ____, and every course is free of charge.",
            "Lessons are taught by (2) ____: experienced professionals who give their time without being paid. They organise weekend (3) ____ on coding, graphic design and starting a small business.",
            "Because modern jobs require (4) ____ skills, every participant receives a laptop to use during the course. Students who work or study during the week can choose a flexible evening (5) ____.",
            "At the end of the course, each team presents a final project, and all participants who complete it receive official (6) ____ which they can show to future employers.",
        ],
        "groups": [
            group(
                "gap",
                "Read the text. Complete each gap (1–6) with ONE WORD from the box. There are more words than you need.",
                [
                    gap(1, "The project is run by the local ____"),
                    gap(2, "Lessons are taught by ____"),
                    gap(3, "They organise weekend ____"),
                    gap(4, "Modern jobs require ____ skills"),
                    gap(5, "Students can choose a flexible evening ____"),
                    gap(6, "Participants receive official ____"),
                ],
                box_title="Word box",
                box=[{"value": w, "label": w} for w in [
                    "certificates", "community", "digital", "salary", "schedule",
                    "volunteers", "workshops", "examinations", "students",
                ]],
            )
        ],
    },
    {
        "number": 2,
        "title": "Part 2 — Choosing a course",
        "question_range": "7–14",
        "paragraphs": [
            "A  WEEKEND PHOTOGRAPHY — Learn to take professional photos with your phone. Saturday mornings in the old city. Bring your own phone.",
            "B  CODING FOR BEGINNERS — No experience needed. Build your first website in eight weeks. Evening classes, online only.",
            "C  BUSINESS ENGLISH — Improve your English for meetings, emails and presentations. Certificate accepted by many international companies.",
            "D  FIRST AID — A one-day course run by doctors. Learn what to do in an emergency. Suitable for parents and teachers.",
            "E  COOKING TRADITIONAL DISHES — Cook plov, samsa and lagman with a professional chef. You eat what you cook!",
            "F  PUBLIC SPEAKING CLUB — Overcome your nerves and speak confidently in front of an audience. Meets every Wednesday.",
            "G  DRIVING THEORY — Prepare for the written part of your driving test. Practice tests every week.",
            "H  GARDENING AT HOME — Grow vegetables and herbs on a balcony or in a small yard. Seeds provided.",
            "I  CHESS CLUB — Play against players of all levels. Tournaments every month.",
            "J  FASHION DESIGN — Design and sew your own clothes. Sewing machines available.",
        ],
        "groups": [
            group(
                "matching",
                "Read the descriptions of eight people (7–14) and the course advertisements (A–J). Choose the most suitable course for each person. There are TWO extra courses.",
                [
                    item(7, "Aziz wants a job in an international company and needs to write better emails in English."),
                    item(8, "Malika loves taking pictures of buildings but cannot afford an expensive camera."),
                    item(9, "Bekzod gets very nervous when he has to talk to a group of people."),
                    item(10, "Nodira works all day and wants to learn to make websites from home."),
                    item(11, "Rustam wants to prepare meals for his family the way his grandmother did."),
                    item(12, "Shahlo is a kindergarten teacher who wants to know how to help a child who is hurt."),
                    item(13, "Jasur has his driving test next month and is worried about the written exam."),
                    item(14, "Zarina lives in a flat and would like to grow her own tomatoes."),
                ],
                box_title="Courses",
                box=lettered(["Weekend Photography", "Coding for Beginners", "Business English", "First Aid", "Cooking Traditional Dishes", "Public Speaking Club", "Driving Theory", "Gardening at Home", "Chess Club", "Fashion Design"]),
            )
        ],
    },
    {
        "number": 3,
        "title": "Part 3 — The new Silk Road",
        "question_range": "15–20",
        "paragraphs": [
            "1  For centuries, the cities of Central Asia grew rich by sitting at the crossroads of trade between China, Persia and Europe. When sea routes became cheaper in the sixteenth century, however, the caravans disappeared, and the region was left far from the main routes of world trade.",
            "2  Today, being landlocked is still a disadvantage. Goods must cross at least one other country before reaching a port, and every border crossing adds time and cost. Studies suggest that landlocked countries pay up to fifty percent more to transport their exports than countries with a coast.",
            "3  Governments have responded by investing heavily in railways. New electrified lines and tunnels through the mountains have shortened journeys considerably, and freight trains now run regularly between China and Europe through the region.",
            "4  Equally important have been changes at the borders. Automated customs systems allow documents to be checked electronically before a train arrives. As a result, waiting times at some crossings have fallen from several days to a few hours.",
            "5  Rail transport is also cleaner than road transport. An electric freight train produces a fraction of the carbon emissions of the lorries needed to carry the same goods, which makes the new corridors attractive to European companies trying to reduce their environmental impact.",
            "6  Not everyone is convinced. Critics point out that many trains travel back from Europe almost empty, because the region imports far more than it exports. Unless local industries grow, they argue, the new Silk Road may benefit transit traffic more than local people.",
        ],
        "groups": [
            group(
                "matching",
                "Read the text. Choose the correct heading (A–H) for each paragraph (15–20). There are TWO extra headings.",
                [
                    item(15, "Paragraph 1"),
                    item(16, "Paragraph 2"),
                    item(17, "Paragraph 3"),
                    item(18, "Paragraph 4"),
                    item(19, "Paragraph 5"),
                    item(20, "Paragraph 6"),
                ],
                box_title="Headings",
                box=lettered([
                    "The hidden cost of having no coastline",
                    "Faster checks, shorter queues",
                    "An environmental advantage",
                    "From centre of trade to isolation",
                    "Doubts about who really benefits",
                    "Building new routes through the mountains",
                    "The return of the camel caravans",
                    "Why air freight is growing fastest",
                ]),
            )
        ],
    },
    {
        "number": 4,
        "title": "Part 4 — Working from anywhere",
        "question_range": "21–29",
        "paragraphs": [
            "When Kamola graduated in computer science three years ago, her parents had a clear plan for her. Like many families in the regions, they hoped she would move to Tashkent and take a secure position with one of the large banks, where a cousin had already built a successful career. Kamola briefly considered applying for a master's degree abroad instead, but in the end she did neither. Today she works as a freelance designer for clients in Germany, Singapore and the United States, all from a small desk in her family's home in Namangan. She is part of a fast-growing group of young Uzbeks who earn foreign salaries without ever leaving the country.",
            "The attraction is not difficult to understand. Kamola estimates that she earns roughly three times what a local bank would pay a new graduate, and, perhaps more importantly for her, she decides when she works. 'I can work late at night, when my clients in America are awake, and spend the afternoon with my grandmother,' she says. Her clients are polite and pay on time, but she admits that she has never met any of them, and the relationship is purely professional. Online platforms have made it possible to find work anywhere in the world, and since high-speed internet reached most regional cities a few years ago, the location of a freelancer's desk has become almost irrelevant.",
            "Yet this freedom comes at a price. Freelancers receive no paid holidays and no pension contributions, and if they fall ill, nobody pays them for the days they cannot work. Income can rise and fall dramatically from one month to the next. Kamola remembers that during her first year there were two separate months in which she earned almost nothing, and she had to borrow money from her brother to cover her expenses. At one point she was convinced that her main client was about to replace her with a cheaper designer; in fact, he increased her workload. Tax, she says, has never been a problem, as the paperwork for IT freelancers is now quite simple.",
            "Loneliness is a difficulty that is rarely mentioned in advertisements for the freelance lifestyle. Without colleagues, many remote workers say they miss the casual conversations and friendships of an office, and some find it hard to stay motivated. To meet this need, coworking spaces have opened in several cities, where freelancers pay a monthly fee to rent a desk and work alongside others. Their internet connections are no faster than those most people have at home, and clients rarely visit; what people are really paying for is company. Kamola goes to one in Namangan twice a week and says it has changed her working life.",
            "Economists, however, are divided about what the trend means for the wider economy. Some point out that foreign income spent locally supports shops, restaurants and services, and that young people who can earn well at home are less likely to emigrate. Others warn that many of the most talented graduates are no longer joining local companies, which may make it harder for those firms to grow and to train the next generation of specialists. The government, for its part, has introduced a simplified tax regime for IT freelancers, in the hope of keeping their earnings visible in official statistics rather than in the informal economy.",
        ],
        "groups": [
            group(
                "mcq",
                "Read the text and answer questions 21–24. Choose the correct answer, A, B, C or D.",
                [
                    mcq(21, "Kamola's parents had hoped that after university she would", ["follow her cousin abroad.", "take a job in the financial sector in the capital.", "set up a company of her own.", "continue her studies with a master's degree."]),
                    mcq(22, "What does Kamola value most about her present work?", ["the opportunity to travel", "her close relationships with clients", "her earnings and control over her timetable", "the predictability of her income"]),
                    mcq(23, "During her first year as a freelancer, Kamola", ["went through periods with very little income.", "lost her most important client.", "received an unexpectedly large tax bill.", "was unable to work because of illness."]),
                    mcq(24, "According to the writer, people pay to use coworking spaces mainly because", ["the internet connection is better than at home.", "they need somewhere to meet clients.", "it is cheaper than working from home.", "they want to be around other people."]),
                ],
            ),
            group(
                "tfng",
                "Do the statements (25–29) agree with the information in the text? Choose TRUE, FALSE or NOT GIVEN.",
                [
                    item(25, "Kamola's clients are based in several different countries."),
                    item(26, "High-speed internet has not yet spread beyond the capital."),
                    item(27, "Most of Kamola's fellow graduates now work for foreign companies."),
                    item(28, "Freelancers must cope with periods of illness without financial help from an employer."),
                    item(29, "Economists share the view that remote work benefits the national economy."),
                ],
            ),
        ],
    },
    {
        "number": 5,
        "title": "Part 5 — Powering the future",
        "question_range": "30–40",
        "paragraphs": [
            "Uzbekistan has set itself an ambitious target: to generate a large share of its electricity from renewable sources within the next decade. In many respects the country is well placed to do so. It enjoys more than three hundred sunny days a year, and the desert regions of Navoi and Karakalpakstan experience strong and fairly reliable winds. Large solar and wind farms, most of them financed and built by foreign companies, have already begun to supply power to the national network, and further projects are planned.",
            "Building power stations, however, is in some ways the easy part. The electricity networks that most countries inherited from the twentieth century were designed around large coal and gas plants, which produce a steady and predictable flow of power that can be increased or reduced on demand. Solar and wind are fundamentally different. Their output rises and falls with the weather and the time of day, and the best locations for generating them are often hundreds of kilometres from the cities where the electricity is consumed. Unless the infrastructure that carries power across the country is substantially upgraded, a considerable proportion of this new energy may simply be wasted, because the existing lines cannot transport it to where it is needed.",
            "Water offers part of the answer. Hydropower, generated by water held behind dams, has the great advantage that it can be switched on within minutes when the sun sets or the wind drops, smoothing out the fluctuations of other renewable sources. Some engineers go further and propose pumped storage, in which surplus solar electricity produced around midday is used to pump water to a reservoir higher up, so that it can be released through turbines in the evening, when demand is at its peak. The difficulty is that suitable sites are limited, and the region's rivers are already under heavy pressure from agriculture.",
            "For this reason, many specialists argue that the most important investment is not in generation at all but in intelligence. A modern grid equipped with digital sensors and artificial intelligence can forecast both production and consumption hours in advance, and automatically direct electricity from areas with a surplus to areas with a shortage. Through regional power-sharing agreements, it can even move electricity across national borders, so that a windy evening in one country can make up for a still evening in its neighbour. Such cooperation existed in Central Asia during the Soviet period and is now being gradually revived.",
            "None of this will be cheap. Estimates of the investment required run to many billions of dollars, and governments are unable to provide most of it themselves. Private companies, both domestic and foreign, are willing to commit their money, but only if they can be confident that the rules will not change unexpectedly and that the prices they receive for their electricity will be fair over the twenty or thirty years that a power station operates. If these conditions are met, the rewards could be considerable: cleaner air in the cities, more natural gas available for export rather than domestic use, and a significant reduction in the greenhouse gas emissions that contribute to climate change. If they are not, the gleaming solar panels in the desert may stand idle for much of the day.",
        ],
        "groups": [
            group(
                "gap",
                "Complete the summary (30–35). Write ONE WORD ONLY from the text for each answer.",
                [
                    gap(30, "Without improvements to the ____ that transports electricity, much new power could be lost."),
                    gap(31, "The country aims to produce a large proportion of its electricity from ____ sources such as the sun and wind."),
                    gap(32, "Power from water held behind dams, known as ____, can respond within minutes when solar output falls."),
                    gap(33, "A modern ____ can predict supply and demand and redirect power automatically."),
                    gap(34, "Much of the ____ required will have to come from the private sector."),
                    gap(35, "If the plan succeeds, the country's greenhouse gas ____ will fall significantly."),
                ],
                title="Summary",
            ),
            group(
                "mcq",
                "Choose the correct answer, A, B, C or D (36–40).",
                [
                    mcq(36, "According to the writer, why do solar and wind power create problems for older networks?", ["They cost more to produce than coal.", "Their supply is variable and often far from users.", "They require large numbers of foreign engineers.", "They cannot be connected to existing power stations."]),
                    mcq(37, "In a pumped storage system, extra solar electricity is used to", ["raise water to a higher reservoir.", "heat water for nearby cities.", "charge batteries in electric vehicles.", "remove salt from river water."]),
                    mcq(38, "What does the writer say about regional power-sharing agreements?", ["They are a completely new idea in Central Asia.", "They allow countries to exchange natural gas.", "They make it possible to move electricity between countries.", "They are opposed by most private investors."]),
                    mcq(39, "Private companies will invest in renewable energy if", ["governments build the power stations first.", "taxes on electricity are reduced immediately.", "consumers agree to pay higher prices.", "the rules are stable and prices are fair in the long term."]),
                    mcq(40, "What is the writer's main purpose in the text?", ["to criticise the role of foreign investors", "to explain the conditions needed for the energy transition to succeed", "to describe the history of hydropower in the region", "to compare Uzbekistan's energy policy with its neighbours'"]),
                ],
            ),
        ],
    },
]

READING_ANSWER_KEY = {
    "1": "community", "2": "volunteers", "3": "workshops", "4": "digital", "5": "schedule", "6": "certificates",
    "7": "C", "8": "A", "9": "F", "10": "B", "11": "E", "12": "D", "13": "G", "14": "H",
    "15": "D", "16": "A", "17": "F", "18": "B", "19": "C", "20": "E",
    "21": "B", "22": "C", "23": "A", "24": "D",
    "25": "TRUE", "26": "FALSE", "27": "NOT GIVEN", "28": "TRUE", "29": "FALSE",
    "30": "infrastructure", "31": "renewable", "32": "hydropower", "33": "grid", "34": "investment", "35": "emissions",
    "36": "B", "37": "A", "38": "C", "39": "D", "40": "B",
}
