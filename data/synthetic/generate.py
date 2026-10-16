"""
Synthetic data generator for the CRM Engagement & Scheduling Agents project.

Produces:
  emails/<client>/<id>_<slug>.eml   RFC 822 emails (multipart text + HTML), threaded
  calendars/mock_calendars.json      Graph-like events + working hours per internal user
  config/team.json                   Internal team, roles, and client -> team assignment
  expected/expected_outcomes.json    Ground truth for testing the agents
Then validates the scheduling expectations with a reference slot-intersection check.

Simulation clock: 2026-10-16 10:00 America/Chicago (all scenarios are "as of" this time).
Run: python generate.py
"""
import json, os, re, shutil
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime
from zoneinfo import ZoneInfo

OUT = os.path.dirname(os.path.abspath(__file__))
ORG_TZ = "America/Chicago"
SIM_NOW = "2026-10-16T10:00:00"

# ---------------------------------------------------------------- people
P = {
    # internal (Contoso)
    "sarah": ("Sarah Mitchell", "sarah.mitchell@contoso.com", "Account Executive"),
    "emily": ("Emily Chen", "emily.chen@contoso.com", "Senior Account Executive"),
    "raj":   ("Raj Patel", "raj.patel@contoso.com", "Solutions Engineer"),
    "david": ("David Okafor", "david.okafor@contoso.com", "Solutions Engineer"),
    "hr":    ("Contoso HR", "hr@contoso.com", "HR"),
    "all":   ("All Staff", "all-staff@contoso.com", ""),
    # external
    "daniel": ("Daniel Brooks", "daniel.brooks@fabrikam.com", "VP Sales Operations, Fabrikam Inc."),
    "karen":  ("Karen Wu", "karen.wu@fabrikam.com", "Sales Ops Analyst, Fabrikam Inc."),
    "priya":  ("Priya Nair", "priya.nair@northwindtraders.com", "Operations Manager, Northwind Traders"),
    "oliver": ("Oliver Bennett", "oliver.bennett@adventure-works.com", "Head of Commercial Operations, Adventure Works Cycles"),
    "sophie": ("Sophie Turner", "sophie.turner@adventure-works.com", "Finance Lead, Adventure Works Cycles"),
    "maria":  ("Maria Gonzalez", "maria.gonzalez@tailspintoys.com", "IT Director, Tailspin Toys"),
    "james":  ("James Carter", "james.carter@wingtiptoys.com", "Procurement Lead, Wingtip Toys"),
    "lisa":   ("Lisa Park", "lisa.park@wingtiptoys.com", "CTO, Wingtip Toys"),
}
INTERNAL_PHONE = {"sarah": "+1 (214) 555-0142", "emily": "+1 (214) 555-0178",
                  "raj": "+1 (214) 555-0115", "david": "+1 (214) 555-0193"}

def addr(k): return f"{P[k][0]} <{P[k][1]}>"
def sig(k):
    name, email, title = P[k]
    if k in INTERNAL_PHONE:
        return f"{name}\n{title} | Contoso\n{INTERNAL_PHONE[k]} | {email}"
    return f"{name}\n{title}"

# ---------------------------------------------------------------- emails
# dir: in = received by Contoso (Inbox), out = sent by Contoso (Sent Items)
E = []
def m(id, client, dir, frm, to, cc, date, tz, subject, body, reply_to=None, attach=None, dup_of=None):
    E.append(dict(id=id, client=client, dir=dir, frm=frm, to=to, cc=cc, date=date, tz=tz,
                  subject=subject, body=body.strip("\n") + "\n\n" + sig(frm),
                  reply_to=reply_to, attach=attach, dup_of=dup_of))

CT, LON, DEN, NY = "America/Chicago", "Europe/London", "America/Denver", "America/New_York"

