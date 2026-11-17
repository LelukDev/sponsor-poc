# Defence script and question practice

This is a team document for practice. It is **not** sent to the professor.

The defence lasts 15 minutes for the talk and the demo, then 5 minutes of questions. Each extra minute costs 1 point, so the plan below lasts **about 13 minutes**. That leaves about 2 minutes of safety. All four of us speak: Joshai opens, Eyal closes.

## 1. Who speaks, and for how long

| Order | Slide | Speaker | Time |
|---|---|---|---|
| 0 | Introduction | **Joshai** | 0:20 |
| 1 | Problem | **Joshai** | 1:15 |
| 2 | Solution | **Lucas** | 1:15 |
| 3 | Live demo | **Lucas** speaks, **Joshai** types | 2:30 |
| 4 | Market analysis | **Henry** | 1:15 |
| 5 | Business model and price | **Eyal** | 1:15 |
| 6 | Traction | **Joshai** | 1:00 |
| 7 | Competition and defensibility | **Henry** | 1:15 |
| 8 | Team | **Henry**, then each person | 0:45 |
| 9 | Financials | **Eyal** | 1:30 |
| 10 | The ask and conclusion | **Eyal** | 1:00 |
| | **Total** | | **13:25** |

| Person | Parts | Speaking time |
|---|---|---|
| Joshai | Introduction, 1 Problem, 6 Traction (and types in the demo) | 2:35 |
| Lucas | 2 Solution, 3 Live demo | 3:45 |
| Henry | 4 Market, 7 Competition, 8 Team | 3:15 |
| Eyal | 5 Price, 9 Financials, 10 Ask and conclusion | 3:45 |

Speaking speed: about 140 words a minute. Each text below is written to fit its time. Say it in your own words, but keep the numbers and the order. Slow down on the numbers. At the end of each part, say the hand-over sentence (in italics) so the change of speaker is smooth.

## 2. The words, slide by slide

### Introduction (Joshai, 0:20)

"Hello, and thank you. We are Joshai, Lucas, Eyal and Henry, MSc students at Albert School. We built Sponsio, an assistant that helps a small sports club find sponsors. In the next thirteen minutes, we show the problem, a live demo that you control, and our plan. Let us start with the problem."

### 1. Problem (Joshai, 1:15)

"Let me start with Julien. Julien is the volunteer treasurer of a football club with 320 members. This is an example, but it is a real situation. Sponsors bring about 9% of the money of a club like his. That is a lot, because 37% of clubs lose money.

When Julien looks for a sponsor, he does the same thing every time. He writes one offer alone, in the evening, and he sends the same PDF to every business. Three things go wrong. The pitch is the same for everyone. Sometimes he offers a slot that is already sold, because nobody has the list in mind. And the offer does not say what the club needs, like a new minibus or a tournament.

For a mid-size club, sponsoring is about 7,200 euros a year. So a better way to sell it is worth real money."

*Hand-over: "Lucas will now show you our solution."*

### 2. Solution (Lucas, 1:15)

"Our solution is simple. The club writes its slots once: the prices, who already sponsors it, and what it needs. Then, to make an offer, you type the name of a local business.

The AI reads the club's list and chooses three offers: an entry offer, a recommended one and a premium one. Then our code checks the AI. It only keeps free slots. It takes the prices from the club's list, not from the AI. It warns if the business is a competitor of a current sponsor. And it blocks alcohol, tobacco and betting before anything is sent to the AI.

Last, the app shows realistic photos with the logo on the kit, the boards or the minibus. You can see on this slide the empty boards before, and the boards with a sponsor's logo after.

This is our moment of truth: you type a business name, and in a few seconds you get an offer with its logo on the club's kit. Let us show you now."

### 3. Live demo (Lucas speaks, Joshai types, 2:30)

Before the talk, open the link and test the five inputs of section 3 below. Show the screen in full size.

