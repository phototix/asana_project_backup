# Marcomm to Codigo daily update — 23 October 2026 (12:50 update)

Generated: 2026-10-23 12:50 SGT
Source: live Asana API and authenticated pre-prod checks, read-only
Scope: Full UAT updates since the previous report, including the Marcomm batch, the verification handoff and the re-verified UAT tickets
Window: 22 October 2026, 14:49 SGT to 23 October 2026, 12:50 SGT
No Asana data was changed.

## Summary

Codigo re-verified the 10 handoff tickets on pre-prod on 22 October. Five remain closed from the earlier pass. Four are back in Client to verify: Contact Us heading capitalisation, Contact Us address formatting, Awareness Place link and Articles Text interface. One has been returned to Fail (To fix again): Digital Download Video/Audio Button.

The 28 Marcomm batch tickets have progressed to 3 New Request on Pre-prod, 15 QA to verify, 4 Fail (To fix again), 2 Client to verify and 4 To update hardcoded content on Pre-prod.

Codigo also re-verified 23 other UAT tickets on pre-prod on 22 October and moved them to Client to verify. They are assigned to Brandon and await his verification.

Dharma School Page Banner Image is now Client to verify. E-Store Product Chinese name is now QA to verify. Contact Us Incomplete department details is now Client to verify, and CMS access has been restored so the Helpdesk content can be updated.

The 11 existing Marcomm-pending items had no changes.

## Today's updates

On 22 October, the five previously failed handoff tickets were re-verified by Codigo on pre-prod. Four are now in Client to verify. Digital Download was moved back to Fail (To fix again) and assigned to Kaung Myat Hein.

The 28 batch tickets moved through QA on 22 October. Fifteen are now in QA to verify, four have failed and returned to Codigo, two are in Client to verify, four remain with Codigo for hardcoded content updates, and three are new requests with Dexter.

The four batch failures are Volunteer Intro Copy and Button Labels, Volunteer Events Section, Join Us Image Replacement and Joyous Heart Divider Image. The two batch tickets in Client to verify are Bright Youth Intro Copy, which is CMS-managed, and Joyous Heart Footer Spacing.

Codigo also re-verified 23 other UAT tickets on pre-prod and moved them to Client to verify.

On 23 October, Articles Text received new comments. Danh explained that the alias is generated from titleEng, and Zin said the EN title field should contain the English title and asked Brandon to check again. Contact Us Incomplete department details is now Client to verify and Zin confirmed the CMS access is restored.

## What Codigo decided

Codigo classified the 28 Marcomm tickets as 21 hardcoded content or layout updates, 3 new requests, 1 CMS-managed update and 3 functional issues. Their current progress is in the Batch progress table below.

## Pre-prod verification of the 10 handoff tickets

Five tickets remain closed. Four are pending re-verification. One has been returned to Codigo.