# ---- Scenario 1: Fabrikam (full lifecycle -> CONVERTED, includes duplicate email)
m("F01", "fabrikam", "in", "daniel", ["sarah"], [], "2026-08-03 09:14", CT,
  "Inquiry: sales analytics platform for our field team", """
Hi Sarah,

A colleague at one of our partners recommended Contoso Insight. We have about 120 field sales reps and our pipeline reporting is currently spread across spreadsheets and Dynamics 365. We're looking for something that consolidates forecasting and gives regional managers a weekly view.

Could someone walk us through what the platform does and give us a rough idea of pricing?

Thanks,""")
m("F02", "fabrikam", "out", "sarah", ["daniel"], ["raj"], "2026-08-03 14:40", CT, None, """
Hi Daniel,

Thanks for reaching out, and glad the recommendation came through. I've copied Raj Patel, one of our Solutions Engineers, who works with a lot of teams your size.

A 30-minute discovery call would be the best start so we can understand your current setup. Would sometime this week or early next week work? Let me know a couple of times and we'll send an invite.

Best,""", reply_to="F01")
m("F03", "fabrikam", "in", "daniel", ["sarah"], ["raj", "karen"], "2026-08-04 10:02", CT, None, """
Hi Sarah,

Thursday Aug 6 at 2:00pm Central works, or Friday morning if that's easier. I've added Karen Wu from our sales ops team, she owns the reporting today.

Thanks,""", reply_to="F02")
m("F04", "fabrikam", "out", "sarah", ["daniel"], ["raj", "karen"], "2026-08-04 11:15", CT, None, """
Hi Daniel,

Confirmed for Thursday, Aug 6, 2:00-2:30pm Central. The Teams invite is on its way to you and Karen.

Talk soon,""", reply_to="F03")
m("F05", "fabrikam", "out", "sarah", ["daniel"], ["raj", "karen"], "2026-08-19 16:20", CT,
  "Fabrikam + Contoso Insight: demo recap and proposal", """
Hi Daniel,

Thanks to you and Karen for the time at yesterday's demo. A quick recap of what we covered:

- Consolidated pipeline and forecast views by region, pulling directly from Dynamics 365
- Weekly manager digest emails
- Rollout plan of roughly 4 weeks for 120 seats

The attached proposal covers 120 seats on an annual plan. Happy to walk through any questions, and Raj can go deeper on the technical side.

Best,""", attach=("Contoso_Insight_Proposal_Fabrikam.txt",
                  "Contoso Insight - Proposal for Fabrikam Inc.\nSeats: 120\nTerm: 12 months\nIncludes: forecasting, regional dashboards, manager digest\nPlaceholder file for testing attachment handling.\n"))
m("F06", "fabrikam", "in", "daniel", ["sarah"], ["raj"], "2026-09-02 09:45", CT, None, """
Hi Sarah,

We've reviewed the proposal internally. A few questions before we take it to finance:

1. Does it support SSO with Microsoft Entra ID?
2. Is customer data stored in US data centers?
3. Is there an option for quarterly billing instead of annual upfront?

Thanks,""", reply_to="F05")
m("F07", "fabrikam", "out", "raj", ["daniel"], ["sarah"], "2026-09-02 15:30", CT, None, """
Hi Daniel,

Jumping in on the technical questions:

1. Yes, SSO is supported through Entra ID (SAML and OIDC).
2. Yes, US customers are hosted in US regions by default.
3. Sarah will confirm on billing, but quarterly billing is available on annual terms.

Happy to set up a short call with your IT team if that helps.

Regards,""", reply_to="F06")
m("F08", "fabrikam", "in", "daniel", ["sarah"], ["raj", "karen"], "2026-09-28 11:05", CT, None, """
Hi Sarah,

Good news: finance approved it and I've signed the order form through DocuSign this morning. 120 seats, quarterly billing, starting in October.

What are the next steps for onboarding?

Thanks,""", reply_to="F07")
m("F08b", "fabrikam", "in", "daniel", ["sarah"], ["raj", "karen"], "2026-09-28 11:05", CT, None,
  "", reply_to="F07", dup_of="F08")  # exact duplicate (same Message-ID) -> idempotency test
m("F09", "fabrikam", "out", "sarah", ["daniel"], ["raj", "karen"], "2026-10-08 10:30", CT, None, """
Hi Daniel,

Welcome aboard! We've scheduled the onboarding kickoff for Tuesday, Oct 27, 9:00-10:00am Central with Raj, who'll lead the technical setup. The Teams invite has been sent to you and Karen.

Looking forward to it,""", reply_to="F08")

# ---- Scenario 2: Northwind Traders (-> NOT CONVERTED, one unanswered nudge)
m("N01", "northwind", "in", "priya", ["sarah"], [], "2026-08-17 08:50", CT,
  "Sales and inventory dashboard options", """
Hello Sarah,

We're exploring tools to give our regional sales team a combined view of sales and inventory. Our budget review is in September, so we're trying to shortlist options before then.

Is Contoso Insight a fit for a team of about 40?

Regards,""")
m("N02", "northwind", "out", "sarah", ["priya"], ["david"], "2026-08-17 13:10", CT, None, """
Hi Priya,

Thanks for getting in touch. Yes, teams of around 40 are a common fit. I've copied David Okafor, a Solutions Engineer, who can tailor a demo.

Would Wednesday, Aug 19 at 10:00am or 3:00pm Central work for a 30-minute intro?

Best,""", reply_to="N01")
m("N03", "northwind", "in", "priya", ["sarah"], ["david"], "2026-08-18 09:30", CT, None, """
Hi Sarah,

3:00pm Wednesday works for me.

Regards,""", reply_to="N02")
m("N04", "northwind", "out", "sarah", ["priya"], ["david"], "2026-08-31 17:05", CT,
  "Northwind Traders: demo follow-up and proposal", """
Hi Priya,

Thanks for joining the demo on Friday. As discussed, here's a summary of the proposal:

- 40 seats, 12-month term
- Inventory data connector included
- Go-live in about 3 weeks

Let me know if you'd like anything adjusted before your budget review.

Best,""")
m("N05", "northwind", "out", "sarah", ["priya"], ["david"], "2026-09-10 09:00", CT, None, """
Hi Priya,

Just checking in on the proposal ahead of your budget review. Happy to answer any questions or adjust the scope.

Best,""", reply_to="N04")
m("N06", "northwind", "in", "priya", ["sarah"], ["david"], "2026-09-23 14:22", CT, None, """
Hi Sarah,

Thank you for your patience. We've decided to go with another vendor whose tool is bundled with our ERP, and budgets came in tighter than expected this year.

We appreciated the demo, and I'd be open to revisiting in Q2 next year.

Regards,""", reply_to="N05")
m("N07", "northwind", "out", "sarah", ["priya"], ["david"], "2026-09-24 10:00", CT, None, """
Hi Priya,

Thanks for letting us know, and I understand. I'll reach out in April to see where things stand. All the best with the rollout.

Best,""", reply_to="N06")