1. (0:15) "Joshai plays Julien. Julien wants an offer for a garage. Joshai, please ask the jury for the name of a business." If the jury gives no idea, type **Garage Martin**. Upload the jury's logo if they have one. If not, use the example logo.
2. (0:25) Click the button. While it runs: "It takes about four to five seconds, and it costs about 0.06 cents."
3. (0:45) Read the result. "Three offers. Look at the recommended one: it uses the minibus, because the club needs to replace it, and the garage is a good fit. The prices are the ones from the club's list. Here are the photos: the logo is on the minibus and on the banner."
4. (0:30) Show the limit: "Now a competitor." Type **Agence immobilière Century**. "A real estate company already sponsors the chest of the jersey, so the tool warns us. It does not hide the problem."
5. (0:25) Show the rule: "Joshai, a wine bar please." Type **Cave à vins du Rhône**. "It is blocked before any AI call, because alcohol advertising is restricted in sport."
6. (0:10) Optional, if time: open the club profile, change one free slot to taken, and generate again. "The offers change, because the slot is gone."

"This is the whole product. The photos are prepared once, and the logo is placed by our code, so the cost stays very low."

If something fails: say it calmly, use the phone hotspot, and show the photos on the slides. Never show the Secrets panel or the key.

*Hand-over: "Henry will now explain the market."*

### 4. Market analysis (Henry, 1:15)

"Now the market. We count it from the bottom up: clubs that can pay, multiplied by our price.

In France there are about 165,000 sports clubs. We keep two types. Mid-size clubs are 31% of them, with a budget of about 80,000 euros. They would pay 15 euros a month, so 180 euros a year. Flagship clubs are 3%, with a budget of about 918,000 euros. They would pay 150 euros a month. Small clubs are 66% of clubs. We leave them out, because their sponsoring is about 1,000 euros a year, so the gain is too small to pay for a tool.

That gives a total market of 18.1 million euros. This is small, and we say it. Our starting point is football and rugby: 4,726 clubs that fit, which is 1.53 million euros. In three years we target 400 clubs, so 137,000 euros a year. That is about 11 new clubs a month. The club data is old, and we know it. We will check it with the ministry."

*Hand-over: "Eyal will now explain why 15 euros a month."*

### 5. Business model and price (Eyal, 1:15)

"Our model is a monthly subscription for each club. A mid-size club pays 15 euros a month. A flagship club pays 150.

How did we choose 15? We start from the value. A mid-size club earns about 7,200 euros a year from sponsors. If the tool raises it by 30%, and a club uses it 40% of the time in the first year, the net gain is about 780 euros a year, or 65 euros a month. Our price of 15 euros is 23% of that value. The rule of our course says to charge between 10 and 30%, so we are in the range.

15 euros is also lower than the 19 to 49 euros that clubs already pay for management software. Our cost to serve a club is only about 3 euros a month, so the margin is high. For the club, the return in year 1 is about 333%.

The 30% rise is an assumption. It is the weakest number we have, and we will test it in pilot clubs."

*Hand-over: "Joshai will now tell you where we are with real clubs."*

### 6. Traction (Joshai, 1:00)

"We want to be honest on this slide: we have no paying club yet. Here is what we can prove, and what comes next.

Today, the demo works on any business, in four to five seconds, for less than one cent. Taken slots are never offered, and sector conflicts are flagged.

In the next 30 days, we will call 10 mid-size clubs, start 3 pilot clubs, and meet 2 contacts in districts or leagues, because they can pass the tool on to many clubs.

There are three things we still must prove: that sponsoring really goes up, that clubs pay 15 euros a month, and that districts help us. Our goal for the pilot is simple: plus 15% of sponsoring, or two new sponsors per club, in one season."

*Hand-over: "Henry will now show you who else works on this."*

### 7. Competition and defensibility (Henry, 1:15)

"Who else works on this? We found four types of players. All Sponsored scans social media and finds deals. Leedeel is a website that links brands and clubs. Spencer.club is a person who connects both sides. And there are generic tools to write proposals.

As far as we can tell, none of them writes one offer for one business, with its logo on the club's kit, and checks the club's list of free slots. We did not test their products, so this is based on their websites.

