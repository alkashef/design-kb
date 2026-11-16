# Design Choices

Design decisions for `design-kb`, a proof of concept (PoC). Requirements are in `specs.md`.

Status: **Decided** means the product owner chose it. **Proposed** means Claude derived it from a requirement. The product owner has not confirmed it.

## Decisions

| ID | Status | Decision | Reason |
|----|--------|----------|--------|
| D-01 | Decided | Store people records in a vector store. | The PoC teaches vector stores. |
| D-02 | Decided | Use embeddings to implement semantic search. | Meets FR-02. |
| D-03 | Decided | Generate fake data for the demo. | No real employee data is needed to prove the idea (NFR-04, NFR-06). |
| D-04 | Proposed | Implement the search filters (team, career level, leaf with minimum level) as vector store metadata filters. | Teaches filtered vector search. Meets FR-04. |
| D-05 | Proposed | Do not store levels 2, 3 and 4. Compute them from assignments when needed. Store only the Aware and Expert flags. | Levels cannot go out of date or contradict the assignments (FR-25, FR-26, FR-27). |
| D-06 | Proposed | Store the skill tree as nodes, each with a link to its parent. | Supports any depth and uneven branches (section 2.2). A leaf is a node with no children. |
| D-07 | Proposed | Build the UI as a web app for desktop browsers. Run it on one machine with no login. | Meets NFR-01, NFR-02 and NFR-03. |
| D-08 | Decided | Store one vector per assignment. Group the results by employee and rank the employees. | Matches precisely, such as "led PLL in 7nm" (example search 1). The text of each vector holds the leaf name and its path in the tree, participation, assignment description and the project's process technology. Employee metadata (team, career level) is copied onto each vector for the filters. |
| D-09 | Decided | Also store one profile vector per employee. Its text holds the skill gaps. | Serves gap search. Aware and Expert flags are not embedded. Filters handle them. |
| D-10 | Decided | Experience search queries only the assignment vectors. Gap search queries only the profile vectors. Each search mode returns a ranked list of employees. | Two separate searches, each with its own vector type. |
| D-11 | Decided | Rank an employee by the score of their best matching assignment vector. | One strong match is what experience search looks for. The best assignment also gives the "short reason for the match" (FR-05). |

## Open Design Questions

| ID | Question |
|----|----------|
| DQ-02 | Which vector store and which embedding model? |
| DQ-03 | How does gap search produce the "short reason for the match" (FR-05)? For example, show the skill gap text. |
| DQ-04 | When data changes, how does the system update the embeddings? For example, re-embed the employee on every save. |
| DQ-05 | Filters on a leaf's minimum level (D-04) need levels in the vector store metadata. D-05 says levels are not stored. Resolve by storing a copy that updates on every save, or by filtering after retrieval. |
