# Plan

Next milestone number: 26

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |

## Milestones


## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

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
