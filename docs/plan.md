# Plan

Next milestone number: 32

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M27** Panes | Every page is a row of panes. Each pane has a frozen head and a body that scrolls alone, and no pane is narrower than 240px | sonnet | high | open |
| **M28** Panel handles | A handle between the panes of a page. `panes.js` drags it, keeps the widths of each page in the browser, and a sidebar button resets them | sonnet | high | open |
| **M29** Engineer detail pane | A click on an engineer row opens a detail panel on the right with a Close control, and the list narrows | sonnet | high | open |
| **M30** Skill tree arrow | The arrow or dot of each outline row starts at the left edge of the text above it (fix) | sonnet | low | open |
| **M31** Add-child sizes | The add-child text box takes the free width of its row and the button has the normal size (fix) | sonnet | low | open |

## Milestones

### M27 — Panes

- **Refs:** FR-53, FR-54, FR-56, NFR-01, D-45, D-19, D-43. Spec 0.5, section 3.5 and the glossary term Panel. Today each page scrolls as a whole, and the split pages grow with their content (M18). The design section "Panels" gives the panes of each page, what each frozen head holds and the default widths.
- **Owner:** `src/web/templates/base.html`, the page templates (`search.html`, `partials/search_body.html`, `partials/preview.html`, `engineers.html`, `engineer_profile.html`, `engineer_form.html`, `projects.html`, `skill_tree.html`, `settings.html`) and `src/web/static/app.css`.
- **Tests first:** route, in a new file `tests/route/test_panes.py`. The tests read the pages through the client and the `app.css` that the Search page links, and merge the plain rules of a selector as `tests/route/test_sidebar_pinned.py` does. The stylesheet selectors are the attribute selectors of the markers: `[data-pane]`, `[data-pane-head]`, `[data-pane-body]` and `[data-pane-flex]`, besides `.shell` and `:root`. The test session changes an existing test only where its requirement changed, and names each one in its report.
  - `test_fr_53_shell_has_the_height_of_the_window_and_does_not_scroll`: the rule `.shell` has `height` 100vh or 100dvh and `overflow` (or `overflow-y`) `hidden`. It fails today, because `.shell` has a `min-height`.
  - `test_fr_53_pane_body_scrolls_vertically_on_its_own`: `[data-pane-body]` has `overflow-y: auto` and `min-height: 0`; `[data-pane]` has `display: flex`, `flex-direction: column` and `min-height: 0`.
  - `test_fr_54_pane_head_does_not_shrink`: `[data-pane-head]` has `flex` `none` or `0 0 auto`.
  - `test_fr_53_every_pane_has_a_head_then_a_body`: on Search (`/` and a `GET /search?q=pll` with results), Engineers, an engineer profile, the Edit engineer form, Projects with a project selected, Skill tree with a node selected and Settings, each element with `data-pane` has exactly 2 element children, the first with `data-pane-head` and the second with `data-pane-body`. The pane IDs of each page, in order: Search `results`, `preview`; Engineers `engineers`; profile `engineer`; form `engineer-form`; Projects `projects`, `project`, `assignment`; Skill tree `outline`, `node`; Settings `settings`.
  - `test_fr_54_head_holds_the_title_and_the_search_and_filter_controls`: the head of `engineers` holds the `h1` "Engineers", the input `filter` and the selects `team` and `career_level`; the head of `results` holds the element with `data-result-count`, and the query input `q` is in no `data-pane-body`; the head of `projects` holds the `h1` "Projects"; the head of `outline` holds the `h1` "Skill tree" and the input of the form that posts to `/skill-tree/nodes`; the head of `settings` holds the `h1` "Settings".
  - `test_fr_53_exactly_one_pane_of_a_page_takes_the_free_width`: on each page of the test above, exactly one pane has `data-pane-flex`: `preview`, `engineers`, `engineer`, `engineer-form`, `project`, `node` and `settings` respectively; and the rule `[data-pane-flex]` has `flex` `1 1 0` (or `1 1 0%`).
  - `test_fr_56_stylesheet_gives_each_pane_a_minimum_width_of_240px`: `:root` defines `--pane-min` as `240px`, and `[data-pane]` has `min-width: var(--pane-min)`.
  - `test_nfr_01_body_names_its_page`: `<body>` has `data-page` with the value `search` on `/`, `engineers` on `/engineers`, `skill_tree` on `/skill-tree`, `projects` on `/projects` and `settings` on `/settings`.
  - Existing tests: `tests/route/test_split_bodies.py` (M18) demands that `.search-body` and `.tree-body` keep a `min-height` and a flex basis above 0, so that the page grows with its content. D-45 replaces that rule, so the test session replaces that test and names it in its report. `tests/route/test_sidebar_pinned.py` stays as it is, because the rule `.sidebar` does not change.
  - Manual: FR-53, FR-54, FR-56.