# ---- Scenario 3: Adventure Works (ENGAGEMENT, London, partial conflicts + DST trap)
m("A01", "adventureworks", "in", "oliver", ["emily"], [], "2026-10-05 10:20", LON,
  "Following up from the retail tech conference", """
Hi Emily,

We spoke briefly at your stand at the conference in London last week. We're looking for a better way to forecast sales across our UK, EU and US regions, and Contoso Insight looked promising.

Could we find a time to learn more?

Best regards,""")
m("A02", "adventureworks", "out", "emily", ["oliver"], [], "2026-10-05 12:05", CT, None, """
Hi Oliver,

Great to hear from you. To make the conversation useful, could you share:

- Roughly how many users would need access?
- Which CRM you use today?
- Your timeline for a decision?

Best,""", reply_to="A01")
m("A03", "adventureworks", "in", "oliver", ["emily"], [], "2026-10-07 16:40", LON, None, """
Hi Emily,

About 60 users across the three regions. We're on Dynamics 365 Sales, and we'd like to make a decision before the end of Q4.

Best regards,""", reply_to="A02")
m("A04", "adventureworks", "out", "emily", ["oliver"], ["raj"], "2026-10-14 09:30", CT, None, """
Hi Oliver,

Thanks, that's helpful. I'd suggest a 60-minute demo tailored to multi-region forecasting with Raj Patel, our Solutions Engineer (copied).

Could you share a few windows that work for you over the next two weeks?

Best,""", reply_to="A03")
m("A05", "adventureworks", "in", "oliver", ["emily"], ["raj", "sophie"], "2026-10-15 11:12", LON, None, """
Hi Emily,

Thanks. Here are a few windows that work (all UK time):

- Tuesday 20 October, 3:00-5:00pm
- Wednesday 21 October, 2:00-3:30pm
- Tuesday 27 October, 2:00-4:00pm

An hour is fine. I've copied Sophie Turner, our finance lead, who will join as well.

Best regards,""", reply_to="A04")

# ---- Scenario 4: Tailspin Toys (NEW LEAD, vague request, then NO OVERLAP -> counter-proposal)
m("T01", "tailspin", "in", "maria", ["sarah"], [], "2026-10-13 08:05", DEN,
  "Intro call about Contoso Insight", """
Hi Sarah,

I found Contoso Insight through your website. We're evaluating analytics platforms for our 25-person sales team.

Could we set up a quick intro call sometime next week? Mornings work best for me.

Thanks,""")
m("T02", "tailspin", "out", "sarah", ["maria"], ["david"], "2026-10-13 15:20", CT, None, """
Hi Maria,

Thanks for reaching out, happy to set that up. A 30-minute intro with me and David Okafor (Solutions Engineer, copied) would be a good start.

Could you share two or three specific times next week, along with your time zone, so we can line up calendars?

Best,""", reply_to="T01")
m("T03", "tailspin", "in", "maria", ["sarah"], ["david"], "2026-10-15 07:48", DEN, None, """
Hi Sarah,

Sure. Monday Oct 19, 9:00-10:00am, or Thursday Oct 22, 8:00-9:00am. I'm in Denver, so Mountain time.

Thanks,""", reply_to="T02")

