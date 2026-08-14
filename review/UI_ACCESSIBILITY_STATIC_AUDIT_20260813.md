# UI Accessibility Static Audit

Date: 2026-08-13

This no-dependency audit checks generated static files for accessibility regressions that are easy to break during generator edits. It does not replace browser, keyboard, or screen-reader QA.

| Status | Check | Detail |
| --- | --- | --- |
| PASS | generated pages exist | 26 HTML files found |
| PASS | skip link target | Homepage includes a skip link target |
| PASS | native assistant dialog | Assistant uses native dialog markup |
| PASS | assistant opener semantics | Ask directory button announces a dialog |
| PASS | assistant title link | Dialog is tied to a visible title |
| PASS | assistant description link | Dialog has visible and screen-reader instructions |
| PASS | assistant result control | Search input controls the results region |
| PASS | assistant live status | Result counts are announced politely |
| PASS | assistant result structure | Results are exposed as list/listitem content |
| PASS | native focus management | Uses dialog showModal instead of a custom focus trap |
| PASS | assistant guide-page routing | Assistant indexes 49 internal routes with a page-relative root |
| PASS | free-tool filter semantics | Tool search, category, and access controls are labelled and report results politely |
| PASS | structured free-tool inventory | Rendered 22 cards from 22 structured tool records |
| PASS | non-obstructive preview watermark | Preview text is decorative, pointer-transparent, 90% transparent, and positioned in the lowest viewport band |
| PASS | responsive tool reflow | Tool controls reflow at tablet/mobile widths and the mobile list starts with six items |
| PASS | visible keyboard focus | Generated controls retain visible focus styles |
| PASS | reduced motion | Decorative motion can be disabled by user preference |
| PASS | generated music removed | No generated music files are referenced by active pages/scripts |
| PASS | regional audio scope | Music controls appear only on Arts & Culture |
| PASS | regional audio present | Arts & Culture references 6 manifest-backed LOC tracks |
| PASS | regional audio source trail | Every player track includes an item page, rights note, and credit line |
| PASS | screen-reader utility | Screen-reader-only helper exists |
| PASS | image alt attributes | All generated pages give img elements alt attributes |

Failures: 0
