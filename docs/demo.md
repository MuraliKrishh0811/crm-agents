# Demo guide: what the assistant does, in plain language

Status, 2026-10-16: **this guide describes the demo we are building. The system is not built yet, so nothing in this guide has been run.** The screens described here will exist after the dashboard is built. Where something is uncertain, this guide says so.

## The idea in one paragraph

Sales teams get a lot of email from customers. This assistant reads those emails, works out where each customer stands (a first contact, an active conversation, a presentation stage, a signed deal, or a lost deal), suggests what to do next, and helps arrange meetings. When a customer suggests times to meet, the assistant checks our team's calendars, finds times that work, and writes a draft reply. **It never books a meeting or sends a message by itself. A person always has to click "approve" first.**

## What is real and what is pretend

This first version runs entirely on practice data. It is **not connected to Microsoft 365 (our real email and calendars) or to Azure (Microsoft's online AI service).** We do not have access to those yet.

| Part | In this demo | Later, with access |
|---|---|---|
| Emails | 32 practice emails saved as files, played back one at a time as if they were arriving | Our real inbox |
| Calendars | Practice calendars for four colleagues, covering 19 to 30 October 2026 | Real calendars |
| The AI | A smaller AI model running on one laptop (it reads and writes text) | A larger online AI service |
| Customer records | A simple database on the laptop | A company database (not chosen yet) |
| Meeting video link | A **made-up link, clearly marked "simulated"** | A real Teams link |
| Today's date | Pretend today is Friday 16 October 2026, 10:00 in Chicago | The real date |

The parts that will talk to Microsoft 365 and Azure are being written from Microsoft's instructions, but they have **never been tried**. We call them "unverified" and keep them switched off. A checklist (`first_day_with_access.md`) lists what to test the first day we get access. Until then, we cannot promise how they will behave.

## The cast (all made up)

Our company is **Contoso**. Four colleagues: Sarah Mitchell and Emily Chen (account executives), and Raj Patel and David Okafor (technical specialists). Five practice customers: Fabrikam, Northwind Traders, Adventure Works Cycles, Tailspin Toys and Wingtip Toys. One of the 32 emails is a company-wide HR announcement that has nothing to do with customers.

## The walkthrough

### 1. Playing back the inbox

We start the assistant and let it read the practice emails in date order. For each email it:

- ignores the HR announcement (it is not about a customer) and ignores an email that is an exact repeat of an earlier one, so nothing is recorded twice;
- links the email to the right customer, even when the subject line is new, by looking at who wrote it and which company they are from;
- notes new people (for example, a colleague who was copied in) as contacts;
- decides whether the customer's stage has changed, and writes a short summary and a suggested next step.

**Nothing is booked or sent during this step.** At the end, the assistant has three meeting requests waiting for a person (Adventure Works, Tailspin and Wingtip).

A waiting request can change before anyone looks at it. If the customer sends a newer email in the same conversation with new times, the newer email **replaces** the older request (the older one stays in the history, marked as replaced). If the customer withdraws the request, it is **cancelled**. If all the times the customer offered have passed, it is closed as **out of date**. Nothing is ever deleted, so the history can be checked.

*Because the AI model is small, it can make mistakes. We keep an answer sheet that is used only for checking our work, never by the assistant itself, and we report how often the model picks the right stage.*

### 2. The pipeline board

The first screen shows customers in five columns: first contact, active conversation, presentation or follow-up, signed, and lost. After playback you would see Fabrikam as signed, Northwind as lost, Adventure Works and Tailspin as active conversations, and Wingtip at presentation or follow-up.

### 3. A customer page

Click a customer to see their stage, their contacts, a timeline of emails and meetings, and the suggested next step. Two examples:

- **Fabrikam**: a full journey from first contact to signed. The suggested next step is a kickoff meeting on 27 October at 9:00 in Chicago, which is already in the calendar.
- **Northwind Traders**: a deal that was lost to a competitor. The assistant recorded the reason (the competitor bundled it with other software, and Northwind's budget was tighter). A reminder to get back in touch in April 2027 is suggested. A polite nudge email that got no reply did **not** change the stage.

### 4. A meeting request that works out: Adventure Works

The customer is in London and asks for a one-hour meeting, offering three time slots. The assistant checks the calendars of the two colleagues on this account, Emily and Raj, and only those two. It then explains each slot:

- **Tuesday 20 October:** not possible. Emily is busy until 10:30 Chicago time.
- **Wednesday 21 October:** possible only as a backup, with a warning. Raj has a "maybe" entry from 8:30 to 9:00.
- **Tuesday 27 October:** works. **10:00 to 11:00 Chicago time, which is 3:00 to 4:00 pm in London.** Raj is busy before 10:00 with the Fabrikam kickoff.

**A time-zone trap the assistant must get right.** London's clocks go back on 25 October. Chicago's clocks go back a week later, on 1 November. So until 1 November the gap between the two cities is 6 hours for some dates and 5 hours for others. Using a fixed gap of 6 hours would book 8:00 in Chicago on 27 October, which is outside the time the customer offered. The assistant uses a proper world-clock table, not the AI model, to work out times. Phrases such as "next Thursday" are worked out from the day the customer **wrote** the email, not from today's date, and offered times that are already in the past are dropped. Each colleague's working hours come from their own calendar (with a standard 8:00 to 17:00 weekday day if none is set). To know **where the customer is**, the assistant uses what it already knows about that person, then any place named in the email, then clues such as the time stamp on the email, which it checks with fixed rules. If it is still unsure, it asks the customer to confirm instead of guessing. Times that fall outside the practice calendars (19 to 31 October) are treated as unknown and are never offered.

The assistant writes a draft reply and **waits**. Nothing is booked yet. The backup option (Wednesday) is listed last with its warning, so the person can see it but is not nudged towards it.

### 5. A person approves

On the approval screen the person sees the proposed time, who would be invited, and the draft reply. They can **approve, edit the draft, or reject**. Editing only changes the wording of the reply; it does not change the times or the people, because those are worked out by fixed rules, and the edit is noted in the history. Approving means picking **exactly one** of the proposed times. In this demo there is no sign-in screen: every approval is recorded, with the time, under the one person who is set up on this laptop. Real sign-in comes later, with Microsoft 365.

Because there is no sign-in, the assistant protects the approve button in another way. It only answers to this laptop, it only accepts approvals that come from its own dashboard, and each approval has to carry a one-time pass that is created fresh every time the assistant starts and is never saved in a file. A web page open in the same browser cannot approve anything by accident. Other programs running on the same laptop are not stopped, which is one reason real sign-in is planned.

When they approve, the assistant works through four steps in order and records each one (the screen shows an overall status: not started, in progress, completed, or partly completed):

1. **It checks the calendars once more** for the chosen time, because things can change between the proposal and the approval.
2. **It creates the meeting** and invitations go to Emily, Raj, the customer's contact Oliver Bennett, and his colleague Sophie Turner (in this demo the video link is made up and marked "simulated").
3. **It sends the confirmation reply.**
4. **It updates the customer record:** Adventure Works moves to "presentation or follow-up", and the system records who approved and when.

If someone has become busy since the proposal, the check in step 1 stops everything: **nothing is booked and nothing is sent**, the request is marked "needs review", the approval goes back to "not started", and the assistant puts fresh options in place of the old ones (the old ones stay in the history). The person then approves one of the fresh options or rejects. If a later step fails (for example, the confirmation cannot be sent), the screen shows exactly which step failed, nothing that was already done is undone, and the person can retry. The meeting is not created twice. Clicking approve a second time never creates a second meeting.

### 6. A request with no possible time: Tailspin Toys

The customer's first email is vague ("let's find a time") with no actual times. The assistant **does not guess**. It drafts a polite question asking for specific times.

Later the customer, in Denver, offers two times. Neither works: Sarah is away for all of Monday 19 October, and David is busy on the morning of Thursday 22 October. So the assistant writes a reply offering two or three mornings that **do** work for both colleagues (for example Tuesday 20 October at 10:00 Chicago time, which is 9:00 in Denver), with the times shown **in Denver time**. No meeting is created. When a person approves, the reply is sent, and Tailspin stays in "active conversation". If the customer's later email is part of the same conversation as the earlier polite question, the earlier waiting question is replaced by this new proposal and kept in the history.

### 7. Moving a meeting that already exists: Wingtip Toys

Wingtip has a walkthrough booked for Thursday 22 October at 1:00 pm Chicago time. The customer, in New York, asks to move it and mentions that a colleague, Lisa Park, will join. The assistant checks the two colleagues on the account:

- **Wednesday 21 October, after 3:00 pm New York time:** not possible. After the working day is taken into account, the colleagues' busy times leave only 30 minutes, and an hour is needed.
- **Friday 23 October:** works. **10:00 to 11:00 Chicago time, which is 11:00 to 12:00 in New York.**

Two details the assistant gets right: David's "lunch" entry is marked as free time, so it does not block the meeting. And Raj is away that day, but he is not on this meeting, so his absence does not matter.

When a person approves, the **existing** meeting is moved, Lisa Park is added, and a confirmation is sent. A second meeting is **not** created. Wingtip stays at "presentation or follow-up".

### 8. "What did the assistant decide?"

An audit screen lists every step the assistant took: which part of the assistant did it, what it decided, and which AI model and data source were used, with the time and how long it took. This is how a person can check the assistant's work. If one email could not be understood, the assistant records the problem and carries on with the rest.

## What always needs a person

- Booking, changing or cancelling a meeting.
- Sending any message to a customer.

The assistant only proposes. That is a rule, not a setting.

## What happens if the person says no

The request is marked "rejected", nothing is booked or sent, and the person can add a reason. Nothing happens automatically afterwards. A new request appears only when the customer writes again.

## What this demo does not show

- Real email or calendars, real Teams meetings, or the real online AI service. Those are not connected, and their behavior is untested.
- A Teams chat assistant ("where does Fabrikam stand?"). It is planned for after the dashboard.
- Real sign-in. In this demo the assistant runs only on this laptop and approvals are recorded under one set-up person. Sign-in with company accounts is designed but not built or tested, and who may approve is for IT to decide later.
- Where the system will eventually run (hosting). Not decided.

## Things we are still deciding

The design questions about how the assistant behaves have all been settled: what replaces, cancels or closes a waiting request, the check before booking, what happens when that check finds a clash or a step fails, how approvals are recorded, how far an edit can go, what happens after a rejection, how the assistant works out where a customer is, what it does about dates outside the practice calendars, and how the approve button is protected. What is left is practical work and checks, not open questions about behavior: trying out the connections to Microsoft 365 and Azure once access is granted, agreeing with the IT team who may approve and what permissions are needed, and choosing where the system will eventually run. The technical design (`hld.md`) lists these.

## Questions people often ask

**Can the assistant send emails on its own?** No. Every send and every booking needs a person's approval.

**Does the AI choose the meeting times?** No. The AI reads and writes text. The times, time zones and calendar checks are worked out by ordinary rules that can be tested.

**Is it accurate?** We measure it against an answer sheet and report the result. Because the model is small, we expect some mistakes, which is why a person checks every proposal.

**What if a colleague's calendar changes before the person approves?** The assistant checks again at the moment of approval. If the time is no longer free, it books nothing and asks the person to review fresh options.

**What if something goes wrong halfway through an approval?** The screen shows which step failed. Steps that already worked are kept and are not repeated, and the person can retry. There is no automatic undo in this first version.

**What if the person approves twice?** Nothing is duplicated. The second click returns the result of the first.

**Could a website I happen to have open approve a meeting?** It should not be able to. The assistant only answers to this laptop, only accepts approvals from its own dashboard, and needs a one-time pass that a website cannot read. We will test this by sending approvals that look like they come from somewhere else and checking that every one is refused. This has been designed but not built or tried yet.

**Is any of this connected to real customers?** No. Everything in this version is practice data.

**What happens next?** The assistant is built in small steps, tested at each step. Once Microsoft 365 and Azure access is granted, we switch over by changing settings and test each connection against the first-day checklist before trusting it.

## Word list

- **Pipeline:** the customers arranged by how far along they are.
- **Stage:** where a customer is, from first contact to signed or lost.
- **Draft reply:** an email written by the assistant that nobody has sent yet.
- **Approve:** a person's click that allows the assistant to book or send.
- **Simulated:** made up for the practice version because the real thing is not connected.
- **Audit:** the record of what the assistant did and decided.