# ---- Scenario 5: Wingtip Toys (PRESENTATION, reschedule existing meeting + new attendee)
m("W01", "wingtip", "in", "james", ["emily"], [], "2026-09-14 10:30", NY,
  "Vendor evaluation: sales forecasting", """
Hi Emily,

Wingtip Toys is evaluating vendors for sales forecasting, with a formal decision expected in Q4. Could we schedule an initial conversation?

Regards,""")
m("W02", "wingtip", "out", "emily", ["james"], ["david"], "2026-09-14 13:00", CT, None, """
Hi James,

Thanks for including us. I've copied David Okafor, our Solutions Engineer. Would Tuesday, Sep 22 at 11:00am Central (12:00pm Eastern) work for a discovery call?

Best,""", reply_to="W01")
m("W03", "wingtip", "out", "emily", ["james"], ["david"], "2026-09-24 16:00", CT,
  "Wingtip Toys: discovery recap and next steps", """
Hi James,

Thanks for the discovery call on Tuesday. Next, we'd like to run a pricing and solution walkthrough with your wider team. Let us know a time in the first half of October or later that suits.

Best,""")
m("W04", "wingtip", "in", "james", ["emily"], ["david"], "2026-10-07 09:15", NY, None, """
Hi Emily,

Thursday, Oct 22 at 2:00pm Eastern works for the walkthrough.

Regards,""", reply_to="W03")
m("W05", "wingtip", "out", "emily", ["james"], ["david"], "2026-10-07 11:40", CT, None, """
Hi James,

Confirmed for Thursday, Oct 22, 1:00-2:00pm Central (2:00-3:00pm Eastern). The Teams invite is on its way.

Best,""", reply_to="W04")
m("W06", "wingtip", "in", "james", ["emily"], ["david", "lisa"], "2026-10-16 08:12", NY, None, """
Hi Emily,

Apologies, something has come up with board prep and I need to move Thursday's walkthrough. Could we do Wednesday Oct 21 any time after 3pm Eastern, or Friday Oct 23 between 11am and 1pm Eastern?

I've also copied our CTO, Lisa Park, who would like to attend.

Regards,""", reply_to="W05")

# ---- Noise: internal email that must not create a CRM record
m("X01", "noise", "in", "hr", ["all"], [], "2026-10-15 08:00", CT,
  "Reminder: benefits open enrollment closes Oct 30", """
Hi all,

A reminder that benefits open enrollment closes on Friday, Oct 30. Please review your selections in the HR portal.

Thanks,""")

# ---------------------------------------------------------------- write .eml
def to_html(text):
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paras = esc.split("\n\n")
    return "<html><body>" + "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paras) + "</body></html>"

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]

