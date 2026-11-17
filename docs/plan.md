# Plan

Next milestone number: 15

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M12** Experience search | Ranked results, reasons, top leaves, preview | sonnet | high | open |
| **M13** Search filters | Team, career level, leaf with minimum level; filters with no query | sonnet | medium | open |
| **M14** Gap search | The skill gaps mode | sonnet | medium | open |

## Milestones

### M12 — Experience search

- **Refs:** FR-01, FR-02, FR-05, D-04, D-10, D-11, D-14, D-18, D-28, D-29.
- **Owner:** `src/domain/ranking.py`, `src/services/search.py`, `src/web/routes/search.py`, `src/web/templates/search.html`, `partials/`.
- **Tests first:** unit: `test_fr_01_rank_employees_puts_the_smallest_best_distance_first`,
  `test_fr_05_rank_employees_keeps_at_most_3_leaves_each_one_time`.
  route: `test_fr_01_query_ranks_the_employee_with_the_matching_assignment_first`,
  `test_fr_01_query_shows_at_most_search_result_limit_employees`,
  `test_fr_01_no_query_and_no_filter_shows_no_results`,
  `test_fr_05_result_shows_name_job_title_team_and_the_best_assignment_as_reason`,
  `test_fr_05_result_shows_at_most_3_leaf_tags`, `test_fr_05_preview_shows_the_first_result`,
  `test_fr_05_preview_route_shows_the_chosen_employee`.
  Manual: FR-02.
- **Build:** `rank_employees` in the domain. `search.py` embeds the query and searches the assignment vectors. The Search page from `docs/ui/SearchSplit.dc.html`: the query, the mode switch, the result list with `data-employee-id`, `data-reason` and `data-result-count`, and the preview that HTMX loads from `/search/preview/{employee_id}`.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M12` pass.

### M13 — Search filters

- **Refs:** FR-03, FR-04, FR-07, AC-01, D-04, D-29.
- **Owner:** `src/services/search.py`, `src/web/routes/search.py`, `src/web/templates/search.html`.
- **Tests first:** route: `test_fr_03_search_page_offers_team_career_level_and_leaf_with_minimum_level`,
  `test_fr_04_team_filter_ranks_only_employees_of_that_team`,
  `test_fr_04_leaf_filter_keeps_only_employees_at_the_minimum_level_or_higher`,
  `test_fr_03_aware_and_expert_flags_count_as_levels_1_and_5_in_the_filter`,
  `test_fr_04_employee_must_meet_all_set_filters`,
  `test_fr_07_filters_with_no_query_list_all_matching_employees_by_name`.
  Manual: AC-01.
- **Build:** step 1 of D-04 in `search.py`: the employees that meet the filters, with levels from assignments, flags and thresholds. Step 2 searches only their vectors. The filter chips of the canvas as one `GET` form.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M13` pass.

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
