# Plan

Next milestone number: 32

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M29** Engineer detail pane | A click on an engineer row opens a detail panel on the right with a Close control, and the list narrows | sonnet | high | blocked |
| **M30** Skill tree arrow | The arrow or dot of each outline row starts at the left edge of the text above it (fix) | sonnet | low | open |
| **M31** Add-child sizes | The add-child text box takes the free width of its row and the button has the normal size (fix) | sonnet | low | open |

## Milestones

### M29 — Engineer detail pane

- **Refs:** FR-10, FR-50, FR-51, FR-52, AC-02, NFR-01, D-47, D-29, D-18. FR-10 changed in spec 0.5: a click on a row of the Engineers list no longer opens the profile page, it opens the detail pane. The profile page (FR-11) stays at `/engineers/{id}`.
- **Owner:** `src/web/preview.py` (new), `src/web/routes/engineers.py`, `src/web/routes/search.py`, `src/web/templates/engineers.html`, `src/web/templates/partials/preview.html` and `src/web/static/app.css`.
- **Tests first:** route, in a new file `tests/route/test_engineer_detail_pane.py`. The data: engineers added with the builders, one of them ("Cy Invented", Design Engineer, Mixed-signal, Senior) with a leaf, a project, an assignment and skill gaps. The pane is the element with `data-pane="engineer-detail"` and carries `data-engineer-id`. The test session changes an existing test only where its requirement changed, and names each one in its report.
  - `test_fr_10_selected_engineer_shows_the_detail_pane_beside_the_list`: `GET /engineers?selected=<id>` has the element `engineer-detail-slot`, and in the row of panes the order is `engineers`, one handle, `engineer-detail`; the pane has the ID of that engineer; the list pane still holds the rows of all engineers; `engineer-detail` has `data-pane-flex` and `engineers` does not.
  - `test_fr_10_without_selection_the_list_pane_is_alone_and_flexible`: `GET /engineers` has an empty `engineer-detail-slot`, no handle, and `engineers` has `data-pane-flex`.
  - `test_fr_10_unknown_selected_engineer_shows_no_pane`: `GET /engineers?selected=E-9999` answers 200 with an empty slot.
  - `test_fr_10_each_row_links_to_the_selection_and_carries_the_htmx_attributes`: each row with `data-engineer-id="<id>"` is a link whose `href` starts with `/engineers?`, holds `selected=<id>` and keeps a filter that was set (`team=Analog` stays); it has `hx-get="/engineer-panel/<id>"`, `hx-target="#engineer-detail-slot"` and `hx-push-url`.
  - `test_fr_10_panel_route_gives_the_pane_of_the_chosen_engineer`: `GET /engineer-panel/<id>` gives one handle and one pane with that ID, and for another ID the pane of the other engineer.
  - `test_fr_10_unknown_engineer_on_the_panel_route_gives_404`: `GET /engineer-panel/E-9999` answers 404.
  - `test_fr_50_detail_pane_shows_the_attributes_the_levels_the_projects_and_the_skill_gaps`: the pane shows the name, job title, career level, team, ID and skill gaps, an element with `data-leaf-id` and `data-level` for the leaf of the assignment, the project name and the assignment description.
  - `test_fr_51_open_full_profile_links_to_the_profile_page`: the pane has an element with `data-open-profile` whose `href` is `/engineers/<id>`, and that address answers 200.
  - `test_fr_52_close_control_links_to_the_list_and_to_the_empty_panel`: the pane has an element with `data-detail-close` whose `href` is `/engineers?` with the filters and no `selected`, with `hx-get="/engineer-panel"` and `hx-push-url`; `GET /engineer-panel` answers 200 with no pane and no handle.
  - `test_ac_02_case_1_selecting_a_row_shows_the_panel_and_narrows_the_list`: the data of case 1 of AC-02; the panel holds Cy Invented, Design Engineer, Mixed-signal, Senior and E-0001, and the list pane is not the flexible one.
  - `test_ac_02_case_2_selecting_another_engineer_shows_one_panel_for_it`: `GET /engineer-panel/<other id>` gives exactly one pane, of the other engineer.
  - `test_ac_02_case_3_closing_the_panel_gives_back_the_list_alone`: the `href` of the Close control gives the page of `test_fr_10_without_selection_...`.
  - Existing tests: the FR-10 test `test_fr_10_open_engineer_shows_the_profile_page` of `tests/route/test_engineers.py` checks the profile page at `/engineers/{id}`; the test session may rename it after FR-11 or FR-51, because FR-10 changed. `test_fr_05_preview_route_shows_the_chosen_engineer` must still pass.
  - Manual: NFR-01.