by_id = {e["id"]: e for e in E}
for e in E:  # resolve thread subject, ids, dates
    e["dt"] = datetime.strptime(e["date"], "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(e["tz"]))
    dom = P[e["frm"]][1].split("@")[1]
    e["msgid"] = f"<{e['id'].lower()}.{e['dt'].strftime('%Y%m%d%H%M')}@{dom}>"
for e in E:
    if e["dup_of"]:
        src = by_id[e["dup_of"]]
        e.update(body=src["body"], msgid=src["msgid"])
    if e["reply_to"]:
        parent = by_id[e["reply_to"]]
        root = parent
        while root["reply_to"]:
            root = by_id[root["reply_to"]]
        e["subject"] = "RE: " + root["subject"]
        refs, cur = [], parent
        while cur:
            refs.insert(0, cur["msgid"]); cur = by_id.get(cur["reply_to"]) if cur["reply_to"] else None
        e["refs"] = refs
        # Outlook-style quoted previous message (agents must ignore quoted text)
        sent = parent["dt"].strftime("%A, %B %d, %Y %I:%M %p")
        e["full_body"] = (e["body"] + "\n\n________________________________\n"
                          f"From: {addr(parent['frm'])}\nSent: {sent}\n"
                          f"To: {', '.join(addr(k) for k in parent['to'])}\n"
                          f"Subject: {parent['subject']}\n\n{parent['body']}")
    else:
        e["refs"] = []
        e["full_body"] = e["body"]

for e in E:
    msg = EmailMessage()
    msg["Message-ID"] = e["msgid"]
    msg["Date"] = format_datetime(e["dt"])
    msg["From"] = addr(e["frm"])
    msg["To"] = ", ".join(addr(k) for k in e["to"])
    if e["cc"]: msg["Cc"] = ", ".join(addr(k) for k in e["cc"])
    msg["Subject"] = e["subject"]
    if e["refs"]:
        msg["In-Reply-To"] = e["refs"][-1]
        msg["References"] = " ".join(e["refs"])
    msg["Thread-Topic"] = re.sub(r"^RE: ", "", e["subject"])
    msg["MIME-Version"] = "1.0"
    msg.set_content(e["full_body"])
    msg.add_alternative(to_html(e["full_body"]), subtype="html")
    if e["attach"]:
        fn, content = e["attach"]
        msg.add_attachment(content.encode(), maintype="text", subtype="plain", filename=fn)
    d = os.path.join(OUT, "emails", e["client"]); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{e['id']}_{slug(e['subject'])}.eml"), "wb") as f:
        f.write(bytes(msg))

# ---------------------------------------------------------------- calendars
WH = {"daysOfWeek": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "startTime": "08:00:00", "endTime": "17:00:00", "timeZone": ORG_TZ}
cal = {k: [] for k in ["sarah", "emily", "raj", "david"]}
def ev(users, eid, subj, start, end, show="busy", allday=False, organizer=None, attendees=None, ical=None):
    for u in users:
        cal[u].append({
            "id": f"{eid}-{u}", "iCalUId": ical or eid, "subject": subj,
            "start": {"dateTime": start, "timeZone": ORG_TZ}, "end": {"dateTime": end, "timeZone": ORG_TZ},
            "showAs": show, "isAllDay": allday, "isOnlineMeeting": bool(attendees),
            "organizer": P[organizer or u][1],
            "attendees": [P[a][1] for a in (attendees or [])],
        })

TEAM = ["sarah", "emily", "raj", "david"]
ev(TEAM, "evt-weekly-0119", "Weekly sales team meeting", "2026-10-19T08:00:00", "2026-10-19T09:00:00", organizer="emily")
ev(TEAM, "evt-weekly-0126", "Weekly sales team meeting", "2026-10-26T08:00:00", "2026-10-26T09:00:00", organizer="emily")
# Sarah
ev(["sarah"], "evt-s1", "Out of office", "2026-10-19T00:00:00", "2026-10-20T00:00:00", show="oof", allday=True)
ev(["sarah"], "evt-s2", "Sales standup", "2026-10-20T08:00:00", "2026-10-20T08:30:00")
ev(["sarah"], "evt-s3", "Customer call: renewals", "2026-10-20T13:00:00", "2026-10-20T14:00:00")
ev(["sarah"], "evt-s4", "Forecast review", "2026-10-21T10:00:00", "2026-10-21T11:00:00")
ev(["sarah"], "evt-s5", "Territory planning", "2026-10-22T14:00:00", "2026-10-22T15:30:00")
# Emily
ev(["emily"], "evt-e1", "Pipeline review", "2026-10-20T09:00:00", "2026-10-20T10:30:00")
ev(["emily"], "evt-e2", "Leadership sync", "2026-10-21T14:00:00", "2026-10-21T15:30:00")
ev(["emily"], "evt-e3", "1:1 with VP Sales", "2026-10-23T13:00:00", "2026-10-23T14:00:00")
ev(["emily"], "evt-e4", "QBR prep", "2026-10-28T10:00:00", "2026-10-28T12:00:00")
# Raj
ev(["raj"], "evt-r1", "Vendor call (tentative)", "2026-10-21T08:30:00", "2026-10-21T09:00:00", show="tentative")
ev(["raj"], "evt-r2", "Out of office", "2026-10-23T00:00:00", "2026-10-24T00:00:00", show="oof", allday=True)
ev(["raj"], "evt-r3", "Architecture review", "2026-10-27T11:00:00", "2026-10-27T12:00:00")
# David
ev(["david"], "evt-d1", "Partner enablement", "2026-10-20T09:00:00", "2026-10-20T10:00:00")
ev(["david"], "evt-d2", "Proof of concept build", "2026-10-21T11:00:00", "2026-10-21T12:00:00")
ev(["david"], "evt-d3", "Internal architecture review", "2026-10-21T15:30:00", "2026-10-21T16:30:00")
ev(["david"], "evt-d4", "Customer workshop", "2026-10-22T08:30:00", "2026-10-22T10:00:00")
ev(["david"], "evt-d5", "Lunch", "2026-10-23T11:30:00", "2026-10-23T12:30:00", show="free")
# Customer meetings already booked (agent-created in earlier cycles)
ev(["sarah", "raj"], "evt-fabrikam-kickoff", "Fabrikam: Onboarding kickoff",
   "2026-10-27T09:00:00", "2026-10-27T10:00:00", organizer="sarah",
   attendees=["sarah", "raj", "daniel", "karen"], ical="fabrikam-kickoff-20261027")
ev(["emily", "david"], "evt-wingtip-walkthrough", "Wingtip Toys: Pricing & solution walkthrough",
   "2026-10-22T13:00:00", "2026-10-22T14:00:00", organizer="emily",
   attendees=["emily", "david", "james"], ical="wingtip-walkthrough-20261022")

calendars = {
    "description": "Mock calendars for internal users. Event shape follows Microsoft Graph /events "
                   "(showAs: free|tentative|busy|oof|workingElsewhere). Times are local to timeZone.",
    "window": {"start": "2026-10-19T00:00:00", "end": "2026-10-31T00:00:00", "timeZone": ORG_TZ},
    "users": {P[u][1]: {"displayName": P[u][0], "workingHours": WH,
                        "events": sorted(cal[u], key=lambda x: x["start"]["dateTime"])} for u in cal},
}
os.makedirs(os.path.join(OUT, "calendars"), exist_ok=True)
json.dump(calendars, open(os.path.join(OUT, "calendars", "mock_calendars.json"), "w"), indent=2)

# ---------------------------------------------------------------- team config
team = {
    "organization": {"name": "Contoso", "domain": "contoso.com", "timeZone": ORG_TZ, "simulationNow": SIM_NOW},
    "members": [{"key": k, "name": P[k][0], "email": P[k][1], "role": P[k][2]} for k in TEAM],
    "assignmentRules": {
        "default": {"accountExecutive": "sarah.mitchell@contoso.com", "solutionsEngineer": "david.okafor@contoso.com"},
        "byClientDomain": {
            "fabrikam.com": ["sarah.mitchell@contoso.com", "raj.patel@contoso.com"],
            "northwindtraders.com": ["sarah.mitchell@contoso.com", "david.okafor@contoso.com"],
            "adventure-works.com": ["emily.chen@contoso.com", "raj.patel@contoso.com"],
            "tailspintoys.com": ["sarah.mitchell@contoso.com", "david.okafor@contoso.com"],
            "wingtiptoys.com": ["emily.chen@contoso.com", "david.okafor@contoso.com"],
        },
    },
    "schedulingPolicy": {
        "durationsMinutes": {"intro": 30, "discovery": 30, "demo": 60, "walkthrough": 60, "kickoff": 60},
        "slotGranularityMinutes": 30,
        "hardBlocking": ["busy", "oof"],
        "softBlocking": ["tentative"],
        "nonBlocking": ["free", "workingElsewhere"],
        "respectInternalWorkingHours": True,
        "maxSuggestions": 3,
        "requireHumanApproval": True,
    },
}
os.makedirs(os.path.join(OUT, "config"), exist_ok=True)
json.dump(team, open(os.path.join(OUT, "config", "team.json"), "w"), indent=2)

# ---------------------------------------------------------------- expected outcomes
def em(id, stage, actions, note=""):
    return {"emailId": id, "expectedStageAfter": stage, "expectedActions": actions, "notes": note}

expected = {
    "stages": ["Initial Lead", "Engagement", "Presentation/Follow-up", "Converted", "Not Converted"],
    "stageDefinitions": {
        "Initial Lead": "First contact; no two-way conversation established yet.",
        "Engagement": "Active two-way conversation, discovery, or arranging an intro/discovery call.",
        "Presentation/Follow-up": "Demo/walkthrough/proposal delivered or a presentation meeting is confirmed.",
        "Converted": "Client has committed (signed, PO, approved purchase).",
        "Not Converted": "Client has declined, chosen another vendor, or gone dark after closure.",
    },
    "simulationNow": SIM_NOW,
    "clients": {
        "fabrikam": {
            "finalStage": "Converted",
            "nextAction": "Run onboarding kickoff on 2026-10-27 09:00-10:00 CT (already scheduled).",
            "emails": [
                em("F01", "Initial Lead", ["create_lead"]),
                em("F02", "Initial Lead", ["log_engagement"]),
                em("F03", "Engagement", ["log_engagement", "add_contact:karen.wu@fabrikam.com"],
                   "Client proposed times for a past call; historical, no scheduling action."),
                em("F04", "Engagement", ["log_engagement", "log_meeting:2026-08-06 14:00 CT discovery"]),
                em("F05", "Presentation/Follow-up", ["log_engagement", "log_attachment:proposal"],
                   "New subject but same client: must link by domain/contacts, not thread."),
                em("F06", "Presentation/Follow-up", ["log_engagement", "set_next_action:answer questions"]),
                em("F07", "Presentation/Follow-up", ["log_engagement"]),
                em("F08", "Converted", ["set_stage:Converted", "set_next_action:onboarding"]),
                em("F08b", "Converted", ["ignore_duplicate"], "Same Message-ID as F08; must not create a second record."),
                em("F09", "Converted", ["log_engagement", "log_meeting:2026-10-27 09:00 CT kickoff"]),
            ]},
        "northwind": {
            "finalStage": "Not Converted",
            "lossReason": "Chose competitor bundled with ERP; tighter budget.",
            "nextAction": "Nurture: re-engage in April 2027.",
            "emails": [
                em("N01", "Initial Lead", ["create_lead"]),
                em("N02", "Initial Lead", ["log_engagement"]),
                em("N03", "Engagement", ["log_engagement"]),
                em("N04", "Presentation/Follow-up", ["log_engagement"]),
                em("N05", "Presentation/Follow-up", ["log_engagement"], "Unanswered nudge; no stage change."),
                em("N06", "Not Converted", ["set_stage:Not Converted", "record_loss_reason"]),
                em("N07", "Not Converted", ["set_next_action:re-engage 2027-04"]),
            ]},
        "adventureworks": {
            "finalStage": "Engagement",
            "nextAction": "Get approval for demo slot and create Teams meeting.",
            "emails": [
                em("A01", "Initial Lead", ["create_lead"]),
                em("A02", "Initial Lead", ["log_engagement"]),
                em("A03", "Engagement", ["log_engagement", "capture:60 users, Dynamics 365, decision by end of Q4"]),
                em("A04", "Engagement", ["log_engagement"]),
                em("A05", "Engagement", ["add_contact:sophie.turner@adventure-works.com", "schedule_meeting"],
                   "See scheduling scenario SCH-ADV."),
            ]},
        "tailspin": {
            "finalStage": "Engagement",
            "nextAction": "Send counter-proposal with internal free morning slots.",
            "emails": [
                em("T01", "Initial Lead", ["create_lead", "request_clarification"],
                   "Vague 'sometime next week, mornings': ask for specific times rather than guess."),
                em("T02", "Initial Lead", ["log_engagement"]),
                em("T03", "Engagement", ["schedule_meeting"], "See scheduling scenario SCH-TAIL."),
            ]},
        "wingtip": {
            "finalStage": "Presentation/Follow-up",
            "nextAction": "Get approval to move walkthrough; update existing event.",
            "emails": [
                em("W01", "Initial Lead", ["create_lead"]),
                em("W02", "Initial Lead", ["log_engagement"]),
                em("W03", "Engagement", ["log_engagement"], "New subject, same client."),
                em("W04", "Engagement", ["log_engagement"]),
                em("W05", "Presentation/Follow-up", ["log_meeting:2026-10-22 13:00 CT walkthrough"]),
                em("W06", "Presentation/Follow-up", ["add_contact:lisa.park@wingtiptoys.com", "reschedule_meeting"],
                   "See scheduling scenario SCH-WING."),
            ]},
        "noise": {"emails": [em("X01", None, ["ignore_noise"], "Internal email; no CRM record.")]},
    },
    "schedulingScenarios": [
        {
            "id": "SCH-ADV", "client": "adventureworks", "triggerEmail": "A05",
            "attendeesInternal": ["emily.chen@contoso.com", "raj.patel@contoso.com"],
            "attendeesExternal": ["oliver.bennett@adventure-works.com", "sophie.turner@adventure-works.com"],
            "durationMinutes": 60, "clientTimeZone": LON,
            "clientSlots": [
                {"client": "2026-10-20 15:00-17:00 BST", "orgTime": "2026-10-20 09:00-11:00 CDT",
                 "result": "rejected", "reason": "Emily busy 09:00-10:30; only 30 min common free."},
                {"client": "2026-10-21 14:00-15:30 BST", "orgTime": "2026-10-21 08:00-09:30 CDT",
                 "result": "fallback_with_warning", "reason": "Raj tentative 08:30-09:00; no 60-min fully-free window."},
                {"client": "2026-10-27 14:00-16:00 GMT", "orgTime": "2026-10-27 09:00-11:00 CDT",
                 "result": "selected", "reason": "Raj busy 09:00-10:00 (Fabrikam kickoff); 10:00-11:00 free for both."},
            ],
            "expectedRecommendation": {"orgTime": "2026-10-27T10:00:00 to 11:00:00 America/Chicago",
                                       "clientTime": "2026-10-27 15:00-16:00 GMT"},
            "expectedAction": "create_event (Teams) after approval; stage -> Presentation/Follow-up",
            "traps": ["UK leaves BST on 2026-10-25, US stays on CDT until 2026-11-01: offset is 6h before, 5h after. "
                      "Using a fixed 6h offset for Oct 27 yields 08:00-09:00 CDT, which is outside the client's window.",
                      "Tentative should be soft, not hard-blocking.",
                      "Add Sophie Turner (cc'd) as attendee."],
        },
        {
            "id": "SCH-TAIL", "client": "tailspin", "triggerEmail": "T03",
            "attendeesInternal": ["sarah.mitchell@contoso.com", "david.okafor@contoso.com"],
            "attendeesExternal": ["maria.gonzalez@tailspintoys.com"],
            "durationMinutes": 30, "clientTimeZone": DEN,
            "clientSlots": [
                {"client": "2026-10-19 09:00-10:00 MDT", "orgTime": "2026-10-19 10:00-11:00 CDT",
                 "result": "rejected", "reason": "Sarah out of office all day."},
                {"client": "2026-10-22 08:00-09:00 MDT", "orgTime": "2026-10-22 09:00-10:00 CDT",
                 "result": "rejected", "reason": "David busy 08:30-10:00 (customer workshop)."},
            ],
            "expectedRecommendation": None,
            "expectedAction": "counter_propose: draft reply with 2-3 slots where Sarah and David are both free, "
                              "in client's mornings (08:00-12:00 MDT = 09:00-13:00 CDT), shown in Mountain time",
            "validCounterProposalExamples": ["2026-10-20 10:00-10:30 CDT (09:00 MDT)",
                                             "2026-10-21 09:00-09:30 CDT (08:00 MDT)",
                                             "2026-10-22 10:00-10:30 CDT (09:00 MDT)"],
            "traps": ["Must not create a meeting when no overlap exists.",
                      "Earlier email T01 was vague; agent should have asked for specifics, not guessed."],
        },
        {
            "id": "SCH-WING", "client": "wingtip", "triggerEmail": "W06",
            "attendeesInternal": ["emily.chen@contoso.com", "david.okafor@contoso.com"],
            "attendeesExternal": ["james.carter@wingtiptoys.com", "lisa.park@wingtiptoys.com"],
            "durationMinutes": 60, "clientTimeZone": NY,
            "existingEvent": "iCalUId wingtip-walkthrough-20261022 (2026-10-22 13:00-14:00 CDT)",
            "clientSlots": [
                {"client": "2026-10-21 after 15:00 EDT", "orgTime": "2026-10-21 14:00-17:00 CDT (capped at working hours)",
                 "result": "rejected", "reason": "Emily busy 14:00-15:30, David busy 15:30-16:30; only 16:30-17:00 common. "
                                                 "17:00-18:00 is outside working hours: may mention but not propose without approval."},
                {"client": "2026-10-23 11:00-13:00 EDT", "orgTime": "2026-10-23 10:00-12:00 CDT",
                 "result": "selected", "reason": "Both free; David's 'Lunch' 11:30-12:30 has showAs=free and must not block."},
            ],
            "expectedRecommendation": {"orgTime": "2026-10-23T10:00:00 to 11:00:00 America/Chicago",
                                       "clientTime": "2026-10-23 11:00-12:00 EDT"},
            "expectedAction": "update_event (PATCH existing event, add lisa.park@wingtiptoys.com) after approval; "
                              "do NOT create a second event",
            "traps": ["Open-ended client window must be capped by internal working hours.",
                      "Raj is OOF Oct 23 but is not on this team; must not block.",
                      "showAs=free events do not block."],
        },
    ],
}
os.makedirs(os.path.join(OUT, "expected"), exist_ok=True)
json.dump(expected, open(os.path.join(OUT, "expected", "expected_outcomes.json"), "w"), indent=2)

# ---------------------------------------------------------------- validation (reference scheduler)
def parse(s): return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(ORG_TZ))
def blocks(user_email, kinds):
    return [(parse(e["start"]["dateTime"]), parse(e["end"]["dateTime"]))
            for e in calendars["users"][user_email]["events"] if e["showAs"] in kinds]
