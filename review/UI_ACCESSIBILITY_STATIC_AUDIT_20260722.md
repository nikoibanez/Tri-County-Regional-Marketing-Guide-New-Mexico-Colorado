# UI Accessibility Static Audit

Date: 2026-07-22

This no-dependency audit checks generated static files for accessibility regressions that are easy to break during generator edits. It does not replace browser, keyboard, or screen-reader QA.

| Status | Check | Detail |
| --- | --- | --- |
| PASS | generated pages exist | 25 HTML files found |
| PASS | skip link target | Homepage includes a skip link target |
| PASS | native assistant dialog | Assistant uses native dialog markup |
| PASS | assistant opener semantics | Ask directory button announces a dialog |
| PASS | assistant title link | Dialog is tied to a visible title |
| PASS | assistant description link | Dialog has visible and screen-reader instructions |
| PASS | assistant result control | Search input controls the results region |
| PASS | assistant live status | Result counts are announced politely |
| PASS | assistant result structure | Results are exposed as list/listitem content |
| PASS | native focus management | Uses dialog showModal instead of a custom focus trap |
| PASS | generated music removed | No generated music files are referenced by active pages/scripts |
| PASS | regional audio present | Music bar references only LOC regional tracks |
| PASS | screen-reader utility | Screen-reader-only helper exists |
| PASS | image alt attributes | All generated pages give img elements alt attributes |

Failures: 0
