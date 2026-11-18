# Asana → Codigo Task Manager migration check

**Date:** 17 November 2026, 12:36 SGT (corrected)
**Asana project:** [KMS] Client UAT tickets (project `1212423157941626`)
**New tool:** https://taskmanager.codigo.co/projects/01a1e3a4-ab90-733e-8cf7-94bc395e9edc/list

## Result

| Check | Result |
|---|---|
| Asana tasks | 303 (298 top-level + 5 subtasks) |
| Found in new tool | 302 (99.7%) |
| Missing | 1 (blank Open Tickets placeholder) |
| Comment counts | 302 / 302 match |
| KMS references | 302 / 302 numeric values match (`KMS-` prefix dropped) |
| Status / assignee / due | 1 task diverged |
| Attachments | 8 videos and 12 link previews missing; no image/PDF/Office files lost |

**Correction:** an earlier version of this report listed 8 Closed tasks as missing. That was an artefact of the board/RSC page audit, which did not load the tail of the Closed section. The Task Manager project CSV export confirms all 8 exist. This report has been rebuilt from that CSV export and the live task-detail API.

The new project holds 298 top-level tasks plus 39 subtasks (337 items). 35 subtasks are new work breakdowns that do not exist in Asana; one top-level "Untitled task" is the migrated version of an untitled Asana task.

## Missing tasks (1)

| Section | Task | Asana |
|---|---|---|
| Open Tickets | *(untitled placeholder: no title, notes, comments or assignee)* | [1219961596020711](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219961596020711) |

This is the only unmatched Asana task. It is an empty placeholder, not a reportable ticket.

**Confirmed present (previously misreported as missing):**

- [Frontend] Invalid OTP code error when updating profile during user signup — [1212651455605632](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212651455605632)
- F-041 - There is no Cancellation: Off Option for Bixep Setup — [1213145021450881](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1213145021450881)
- [CMS] Dharma School Course Setup - Title for Chinese totally not allow English Character. — [1212562259010656](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212562259010656)
- [Frontend] Dharma Education -> Explore -> Buddhist College of Singapore Link — [1212612665289224](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212612665289224)
- [Frontend] Tour routes in Interactive Map — [1212601809091622](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212601809091622)
- [Frontend] Redundant Dharma and Dharma Courses (for adults) buttons. — [1212577473768549](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212577473768549)
- [CMS] I cannot create a project, and the project is internal or external for event creation? — [1212593713869443](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212593713869443)
- [Frontend] Wrong Spelling "Dragon Pong" in interactive map — [1212562259010650](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212562259010650)

## Divergence (1)

| Task | Asana | New tool |
|---|---|---|
| [Web] Contact Us - Acknowledgement email Chinese version | Fix In Progress, Harry, due 16 Nov | QA to verify, Zin Hnin Wai, due 18 Nov |

This looks like a post-migration update in the new tool rather than a migration error. Confirm which system is authoritative.

Three other tasks changed to **Closed in both systems** after the 15 November baseline, so they are not discrepancies: Online Pledge Count choice, Dharma School delete test record, Offering Listing Stock.

## Attachments

**8 screen recordings were not carried over:**

| Task | Missing file |
|---|---|
| [CMS] Bright Youth Page Upload Image | Screen Recording 2026-07-07 at 09.44.52.mov |
| [CMS] Finance - Code Management module | Screen Recording 2026-07-07 at 10.23.42.mov |
| [Web & CMS] Contents not loading and unable to update | Screen Recording 2026-10-15 at 12.04.05.mov |
| [Web] - Join Us - Volunteer - Volunteer Events Section | Screen Recording 2026-10-27 at 12.40.40.mov |
| Select date range for Facility Bookings - Internal Facilities | Screen Recording 2026-06-11 at 08.48.31.mov |
| [Web] Awaken Online - Articles - Text interface | Screen Recording 2026-11-12 at 10.05.17.mov |
| [Awaken Online] Article drafts cannot be published | KMS CMS - Google Chrome 2026-06-11 12-39-49.mp4 |
| [E-Store] Additional Info Sections Error | KMS CMS - Google Chrome 2026-06-12 09-10-15.mp4 |

**12 Figma link previews on 11 tasks** were not carried over. Asana stores these as URL attachments; the new tool does not. They are links, not files, and can be re-added in the description or comments.

No image, PDF or Office attachments are missing. The 8 previously misreported tasks added no attachment losses.

## Section reconciliation

| Section | Asana | Found | Missing |
|---|---:|---:|---:|
| To disscuss/confirm | 5 | 5 | 0 |
| Open Tickets | 1 | 0 | 1 |
| New Request on Pre-prod | 8 | 8 | 0 |
| To update hardcoded content on Pre-prod | 2 | 2 | 0 |
| Fix In Progress | 3 | 3 | 0 |
| Fail (To fix again) | 1 | 1 | 0 |
| QA to verify | 7 | 7 | 0 |
| Client to verify | 3 | 3 | 0 |
| Closed | 248 | 248 | 0 |
| Invalid / Duplicate ticket - To Ignore | 8 | 8 | 0 |
| To verify again (KMS internal use - CR) | 17 | 17 | 0 |
| **Total** | **303** | **302** | **1** |

Asana counts include 5 subtasks. The new tool's "Closed" section display count includes 8 nested subtasks, so it is not directly comparable to the Asana top-level count.

## Method

- Signed in with your account through the browser (email OTP). All calls were read-only; nothing was changed in Asana or the new tool.
- Sources: the Task Manager project CSV export and task-detail API (17 November 12:24–12:36 SGT), live Asana API, and the 15 November local Asana backup.
- The earlier audit read the project board/RSC payload, which exposed 290 of the 298 top-level tasks. The CSV export exposed all 298 and corrected the 8-task false negative.
- Matching: normalised task title. Untitled Asana tasks were matched by creation timestamp (the Fix In Progress blank task matches the new "Untitled task" exactly at 2026-11-04T07:00:18.021Z).
- Comment and attachment comparisons use live Asana data, not just the backup.

## Caveats

- Matching is title-based. A task renamed without any shared tokens could be reported as missing even if it exists.
- The project page/RSC payload can omit lazy-loaded rows. The CSV export is the authoritative list; use it for future audits.
- The new tool has no official API; its internal endpoints were used and may change without notice.
- Attachment comparison is by filename. URL link previews are counted by Asana as attachments.
- The four matched Asana subtasks have no comments; their two attachments were verified present.

## Files

- `task-comparison.csv` — all 303 Asana rows with match status and field-level comparison
- `missing-tasks.csv` — the 1 missing placeholder
- `summary.json` — machine-readable counts and mismatch lists

## Recommended next steps

1. Ignore the blank Open Tickets placeholder unless the vendor can confirm it should exist.
2. Confirm the true status, owner and due date for the Chinese acknowledgement ticket.
3. Ask whether the 8 screen recordings were intentionally excluded; if not, re-upload them from Asana.
4. Decide whether the 12 Figma link previews need to be re-added.
