# Keyword review against canonical master

Prepared 2026-10-22 against `origin/master` at `9247beea1b850cb044ec51fe6974368eccdf8716`. This is the cumulative public-search difference in draft PR #83, not just the latest sweep's change count.

| Listing | Search change relative to master | Review rationale |
| --- | --- | --- |
| Eagle Nest Mercantile | Add `gift shop`, `jewelry` | Review against the business website before publication. |
| Budget Host & Summit RV Park | Add `lodging` | Motel/RV park; review the shared visitor stay page. |
| Fishers Peak State Park | Add `hiking` | Review the state-park visitor page. |
| Summit RV Park | Add `lodging`; block inferred `hotel` | The shared stay page also lists hotels; the RV park should not inherit that type. |
| La Veta Oil Company | Remove `directory`; block `business directory` and `directory` from the commercial-directory host | The business appears in a directory but is not itself one. |
| Spanish Peaks Country Galleries Directory | Remove `business directory` | A gallery directory is not a general business directory. |

The 2026-10-22 source sweep checked 120 URLs and had 114 fetch failures or access limits. Existing source keywords and blocked-inference records are retained when a page cannot be checked; failures do not imply that a business or page has closed. PR #83 changes review state and these controlled search terms, not public directory inclusion or contact records. Its generated candidate and source-registry files overlap draft PR #86, so reconcile #86 against #83 before the second merge. Human review is still required for public keyword changes.
