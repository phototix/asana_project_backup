# Marcomm to Codigo daily update — 21 October 2026 (22:10 update)

Generated: 2026-10-21 22:10 SGT
Source: live Asana API and authenticated pre-prod checks, read-only
Scope: Open Tickets, Client to verify, New Request on Pre-prod, To update hardcoded content on Pre-prod
Window: 21 October 2026, 19:35 SGT onwards
No Asana data was changed.

## Summary

Codigo triaged the 28 tickets created from Marcomm's update set between 19:35 and 19:39. Codigo classified 21 as hardcoded content or layout updates, 3 as new requests, 1 as a CMS-managed update, and 3 as functional issues. All 28 were given a due date of 22 October 2026.

Between 20:49 and 20:53, Codigo verified 10 tickets on pre-prod, moved them from QA to verify into Client to verify, assigned them to Brandon, and attached screenshots. We checked all 10. Five passed and were closed, and five failed and were returned to Codigo. No tickets remain pending verification.

Since the 21:41 report, Publication Fail redirection and Publication Download Problem were verified and closed. Articles Text interface and Digital Download Video/Audio Button were returned to Codigo as failures. Rename Helpdesk is also closed.

Two additional tickets appeared in the window. The Dharma School Page Banner Image needs clarification on whether the images are hardcoded or CMS-managed. The E-Store Product Chinese name not shown is a functional issue.

Brandon's verification comments are included in the Pre-prod verification table. There were no changes to the 11 existing Marcomm-pending tickets, so they are not repeated.

## What Codigo decided

The 21 hardcoded content or layout updates are with Kaung Myat Hein and are due 22 October 2026. Codigo will apply the approved content on pre-prod. The tickets are Home Page - Mailing List Copy, Home Page - Latest Happenings Section, Home Page - Upcoming Events Chinese Label, Join Us - Volunteer - Intro Copy and Button Labels, Join Us - Volunteer - Top Banner, Join Us - Volunteer - Volunteer Events Section, Join Us - Volunteer - Join Us Image Replacement, Join Us - Bright Youth - Top Banner, Join Us - Bright Youth - Four Pillars Text, Join Us - Bright Youth - Membership Heading, Join Us - Bright Youth - Empty State Chinese Label, Join Us - Bright Youth - Page Section Order, Join Us - Joyous Heart - Top Banner, Join Us - Joyous Heart - Gallery Chinese Label, Join Us - Joyous Heart - Section Order, Join Us - Career - Top Banner, Join Us - Career - Intro Content and Photo, Join Us - Career - Divider Image, Join Us - Career - How to Apply Copy, Join Us - Career - Walk-In Interview Label, and Join Us - Career - Application Button Label.

The 3 new requests are with Dexter and are due 22 October 2026. They are Home Page - Top Banner and Activities Layout, Join Us - Volunteer - Areas of Service, and Join Us - Volunteer - Application Process. Marcomm should confirm these against the KMS Figma.

The CMS-managed update is Join Us - Bright Youth - Intro Copy. It is with Brandon and is due 22 October 2026. The intro is CMS-managed, and staging still contains the editor test line. Marcomm should provide the final English and Chinese copy.

The 3 functional issues are with Kaung Myat Hein and are due 22 October 2026. They are Join Us - Career - Chinese Text Visibility, Join Us - Joyous Heart - Divider Image, and Join Us - Joyous Heart - Footer Spacing.

## Pre-prod verification of the 10 handoff tickets

We checked the English pages and the Chinese pages where relevant. Each ticket below includes the Asana URL for manual review. Verified by shows Brandon's verification comment and time. Current status shows the Asana section after verification.

