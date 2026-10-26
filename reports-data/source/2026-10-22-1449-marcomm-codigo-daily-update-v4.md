# Marcomm to Codigo daily update — 22 October 2026 (14:49 update)

Generated: 2026-10-22 14:49 SGT
Source: live Asana API and authenticated pre-prod checks, read-only
Scope: Full UAT updates in the window, including the Marcomm batch, the verification handoff and the re-verified UAT tickets
Window: 21 October 2026, 14:40 SGT to 22 October 2026, 14:49 SGT
No Asana data was changed.

## Summary

Codigo triaged the 28 tickets created from Marcomm's update set between 19:35 and 19:39 on 21 October. Codigo classified 21 as hardcoded content or layout updates, 3 as new requests, 1 as a CMS-managed update, and 3 as functional issues. All 28 were given a due date of 22 October 2026.

Between 20:49 and 20:53 on 21 October, Codigo verified 10 tickets on pre-prod, moved them into Client to verify, assigned them to Brandon, and attached screenshots. Five passed and were closed. The other five failed and were returned to Codigo.

On 22 October, between 14:39 and 14:42 SGT, Codigo re-verified those five on pre-prod and moved them back to Client to verify, assigned to Brandon. They are pending re-verification by Brandon.

Codigo also re-verified 14 other UAT tickets on pre-prod in the same batch and moved them to Client to verify. They are assigned to Brandon and await his verification.

Two additional tickets changed. The Dharma School Page Banner Image is now Fix In Progress with Kaung Myat Hein. The E-Store Product Chinese name not shown remains Open Tickets with Kaung Myat Hein.

Earlier updates in the window include the Dharma School banner update, the Monkhood and Things to note requirements, the top banner and privacy acknowledgments, the Mailing list subscription feedback move, the Master Audit Trail move and the Articles Ends On move to QA.

Brandon's verification comments are included in the Pre-prod verification table. The 11 existing Marcomm-pending items had no changes.

## Earlier updates in the window

At 14:43 SGT on 21 October, Brandon updated the Dharma School Page Banner Image and moved it into Open Tickets. It was moved to Fix In Progress on 22 October.

At 15:29, Brandon provided the confirmed requirements for Monkhood contents and Things to note description. Dexter replied on Monkhood at 15:58.

Between 15:58 and 16:08, Dexter asked for the four top banner images, the privacy notice details and the Footer CTAs information. Brandon replied with the holding acknowledgment at 16:35.

At 18:25, Mailing list subscription feedback was moved to Fix In Progress. At 18:27, Master Audit Trail was moved to To discuss/confirm. At 19:22, Articles Ends On was moved to QA to verify.

## What Codigo decided

The 21 hardcoded content or layout updates are with Kaung Myat Hein and are due 22 October 2026. Codigo will apply the approved content on pre-prod. The tickets are Home Page - Mailing List Copy, Home Page - Latest Happenings Section, Home Page - Upcoming Events Chinese Label, Join Us - Volunteer - Intro Copy and Button Labels, Join Us - Volunteer - Top Banner, Join Us - Volunteer - Volunteer Events Section, Join Us - Volunteer - Join Us Image Replacement, Join Us - Bright Youth - Top Banner, Join Us - Bright Youth - Four Pillars Text, Join Us - Bright Youth - Membership Heading, Join Us - Bright Youth - Empty State Chinese Label, Join Us - Bright Youth - Page Section Order, Join Us - Joyous Heart - Top Banner, Join Us - Joyous Heart - Gallery Chinese Label, Join Us - Joyous Heart - Section Order, Join Us - Career - Top Banner, Join Us - Career - Intro Content and Photo, Join Us - Career - Divider Image, Join Us - Career - How to Apply Copy, Join Us - Career - Walk-In Interview Label, and Join Us - Career - Application Button Label.

