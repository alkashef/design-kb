# Plan

Next milestone number: 15

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M6** Assignments | Create, edit and delete assignments; leaf-only and duplicate rules | sonnet | high | open |
| **M7** Flags and 360 view | Aware and Expert flags; the profile shows every level | sonnet | high | open |
| **M8** Tree guards and node views | Refused deletions; employees of a leaf or a node | sonnet | medium | open |
| **M9** Threshold settings | The Settings page: ranges, checks, reset | sonnet | medium | open |
| **M10** Vectors | Embedding on each change; message when Ollama is down | opus | high | open |
| **M11** Seed data | 40 employees, 15 projects, about 30 leaves, loaded at first start | sonnet | high | open |
| **M12** Experience search | Ranked results, reasons, top leaves, preview | sonnet | high | open |
| **M13** Search filters | Team, career level, leaf with minimum level; filters with no query | sonnet | medium | open |
| **M14** Gap search | The skill gaps mode | sonnet | medium | open |

## Milestones

### M6 — Assignments

- **Refs:** FR-22, FR-28, FR-29, FR-40, FR-41, FR-42, D-25, D-29.
- **Owner:** `src/services/assignments.py`, `src/domain/entry_rules.py`, `src/web/routes/projects.py`, `src/web/templates/projects.html`, `employee_profile.html`.
- **Tests first:** route: `test_fr_22_create_assignment_shows_on_the_project_and_on_the_profile`,
  `test_fr_22_edit_assignment_saves_participation_and_description`,
  `test_fr_28_delete_assignment_removes_it`, `test_fr_29_delete_employee_deletes_its_assignments`,
  `test_fr_29_delete_project_deletes_its_assignments`,
  `test_fr_40_assignment_form_lists_only_leaves`,
  `test_fr_41_assignment_on_a_node_with_children_is_rejected_with_a_message`,
  `test_fr_42_second_assignment_for_the_same_employee_project_and_leaf_is_rejected`.
- **Build:** the table `assignments`. The assignment rows and the "Add assignment" panel of `docs/ui/Projects.dc.html`. The table "Projects and assignments" of the profile page. The rules for a leaf and for a duplicate in `entry_rules.py`.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M6` pass.

### M7 — Flags and 360 view

- **Refs:** FR-11, FR-23, FR-24, FR-26, FR-27, FR-29, FR-40, FR-41, D-05, D-29.
- **Owner:** `src/services/flags.py`, `src/services/employees.py`, `src/domain/entry_rules.py`, `src/web/routes/employees.py`, `src/web/templates/employee_form.html`, `employee_profile.html`, `employees.html`.
- **Tests first:** route: `test_fr_23_expert_flag_shows_level_5_on_the_profile`,
  `test_fr_23_aware_flag_shows_level_1_on_the_profile`, `test_fr_23_removed_flag_removes_the_level`,
  `test_fr_24_aware_flag_on_a_leaf_with_an_assignment_is_rejected_with_a_message`,
  `test_fr_26_flag_value_other_than_aware_or_expert_is_rejected`,
  `test_fr_27_expert_flag_shows_level_5_over_the_computed_level`,
  `test_fr_11_profile_shows_attributes_the_level_of_every_leaf_and_the_assignments`,
  `test_fr_29_delete_employee_deletes_its_flags`, `test_fr_40_flag_form_lists_only_leaves`,
  `test_fr_41_flag_on_a_node_with_children_is_rejected_with_a_message`.
- **Build:** the table `flags`. The section "Skill flags" of `docs/ui/EmployeeForm.dc.html`. The section "Skill levels" of the profile page: each leaf with `data-leaf-id` and `data-level` (0 for no level) and the source of the level. The column "Top skills" of the Employees list: the 2 highest levels.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M7` pass.

### M8 — Tree guards and node views

