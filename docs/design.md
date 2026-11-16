# Design Choices

Design decisions for `design-kb`, a proof of concept (PoC). Requirements are in `specs.md`.

Status: **Decided** means the product owner chose it. **Proposed** means Claude derived it from a requirement. The product owner has not confirmed it.

## Decisions

| ID | Status | Decision | Reason |
|----|--------|----------|--------|
| D-01 | Decided | Use one vector store that holds both structured data and embeddings. It stores all records: employees, projects, assignments, flags, the skill tree and settings. There is no separate database. | The PoC teaches vector stores. |
| D-02 | Decided | Use embeddings to implement semantic search. | Meets FR-02. |
| D-03 | Decided | Generate fake data for the demo. | No real employee data is needed to prove the idea (NFR-04, NFR-06). |
| D-04 | Decided | Apply the search filters in two steps. Step 1: query the structured records for the employees that meet the filters, and compute their levels from assignments and flags. Step 2: run the vector search only on the vectors of those employees. | The store holds structured data (D-01), so no copy of team, career level or levels is needed in the vectors. Meets FR-04. Filter-only search (FR-07) uses step 1 alone. |
| D-05 | Decided | Do not store levels 2, 3 and 4. Compute them from assignments when needed. Store only the Aware and Expert flags. | Levels cannot go out of date or contradict the assignments (FR-25, FR-26, FR-27). |
| D-06 | Proposed | Store the skill tree as nodes, each with a link to its parent. | Supports any depth and uneven branches (section 2.2). A leaf is a node with no children. |
| D-07 | Proposed | Build the UI as a web app for desktop browsers. Run it on one machine with no login. | Meets NFR-01, NFR-02 and NFR-03. |
| D-08 | Decided | Store one vector per assignment. Group the results by employee and rank the employees. | Matches precisely, such as "led PLL in 7nm" (example search 1). The text of each vector holds the leaf name, its description and its path in the tree, participation, assignment description and the project's process technology. Each vector links to its employee and assignment records. |
| D-09 | Decided | Also store one profile vector per employee. Its text holds the skill gaps. | Serves gap search. Aware and Expert flags are not embedded. Filters handle them. |
| D-10 | Decided | Experience search queries only the assignment vectors. Gap search queries only the profile vectors. Each search mode returns a ranked list of employees. | Two separate searches, each with its own vector type. |
| D-11 | Decided | Rank an employee by the score of their best matching assignment vector. | One strong match is what experience search looks for. The best assignment also gives the "short reason for the match" (FR-05). |
| D-12 | Superseded | Was: store a copy of levels in the metadata of each vector. | Replaced by D-04. The copy came from the wrong assumption that the store holds only vectors. |
| D-13 | Decided | Re-embed an assignment vector when its assignment, its project's process technology or its leaf name or description changes. Re-embed a profile vector when the skill gaps change. A change to team or career level needs no re-embedding. | Keeps vectors current at the lowest cost. Filters read the structured records (D-04), so they do not depend on the vectors. |
| D-14 | Decided | Show the matching text as the reason for the match. Experience search shows the best matching assignment (D-11). Gap search shows the skill gap text. No LLM is used. | Needs no extra processing. The matching text is the evidence (FR-05). |
| D-15 | Decided | Use LanceDB as the vector store. Keep structured records (employees, projects, flags, skill tree, settings) in tables with no vector column. Keep the assignment vectors and profile vectors in their own tables, linked by ID. | Embedded, so no server is needed (NFR-03). Stores structured tables and supports field filters. Verify at build time that a vector search can be limited to a set of employee IDs (D-04). |
| D-16 | Decided | Use `qwen3-embedding:0.6b`, run through Ollama on the same machine, as the starting embedding model. Fallback: `nomic-embed-text`. Make the model a single setting. | Runs locally with no API key. Handles technical vocabulary better than smaller models. Example searches 1 to 3 (AC-01) decide whether to swap it. |

## Open Design Questions

| ID | Question |
|----|----------|

None.