| Ticket | Asana URL | Pre-prod page | Check | Result | Evidence | Verified by | Current status |
|---|---|---|---|---|---|---|---|
| Contact Us heading capitalisation (1219573589097794) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573589097794 | /contact-us and /zh/contact-us | Main heading reads “Contact Us” | Fail | The main heading is “Contact Us”, but the footer heading still reads “Contact us”. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219739894383630 | Brandon — Fail noted 13:36 | Fail (To fix again) |
| Contact Us address formatting (1219573808950447) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573808950447 | /contact-us and /zh/contact-us | Address reads “88 Bright Hill Road, Singapore 574117” | Fail | The visible address reads “88 Bright Hill Road Singapore 574117” without the comma. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219739894383624 | Brandon — Fail noted 13:33 | Fail (To fix again) |
| Contact Us “Send A Message” heading (1219584612353363) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612353363 | /contact-us | Heading reads “Send a Message” | Pass | “Send a Message” is present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291709 | Brandon — Verified 13:21 | Closed |
| Contact Us “TODO: Verify Human” placeholder (1219584909725076) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584909725076 | /contact-us | Placeholder removed | Pass | “TODO: Verify Human” is not present. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291703 | Brandon — Verified 13:19 | Closed |
| Contact Us Rename “Helpdesk” (1219584612537724) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219584612537724 | /contact-us and /zh/contact-us | “Department Contacts” shown, “Helpdesk” removed | Pass | “Department Contacts” is present and “Helpdesk” is not. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219736536291715 | Brandon — Checked 13:22 | Closed |
| Awareness Place link (1219573938802132) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219573938802132 | /contact-us and /zh/contact-us | Link points to https://awarenessplace.com/ | Fail | The link is http://www.awarenessplace.com/. | Brandon — Fail noted 13:29 | Fail (To fix again) |
| Publication Fail redirection (1219575603663567) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575603663567 | /awaken-online/books | Publication “生活处处皆是禅” opens the detail page | Pass | Brandon checked the redirect on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741327390513 | Brandon — Checked 13:57 | Closed |
| Publication Download Problem (1219575536622988) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575536622988 | /awaken-online/books | “Download PDF” triggers a file download | Pass | Brandon checked the PDF download on pre-prod. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741328735444 | Brandon — Checked 13:59 | Closed |
| Articles Text interface (1219575656532229) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575656532229 | /awaken-online/articles | Paragraph breaks render on the article page | Fail | The breakline in the editor is still not reflected, and the page is gone and unable to open after the CMS update. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741729084436 and https://app.asana.com/app/asana/-/get_asset?asset_id=1219741729084434 | Brandon — Fail noted 14:06 | Fail (To fix again) |
| Digital Download Video/Audio Button (1219575604730061) | https://app.asana.com/1/1610754927873/project/1212423157941626/task/1219575604730061 | /awaken-online/digital | Download buttons trigger file downloads | Fail | Clicking download for both Audio and Video produced a Chrome download error. Evidence: https://app.asana.com/app/asana/-/get_asset?asset_id=1219741934358728 | Brandon — Fail noted 14:08 | Fail (To fix again) |

## Verification updates since 21:41

Publication Fail redirection and Publication Download Problem were verified and closed after Brandon's checks. Articles Text interface and Digital Download Video/Audio Button were returned to Fail (To fix again). No tickets remain in Client to verify from this handoff.

## Additional tickets in the window

Dharma School Page Banner Image (1213988637581792) is in Open Tickets, assigned to Zin Nhin, and has no due date. Codigo needs clarification on whether the Dharma School landing banner and hover-menu images are hardcoded or CMS-managed.

E-Store Product Chinese name not shown (1219692039810792) is in Open Tickets, assigned to Kaung Myat Hein, and is due 22 October 2026. Codigo observed that the Chinese product name is saved in the CMS but the staging E-store still shows English product names. This is a functional issue.

## Marcomm actions

Please update the Bright Youth intro English and Chinese copy in the CMS. Please confirm the three new requests against the KMS Figma. Please clarify whether the Dharma School banner images are hardcoded or CMS-managed.

No Marcomm action is needed on the 21 hardcoded tickets unless the approved content is missing. The five failed checks have been returned to Codigo for correction. No tickets remain pending verification.

The 11 existing pending items had no changes in this window.