| Ticket | Asana URL | Pre-prod page | Check | Result | Evidence | Verified by | Current status |
|---|---|---|---|---|---|---|---|
| Contact Us heading capitalisation (1219573589097794) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573589097794 | /contact-us and /zh/contact-us | Main heading reads “Contact Us” | Pending re-verification | The main heading is “Contact Us”, but the footer heading still read “Contact us” on 21 October. Codigo re-verified on pre-prod on 22 October 14:39: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 13:36; Zin — Re-verified 22 Oct 14:39 | Client to verify |
| Contact Us address formatting (1219573808950447) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573808950447 | /contact-us and /zh/contact-us | Address reads “88 Bright Hill Road, Singapore 574117” | Pending re-verification | The visible address read “88 Bright Hill Road Singapore 574117” without the comma on 21 October. Codigo re-verified on pre-prod on 22 October 14:39 and attached a screenshot at 15:11: https://app.asana.com/app/asana/-/get_asset?asset_id=1219764705436246 | Brandon — Fail noted 21 Oct 13:33; Zin — Re-verified 22 Oct 14:39 | Client to verify |
| Contact Us “Send A Message” heading (1219584612353363) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612353363 | /contact-us | Heading reads “Send a Message” | Pass | “Send a Message” is present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291709 | Brandon — Verified 21 Oct 13:21 | Closed |
| Contact Us “TODO: Verify Human” placeholder (1219584909725076) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584909725076 | /contact-us | Placeholder removed | Pass | “TODO: Verify Human” is not present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291703 | Brandon — Verified 21 Oct 13:19 | Closed |
| Contact Us Rename “Helpdesk” (1219584612537724) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612537724 | /contact-us and /zh/contact-us | “Department Contacts” shown, “Helpdesk” removed | Pass | “Department Contacts” is present and “Helpdesk” is not. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291715 | Brandon — Checked 21 Oct 13:22 | Closed |
| Awareness Place link (1219573938802132) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573938802132 | /contact-us and /zh/contact-us | Link points to https://awarenessplace.com/ | Pending re-verification | The link was http://www.awarenessplace.com/ on 21 October. Codigo re-verified on pre-prod on 22 October 14:40 and attached a screenshot at 15:09: https://app.asana.com/app/asana/-/get_asset?asset_id=1219764705436240 | Brandon — Fail noted 21 Oct 13:29; Zin — Re-verified 22 Oct 14:40 | Client to verify |
| Publication Fail redirection (1219575603663567) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575603663567 | /awaken-online/books | Publication “生活处处皆是禅” opens the detail page | Pass | Brandon checked the redirect on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741327390513 | Brandon — Checked 21 Oct 13:57 | Closed |
| Publication Download Problem (1219575536622988) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575536622988 | /awaken-online/books | “Download PDF” triggers a file download | Pass | Brandon checked the PDF download on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741328735444 | Brandon — Checked 21 Oct 13:59 | Closed |
| Articles Text interface (1219575656532229) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575656532229 | /awaken-online/articles | Paragraph breaks render on the article page | Pending re-verification | The breakline in the editor was still not reflected and the page was gone after the CMS update on 21 October. Codigo re-verified on pre-prod on 22 October 14:42. On 23 October, Danh explained the alias is generated from titleEng, and Zin said the EN title field should contain the English title and asked Brandon to check again. | Brandon — Fail noted 21 Oct 14:06; Zin — Re-verified 22 Oct 14:42; Zin — English title issue 23 Oct 12:31 | Client to verify |
| Digital Download Video/Audio Button (1219575604730061) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575604730061 | /awaken-online/digital | Download buttons trigger file downloads | Fail | Clicking download for both Audio and Video produced a Chrome download error on 21 October. Zin re-verified on pre-prod on 22 October 14:42, then the ticket was moved back to Fail (To fix again) at 14:52 and assigned to Kaung Myat Hein. | Brandon — Fail noted 21 Oct 14:08; Zin — Returned to Codigo 22 Oct 14:52 | Fail (To fix again) |

## Batch progress — 28 Marcomm tickets

The current status and next action for each of the 28 Marcomm tickets.