- **Build:** as D-47 says. Move `preview_of` of `routes/search.py` into `src/web/preview.py` as `preview_context(request, engineer_id)`, which answers 404 for an unknown ID, and call it from both routes. In `partials/preview.html`, give "Open full profile" the marker `data-open-profile`, and show a Close control (`data-detail-close`) only when a `close_href` is given. Add `GET /engineer-panel/{engineer_id}` and `GET /engineer-panel`, the parameter `selected` of `GET /engineers`, and the slot `<div id="engineer-detail-slot">` that holds the handle and the pane `engineer-detail` (head: the engineer header with "Open full profile" and Close). A row of the list is a link with the HTMX attributes of D-47, and the row of the selected engineer is marked as selected. The list pane has the width 600px (`--pane-width` fallback) while the detail is open, and is flexible when alone. Below 720px the list pane hides the columns JOB TITLE, CAREER and TOP SKILLS (a container query on the pane). Change no other route and no message text.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M29` pass.
- **Blocked:** The tests `test_fr_10_selected_engineer_shows_the_detail_pane_beside_the_list` and `test_ac_02_case_1_...` need a page that D-47 forbids, and a build session may not change a file in `tests/`.
  - `tests/route/test_engineer_detail_pane.py`, `row_order` and `find_parent` (lines 62-84): the order `[engineers, handle, engineer-detail]` is read from the direct children of the parent of the list pane, so the handle and the detail pane must be direct siblings of the list pane in the row of panes.
  - D-47 (`docs/design.md`) and the plan block say that the slot `<div id="engineer-detail-slot">` holds the handle and the pane, and the row carries `hx-target="#engineer-detail-slot"` (the default swap is innerHTML). Then the handle and the pane are children of the slot, not of the row, and `row_order` gives `[engineers]` only.
  - A flat row (the handle and the pane beside the list pane, the slot empty) satisfies the tests, but then an HTMX swap into the slot puts the new handle and pane inside the slot, and a page load puts them beside it, so a second click shows two handles and two panes unless extra out-of-band swaps are added. That is a different design from D-47, and I did not choose it on my own.
  - Nothing else was changed (the new test file stays as the test session wrote it). To continue, approve one of these:
    1. The test session fixes the test: `row_order` reads the panes and handles in the order of the page, below the row (the descendants of the row, so that the slot may sit between), and the slot holds the handle and the pane as D-47 says. Then run the milestone again.
    2. Change D-47 to a flat row: the handle and the detail pane are siblings of the list pane, `engineer-detail-slot` is an empty marker, and the swap uses out-of-band deletes of the old handle and pane. The build session then follows the tests as they are.

### M30 — Skill tree arrow

- **Refs:** NFR-01, D-48, D-19. No requirement changes. The fault: the arrow of a folding row sits at 8px from the left edge (`left: 8 + 22 × depth` px, in a box 20px wide), while the hint text and the title start at 28px and the dot of a leaf at 28px. D-48 puts the caret or dot box, 14px wide with its glyph at the left, at 28px plus 22px for each level of depth, with a gap of 10px to the name.
- **Owner:** `src/web/templates/skill_tree.html` and `src/web/static/app.css`.
- **Tests first:** route, in a new file `tests/route/test_skill_tree_outline_alignment.py`, on a tree with a top-level branch, a branch below it, and a leaf at depth 2.
  - `test_nfr_01_branch_caret_starts_where_the_row_content_starts`: each row with `data-node-id` has the inline style `padding-left` of `28 + 22 × depth` px; each element with the class `caret-toggle` has an inline `left` of the same value as the `padding-left` of its row. It fails today, because the `left` is 20px smaller.
  - `test_nfr_01_caret_boxes_are_14px_wide_with_the_glyph_at_the_left`: the plain rules `.caret` and `.caret-toggle` have `width: 14px`, and `.caret-toggle` has `text-align: left`. It fails today (12px and 20px).
  - `test_nfr_01_every_outline_row_starts_with_a_caret_box`: the first element child of each row with `data-node-id`, branch or leaf, has the class `caret`, so that the names of a branch and of a leaf at the same depth start at the same place.
  - Manual: NFR-01.
- **Build:** put the caret toggle of a branch at `left` `28 + 22 × depth` px, 14px wide with `text-align: left`, make the box of the leaf dot 14px wide, and give each branch row a hidden `.caret` box like the one of a leaf, so that the name of every row starts 24px right of the box. Keep the structure that the fold tests of M20 read (the row inside the `<summary>`, `<details>` for a node with children). Change no route and no text.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M30` pass.

### M31 — Add-child sizes