The 3 new requests are with Dexter and are due 22 October 2026. They are Home Page - Top Banner and Activities Layout, Join Us - Volunteer - Areas of Service, and Join Us - Volunteer - Application Process. Marcomm should confirm these against the KMS Figma.

The CMS-managed update is Join Us - Bright Youth - Intro Copy. It is with Brandon and is due 22 October 2026. The intro is CMS-managed, and staging still contains the editor test line. Marcomm should provide the final English and Chinese copy.

The 3 functional issues are with Kaung Myat Hein and are due 22 October 2026. They are Join Us - Career - Chinese Text Visibility, Join Us - Joyous Heart - Divider Image, and Join Us - Joyous Heart - Footer Spacing.

## Pre-prod verification of the 10 handoff tickets

We checked the English and Chinese pages where relevant. The five passed tickets are closed. The five previously failed tickets were re-verified by Codigo on pre-prod on 22 October and are awaiting Brandon's re-verification.

| Ticket | Asana URL | Pre-prod page | Check | Result | Evidence | Verified by | Current status |
|---|---|---|---|---|---|---|---|
| Contact Us heading capitalisation (1219573589097794) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573589097794 | /contact-us and /zh/contact-us | Main heading reads “Contact Us” | Pending re-verification | The main heading is “Contact Us”, but the footer heading still read “Contact us” on 21 October. Codigo re-verified on pre-prod on 22 October 14:39: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 13:36; Zin — Re-verified 22 Oct 14:39 | Client to verify |
| Contact Us address formatting (1219573808950447) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573808950447 | /contact-us and /zh/contact-us | Address reads “88 Bright Hill Road, Singapore 574117” | Pending re-verification | The visible address read “88 Bright Hill Road Singapore 574117” without the comma on 21 October. Codigo re-verified on pre-prod on 22 October 14:39: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 13:33; Zin — Re-verified 22 Oct 14:39 | Client to verify |
| Contact Us “Send A Message” heading (1219584612353363) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612353363 | /contact-us | Heading reads “Send a Message” | Pass | “Send a Message” is present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291709 | Brandon — Verified 21 Oct 13:21 | Closed |
| Contact Us “TODO: Verify Human” placeholder (1219584909725076) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584909725076 | /contact-us | Placeholder removed | Pass | “TODO: Verify Human” is not present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291703 | Brandon — Verified 21 Oct 13:19 | Closed |
| Contact Us Rename “Helpdesk” (1219584612537724) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612537724 | /contact-us and /zh/contact-us | “Department Contacts” shown, “Helpdesk” removed | Pass | “Department Contacts” is present and “Helpdesk” is not. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291715 | Brandon — Checked 21 Oct 13:22 | Closed |
| Awareness Place link (1219573938802132) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573938802132 | /contact-us and /zh/contact-us | Link points to https://awarenessplace.com/ | Pending re-verification | The link was http://www.awarenessplace.com/ on 21 October. Codigo re-verified on pre-prod on 22 October 14:40: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 13:29; Zin — Re-verified 22 Oct 14:40 | Client to verify |
| Publication Fail redirection (1219575603663567) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575603663567 | /awaken-online/books | Publication “生活处处皆是禅” opens the detail page | Pass | Brandon checked the redirect on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741327390513 | Brandon — Checked 21 Oct 13:57 | Closed |
| Publication Download Problem (1219575536622988) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575536622988 | /awaken-online/books | “Download PDF” triggers a file download | Pass | Brandon checked the PDF download on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741328735444 | Brandon — Checked 21 Oct 13:59 | Closed |
| Articles Text interface (1219575656532229) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575656532229 | /awaken-online/articles | Paragraph breaks render on the article page | Pending re-verification | The breakline in the editor was still not reflected and the page was gone after the CMS update on 21 October. Codigo re-verified on pre-prod on 22 October 14:42: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 14:06; Zin — Re-verified 22 Oct 14:42 | Client to verify |
| Digital Download Video/Audio Button (1219575604730061) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575604730061 | /awaken-online/digital | Download buttons trigger file downloads | Pending re-verification | Clicking download for both Audio and Video produced a Chrome download error on 21 October. Codigo re-verified on pre-prod on 22 October 14:42: https://app.asana.com/0/1212450122576205/ | Brandon — Fail noted 21 Oct 14:08; Zin — Re-verified 22 Oct 14:42 | Client to verify |