def free_slots(users, win_start, win_end, dur, kinds=("busy", "oof"), step=30):
    out, t = [], win_start
    while t + timedelta(minutes=dur) <= win_end:
        e = t + timedelta(minutes=dur)
        in_hours = t.hour >= 8 and (e.hour < 17 or (e.hour == 17 and e.minute == 0)) and t.date() == e.date()
        if in_hours and all(not (s < e and t < en) for u in users for s, en in blocks(u, kinds)):
            out.append(t)
        t += timedelta(minutes=step)
    return out
def client(s, tz): return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(tz)).astimezone(ZoneInfo(ORG_TZ))

E_, R_, S_, D_ = (P[k][1] for k in ["emily", "raj", "sarah", "david"])
# SCH-ADV
assert free_slots([E_, R_], client("2026-10-20T15:00", LON), client("2026-10-20T17:00", LON), 60) == []
assert free_slots([E_, R_], client("2026-10-21T14:00", LON), client("2026-10-21T15:30", LON), 60, kinds=("busy", "oof", "tentative")) == []
soft = [t for t in [parse("2026-10-21T08:00:00"), parse("2026-10-21T08:30:00")]
        if all(not (s < t + timedelta(minutes=60) and t < en) for u in [E_, R_] for s, en in blocks(u, ("busy", "oof")))]