- **Refs:** FR-12, FR-13, FR-33, FR-34, D-29.
- **Owner:** `src/services/skill_tree.py`, `src/domain/entry_rules.py`, `src/web/routes/skill_tree.py`, `src/web/templates/skill_tree.html`.
- **Tests first:** route: `test_fr_33_delete_a_leaf_with_an_assignment_is_refused_with_a_message`,
  `test_fr_33_delete_a_leaf_with_a_flag_is_refused_with_a_message`,
  `test_fr_34_add_child_to_a_leaf_with_an_assignment_is_refused_with_a_message`,
  `test_fr_34_add_child_to_a_leaf_with_a_flag_is_refused_with_a_message`,
  `test_fr_12_leaf_lists_its_employees_highest_level_first`,
  `test_fr_13_node_lists_employees_with_their_level_in_each_leaf_below`.
- **Build:** the two rules in `entry_rules.py`, and the message of `docs/ui/SkillTree.dc.html`. The list of the employees with a level, for a leaf and for a node with children.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M8` pass.

### M9 — Threshold settings

- **Refs:** FR-31, FR-32, FR-35, FR-36, D-25, D-29.
- **Owner:** `src/services/thresholds.py`, `src/domain/entry_rules.py`, `src/web/routes/settings.py`, `src/web/templates/settings.html`.
- **Tests first:** route: `test_fr_32_settings_page_shows_the_default_ranges`,
  `test_fr_31_saved_ranges_change_the_level_on_a_profile`,
  `test_fr_31_empty_to_value_means_no_upper_limit`,
  `test_fr_35_value_that_is_not_a_whole_number_is_rejected_with_a_message`,
  `test_fr_35_from_value_above_its_to_value_is_rejected_with_a_message`,
  `test_fr_36_reset_restores_the_default_ranges`.
- **Build:** the table `thresholds`. The page from `docs/ui/Settings.dc.html` with the 12 fields, "Save thresholds" and "Reset to defaults". Each page that shows a level reads the saved thresholds.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M9` pass.

### M10 — Vectors

- **Refs:** D-08, D-09, D-13, D-16, D-27.
- **Owner:** `src/domain/vector_text.py`, `src/services/indexing.py`, `src/adapters/embedder.py`, `src/adapters/store.py`.
- **Tests first:** unit: `test_d_08_assignment_text_has_its_6_lines_in_order`,
  `test_d_09_profile_text_is_the_skill_gaps`.
  route: `test_d_13_new_assignment_embeds_its_text`,
  `test_d_13_changed_process_technology_embeds_the_assignments_of_the_project_again`,
  `test_d_13_changed_leaf_name_embeds_its_assignments_again`,
  `test_d_13_changed_skill_gaps_embed_the_profile_again`, `test_d_13_changed_team_embeds_nothing`,
  `test_d_27_empty_skill_gaps_embed_no_profile`,
  `test_d_27_model_that_does_not_answer_gives_503_and_saves_nothing`.
- **Build:** the tables `assignment_vectors`, `profile_vectors` and `meta`. `indexing.py` embeds first and then writes, and the services of assignments, projects, the skill tree and employees call it. A deleted record loses its vectors. `create_app` embeds all vectors again when the model or the vector size in `meta` differs. `OllamaEmbedder` calls `POST /api/embed` with `urllib`.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M10` pass.

### M11 — Seed data

- **Refs:** NFR-04, NFR-05, NFR-06, D-03, D-26.
- **Owner:** `src/domain/seed_data.py`, `src/services/seed.py`, `src/app.py`.
- **Tests first:** unit: `test_nfr_04_seed_has_40_employees_15_projects_and_6_top_level_nodes`,
  `test_nfr_04_seed_has_between_25_and_35_leaves`,
  `test_nfr_04_seed_holds_the_persons_of_the_3_example_searches`,
  `test_nfr_05_seed_assignments_and_flags_obey_the_entry_rules`.
  route: `test_nfr_04_first_start_loads_the_seed_data_into_an_empty_store`,
  `test_nfr_04_start_with_employees_in_the_store_loads_nothing`.
  Manual: NFR-06.
- **Build:** `seed_data.build()` with fixed records and invented names. The seed holds a lead of a PLL design on a 7nm project, a member with level 2 or higher in a CDR leaf, and a senior employee of the team Analog with a level in a low-noise amplifier leaf. `seed.py` loads the records and their vectors when `load_seed` is true and the store has no employee.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M11` pass.

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
