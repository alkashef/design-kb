# Plan

Next milestone number: 15

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M14** Gap search | The skill gaps mode | sonnet | medium | open |

## Milestones

### M14 — Gap search

- **Refs:** FR-03, FR-06, D-09, D-10, D-14, D-29.
- **Owner:** `src/services/search.py`, `src/web/routes/search.py`, `src/web/templates/search.html`, `partials/`.
- **Tests first:** route: `test_fr_06_gap_query_ranks_the_employee_with_the_matching_skill_gap_first`,
  `test_fr_06_gap_result_shows_the_skill_gap_text_as_reason`,
  `test_fr_06_employee_with_empty_skill_gaps_is_not_in_the_gap_results`,
  `test_fr_03_filters_apply_in_gap_search`.
- **Build:** the mode `gaps` searches the profile vectors. The result list and the preview from `docs/ui/SearchGaps.dc.html`: the matching skill gap and the strongest skills.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M14` pass.

## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
