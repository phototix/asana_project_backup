# Asana tickets assigned to KMS — review by 18 November 2026

Prepared from the 16 November 2026 vendor comment review and pre-prod check results. No Asana API calls were made and no Asana data was changed. CMS-dependent checks remain pending because the M365 OTP service was unavailable.

## Purpose

Codigo has asked Marcomm and the key users to complete their review and prioritisation of the tickets assigned to KMS by 18 November 2026. This page consolidates the KMS-owned actions so they can be reviewed, assigned an owner and returned to Codigo in one response. For this page, active tickets assigned to Brandon are treated as KMS-owned.

## Snapshot

- 48 active tickets: 31 non-CR and 17 CR/internal review.
- 8 active tickets are assigned to Brandon in the 16 November Asana view: 4 KMS actions and 4 CR/internal items.
- 11 KMS decisions and assets are still needed.
- 7 KMS verification actions are still open.
- 17 CR/internal items need a launch-scope or post-launch decision.
- 3 vendor-side defects remain on pre-prod: Download HTTP 413, Online Pledge registration route page-not-found, and Contact Us not deployed to pre-prod.
- CMS checks are blocked by the M365 OTP outage.
- Launch scope and Priority are intentionally blank for KMS reviewers.

## Active tickets assigned to Brandon (KMS)

| Ticket | Asana status | KMS action | Suggested owner | Launch scope | Priority | Notes |
|---|---|---|---|---|---|---|
| [Dharma School — Unable to delete test record](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219636982479482) 1219636982479482 | Client to verify | Verify the test record is removed and confirm the OPEN/CLOSED versus SCHEDULED/DRAFT deletion policy. | KMS |  |  |  |
| [Offering Listing — Stock page error](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1220457628953032) 1220457628953032 | Client to verify | Verify the CMS Stock page and close if there is no error. | KMS |  |  |  |
| [Online Pledge — Count choice and preview](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219961154288257) 1219961154288257 | Client to verify | Verify the count options and preview on pre-prod. The vendor registration route is still failing. | KMS |  |  |  |
| [Things to Note description](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219477239416627) 1219477239416627 | To discuss/confirm | Confirm the optional title and approve at least 2000 characters for launch. | KMS UAT and Marcomm |  |  |  |
| [Major Events image dimensions and CMS gaps](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219875631714216) 1219875631714216 | KMS internal CR | Confirm whether the image dimensions and CMS gaps are launch scope or post-launch. | KMS and Marcomm |  |  |  |
| [Home Page banner and activities layout](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219729871505000) 1219729871505000 | KMS internal CR | Confirm whether the layout change is launch scope or post-launch. | KMS and Marcomm |  |  |  |
| [Digital — Embed Audio](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575656937178) 1219575656937178 | KMS internal CR | Confirm the expected embed method and whether an agreed-delivery fix is required. | KMS and Marcomm |  |  |  |
| [Digital — Uploading multiple tracks](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575486874259) 1219575486874259 | KMS internal CR | Confirm the signed-off requirement and whether this is agreed delivery or a CR. | KMS and Marcomm |  |  |  |

## KMS decisions and assets (11)

| Item | Decision or asset needed | Related ticket(s) | Suggested owner | Launch scope | Priority | Notes |
|---|---|---|---|---|---|---|
| Public support address and footer wording | Choose support@ or kmssupport@, confirm IT monitoring, and confirm the Contact Us instruction. | 1220102256915679, 1220102510774403 | KMS IT and Marcomm |  |  |  |
| Sender address | Record IT approval for kmssupport@kmspks.org. | 1220102510002407 | KMS IT |  |  |  |
| Multi-day event layout | Accept the Multi Date and Date Range workaround and request a Shuilu pre-prod example. | 1219961154393766 | KMS UAT |  |  |  |
| Things to Note | Confirm the optional title and at least 2000 characters. | 1219477239416627 | KMS UAT and Marcomm |  |  |  |
| Online Pledge prayer field | Confirm with SED whether the field stays. If it stays, approve the bilingual dropdown. | 1219961002853139 | SED and KMS UAT |  |  |  |
| Transference of Merit | Confirm the placement and provide the reference. | 1219961002927191 | Marcomm and KMS UAT |  |  |  |
| Volunteer structure | Confirm the Figma and whether Application Process and Areas of Service are launch scope. | 1219730039233996, 1219730213867125 | Marcomm and users |  |  |  |
| Awaken Online banners | Provide the four banner images and confirm the text-only scope. | 1219575486029162, 1219575536473541, 1219575604118790, 1219575656367817 | KMS content owner |  |  |  |
| About Us footer CTAs | Provide the Mailchimp URL, final image and link details. | 1219575603219202 | KMS content owner |  |  |  |
| About + Visit content | Re-share the photos and confirm the exact Word changes. | 1219570452486112 | KMS content owner |  |  |  |
| Online Pledge content limit | Confirm the 2000-character limit and content scope. | 1219961049118002 | Marcomm and KMS UAT |  |  |  |

