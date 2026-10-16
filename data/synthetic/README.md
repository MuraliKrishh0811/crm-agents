# Synthetic CRM Test Data

Fallback data for the CRM Engagement & Scheduling Agents. Internal org is **Contoso** (`contoso.com`, America/Chicago). Simulation clock: **2026-10-16 10:00 CT**.

Regenerate anytime with `python generate.py` (Python 3.9+, stdlib only). The script also re-validates every scheduling expectation against the mock calendars.

## Folder layout

| Path | Contents |
|---|---|
| `emails/<client>/*.eml` | 32 threaded emails (text + HTML, Outlook-style quoted replies, one attachment) |
| `calendars/mock_calendars.json` | Graph-style events and working hours for 4 internal users, Oct 19-30 2026 |
| `config/team.json` | Team members, client-to-team assignment, scheduling policy |
| `expected/expected_outcomes.json` | Ground truth: stage after each email, actions, scheduling results, traps |

## Internal team

| Person | Role | Email |
|---|---|---|
| Sarah Mitchell | Account Executive | sarah.mitchell@contoso.com |
| Emily Chen | Senior Account Executive | emily.chen@contoso.com |
| Raj Patel | Solutions Engineer | raj.patel@contoso.com |
| David Okafor | Solutions Engineer | david.okafor@contoso.com |

## Scenarios

| Client | Contact (time zone) | Team | Final stage | What it tests |
|---|---|---|---|---|
| Fabrikam | Daniel Brooks (Central) | Sarah + Raj | Converted | Full lifecycle, new-subject thread linking, attachment, **duplicate email** (F08b) |
| Northwind Traders | Priya Nair (Central) | Sarah + David | Not Converted | Unanswered nudge, loss reason, nurture next action |
| Adventure Works | Oliver Bennett (London) | Emily + Raj | Engagement → scheduling | Partial conflicts, tentative handling, **DST offset change** |
| Tailspin Toys | Maria Gonzalez (Denver) | Sarah + David | Engagement → counter-proposal | New lead, vague request, **no overlap**, out-of-office |
| Wingtip Toys | James Carter (New York) | Emily + David | Presentation/Follow-up → reschedule | **Reschedule existing event**, new attendee, open-ended window, `showAs=free` |
| Noise | Contoso HR | - | - | Must be ignored (no CRM record) |

## Scheduling scenarios (expected results)

**SCH-ADV, Adventure Works (60 min, triggered by A05)**
- Tue Oct 20, 15:00-17:00 BST → 09:00-11:00 CDT: rejected (Emily busy until 10:30).
- Wed Oct 21, 14:00-15:30 BST → 08:00-09:30 CDT: fallback only (Raj tentative 08:30-09:00).
- Tue Oct 27, 14:00-16:00 GMT → 09:00-11:00 CDT: **selected 10:00-11:00 CDT (15:00-16:00 GMT)**.
- Trap: the UK leaves summer time on Oct 25 but the US stays on CDT until Nov 1, so the offset drops from 6h to 5h. An agent using a fixed offset picks 08:00-09:00 CDT, which is outside the client's window.

**SCH-TAIL, Tailspin Toys (30 min, triggered by T03)**
- Mon Oct 19 → Sarah out of office. Thu Oct 22 → David in a workshop. No overlap.
- Expected: **no meeting created**; draft a counter-proposal with 2-3 mutual morning slots shown in Mountain time.

**SCH-WING, Wingtip Toys (60 min, triggered by W06)**
- Wed Oct 21 after 3pm ET → only 30 min mutual free before 17:00 CT; rejected.
- Fri Oct 23 11:00-13:00 ET → **selected 10:00-11:00 CDT (11:00-12:00 ET)**. David's "Lunch" is `showAs=free` and must not block. Raj's out-of-office that day is irrelevant (not on the team).
- Expected: **update the existing event** (`iCalUId wingtip-walkthrough-20261022`) and add Lisa Park; do not create a second event.

## General traps across the data
- Replies contain quoted previous messages; extract times only from the new text.
- New subjects (F05, N04, W03) start new threads for the same client; link by domain/contact.
- Outbound (Sent Items) emails also update the CRM history.
- Historical times mentioned in old emails (Aug/Sep) must not trigger scheduling.

## Loading into Outlook later
For Graph testing you can import these `.eml` files into test mailboxes (drag into Outlook desktop, or create them via Graph using MIME). `.msg` isn't generated because it needs Outlook or a commercial library; the Mail Provider should parse `.eml` for the fallback path.