- **Refs:** NFR-01, D-48, D-19. No requirement changes. The fault: in the add-child form of the node detail the button has the rule `.button-outline` (`width: 100%`), so it takes the whole row and leaves the text box small. D-48 gives the text box the free width of its row, and the button the size of Delete. On the artboard `docs/ui/SkillTree.dc.html` all buttons of the node detail are 42px high; in `app.css` the buttons of `.actions` are 40px high today.
- **Owner:** `src/web/static/app.css`.
- **Tests first:** route, in a new file `tests/route/test_skill_tree_add_child_sizes.py`. The tests resolve the plain class rules of `app.css` that apply to an element, in file order, as the style tests of M22 and M24 do.
  - `test_nfr_01_add_child_text_box_takes_the_free_width_of_its_row`: the form that posts to `/skill-tree/nodes` inside the node detail has `display: flex` on its class, and its text box has `flex` with a grow of 1 or more, `min-width: 0` and `height: 42px`. It fails today (40px).
  - `test_nfr_01_add_child_button_has_the_size_of_delete`: the "Add child" button and the "Delete" button of the node detail resolve to the `height` 42px and the `padding` `0 18px`, and "Add child" has a `width` that is not 100% (`auto`, or none with `flex: 0 0 auto`). It fails today.
  - Manual: NFR-01.
- **Build:** CSS only. Give the button of the add-child form `width: auto`, `flex: 0 0 auto`, `height: 42px` and `padding: 0 18px`; give its text box `height: 42px`; set the buttons of `.actions` in the node detail to 42px, as on the artboard. Change no template, no route and no text.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M31` pass.

## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- FR-53, FR-54, M27: on each of the 8 pages, with long content, scroll each pane with the mouse wheel. Projects: "Projects", the project and "Add assignment" scroll one by one. Search: the results and the preview scroll alone. Skill tree: the outline and the node detail scroll alone. Engineers with the detail pane open: the list and the detail scroll alone. The title of each pane and its search or filter controls (the Engineers filters, the Search query band) stay at the top, and the sidebar stays in view.
- FR-56, FR-55, M27, M28: drag each handle (Search 1, Skill tree 1, Projects 2, Engineers 1 while the detail pane is open). The panes follow the pointer. No pane gets narrower than 240px, and a pane never disappears.
- FR-57, A-11, M28: change the widths on Projects, reload the page and open it again: the widths stay. Open Search: its widths are the defaults. Open the same page in another browser: the defaults.
- FR-58, M28: choose "Reset widths" in the sidebar: the page shows its default widths, and after a reload they stay the defaults. The button is not shown on Engineer profile, Edit engineer and Settings.
- AC-02 case 4, M28: do the case on the Projects page (widen the project panel, open Search, then Projects).
- NFR-01, M29: on Engineers, select a row: the list narrows to about 600px and hides JOB TITLE, CAREER and TOP SKILLS; the panel on the right shows the engineer; Close gives back the full-width list; "Open full profile" opens the profile page. Compare with the artboard `docs/ui/Engineers.dc.html`.
- NFR-01, M30, M31: on Skill tree, select a leaf at depth 2: the arrow of each row starts at the left edge of the hint text, at each depth. The add-child text box fills the free width of its row, and "Add child" is as large as "Delete". Compare with `docs/ui/SkillTree.dc.html`.
- NFR-01, M27, M28: compare Search, Search (skill gaps), Projects and Skill tree with the artboards in `docs/ui/`: the handles and the "Reset widths" button in the sidebar.
- D-44, M25: before the first start after M25, delete the folder `data/` (`DATA_DIR`) one time. Its tables have the earlier names, and the store does not migrate them. Then start Ollama and the app: the seed data loads again, and the Engineers page lists 40 engineers.
- NFR-01, M25: open each of the 8 pages and compare its texts with its artboard in `docs/ui/`: the sidebar link "Engineers", the button "Add engineer", the headings "Engineers" and "Edit engineer", and the labels "Engineer ID" and "Engineer name".
- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-01, M16, M18: on Engineers, Search, Skill tree and Projects, each with a long list, scroll down. The sidebar stays in view, and its Add engineer button stays reachable.
- NFR-01, M19, M20: open Skill tree and select a leaf at depth 2. The add-child text box and button sit in a card like the Name and Description card. The path to the leaf is open, the other branches are folded, and the caret folds and unfolds a branch. Compare with the artboard `docs/ui/SkillTree.dc.html`.
- NFR-01, M17: open Settings and compare the Level thresholds with the artboard `docs/ui/Settings.dc.html`: the table, its 5 columns and its 5 rows.
- NFR-01, M22, M23, M24: open each of the 8 pages and compare its colors and fonts with its artboard in `docs/ui/` (D-43): the dark sidebar, the grey surfaces, the beige cards, the orange accent on fills and edges only, JetBrains Mono on the navigation, the buttons and the filters, and the red Delete buttons and error message. Read the text on each surface: nobody measured the contrast on a screen.
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
