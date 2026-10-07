"""IELTS Academic practice test — Listening & Reading Set 1 (original content, written for this platform).

Calibrated against authentic Cambridge IELTS Academic papers: long passages (~850-950 words),
paraphrased questions, distractors in the recordings, and the full range of task types
(table / note / summary completion, phrase-bank summaries, "Choose TWO", matching information,
matching features, writer's-purpose MCQs, TFNG and YNNG).

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
        "title": "Part 1 — Volunteering enquiry",
        "context": "You will hear a man phoning a volunteer centre.",
        "groups": [
            group(
                "gap",
                "Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.",
                [
                    gap(1, "Name: Daniel ____"),
                    gap(2, "Postcode: ____"),
                    gap(3, "Preferred area of work: the ____"),
                    gap(4, "Previous experience: helped at a ____ for two summers"),
                    gap(5, "Available on ____ mornings"),
                ],
                title="RIVERSIDE VOLUNTEER CENTRE — Enquiry form",
            ),
            group(
                "gap",
                "Complete the table below. Write ONE WORD AND/OR A NUMBER for each answer.",
                [
                    gap(6, "Training: one session lasting ____ hours"),
                    gap(7, "Reference: must come from a ____"),
                    gap(8, "Clothing: old clothes and strong ____"),
                    gap(9, "Food: a free ____ after each shift"),
                    gap(10, "Parking: in the car park behind the ____"),
                ],
                title="Information for new volunteers",
                table={
                    "columns": ["Topic", "Details"],
                    "rows": [
                        ["Training", "one session on a Saturday, lasting [[6]] hours"],
                        ["Reference", "must come from a [[7]]"],
                        ["Clothing", "old clothes and strong [[8]] (gloves are provided)"],
                        ["Food", "a free [[9]] after each shift"],
                        ["Parking", "in the car park behind the [[10]]"],
                    ],
                },
            ),
        ],
        "script": [
            ("NARRATOR", "IELTS Academic Listening practice test. Part one. You will hear a man telephoning a volunteer centre to ask about volunteering. First, you have some time to look at questions one to five."),
            ("PAUSE", "25"),
            ("NARRATOR", "You will see that there is an example. This time only, the conversation relating to the example is played first."),
            ("FEMALE_GB", "Good morning, Riverside Volunteer Centre, Megan speaking."),
            ("MALE_GB", "Oh, hi. I saw your advert in the local paper, the one asking for volunteers for the spring season, and I wanted to find out a bit more."),
            ("NARRATOR", "The man saw the advert in the local paper. Now we shall begin. You should answer the questions as you listen, because you will not hear the recording a second time. Listen carefully and answer questions one to five."),
            ("FEMALE_GB", "Good morning, Riverside Volunteer Centre, Megan speaking."),
            ("MALE_GB", "Oh, hi. I saw your advert in the local paper, the one asking for volunteers for the spring season, and I wanted to find out a bit more."),
            ("FEMALE_GB", "Of course. Shall I take a few details first, and then I can explain how it all works?"),
            ("MALE_GB", "Sure, that's fine."),
            ("FEMALE_GB", "Can I have your name, please?"),
            ("MALE_GB", "Yes, it's Daniel Fairbrook."),
            ("FEMALE_GB", "Is that F, A, I, R, B, R, double O, K?"),
            ("MALE_GB", "That's it. People often put an E on the end, but there isn't one."),
            ("FEMALE_GB", "No E. Got it. And your address?"),
            ("MALE_GB", "Fourteen Elmfield Road, in Hucclecote."),
            ("FEMALE_GB", "And the postcode?"),
            ("MALE_GB", "G, L, four, seven, T, R."),
            ("FEMALE_GB", "Sorry, was that seven, D, R?"),
            ("MALE_GB", "No, T. T for Tango. Seven, T, R."),
            ("FEMALE_GB", "Thanks. Now, we have volunteers working in several different areas. There's the café, the gift shop, and outdoors in the garden. Do you have a preference?"),
            ("MALE_GB", "Hmm. Well, I did think about the café, because I've done a bit of cooking at home, but honestly, I'd much rather be outside. So the garden, if you've got space."),
            ("FEMALE_GB", "We certainly have. We're always short of people there. And have you done any volunteering before?"),
            ("MALE_GB", "Not officially. I did help out at a garden centre for one weekend, but the main thing was two summers at my local library, running a reading club for young children."),
            ("FEMALE_GB", "That's lovely. I'll put that down. So when would you be available?"),
            ("MALE_GB", "Weekdays are a bit tricky because of my course. I was going to say Tuesday mornings, but I've just found out I've got a lecture then, so, er, Thursday mornings would be best."),
            ("FEMALE_GB", "Thursday mornings. That works well, actually, because that's when the garden team meets."),
            ("NARRATOR", "Before you hear the rest of the conversation, you have some time to look at questions six to ten."),
            ("PAUSE", "25"),
            ("NARRATOR", "Now listen and answer questions six to ten."),
            ("FEMALE_GB", "So, a few practical things. Everyone has to do an introductory training session before they start. It used to be a whole day, but people found that rather a lot, so we've cut it down to three hours. It's always on a Saturday."),
            ("MALE_GB", "That's fine."),
            ("FEMALE_GB", "We also need a reference. Most people ask a previous employer, but as you're a student, it should really come from one of your tutors."),
            ("MALE_GB", "OK. I'll ask my tutor this week."),
            ("FEMALE_GB", "As for clothing, you will get muddy, so please wear old clothes. We provide gloves and all the tools, but you'll need to bring strong boots. Trainers really aren't suitable on the wet ground."),
            ("MALE_GB", "Right. Should I bring something to eat?"),
            ("FEMALE_GB", "You might want a snack, but we give all our volunteers a free lunch in the café at the end of each shift."),
            ("MALE_GB", "Brilliant. And is there anywhere to park? I'll probably drive."),
            ("FEMALE_GB", "The car park at the front is only for visitors, I'm afraid, so please don't use that. But there's a smaller one behind the church on the corner, and volunteers can park there for free."),
            ("MALE_GB", "Perfect. Thanks very much, Megan."),
            ("NARRATOR", "That is the end of part one. You now have one minute to check your answers to part one."),
            ("PAUSE", "30"),
        ],
    },
    {
        "number": 2,
        "title": "Part 2 — Harbourside Arts Festival: volunteer briefing",
        "context": "You will hear the festival manager talking to a group of volunteers.",
        "groups": [
            group(
                "mcq",
                "Choose the correct letter, A, B or C.",
                [
                    mcq(11, "What is different about the festival this year?", [
                        "It will last longer than before.",
                        "It is being held in a new location.",
                        "Tickets are cheaper than last year.",
                    ]),
                    mcq(12, "Most of the festival's funding now comes from", [
                        "local businesses.",
                        "the city council.",
                        "ticket sales.",
                    ]),
                    mcq(13, "Volunteers at the information tents must", [
                        "carry a radio with them at all times.",
                        "keep their badge visible while on duty.",
                        "have completed a first aid course.",
                    ]),
                    mcq(14, "The main aim of the festival this year is to", [
                        "attract a younger audience.",
                        "support artists from the local area.",
                        "raise money for the harbour restoration.",
                    ]),
                ],
            ),
            group(
                "multi",
                "Choose TWO letters, A–E.",
                [
                    item(15, "Which TWO things should volunteers NOT do?"),
                    item(16, "Which TWO things should volunteers NOT do?"),
                ],
                box=lettered([
                    "give visitors directions",
                    "accept money from visitors",
                    "take photographs of performers",
                    "sell festival programmes",
                    "explain the refund policy",
                ]),
            ),
            group(
                "matching",
                "What does the speaker say about each venue? Choose FOUR answers from the box and write the correct letter, A–F, next to Questions 17–20.",
                [
                    item(17, "The Boathouse"),
                    item(18, "The Customs Hall"),
                    item(19, "Lighthouse Lawn"),
                    item(20, "Market Square"),
                ],
                box_title="Comments",
                box=lettered([
                    "wheelchair users must use a side entrance",
                    "has the largest capacity",
                    "will close early on one day",
                    "needs more volunteers",
                    "is being used for the first time",
                    "has very limited seating",
                ]),
            ),
        ],
        "script": [
            ("NARRATOR", "Part two. You will hear the manager of an arts festival talking to a group of volunteers. First, you have some time to look at questions eleven to sixteen."),
            ("PAUSE", "30"),
            ("NARRATOR", "Now listen carefully and answer questions eleven to sixteen."),
            ("GUIDE_AU", "Good evening, everyone, and thank you all for coming along to this briefing. I know some of you have helped us before, but for those who are new, let me start with what's changed this year."),
            ("GUIDE_AU", "Those of you who were with us last time will remember that the festival ran for ten days. We did talk about extending it to two weeks, but in the end we decided that ten days is about right, so that's staying the same. The big difference is that we've moved from Victoria Park down to the harbour front, which gives us a lot more space. And I'm pleased to say that, despite rising costs, ticket prices haven't gone up at all; they're exactly what they were last year."),
            ("GUIDE_AU", "People often assume that the city council pays for all this. That used to be partly true, but the council's grant was reduced this year, and it now covers less than a fifth of our costs. Ticket sales help, of course, but the bulk of our money, around sixty per cent, comes from sponsorship by firms here in town, everything from bakeries to shipping companies, and we're very grateful to them."),
            ("GUIDE_AU", "Now, for those of you working at the information tents. You'll each be given a radio, but it's really only for emergencies, so it can stay in the tent; you don't need to carry it around. First aid is being handled by a professional team, so no medical training is needed. The one thing I do insist on is that your volunteer badge is clearly visible for the whole time you're on duty, so that visitors know who to come to."),
            ("GUIDE_AU", "You might be wondering what we're hoping to achieve. We'll always showcase local artists, and part of our profits will go to the harbour restoration fund, as usual. But over the last few years our audience has been getting steadily older, and the board has decided that this year the top priority is bringing in people under twenty-five. That's why you'll see so many more free events in the evenings."),
            ("GUIDE_AU", "Right, a few dos and don'ts. Giving directions is a huge part of the job, so please do help people find their way around. If someone asks about refunds, you're welcome to explain the policy; it's printed on the back of your card. Programmes are on sale at every tent, and you can sell those too. However, if a visitor offers you money as a thank-you, you must politely refuse it, however kind the gesture. And please don't take pictures of the performers, not even on your own phone, because of our agreements with the artists."),
            ("NARRATOR", "Before you hear the rest of the talk, you have some time to look at questions seventeen to twenty."),
            ("PAUSE", "25"),
            ("NARRATOR", "Now listen and answer questions seventeen to twenty."),
            ("GUIDE_AU", "Finally, let me say a word about the main venues. The Boathouse is a beautiful old building, and it's perfect for poetry readings, but there's only room for about forty chairs, so expect quite a few people standing at the back."),
            ("GUIDE_AU", "The Customs Hall, by contrast, can hold eight hundred people, so that's where all the big concerts will be. And it's fully accessible: wheelchair users can come straight in through the main doors."),
            ("GUIDE_AU", "Lighthouse Lawn will host the outdoor theatre. Because of noise regulations near the houses, everything there finishes at six o'clock on the Sunday, rather than ten as on the other days."),
            ("GUIDE_AU", "And lastly, Market Square. Some of you may think it's a new venue, but we actually used it two years ago. What is different is that we've doubled the number of food stalls there, so we really need more of you there than we currently have on the rota. Right, any questions?"),
            ("NARRATOR", "That is the end of part two. You now have some time to check your answers."),
            ("PAUSE", "20"),
        ],
    },
    {
        "number": 3,
        "title": "Part 3 — Tutorial: research on the four-day working week",
        "context": "You will hear two students, Leila and Marcus, discussing their project with their tutor.",
        "groups": [
            group(
                "mcq",
                "Choose the correct letter, A, B or C.",
                [
                    mcq(21, "Why did the students choose the four-day week as their topic?", [
                        "Their tutor recommended it.",
                        "A relative of Marcus works for a company in the trial.",
                        "It has received a lot of media attention.",
                    ]),
                    mcq(22, "What surprised Leila about the results of the trial?", [
                        "Productivity stayed the same.",
                        "Employees took fewer days off sick.",
                        "Managers were the most enthusiastic group.",
                    ]),
                    mcq(23, "What problem did the students have with their survey?", [
                        "They received too few responses.",
                        "Some questions were interpreted differently.",
                        "It was sent out at a busy time of year.",
                    ]),
                    mcq(24, "The tutor suggests that the students should", [
                        "interview a trade union representative.",
                        "compare the results with other countries.",
                        "concentrate on a single industry.",
                    ]),
                ],
            ),
            group(
                "multi",
                "Choose TWO letters, A–E.",
                [
                    item(25, "Which TWO disadvantages of the four-day week will the students include in their report?"),
                    item(26, "Which TWO disadvantages of the four-day week will the students include in their report?"),
                ],
                box=lettered([
                    "higher prices for customers",
                    "difficulty arranging meetings",
                    "tiredness caused by longer working days",
                    "shorter opening hours for customers",
                    "staff feeling guilty about time off",
                ]),
            ),
            group(
                "matching",
                "Who will do each of the following tasks? Write the correct letter, A, B or C, next to Questions 27–30.",
                [
                    item(27, "contact the companies"),
                    item(28, "design the slides"),
                    item(29, "write the literature review"),
                    item(30, "prepare the handout"),
                ],
                box_title="People",
                box=lettered(["Leila", "Marcus", "both Leila and Marcus"]),
            ),
        ],
        "script": [
            ("NARRATOR", "Part three. You will hear two students, Leila and Marcus, talking to their tutor about a research project on the four-day working week. First, you have some time to look at questions twenty-one to twenty-six."),
            ("PAUSE", "30"),
            ("NARRATOR", "Now listen carefully and answer questions twenty-one to twenty-six."),
            ("TUTOR", "Come in, both of you. So, the four-day week. Remind me how you settled on that. I think I'd suggested something on remote working, hadn't I?"),
            ("FEMALE_IE", "You did, and we looked into it. But then Marcus mentioned that his mum's company was one of the firms taking part in the national trial."),
            ("MALE_IE", "Yes, and she said we could talk to people there, which seemed too good a chance to miss. I know it's been in the news a lot, but honestly that wasn't the reason. If anything, that made us worry it had all been said already."),
            ("TUTOR", "Fair enough. And what have you found so far in the published results?"),
            ("FEMALE_IE", "Well, the headline finding is that productivity stayed more or less the same, which everyone had expected from the earlier pilot schemes. And sick days went down, but again, that was predicted. What I really didn't expect was that it was the managers, rather than the ordinary staff, who were keenest to carry on afterwards."),
            ("TUTOR", "Interesting. And your own survey of the employees?"),
            ("MALE_IE", "We got a hundred and twenty responses, which is more than we needed. The trouble is that a couple of the questions were read in different ways. For example, when we asked about workload, some people thought we meant the number of hours, and others thought we meant how stressful the work was."),
            ("TUTOR", "That's a very common problem. Don't worry, just acknowledge it in your methodology. Now, at the moment you've got companies from retail, finance, manufacturing and software. That's a lot for a project of this size. I'd pick one sector and look at it properly. You could compare with other countries later, but not in this assignment."),
            ("FEMALE_IE", "OK. Probably software, then, since that's where most of our responses came from."),
            ("TUTOR", "Good. What about the disadvantages? You'll need a balanced picture."),
            ("MALE_IE", "We talked about prices going up for customers, but there's really no evidence of that, so we've dropped it. Meetings came up too, but most of the companies just moved them online, so it wasn't a real issue."),
            ("FEMALE_IE", "But a lot of people in the firms that switched to four ten-hour days said they were exhausted by Thursday, so we'll definitely include that. And the customer-facing firms had to close one extra day a week, which some clients complained about, so that goes in as well."),
            ("MALE_IE", "Some people did say they felt a bit guilty at first, but it seemed to wear off after a few weeks, so we'll leave it out."),
            ("NARRATOR", "Before you hear the rest of the discussion, you have some time to look at questions twenty-seven to thirty."),
            ("PAUSE", "25"),
            ("NARRATOR", "Now listen and answer questions twenty-seven to thirty."),
            ("TUTOR", "So, how are you dividing up the work?"),
            ("FEMALE_IE", "I'll get in touch with the companies to arrange the interviews. Marcus offered, but I've already been emailing the HR people, so it makes sense for me to carry on."),
            ("MALE_IE", "And I'll do the slides. I've got the software at home, and Leila hates designing them."),
            ("FEMALE_IE", "True! The literature review is the biggest job, so we'll split that between us and each read half of the articles."),
            ("TUTOR", "And the handout for the presentation?"),
            ("MALE_IE", "I thought I could do that as well..."),
            ("FEMALE_IE", "No, you've got enough with the slides. I'll do the handout; it's mostly just a summary of the findings anyway."),
            ("TUTOR", "Sounds sensible. Let's meet again in two weeks."),
            ("NARRATOR", "That is the end of part three. You now have some time to check your answers."),
            ("PAUSE", "20"),
        ],
    },
    {
        "number": 4,
        "title": "Part 4 — Lecture: kelp forests",
        "context": "You will hear part of a lecture about kelp forests.",
        "groups": [
            group(
                "gap",
                "Complete the notes below. Write ONE WORD ONLY for each answer.",
                [
                    gap(31, "Grow in cold, shallow water that is rich in ____"),
                    gap(32, "Can grow by up to half a metre in a single ____"),
                    gap(33, "Give young fish ____ from predators"),
                    gap(34, "Absorb carbon dioxide and may reduce local ocean ____"),
                    gap(35, "Sea otters were hunted for their ____, so urchin numbers rose"),
                    gap(36, "Higher water ____ weakens the kelp"),
                    gap(37, "Urchin 'barrens' can last for ____"),
                    gap(38, "Otters use ____ to break open urchins"),
                    gap(39, "Collected urchins are sold as a ____"),
                    gap(40, "Volunteers record changes with underwater ____"),
                ],
                title="Kelp forests — importance, threats and recovery",
            )
        ],
        "script": [
            ("NARRATOR", "Part four. You will hear part of a lecture about kelp forests. First, you have some time to look at questions thirty-one to forty."),
            ("PAUSE", "45"),
            ("NARRATOR", "Now listen carefully and answer questions thirty-one to forty."),
            ("LECTURER", "Good morning, everyone. Today I'm going to talk about one of the most productive ecosystems on the planet, and one that most people have never seen: the kelp forest."),
            ("LECTURER", "Kelp is a type of large brown seaweed, and where conditions are right it forms dense underwater forests. You'll find them along about a quarter of the world's coastlines, but only in cold, shallow water. Temperature matters, but what really determines where kelp grows is that the water must be rich in nutrients, which usually means areas where cold water rises up from the deep ocean."),
            ("LECTURER", "What makes kelp remarkable is its speed of growth. Giant kelp, the largest species, can grow by as much as half a metre in a single day, which makes it one of the fastest-growing organisms on Earth. Some people say it grows faster than bamboo, which is roughly true."),
            ("LECTURER", "So why do these forests matter? Firstly, they're home to an extraordinary variety of life. For young fish in particular, the tangle of fronds provides shelter from larger predators. It's often described as a nursery, and that's a good way of thinking about it. Secondly, like forests on land, kelp absorbs carbon dioxide as it grows. Researchers are still debating how much of that carbon is stored permanently, but there's good evidence that kelp forests can reduce the acidity of the water around them, which helps shellfish build their shells."),
            ("LECTURER", "Now, the threats. The story of the Pacific coast of North America is a classic example. The main grazer of kelp there is the sea urchin. Normally urchin numbers are kept down by sea otters, which eat them. But in the eighteenth and nineteenth centuries, otters were hunted almost to extinction. People weren't interested in the meat; it was their fur, which is the thickest of any animal, that was so valuable. With the otters gone, urchin populations exploded and they ate the kelp down to the rock."),
            ("LECTURER", "More recently, climate change has added to the pressure. Marine heatwaves have become more frequent, and when the water temperature rises, kelp becomes weaker and grows more slowly, just when the urchins are hungriest. In parts of northern California, more than ninety per cent of the kelp has disappeared in less than a decade."),
            ("LECTURER", "What's left behind is known as an urchin barren: bare rock covered in urchins and very little else. And the worrying thing is that these barrens are extremely stable. Once they form, they can last for decades, because the starving urchins simply wait and eat any new kelp that tries to grow."),
            ("LECTURER", "So what can be done? One approach is to bring back the predators. Where sea otters have returned, the kelp has often recovered. Otters are one of the few mammals that use tools: they float on their backs and use rocks to break open the urchins' shells."),
            ("LECTURER", "Another approach is direct removal. Teams of divers collect urchins by hand, and, rather neatly, in some places the urchins are then sold as a delicacy to restaurants, which helps pay for the work. And finally, there's a lot of interest in citizen science. Volunteer divers are trained to monitor the forests, and they record changes using underwater cameras, which gives scientists far more data than they could ever collect themselves."),
            ("NARRATOR", "That is the end of the listening test. You now have two minutes to check your answers."),
            ("PAUSE", "10"),
        ],
    },
]

LISTENING_ANSWER_KEY = {
    "1": "Fairbrook", "2": "GL4 7TR", "3": "garden", "4": "library", "5": "Thursday",
    "6": "3/three", "7": "tutor", "8": "boots", "9": "lunch", "10": "church",
    "11": "B", "12": "A", "13": "B", "14": "A", "15": "B", "16": "C",
    "17": "F", "18": "B", "19": "C", "20": "D",
    "21": "B", "22": "C", "23": "B", "24": "C", "25": "C", "26": "D",
    "27": "A", "28": "B", "29": "C", "30": "A",
    "31": "nutrients", "32": "day", "33": "shelter", "34": "acidity", "35": "fur",
    "36": "temperature/temperatures", "37": "decades", "38": "rocks/stones", "39": "delicacy", "40": "cameras",
}

# ---------------------------------------------------------------------------
# READING
# ---------------------------------------------------------------------------

READING_PASSAGES = [
    {
        "number": 1,
        "title": "Britain's Canal Age",
        "question_range": "1–13",
        "paragraphs": [
            "In the middle of the eighteenth century, moving heavy goods across Britain was slow, expensive and frequently impossible. Roads were little more than rutted tracks, which turned to mud in winter, and a horse pulling a cart could manage perhaps a tonne of cargo at best. Rivers offered an alternative, but many were too shallow or too winding to be relied upon, and they rarely went where industry needed them to go. It was against this background that the canal, an artificial waterway built specifically for transport, began to transform the British economy.",
            "The first canal of the industrial era is usually said to be the Bridgewater Canal, which opened in 1761. It was commissioned by the Duke of Bridgewater, who owned coal mines at Worsley and wanted a cheaper way of getting his coal to the rapidly growing town of Manchester, ten miles away. The engineer he employed, James Brindley, had almost no schooling and is said to have been barely able to write, yet he designed a route that crossed the River Irwell on an aqueduct, a bridge carrying water, which astonished those who came to see it. Within a year of the canal's completion, the price of coal in Manchester had fallen by half.",
            "The success of the Bridgewater Canal set off what historians call 'canal mania'. Between 1790 and 1810 alone, Parliament approved more than a hundred new canal schemes, many of them financed by small investors such as shopkeepers, clergymen and farmers, who bought shares in the expectation of handsome returns. Some were well rewarded: shares in the Oxford Canal paid dividends of over thirty per cent for many years. Others lost everything, as a number of canals were begun but never finished, or were built through areas that simply did not generate enough traffic to make them pay.",
            "The advantages of water transport were considerable. A single horse walking along the towpath beside a canal could pull a narrowboat carrying around thirty tonnes, roughly fifty times what the same animal could move by road. Fragile goods benefited too. The pottery manufacturer Josiah Wedgwood was among the most enthusiastic promoters of the Trent and Mersey Canal, because the smooth journey meant far fewer of his plates and teapots arrived broken than when they had been carried by packhorse over rough roads.",
            "The people who worked the boats, however, saw rather fewer of the profits. Boatmen were generally paid by the load rather than by the hour, which encouraged them to travel as quickly as possible and to work very long days. As competition increased in the early nineteenth century and wages fell, many could no longer afford to rent a house on land, and whole families began to live in the tiny rear cabin of the narrowboat itself, a space often no more than three metres long. Children helped to lead the horse and operate the locks from an early age, and few received any regular schooling, a situation that reformers would campaign against for decades. The brightly painted roses and castles that now decorate many leisure boats are a reminder of this period, when families took pride in making their cramped floating homes as cheerful as possible.",
            "Building the canals was, however, extraordinarily demanding. Engineers had to keep the water level as constant as possible, which meant following the contours of the land and avoiding hills wherever they could. Where this was not possible, they relied on locks, chambers with gates at each end in which boats are raised or lowered, or, more dramatically, on tunnels. The Standedge Tunnel in Yorkshire, completed in 1811, runs for more than five kilometres beneath the Pennine hills and took seventeen years to build. Almost all of the digging was done by labourers known as 'navigators', a term later shortened to 'navvies', who moved vast quantities of earth with little more than shovels and wheelbarrows.",
            "Canals also had to be supplied with water, a problem that is often overlooked. Every time a boat passes through a lock, thousands of litres flow downhill, and this water must be replaced. Engineers therefore constructed reservoirs on high ground to feed the highest sections of the network, and in dry summers traffic was sometimes halted altogether because there was not enough water to operate the locks.",
            "The canal age proved surprisingly short. From the 1830s onwards, the railways offered something that canals could not: speed. A journey that took a narrowboat several days could be completed by train in a matter of hours, and the railway companies were quick to cut their rates in order to win customers away from the waterways. Many canal companies were bought up by railway companies, which then had little interest in maintaining them. By the middle of the twentieth century, much of the network was derelict, its channels choked with rubbish and weeds.",
            "That the canals survive at all is largely thanks to campaigners. In 1946 a group of enthusiasts founded the Inland Waterways Association, and volunteers began clearing abandoned channels and repairing locks. Today more than three thousand kilometres of canal are open to boats, but the traffic is almost entirely recreational. The towpaths once walked by working horses are now used by cyclists, walkers and anglers, and some economists argue that canals generate more value through tourism today than they ever did through trade.",
        ],
        "groups": [
            group(
                "tfng",
                "Do the following statements agree with the information given in Reading Passage 1? Choose TRUE if the statement agrees with the information, FALSE if the statement contradicts the information, NOT GIVEN if there is no information on this.",
                [
                    item(1, "Before the canal age, rivers were an unreliable way of moving goods."),
                    item(2, "James Brindley had received a thorough training in engineering."),
                    item(3, "The Duke of Bridgewater became considerably richer within a year of the canal opening."),
                    item(4, "All of the canals approved by Parliament between 1790 and 1810 were eventually completed."),
                    item(5, "Josiah Wedgwood contributed money towards the cost of building the Trent and Mersey Canal."),
                    item(6, "Railway companies lowered their charges in order to compete with the canals."),
                ],
            ),
            group(
                "gap",
                "Complete the table below. Choose ONE WORD ONLY from the passage for each answer.",
                [
                    gap(7, "A horse could pull about ____ times more on a canal than on a road"),
                    gap(8, "Fewer of Wedgwood's goods were ____ in transit"),
                    gap(9, "Changes in height were managed with locks or ____"),
                    gap(10, "Diggers' name later shortened to '____'"),
                    gap(11, "____ were built on high ground"),
                    gap(12, "The main advantage of the railways was ____"),
                    gap(13, "Some argue canals now produce more value from ____ than from trade"),
                ],
                title="The canal age",
                table={
                    "columns": ["Topic", "Details"],
                    "rows": [
                        ["Efficiency", "a horse could pull a load about [[7]] times greater than on a road"],
                        ["Fragile goods", "fewer of Wedgwood's products were [[8]] during the journey"],
                        ["Construction", "changes in height were dealt with by locks or [[9]]; diggers were known as 'navigators', later shortened to '[[10]]'"],
                        ["Water supply", "[[11]] were constructed on high ground"],
                        ["Decline", "the railways' chief advantage was [[12]]"],
                        ["Today", "some experts say canals now create more value from [[13]] than from trade"],
                    ],
                },
            ),
        ],
    },
    {
        "number": 2,
        "title": "Why We Put Things Off",
        "question_range": "14–26",
        "paragraphs": [
            "A  Almost everyone delays tasks from time to time, but for some people it is a persistent problem. Surveys in several countries suggest that around one adult in five regards themselves as a chronic procrastinator, someone whose delays regularly damage their work, finances or health. For a long time this behaviour was dismissed as simple laziness. Yet the label does not fit. A lazy person is content to do nothing and feels no particular discomfort about it; the procrastinator, by contrast, is often busy with other activities while feeling anxious and guilty about the task that is being avoided. The costs can be considerable. Studies of tax returns, for instance, have found that people who file at the last minute make more errors and are more likely to pay penalties, while students who habitually delay tend to report higher levels of stress and illness towards the end of the academic year, precisely when they can least afford them.",
            "B  According to the psychologist Helen Marsh, the key to understanding procrastination is to recognise that it is not primarily a problem of time management at all. 'People do not put things off because they cannot read a calendar,' she says. 'They put them off because the task makes them feel bad: it is boring, or confusing, or it threatens their sense of being competent.' Delaying the task brings immediate relief from these feelings, and that relief is itself rewarding, which makes the habit difficult to break. In Marsh's view, we are not avoiding the work so much as the emotions attached to it.",
            "C  If this is correct, it might be expected that being hard on ourselves would help. The evidence suggests the opposite. In a study of first-year university students, Rafael Ortega asked participants how they felt about having delayed revision before their mid-term examinations. Those who reported having forgiven themselves for their earlier delays procrastinated significantly less before the next set of exams. Ortega argues that self-criticism simply adds another layer of negative emotion to the task, making it even more unpleasant to begin. He is careful to point out that self-forgiveness is not the same as making excuses: the students who did best acknowledged that the delay had been a mistake, but did not dwell on it.",
            "D  Deadlines would seem to be an obvious remedy, but their effect depends on who sets them. The behavioural economist Priya Natarajan divided students on a writing course into three groups. One group was given fixed, evenly spaced deadlines for three essays; a second was allowed to choose its own deadlines in advance; and a third had a single deadline at the end of the term for all three essays. The students with imposed deadlines produced the best work, and those with only a final deadline the worst. Those who chose their own deadlines came in between: many saw the value of committing themselves, but set their deadlines later than was sensible.",
            "E  Part of the difficulty may lie in the way we think about the future. Research by Karin Holt suggests that, when people think about themselves in ten or twenty years' time, the brain responds in a way that is closer to thinking about a stranger than to thinking about the present self. It is therefore easy to leave unpleasant work to this 'other person'. In one of Holt's experiments, participants who were shown digitally aged images of their own faces subsequently put more money into savings and were less likely to delay a dull but important task.",
            "F  Modern working conditions have not helped. Liam Doyle, who studies workplace behaviour, found that office employees were interrupted, on average, every eleven minutes, and that it often took them far longer than that to return to what they had been doing. Smartphones and messaging applications offer a constant supply of small, instant rewards, and each notification provides a convenient excuse to step away from a demanding task. In this sense, digital technology has made the urge to procrastinate easier to act on than ever before. Working from home has added a further complication: without colleagues nearby, there is no one to notice when a task has been abandoned, and household chores can suddenly seem surprisingly attractive when the alternative is a difficult report. Doyle notes that many remote workers now deliberately recreate the conditions of the office, by working in libraries or cafés, simply in order to be seen.",
            "G  In some ways procrastination resembles overeating: in both cases, people choose a small immediate pleasure over a larger long-term goal, even though they know they will regret it. Telling a chronic procrastinator simply to try harder is about as useful as telling a hungry person to stop thinking about food. The most effective strategies therefore aim to make beginning easier rather than relying on willpower. Experts recommend breaking a large task into a series of small steps, each of which feels manageable. Another popular technique is to commit to working on something for just five minutes, since getting started is usually the hardest part and many people find they continue once they have begun. Removing temptations, such as putting the phone in another room, also helps, because it is far easier to resist a distraction that requires effort to reach.",
        ],
        "groups": [
            group(
                "matching",
                "Reading Passage 2 has seven paragraphs, A–G. Which paragraph contains the following information? NB You may use any letter more than once.",
                [
                    item(14, "a comparison between procrastination and another harmful habit"),
                    item(15, "a reference to the role of digital devices in encouraging delay"),
                    item(16, "an explanation of why a common description of procrastinators is inaccurate"),
                    item(17, "an account of an experiment in which participants had different time limits"),
                ],
                box=lettered(["", "", "", "", "", "", ""]),
            ),
            group(
                "matching",
                "Look at the following statements (Questions 18–22) and the list of researchers below. Match each statement with the correct researcher, A–E.",
                [
                    item(18, "Treating oneself kindly after delaying a task can lead to less delay in future."),
                    item(19, "People's work is frequently broken up by distractions."),
                    item(20, "Delaying a task is a way of escaping uncomfortable feelings."),
                    item(21, "Time limits set by others are more effective than those people set for themselves."),
                    item(22, "People may think of their future selves almost as different people."),
                ],
                box_title="List of Researchers",
                box=lettered(["Helen Marsh", "Rafael Ortega", "Priya Natarajan", "Karin Holt", "Liam Doyle"]),
            ),
            group(
                "gap",
                "Complete the summary below. Choose ONE WORD ONLY from the passage for each answer.",
                [
                    gap(23, "Experts suggest dividing a large task into small ____."),
                    gap(24, "Another technique is to commit to working for only five ____."),
                    gap(25, "This works because getting ____ is usually the most difficult part."),
                    gap(26, "It also helps to remove ____ such as phones from the work area."),
                ],
                title="Overcoming procrastination",
            ),
        ],
    },
    {
        "number": 3,
        "title": "Who Should Own the Past?",
        "question_range": "27–40",
        "paragraphs": [
            "For much of the twentieth century, the great museums of Europe and North America presented themselves as 'universal' institutions: places where the achievements of every civilisation could be admired side by side, and where visitors could trace the story of humanity under a single roof. It is an attractive idea, and it has given millions of people their first encounter with the art of distant cultures, from Egyptian sculpture to the bronzes of West Africa. Generations of scholars have built their careers on these collections, and much of what we know about ancient societies was first established by researchers working in their storerooms. What it tended to leave out, however, was the question of how so many of these objects had arrived in the first place. A significant proportion were acquired through military conquest, colonial administration or trade on deeply unequal terms, and some were simply taken.",
            "Over the past two decades, requests for the return of such objects have grown both more numerous and more difficult to ignore. Museums have responded with a familiar set of arguments. Objects, they say, are safer in institutions with the resources to conserve them; they are seen by far more people in London, Paris or New York than they would be elsewhere; and the universal museum promotes understanding between cultures in a way that national museums cannot. Some add that if every object were returned to its place of origin, the great collections would be emptied. These arguments are not without merit, but in my view they are considerably weaker than they first appear.",
            "It should be said that the legal position has not made matters simpler. International agreements on the protection of cultural property were mostly drawn up in the second half of the twentieth century and do not apply to objects removed before they came into force. In several countries, moreover, national museum collections are protected by legislation that prevents trustees from giving items away, even when they would like to. As a result, discussions about return have often taken place outside the courts altogether, through negotiation between governments, museums and communities. This has the advantage of flexibility, but it also means that outcomes depend heavily on political will and public pressure, and that similar requests can be treated in very different ways.",
            "Consider the claim about safety. It rests on the assumption that the risks to cultural heritage lie elsewhere, and yet major Western museums have themselves suffered fires, floods and thefts, some of them in very recent years. Many of the countries now asking for the return of their heritage have, in the meantime, built modern museums with sophisticated conservation facilities. The safety argument may once have been persuasive; today it is often little more than a habit of thought.",
            "The argument about visitor numbers is subtler, but it, too, deserves scrutiny. It is undoubtedly true that a carved figure in a famous gallery will be looked at by more people than the same figure in a regional museum. But the number of people who pass an object is not the only measure of its value. For the communities that made them, many such objects are not works of art in the Western sense but sacred items, or records of family and history, and their absence is felt in ways that visitor figures cannot capture. Nor is physical possession necessary for an object to be seen around the world. High-resolution photography and three-dimensional scanning now allow collections to be explored by anyone with an internet connection, wherever the objects themselves happen to be.",
            "It is also worth correcting a common misunderstanding about what return involves. Opponents sometimes speak as though repatriation were the end of a relationship, after which an object disappears from view. In practice, the opposite is frequently the case. Returns have led to long-term loans in the other direction, joint research projects and exhibitions planned by curators from both institutions, and museum staff who once regarded each other as adversaries have become collaborators. Far from emptying museums, repatriation has often enriched them with knowledge they did not previously possess.",
            "None of this means that every case is straightforward. Political boundaries have changed so often that the state which exists today may have little connection with the place from which an object was removed. Museum records are often incomplete, so that it can be genuinely difficult to establish how and when something was acquired. And communities themselves do not always speak with one voice: there may be conflicting views about whether an object should be displayed, stored or returned to ceremonial use.",
            "What these difficulties suggest is not that claims should be resisted, but that each one should be considered individually, on the basis of the best available evidence. What needs to change is the starting assumption. For too long, the burden of proof has rested on those requesting return; it should rest instead on those who wish to keep objects whose history is troubling. A museum's real value does not lie in what it owns but in what it knows and shares: the stories it can tell, and the understanding it can build. Perhaps the most universal thing a museum can do is to listen.",
        ],
        "groups": [
            group(
                "mcq",
                "Choose the correct letter, A, B, C or D.",
                [
                    mcq(27, "What point does the writer make about the idea of the 'universal' museum in the first paragraph?", [
                        "It overlooked the ways in which many objects were obtained.",
                        "It has never been popular with the general public.",
                        "It has now been abandoned by most large museums.",
                        "It was developed in response to requests for returns.",
                    ]),
                    mcq(28, "What does the writer suggest about the argument that objects are safer in Western museums?", [
                        "It is supported by a growing body of evidence.",
                        "It ignores the risks that those museums themselves face.",
                        "It applies only to objects that are especially fragile.",
                        "It has been officially withdrawn by most museums.",
                    ]),
                    mcq(29, "What is the writer doing in the fourth paragraph?", [
                        "explaining why museum visitor numbers have declined",
                        "describing in detail how three-dimensional scans are produced",
                        "questioning the idea that large audiences justify keeping objects",
                        "comparing museums in different European capitals",
                    ]),
                    mcq(30, "According to the writer, the return of objects to their place of origin", [
                        "has frequently led to new forms of cooperation.",
                        "is usually opposed by the communities involved.",
                        "should be decided by the courts rather than museums.",
                        "has caused a number of museums to close.",
                    ]),
                ],
            ),
            group(
                "matching",
                "Complete the summary using the list of phrases, A–J, below. Choose the correct letter, A–J, for each answer.",
                [
                    item(31, "Political ____ mean that today's state may not be the one from which an object was taken."),
                    item(32, "Museum records are often ____, so an object's history can be hard to establish."),
                    item(33, "Within a community there may be ____ about what should happen to an object."),
                    item(34, "The writer argues that the ____ should change in favour of return."),
                    item(35, "Each claim should be judged ____."),
                    item(36, "A museum's true value lies in its ____ rather than its possessions."),
                ],
                box_title="List of phrases",
                box=lettered([
                    "conflicting views",
                    "financial pressure",
                    "incomplete",
                    "shared knowledge",
                    "large collections",
                    "starting assumption",
                    "public opinion",
                    "changing borders",
                    "legal ownership",
                    "on its own merits",
                ]),
            ),
            group(
                "ynng",
                "Do the following statements agree with the claims of the writer in Reading Passage 3? Choose YES if the statement agrees with the claims of the writer, NO if the statement contradicts the claims of the writer, NOT GIVEN if it is impossible to say what the writer thinks about this.",
                [
                    item(37, "Most museum directors privately accept that some objects ought to be returned."),
                    item(38, "Digital technology can make collections accessible without the need to own the objects."),
                    item(39, "Returning an object usually ends the original museum's involvement with it."),
                    item(40, "The importance of a museum should be measured mainly by the size of its collection."),
                ],
            ),
        ],
    },
]

READING_ANSWER_KEY = {
    "1": "TRUE", "2": "FALSE", "3": "NOT GIVEN", "4": "FALSE", "5": "NOT GIVEN", "6": "TRUE",
    "7": "fifty/50", "8": "broken", "9": "tunnels", "10": "navvies", "11": "reservoirs", "12": "speed", "13": "tourism",
    "14": "G", "15": "F", "16": "A", "17": "D",
    "18": "B", "19": "E", "20": "A", "21": "C", "22": "D",
    "23": "steps", "24": "minutes", "25": "started", "26": "temptations",
    "27": "A", "28": "B", "29": "C", "30": "A",
    "31": "H", "32": "C", "33": "A", "34": "F", "35": "J", "36": "D",
    "37": "NOT GIVEN", "38": "YES", "39": "NO", "40": "NO",
}