| Ticket | Current status | Assignee | Next action |
|---|---|---|---|
| [Web] - Home Page - Top Banner and Activities Layout (1219729871505000) | New Request on Pre-prod | Dexter | Dexter to assess and implement; Marcomm to confirm the Figma. |
| [Web] - Home Page - Upcoming Events Chinese Label (1219729871681039) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Home Page - Latest Happenings Section (1219730038770916) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Home Page - Mailing List Copy (1219729966737873) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Volunteer - Intro Copy and Button Labels (1219729884657529) | Fail (To fix again) | Kaung Myat Hein | Codigo to fix and return for verification. |
| [Web] - Join Us - Volunteer - Top Banner (1219730156544417) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Volunteer - Volunteer Events Section (1219746446656349) | Fail (To fix again) | Kaung Myat Hein | Codigo to fix and return for verification. |
| [Web] - Join Us - Volunteer - Application Process (1219730039233996) | New Request on Pre-prod | Dexter | Dexter to assess and implement; Marcomm to confirm the Figma. |
| [Web] - Join Us - Volunteer - Areas of Service (1219730213867125) | New Request on Pre-prod | Dexter | Dexter to assess and implement; Marcomm to confirm the Figma. |
| [Web] - Join Us - Volunteer - Join Us Image Replacement (1219729885418308) | Fail (To fix again) | Kaung Myat Hein | Codigo to fix and return for verification. |
| [Web] - Join Us - Bright Youth - Top Banner (1219730157051326) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Bright Youth - Intro Copy (1219730214216446) | Client to verify | Brandon | Marcomm/you to update the EN/CN copy in the CMS, then verify. |
| [Web] - Join Us - Bright Youth - Membership Heading (1219730214000918) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Bright Youth - Four Pillars Text (1219729872643659) | To update hardcoded content | Kaung Myat Hein | Codigo to apply the approved content on pre-prod. |
| [Web] - Join Us - Bright Youth - Page Section Order (1219729872441193) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Bright Youth - Empty State Chinese Label (1219729885362231) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Joyous Heart - Top Banner (1219730040037065) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Joyous Heart - Divider Image (1219730214602139) | Fail (To fix again) | Kaung Myat Hein | Codigo to fix and return for verification. |
| [Web] - Join Us - Joyous Heart - Section Order (1219730157523754) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Joyous Heart - Gallery Chinese Label (1219730214327943) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Joyous Heart - Footer Spacing (1219730040218133) | Client to verify | Brandon | Client to verify; close if pass. |
| [Web] - Join Us - Career - Top Banner (1219730214723788) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Career - Intro Content and Photo (1219729886373019) | To update hardcoded content | Kaung Myat Hein | Codigo to apply the approved content on pre-prod. |
| [Web] - Join Us - Career - Divider Image (1219729885998686) | QA to verify | Brandon | Client QA and verification pending. |
| [Web] - Join Us - Career - How to Apply Copy (1219730215265066) | To update hardcoded content | Kaung Myat Hein | Codigo to apply the approved content on pre-prod. |
| [Web] - Join Us - Career - Walk-In Interview Label (1219730158203178) | To update hardcoded content | Kaung Myat Hein | Codigo to apply the approved content on pre-prod. |
| [Web] - Join Us - Career - Chinese Text Visibility (1219730152343193) | QA to verify | Danh | Client QA and verification pending. |
| [Web] - Join Us - Career - Application Button Label (1219730041124358) | QA to verify | Brandon | Client QA and verification pending. |

## Other UAT re-verifications

Codigo re-verified these UAT tickets on pre-prod on 22 October and moved them to Client to verify. They are assigned to Brandon and await his verification.