## Other KMS verification actions (5)

Two further verification actions, Dharma School test record and Offering Listing Stock, are listed in the Brandon-assigned table above.

| Ticket | Asana status | KMS action | Suggested owner | Launch scope | Priority | Notes |
|---|---|---|---|---|---|---|
| [Mailing list subscription feedback](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573938599764) 1219573938599764 | Client to verify | Check the staging export fields, confirm whether subscription date and time can be added, and approve pre-prod if acceptable. | KMS |  |  |  |
| [Chinese acknowledgement email](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1220102510328267) 1220102510328267 | Fix In Progress | Verify the Chinese content, reference number, date and time, subject and signature on pre-prod. | KMS |  |  |  |
| [Acknowledgement email sender display name](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1220102256145249) 1220102256145249 | QA to verify | Approve the pre-prod deployment and verify the sender shows KMSPKS. | KMS |  |  |  |
| [Dharma School — Course page not found](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219804537175138) 1219804537175138 | QA to verify | Confirm the pre-prod course target and verify the course page. | KMS |  |  |  |
| [Remove validation from Contact Information phone field](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1220374393195121) 1220374393195121 | QA to verify | Link this to 1219961002989323, confirm the combined scope, and ask Codigo for one workaround. | KMS |  |  |  |

## CR/internal review (17)

