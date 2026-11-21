# Plan

Next milestone number: 32

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M30** Skill tree arrow | The arrow or dot of each outline row starts at the left edge of the text above it (fix) | sonnet | low | open |
| **M31** Add-child sizes | The add-child text box takes the free width of its row and the button has the normal size (fix) | sonnet | low | open |

## Milestones

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