- **Build:** in `base.html`, `<body data-page="{{ active_page }}">`. In `app.css`, give `.shell` the height of the window with `overflow: hidden`, and `.main` `min-height: 0`; keep the rule `.sidebar` as it is. Make each page a row of panes as the design says: `<section data-pane="<id>">` with a first child `data-pane-head` (the title and the search or filter controls) and a second child `data-pane-body` (the rest), with the IDs, heads and flexible pane of the table "Panels". The Search band (mode toggle, query box, filters) stays above the row, outside the panes. Write the rules of "Panels" for `[data-pane]`, `[data-pane-head]`, `[data-pane-body]` and `[data-pane-flex]` and the custom property `--pane-min`; the rows no longer wrap and get `min-height: 0` and `overflow-x: auto`; a page with one pane keeps its content width of 980px inside the body. The fixed panes keep the widths they have today. Change no route, no form field, no message text and no marker of D-29; keep the class `panel` of the cards.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M27` pass.

### M28 — Panel handles

- **Refs:** FR-55, FR-57, FR-58, NFR-01, D-46, D-45. Assumption A-11 (the widths belong to the browser). The drag, the minimum width and the kept widths need a browser (D-23), so the route tests check the markers, the stylesheet and the script file only.
- **Owner:** `src/web/static/panes.js` (new), `src/web/static/app.css`, `src/web/templates/base.html`, and the Search body, Projects and Skill tree templates.
- **Tests first:** route, in a new file `tests/route/test_pane_handles.py`. Handles are elements with `data-pane-handle` and `role="separator"`. The test session changes an existing test only where its requirement changed, and names each one in its report.
  - `test_fr_55_search_page_has_one_handle_between_results_and_preview`: on `GET /` the siblings in the row of the pane `results` are, in this order, `results`, one handle with `aria-orientation="vertical"`, and `preview`. A `GET /search?q=pll` with the header `HX-Request` (the swapped part) has the same order.
  - `test_fr_55_projects_page_has_a_handle_between_each_two_panes`: with a project selected the order is `projects`, handle, `project`, handle, `assignment`. With no project in the store it is `projects`, handle, `project`.
  - `test_fr_55_skill_tree_page_has_one_handle_between_outline_and_node`: `outline`, handle, `node`.
  - `test_fr_55_pages_with_one_pane_have_no_handle`: the Engineers list, an engineer profile, the Edit engineer form and Settings have no `data-pane-handle`.
  - `test_fr_58_every_page_has_the_reset_button_in_the_sidebar`: each page has exactly one element with `data-pane-reset` inside the sidebar, with the text "Reset widths", before the link "Add engineer".
  - `test_fr_57_every_page_links_panes_js_and_the_script_is_served`: each page has `<script src="/static/panes.js">`, and `GET /static/panes.js` answers 200 with a JavaScript media type.
  - `test_fr_55_fixed_panes_take_their_width_from_the_pane_width_property`: the plain rule of `[data-pane="results"]` has `flex` `0 0 var(--pane-width, 460px)`, and likewise `outline` 420px, `projects` 420px and `assignment` 340px; the rule `[data-pane-handle]` has a width of 8px (as `width: 8px` or `flex: 0 0 8px`) and `cursor: col-resize`.
  - `test_d_46_every_function_of_panes_js_has_a_one_line_jsdoc`: each `function` declaration or function expression in `/static/panes.js` has a one-line `/** ... */` comment directly before it (`CLAUDE.md`, Code quality). It fails today, because the file does not exist.
  - Manual: FR-55, FR-56, FR-57, FR-58.
- **Build:** write `panes.js` as D-46 says. It uses event delegation on `document` and pointer events, so that a handle that HTMX swaps in works. A drag changes `--pane-width` (in pixels, on the pane) of the nearest pane without `data-pane-flex`: the pane on the left of the handle, or the one on the right when the left one is the flexible pane. It stops where either neighbour would get narrower than `--pane-min` (read with `getComputedStyle` from `:root`). It keeps `{pane id: pixels}` in `localStorage` under `design-kb.panes.<page>` (`<page>` is `data-page` of `<body>`), inside `try/catch`, because a blocked storage must not break the page; it applies the kept widths at load and after `htmx:afterSwap`. The button `data-pane-reset` deletes the key and the `--pane-width` values; it is rendered `hidden` and shown by the script only when the page has a handle. Every function has a one-line JSDoc. In `base.html`, link `/static/panes.js` and put the button in the sidebar footer above "Add engineer", with the look of "Panels". Add the handles to the Search body partial, to Projects and to Skill tree. In `app.css`, write the rule of the handle (8px, no fill, a 2px line in `--line-strong`, `--accent` on hover and while dragging) and give the fixed panes `flex: 0 0 var(--pane-width, <default>)`. No new library and no new setting.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M28` pass.

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