| Ticket | Vendor position | KMS decision needed | Suggested owner | Launch scope | Priority | Notes |
|---|---|---|---|---|---|---|
| [Monkhood contents](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219570452486114) 1219570452486114 | Dexter, 26 Oct: CR scope for two new Monkhood sections. | Decide whether the two new sections are launch scope. | KMS and Marcomm |  |  |  |
| [Remove Quick Links section](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573694440141) 1219573694440141 | Dexter, 21 Oct: dynamic footer change treated as CR requiring deployment. | Confirm whether removal is agreed delivery or a post-launch change. | KMS and Marcomm |  |  |  |
| [Digital — Uploading multiple tracks](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575486874259) 1219575486874259 | Revee Low, 12 Nov: signed-off UI supports one audio track and multiple tracks is a CR. | Confirm the signed-off requirement and whether it is agreed delivery. | KMS and Marcomm |  |  |  |
| [Digital — Embed Audio](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575656937178) 1219575656937178 | Revee Low, 12 Nov: explains the YouTube MP4 versus audio format limitation. | Confirm the expected embed method and whether an agreed-delivery fix is needed. | KMS and Marcomm |  |  |  |
| [Home Page banner and activities layout](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219729871505000) 1219729871505000 | Dexter, 11 Nov: considers the layout change a CR. | Decide whether the layout change is launch scope or post-launch. | KMS and Marcomm |  |  |  |
| [Major Events image dimensions and CMS gaps](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219875631714216) 1219875631714216 | Dexter, 11 Nov: considers it a CR and asks whether to proceed. | Decide whether to proceed before or after launch. | KMS and Marcomm |  |  |  |
| [Implementation does not match Figma](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1213989518433853) 1213989518433853 | Zin Hnin Wai, 22 Apr: asks for the specific mismatches. | Identify the exact Figma gaps before any new engagement. | KMS and Marcomm |  |  |  |
| [CMS Finance Reports](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214952333854156) 1214952333854156 | Dexter, 15 Jul: custom report treated as CR. | Decide whether the report is launch scope. | KMS |  |  |  |
| [E-Store Terms and Conditions](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214953011146821) 1214953011146821 | Dexter, 20 May: UX/UI and front-end change treated as CR. | Confirm the agreed scope with Ivan and Marcomm. | KMS and Marcomm |  |  |  |
| [Top Web banner](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1213989518433862) 1213989518433862 | Revee Low, 15 Jun: banner editability constraints explained. | Confirm the final banner requirement. | KMS and Marcomm |  |  |  |
| [Activities images, tags and countdown](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214000237343885) 1214000237343885 | Revee Low, 20 Apr: treated as CR due to rework. | Decide whether any part is launch scope. | KMS and Marcomm |  |  |  |
| [Bright Youth Membership pillars](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214558863102590) 1214558863102590 | Revee Low, 7 May: hardcoded pillars were agreed with the Bright Youth team. | Confirm the original agreement and the current ask. | KMS and Marcomm |  |  |  |
| [CMS Fundraising section](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214109740637992) 1214109740637992 | Dexter, 23 Apr: new section treated as CR. | Decide whether fundraising is launch scope. | KMS and Marcomm |  |  |  |
| [CMS Combining donation sections](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1214109740637997) 1214109740637997 | Dexter, 23 Apr: treated as CR. | Decide whether it is launch scope or post-launch. | KMS |  |  |  |
| [Add reason of no-show](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1213072901656085) 1213072901656085 | Revee Low, 9 Apr: asks KMS to raise a chargeable change request. | Confirm whether it is agreed delivery before opening any request. | KMS |  |  |  |
| [Career Page form field updates](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212672958117520) 1212672958117520 | Revee Low, 5 Mar: treated as CR. | Confirm launch scope and priority. | KMS and Marcomm |  |  |  |
| [Career Page minor post-signoff enhancement](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1212672958117526) 1212672958117526 | Revee Low, 2 Feb: treated as CR. | Confirm launch scope and priority. | KMS and Marcomm |  |  |  |

## Vendor-side blockers and dependencies

| Item | Status | Evidence | Next action | Owner |
|---|---|---|---|---|
| [Download Video/Audio Button](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575604730061) 1219575604730061 | Fail | The /api/download proxy returns HTTP 413 and downloads cancel in EN and CN. | Codigo to investigate the proxy and provide a fix ETA. | Codigo |
| [Online Pledge — Count choice and preview](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219961154288257) 1219961154288257 | Fail | The registration route returns a page-not-found body, so the count options and preview cannot be verified. | Codigo to restore the route and confirm on pre-prod. | Codigo |
| [Contact Us — Submission confirmation and privacy notice](https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612769805) 1219584612769805 | Fail | The staging fix is verified but pre-prod still shows the old toast. | Codigo to deploy to pre-prod and confirm. | Codigo |
| M365 OTP access | Blocked | CMS checks could not run because the M365 OTP service was unavailable. | KMS IT to restore access. | KMS IT |

The KMS position also remains that Master Audit Trail 1219566240500919 and Contents not loading 1219526058649071 are agreed delivery, not CRs. These should be included in the consolidated 18 November response to Codigo.

## 18 November checklist

- Confirm the indicative launch date or window with Ivan and share it with Codigo.
- Complete the 11 KMS decisions and assets.
- Complete the 7 KMS verification actions.
- Classify the 17 CR/internal items as agreed delivery, launch-scope CR, or post-launch.
- Confirm the launch priority for the 8 Brandon-assigned tickets.
- Restore M365 OTP access so the pending CMS checks can be completed.
- Send one consolidated KMS response to Codigo by 18 November 2026.

## Source and limitations

- Prepared 16 November 2026 from the 16 November vendor comment review and the pre-prod check results.
- The 16 November automated run covered 16 tickets: 1 Pass, 3 Fail and 12 Needs manual review.
- No Asana comments, status changes, assignee changes or due-date changes were made.
- No Asana API calls were made for this page.
- Re-check live Asana status before sending the consolidated response.