## Other pre-prod re-verifications

On 22 October between 14:39 and 14:42 SGT, Codigo also re-verified the following UAT tickets on pre-prod and moved them to Client to verify. They are assigned to Brandon and await his verification.

| Ticket | Asana URL | Pre-prod page | Previous issue | Assignee | Current status |
|---|---|---|---|---|---|
| Contact Us image to be remove (1219570600171991) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219570600171991 | /contact-us | Ceremony or large photo still present below the contact information | Brandon | Client to verify |
| See all Gates button (1219573590035450) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573590035450 | /visit/getting-here | See all Gates still present or Getting Here link missing | Brandon | Client to verify |
| Affiliates title misspelling (1219573694402884) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573694402884 | / | Affiliates typo remains or Affiliates missing | Brandon | Client to verify |
| Remove Singapore Buddhist Free Clinic (1219573626459723) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573626459723 | / | Singapore Buddhist Free Clinic still listed in the footer | Brandon | Client to verify |
| Awaken Online About Us Top Banner (1219575226602332) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575226602332 | /awaken-online | Awaken Online text still shown on the About Us top banner | Brandon | Client to verify |
| About Us Category Name (1219575485734167) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575485734167 | /awaken-online | Category tabs not updated to Publications, Articles and Digital Content | Brandon | Client to verify |
| About Us “About Us” section (1219575535926742) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575535926742 | /awaken-online | About Us section copy not updated | Brandon | Client to verify |
| About Us New Book Uploads (1219575227297229) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575227297229 | /awaken-online | Still New Book Uploads or missing Latest Publications | Brandon | Client to verify |
| About Us Recently Published Magazines (1219575416943234) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575416943234 | /awaken-online | Magazine section title not updated | Brandon | Client to verify |
| About Us Latest Digital (1219575603344482) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575603344482 | /awaken-online | Latest Digital Content title not updated | Brandon | Client to verify |
| Publication Sub-categories (1219575603657479) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575603657479 | /awaken-online/books | Nav still shows Book instead of Publications | Brandon | Client to verify |
| Publication Recommended for You (1219575226896032) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575226896032 | /awaken-online/books | Still Books Recommended for You or missing the new title | Brandon | Client to verify |
| Awaken Magazine Recommended for You (1219575536623130) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575536623130 | /awaken-online/magazines | Still Awaken Magazine Recommended for You or missing New Releases | Brandon | Client to verify |
| Articles Recommended for You (1219575486562635) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575486562635 | /awaken-online/articles | Still Articles Recommended for You or missing Featured Articles | Brandon | Client to verify |

## Additional tickets in the window

Dharma School Page Banner Image (1213988637581792) is in Fix In Progress, assigned to Kaung Myat Hein, and has no due date. Zin needs clarification on whether the Dharma School landing banner and hover-menu images are hardcoded or CMS-managed.

E-Store Product Chinese name not shown (1219692039810792) is in Open Tickets, assigned to Kaung Myat Hein, and is due 22 October 2026. Codigo observed that the Chinese product name is saved in the CMS but the staging E-store still shows English product names. This is a functional issue.

## Marcomm actions

Please update the Bright Youth intro English and Chinese copy in the CMS. Please confirm the three new requests against the KMS Figma. Please clarify whether the Dharma School banner images are hardcoded or CMS-managed.

No Marcomm action is needed on the 21 hardcoded tickets unless the approved content is missing. The five previously failed handoff tickets and the 14 other UAT tickets have been re-verified by Codigo on pre-prod and await Brandon's verification. The five passed handoff tickets are closed.

The 11 existing pending items had no changes in this window.