assert soft, "expected a tentative-only fallback on Oct 21"
adv = free_slots([E_, R_], client("2026-10-27T14:00", LON), client("2026-10-27T16:00", LON), 60)
assert adv == [parse("2026-10-27T10:00:00")], adv
naive = free_slots([E_, R_], parse("2026-10-27T08:00:00"), parse("2026-10-27T10:00:00"), 60)
assert naive == [parse("2026-10-27T08:00:00")], naive  # the wrong answer a fixed-offset agent would give
# SCH-TAIL
assert free_slots([S_, D_], client("2026-10-19T09:00", DEN), client("2026-10-19T10:00", DEN), 30) == []
assert free_slots([S_, D_], client("2026-10-22T08:00", DEN), client("2026-10-22T09:00", DEN), 30) == []
for ex in ["2026-10-20T10:00:00", "2026-10-21T09:00:00", "2026-10-22T10:00:00"]:
    t = parse(ex); assert t in free_slots([S_, D_], t, t + timedelta(minutes=30), 30), ex
# SCH-WING (existing walkthrough is on Oct 22, outside both windows)
assert free_slots([E_, D_], client("2026-10-21T15:00", NY), parse("2026-10-21T17:00:00"), 60) == []
wing = free_slots([E_, D_], client("2026-10-23T11:00", NY), client("2026-10-23T13:00", NY), 60)
assert wing[0] == parse("2026-10-23T10:00:00"), wing

print(f"Generated {len(E)} emails, calendars for {len(cal)} users. All scheduling expectations validated.")
