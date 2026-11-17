# Defence script and question practice

This is a team document for practice. It is **not** sent to the professor.

The defence lasts 15 minutes for the talk and the demo, then 5 minutes of questions. Each extra minute costs 1 point, so we aim for **12 to 13 minutes**. All four of us speak. Replace A, B, C, D with your first names.

## 1. Who speaks and for how long

| Slide | Who | Time | One sentence to say |
|---|---|---|---|
| 1 Problem | A | 1 min | A volunteer treasurer writes every offer alone, and some slots stay unsold. |
| 2 Solution | A | 1 min | A business name goes in, an offer with its logo on the kit comes out. |
| 3 Live demo | B | 3 min | The jury chooses, and the offer changes. |
| 4 Market analysis | C | 1 min | 56,100 clubs can pay, and we can reach 4,726 today. |
| 5 Business model and price | C | 1 min | €15 a month, which is 23% of the value we create. |
| 6 Traction | D | 1 min | No paying club yet. Here is what is proven and what comes next. |
| 7 Competition and defensibility | D | 1.5 min | Others write offers or find deals. We show the logo on the kit. |
| 8 Team | all | 0.5 min | Each person says who they are in one sentence. |
| 9 Financials | C | 1 min | We break even at 122 clubs, in month 11. |
| 10 The ask | D | 0.5 min | €35,000 for 18 months, three milestones. |

**First sentence (A): a person, a pain, a number.** "Julien is the volunteer treasurer of a club with 320 members. Sponsors bring about 9% of the club's money, and he writes every offer alone, in the evening."

## 2. The demo (B), 3 minutes

Open the link 10 minutes before. Test these five inputs first.

| # | Input | What you should see | Type |
|---|---|---|---|
| 1 | Garage Martin | The minibus and the entrance banner, linked to the need to replace the minibus | easy |
| 2 | Pharmacie des Tilleuls | The boards and the bibs, for families, with no forced minibus | easy |
| 3 | Agence immobilière Century | A warning: a real estate company already sponsors the club | tricky |
| 4 | Chez Momo | A person must check: we cannot tell what the business does | tricky |
| 5 | Cave à vins du Rhône | Blocked before any call to the AI | out of scope |

Steps:
1. Say in one sentence who the user is: "Julien wants an offer for a garage."
2. Let the jury choose the business. Upload the jury's own logo if they have one.
3. Point out two things: taken slots are never offered, and the price comes from the club's list, not from the AI.
4. Show one limit case: a competitor of a sponsor, or the wine cellar.
5. Say the numbers: about $0.0006 and 4 to 5 seconds for the writing.

If the network fails, use your phone as a hotspot. If the app is asleep, wait a few seconds and do not reload many times. Never show the API key or the *Secrets* panel. Never replace the demo with a video.

## 3. What not to say

- "We have clients", or "clubs have confirmed": it is not true yet.
- "Sponsoring will rise by 30% for sure": it is an assumption, the weakest one in our numbers.
- "The market is worth billions": ours is small (€1.53M that we can reach).
- "The photos are made by AI live": no. They are prepared once, and the logo is placed by code.
- "We have no competitors": we do (All Sponsored, Leedeel, Spencer.club, SPONSO+, proposal tools).

## 4. Questions the jury may ask

**Why this use case, and not another?**
We scored six ideas with the three-question test (pay, switch, degrade), then RICE and ICE. Membership fee reminders score higher on volume, but cheap tools already exist, so it is a fill-in to buy. Sponsoring is the only idea that is must-have, high impact and easy to build: a quick win. Our confidence scores are guesses, so we will call 10 clubs to test them.

**Where does the +30% come from?**
It is an assumption, not a measure. We test it with three pilot clubs over one season. Even at 30% use of the tool, our price is 31% of the value, so the model still holds.

**What is your moment of truth?**
A business name goes in, and an offer with its logo on the club's kit comes out. The demo shows it live, on an input the jury chooses.

**What did you build, and what did you buy?**
We built the workflow (choice of slots, checks) and the screen. We bought the AI model (small by default, large as backup) and the hosting. We rely on partners for distribution (districts and leagues).

**What does one offer cost?**
About $0.0006 and 4 to 5 seconds of writing (measured). With 400 clubs, the AI costs about $4.3 a month, which is 0.04% of revenue. With the large model it would be about $85, or 0.7%. The photos are made once for $0.47 in total, and placing the logo is free.

**Is 4 to 5 seconds too slow?**
It is above the 3-second target of the course. We would show the text as it is written.

**How did you size the market?**
From the bottom up: clubs that sign × price per club. 51,150 mid-size and 4,950 big clubs in France give €18.1M. Football and rugby give 4,726 clubs and €1.53M. In three years we aim for 400 clubs and €136,800 a year.

**Who will sign 11 clubs a month?**
Districts and leagues that pass the tool to their clubs, and direct calls. We have no agreement yet.

**How reliable are your numbers?**
The split of clubs by size uses data from 2011 and 2012, and the national total (about 165,000) is a weak source. We should check them with the Ministry of Sports.

**Why a subscription, and not a share of the sponsors you help sign?**
A share follows the value better, but it is hard to measure and hard to predict. We keep it as an option for big clubs.

**Why €15?**
It is 23% of the €65 of value created each month, and lower than the €19 to €49 clubs pay for management software. The course rule is 10 to 30% of the value.

**Why not small clubs?**
They are 66% of clubs, but their sponsoring is about €1,060 a year. After costs, the gain is under €100, so they cannot pay.

**What stops a competitor from copying you?**
Nothing in the technology: a prompt and a screen can be copied in a weekend. We rely on data (which offers are accepted), distribution (districts and leagues) and the club's own workflow (slots, sponsors, renewals).

**Does All Sponsored already do this?**
It measures the visibility of clubs and finds deals. As far as we can tell, it does not write one offer per business with the logo on the club's kit. We did not test it.

**Why €35,000?**
It is the lowest cash point (€14,967) plus six months of fixed costs (€18,000), rounded up.

**What if you sign half as many clubs?**
The break-even point moves later. We can change one number in `dossier/calc.py` and see the new result.

**Personal data, AI Act, fairness?**
The prototype uses no personal data. In real use we would keep only what we need, set a storage time and sign a data agreement with the AI provider. We see the tool as limited risk, so the text is marked as written with AI. The tool does not rank people. The dates of the AI Act must be checked on the official site.

**What if the AI makes a mistake?**
The code checks every slot and sets every price. The email says it must be read before sending, and a person is asked to check unclear cases.

**One question for each person**
Each member must explain their own numbers alone: where each figure comes from (source or assumption), and what would change it. Practise by asking each other questions on the numbers file.

## 5. The day before

- [ ] The demo link is open and tested with a real logo (png and jpg) and the five inputs
- [ ] The deck PDF and the link are sent before Monday 23 November
- [ ] One full rehearsal, timed, under 13 minutes
- [ ] Phone ready as a hotspot, laptop charged
- [ ] Everyone can answer the questions on their own part