| Ticket | Pre-prod page | Previous issue | Assignee | Current status |
|---|---|---|---|---|
| [Web] Contact Us image to be remove (1219570600171991) | /contact-us | Ceremony or large photo still present below the contact information | Brandon | Client to verify |
| [Web] See all Gates button (1219573590035450) | /visit/getting-here | See all Gates still present or Getting Here link missing | Brandon | Client to verify |
| [Web] Affiliates title misspelling (1219573694402884) | / | Affiliates typo remains or Affiliates missing | Brandon | Client to verify |
| [Web] Remove Singapore Buddhist Free Clinic (1219573626459723) | / | Singapore Buddhist Free Clinic still listed in the footer | Brandon | Client to verify |
| [Web] Awaken Online - About Us - Top Banner (1219575226602332) | /awaken-online | Awaken Online text still shown on the About Us top banner | Brandon | Client to verify |
| [Web] Awaken Online - About Us - Category Name (1219575485734167) | /awaken-online | Category tabs not updated to Publications, Articles and Digital Content | Brandon | Client to verify |
| [Web] Awaken Online - About Us - “About Us” section (1219575535926742) | /awaken-online | About Us section copy not updated | Brandon | Client to verify |
| [Web] Awaken Online - About Us - New Book Uploads (1219575227297229) | /awaken-online | Still New Book Uploads or missing Latest Publications | Brandon | Client to verify |
| [Web] Awaken Online - About Us - Recently Published Magazines (1219575416943234) | /awaken-online | Magazine section title not updated | Brandon | Client to verify |
| [Web] Awaken Online - About Us - Latest Digital (1219575603344482) | /awaken-online | Latest Digital Content title not updated | Brandon | Client to verify |
| [Web] Awaken Online - Publication - Sub-categories (1219575603657479) | /awaken-online/books | Nav still shows Book instead of Publications | Brandon | Client to verify |
| [Web] Awaken Online - Publication - Recommended for You (1219575226896032) | /awaken-online/books | Still Books Recommended for You or missing the new title | Brandon | Client to verify |
| [Web] Awaken Online - Awaken Magazine - Recommended for You (1219575536623130) | /awaken-online/magazines | Still Awaken Magazine Recommended for You or missing New Releases | Brandon | Client to verify |
| [Web] Awaken Online - Articles - Recommended for You (1219575486562635) | /awaken-online/articles | Still Articles Recommended for You or missing Featured Articles | Brandon | Client to verify |
| [Web] Awaken Online - Publication - After Upload (1219575603604377) | /awaken-online/books | Breadcrumb or tag not updated to Publication | Brandon | Client to verify |
| [Web] Awaken Online - Publication - Publication repeated (1219575228008122) | /awaken-online/books | Same publication title appears in featured and recommended | Brandon | Client to verify |
| [Web] Awaken Online - Publication - Category Tag (1219575486141720) | /awaken-online/books | Card tags still Book or missing Publication | Brandon | Client to verify |
| [Web] Awaken Online - About Us - Header (1219575485721204) | /awaken-online | About Us header text not updated | Brandon | Client to verify |
| [Web & CMS] Privacy Policy, Terms & Condition & Whistleblower Policy  (1219570600171995) | /privacy-policy and /terms-and-conditions and /whistleblower-policy | Paragraph spacing missing; Terms and Conditions CMS editor error | Brandon | Client to verify |
| [Web] Awaken Online - Publication - Publish Date not showing (1219575486359563) | /awaken-online/books | Publish date missing from the CMS listing and detail view | Brandon | Client to verify |
| [Web] Awaken Online - Awaken Magazine - Publish Date not showing (1219575656344472) | /awaken-online/magazines | Publish date column not visible in the CMS listing | Brandon | Client to verify |
| [Web] Awaken Online - Digital - Download Video Button (1219575604552330) | /awaken-online/digital | Download Video button issue | Brandon | Client to verify |
| [Web] Awaken Online - Articles - "Ends On" Function (1219575481338668) | /awaken-online/articles | Ends On function issue | Brandon | Client to verify |

## Additional tickets

| Ticket | Pre-prod page | Update | Assignee | Current status |
|---|---|---|---|---|
| [Web] – Dharma School Page Banner Image (1213988637581792) | /dharma-education/school/an-overview | Zin verified on pre-prod on 23 October 11:37; awaiting Brandon's verification. | Brandon | Client to verify |
| [Web] - E-Store - Product Chinese name not shown  (1219692039810792) | /e-store and /zh/e-store | Moved to QA to verify on 23 October 12:45; the Chinese name is saved in CMS but the storefront shows English. | Danh | QA to verify |
| [Web] Contact Us - Incomplete department contact details (1219584933906424) | /contact-us | CMS access restored; Zin asks Brandon to update the Helpdesk content in the CMS on 23 October 12:36. | Brandon | Client to verify |

## Marcomm actions

Please update the Bright Youth intro English and Chinese copy in the CMS. The Contact Us department contact content can now be updated in the CMS as well. Please confirm the three new requests against the KMS Figma. Please clarify whether the Dharma School banner images are hardcoded or CMS-managed.

No Marcomm action is needed on the hardcoded content tickets unless the approved content is missing. The four failed batch tickets have been returned to Codigo. The five passed handoff tickets are closed, four handoff tickets and the 23 other UAT tickets await Brandon's verification, and Digital Download has been returned to Codigo.

The 11 existing pending items had no changes in this window.