Can they copy us? A prompt and a screen can be copied in a weekend, and we know it. So we do not rely on technology. We rely on three things. First, data on which offers are accepted. Second, links with districts and leagues, who bring us many clubs at once. Third, the club's own habits: once its slots and sponsors are in the tool, it is hard to leave."

### 8. Team (Henry, then each person, 0:45)

Henry: "Our team has four people, and each one owns one part."
- Joshai (5 s): "I work on the clubs: their needs, the pilots and the districts."
- Lucas (5 s): "I built the app, the checks and the photos."
- Eyal (5 s): "I built the price, the cash plan and the ask."
- Henry (5 s): "I worked on the market and the competition."

*Hand-over: "Eyal will now take you through the numbers."*

### 9. Financials (Eyal, 1:30)

"Now the numbers. The graph shows our cash over 36 months. We start with fixed costs of 3,000 euros a month. We assume the number of clubs grows in a straight line up to 400 after 3 years.

Our gross margin is 86%, because the AI costs almost nothing: about 4 dollars a month for 400 clubs.

The break-even point is 122 clubs, and we reach it in month 11. Before that, cash goes down to its lowest point, minus 15,000 euros. After that, it goes up. At month 36, we have 400 clubs, 11,400 euros of revenue a month, and about 74,000 euros of cash.

Everything here depends on our assumptions: the prices, and the speed at which we sign clubs. If we sign half as many clubs, break-even comes later. Our calculation file lets us change one number and see the result."

### 10. The ask and conclusion (Eyal, 1:00)

"So here is our ask. We are looking for 35,000 euros, for 18 months. It is built from two numbers: the lowest cash point, about 15,000 euros, plus six months of fixed costs, 18,000 euros, rounded up.

In 18 months, we will deliver three things: three pilot clubs with measured results, one agreement with a district or a league, and the 122 paying clubs that we need to break even.

To conclude: a club has space to sell and no time to sell it. Sponsio writes the offer in seconds and shows the sponsor's logo on the club's own kit. You have seen a working product, a small market that we can count, and a clear plan. Thank you. We are ready for your questions."

## 2b. Who answers which question

| Topic of the question | Who answers first |
|---|---|
| Club needs, pilots, districts, why this use case | Joshai |
| AI, cost per offer, tools, data, AI Act, errors | Lucas |
| Market size, competitors, copying | Henry |
| Price, margin, financials, the ask | Eyal |

If a question is for someone else, say "Eyal, can you answer?" in two seconds. Do not talk over each other. Nobody invents a number: if you do not know, say "it is an assumption, and we will test it."

## 3. The demo checks

Open the link 10 minutes before. Test these five inputs first.

| # | Input | What you should see | Type |
|---|---|---|---|
| 1 | Garage Martin | The minibus and the entrance banner, linked to the need to replace the minibus | easy |
| 2 | Pharmacie des Tilleuls | The boards and the bibs, for families, with no forced minibus | easy |
| 3 | Agence immobilière Century | A warning: a real estate company already sponsors the club | tricky |
| 4 | Chez Momo | A person must check: we cannot tell what the business does | tricky |
| 5 | Cave à vins du Rhône | Blocked before any call to the AI | out of scope |

If the network fails, use your phone as a hotspot. If the app is asleep, wait a few seconds and do not reload many times. Never show the API key or the *Secrets* panel. Never replace the demo with a video.

## 4. What not to say

- "We have clients", or "clubs have confirmed": it is not true yet.
- "Sponsoring will rise by 30% for sure": it is an assumption, the weakest one in our numbers.
- "The market is worth billions": ours is small (€1.53M that we can reach).
- "The photos are made by AI live": no. They are prepared once, and the logo is placed by code.
- "We have no competitors": we do (All Sponsored, Leedeel, Spencer.club, SPONSO+, proposal tools).

## 5. Questions the jury may ask

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

## 6. The day before

- [ ] The demo link is open and tested with a real logo (png and jpg) and the five inputs
- [ ] The deck PDF and the link are sent before Monday 23 November
- [ ] One full rehearsal, timed, under 13 minutes
- [ ] Phone ready as a hotspot, laptop charged
- [ ] Everyone can answer the questions on their own part
