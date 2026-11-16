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

## Open Design Questions

| ID | Question |
|----|----------|
| DQ-01 | What is the embedded unit? One document per employee, or one per assignment? This sets what the vector store returns. |
| DQ-02 | Which vector store and which embedding model? |
| DQ-03 | How does the system produce the "short reason for the match" (FR-05)? For example, show the best matching assignment description. |
| DQ-04 | When data changes, how does the system update the embeddings? For example, re-embed the employee on every save. |
