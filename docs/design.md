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
| D-06 | Decided | Store the skill tree as nodes, each with a link to its parent. | Supports any depth and uneven branches (section 2.2). A leaf is a node with no children. |
| D-07 | Decided | Build the UI as a web app for desktop browsers. Run it on one machine with no login. | Meets NFR-01, NFR-02 and NFR-03. |
| D-08 | Decided | Store one vector per assignment. Group the results by employee and rank the employees. | Matches precisely, such as "led PLL in 7nm" (example search 1). The text of each vector holds the leaf name, its description and its path in the tree, participation, assignment description and the project's process technology. Each vector links to its employee and assignment records. |
| D-09 | Decided | Also store one profile vector per employee. Its text holds the skill gaps. | Serves gap search. Aware and Expert flags are not embedded. Filters handle them. |
| D-10 | Decided | Experience search queries only the assignment vectors. Gap search queries only the profile vectors. Each search mode returns a ranked list of employees. | Two separate searches, each with its own vector type. |
| D-11 | Decided | Rank an employee by the score of their best matching assignment vector. | One strong match is what experience search looks for. The best assignment also gives the "short reason for the match" (FR-05). |
| D-12 | Superseded | Was: store a copy of levels in the metadata of each vector. | Replaced by D-04. The copy came from the wrong assumption that the store holds only vectors. |
| D-13 | Decided | Re-embed an assignment vector when its assignment, its project's process technology or its leaf name or description changes. Re-embed a profile vector when the skill gaps change. A change to team or career level needs no re-embedding. | Keeps vectors current at the lowest cost. Filters read the structured records (D-04), so they do not depend on the vectors. |
| D-14 | Decided | Show the matching text as the reason for the match. Experience search shows the best matching assignment (D-11). Gap search shows the skill gap text. No LLM is used. | Needs no extra processing. The matching text is the evidence (FR-05). |
| D-15 | Decided | Use LanceDB as the vector store. Keep structured records (employees, projects, flags, skill tree, settings) in tables with no vector column. Keep the assignment vectors and profile vectors in their own tables, linked by ID. | Embedded, so no server is needed (NFR-03). Stores structured tables and supports field filters. Verify at build time that a vector search can be limited to a set of employee IDs (D-04). |
| D-16 | Decided | Use `qwen3-embedding:0.6b`, run through Ollama on the same machine, as the starting embedding model. Fallback: `nomic-embed-text`. Make the model a single setting. | Runs locally with no API key. Handles technical vocabulary better than smaller models. Example searches 1 to 3 (AC-01) decide whether to swap it. |
| D-17 | Decided | Use the "Graphite" visual style: dark theme, Inter with JetBrains Mono details, mint accent. | Chosen from 3 styles on the UI canvas: https://claude.ai/artifact/VYZEh8JbCKG2AAPS81wozN |
| D-18 | Decided | The landing page is search. Its layout is the split view: sidebar, a narrow result list, and a preview panel for the selected employee. | Lets the user inspect a candidate without leaving the page. Chosen from 3 layouts (L1 to L3) on the UI canvas. |
| D-19 | Decided | The app has 8 pages in the Graphite style with the split view shell: Search (experience), Search (skill gaps), Employees, Employee profile (360 view), Edit employee, Project and assignments, Skill tree, Settings. The sidebar links to Search, Employees, Skill tree, Projects and Settings. | Product owner reviewed and approved the pages on the UI canvas: https://claude.ai/artifact/VYZEh8JbCKG2AAPS81wozN. The canvas is the visual reference for the build. |
| D-20 | Decided | Build the app in Python with FastAPI. Render the pages on the server with Jinja templates. Use HTMX for the interactive parts. | One language and one process, with no separate front-end build. LanceDB, Ollama and the embedding step all work from Python. The canvas pages port directly to templates. |
| D-21 | Decided | Keep the source code in four layers under `src/`: `web/` (the routes, the Jinja templates and the static files), `services/` (application logic), `domain/` (pure business logic) and `adapters/` (`store.py` for LanceDB and `embedder.py` for Ollama). `main.py` in the root is the entry point, `src/config.py` reads the settings and `src/app.py` is the app factory. `web` imports `services`. `services` and `adapters` import `domain`. `domain` imports none of them. The entry point creates the store and the embedder and passes them to the app factory. Tests are in `tests/unit/` and `tests/route/`. The files of the vector store are in `data/`, which is not committed. | The folder shows the layer of a module. A unit test needs no store and no server, and a test can pass a fake embedder. Chosen from 3 structures: four layers, feature folders, and a flat `src/`. |
| D-22 | Decided | Give each layer the modules in section "Architecture". One module owns one concern. | A milestone can name the module that owns its change (D-21). |
| D-23 | Decided | Approve these libraries: FastAPI, Uvicorn (the server), Jinja2, python-multipart (form data), LanceDB, and HTMX as one local JavaScript file. For the tests: pytest and httpx (the FastAPI test client needs it). Call the HTTP API of Ollama with `urllib` of the standard library. Read `config/.env` with code in `config.py`. Write the seed data in code. Use no browser test tool. | The smallest set that builds D-15, D-16 and D-20. The standard library does the rest. |
| D-24 | Decided | Use the settings in section "Settings". | Each value that changes behavior comes from `config/.env`. |
| D-25 | Decided | Keep the records in the LanceDB tables of section "Data storage". The system gives a new employee the next free ID in the form `E-0001`. The career levels are a fixed list: Junior, Mid, Senior, Staff, Principal. The team is free text. | Meets D-01, D-05, D-06 and D-15. The Edit employee page shows the ID as read-only and the career level as a list. |
| D-26 | Decided | Write the seed data in `src/domain/seed_data.py` as fixed records with invented names. Load it when the app starts and the store has no employee. The seed data holds the persons that the 3 example searches of AC-01 expect. | Meets NFR-04, NFR-05 and NFR-06. Fixed records give the same demo on each machine (D-03). |
| D-27 | Decided | Embed before the records are written: when the embedding model does not answer, save nothing and show a message. Compare vectors by cosine distance. Search all vectors of the filtered employees, with no approximate index. Keep the model name and the vector size in the table `meta`. When they differ from the settings at start, embed all vectors again. Make no profile vector for an employee with empty skill gaps. | No half-saved state. The data is small (A-09), so an exact search is fast. A changed model (D-16) cannot leave old vectors in the store. |
| D-28 | Decided | Show the best `SEARCH_RESULT_LIMIT` employees for a query. Show all employees, sorted by name, for a search with filters and no query (FR-07). Show no results for no query and no filter. A result row shows at most 3 tags of the form "leaf · level name" (FR-05) in the place where the canvas shows one. The first result is selected, and its preview shows. | AC-01 reads the top 5. The tag element comes from the canvas. |
| D-29 | Decided | Use the routes, form fields, response rules and HTML markers in section "Interfaces". A form posts to the server, and the server answers with a redirect or with the page and a message. | The test session writes route tests from these names without the code. |
| D-30 | Decided | Use the test policy in section "Test policy": unit tests for `src/domain`, route tests for the pages and forms with a fake embedder and a temporary store, and checks by hand for the look of the pages, FR-02 and AC-01. | The product owner chose unit and route tests. This is a PoC, so browser tests are cut. |
| D-31 | Decided | Build each page as a Jinja template from its artboard in `docs/ui/`. `docs/ui/` holds a copy of the 8 chosen artboards of the canvas (D-19), made on 2026-11-17. Never edit the copies: copy them again from the canvas. Keep the Graphite colors as CSS custom properties in one stylesheet. Keep HTMX and the 2 fonts (Inter, JetBrains Mono) as local files in `src/web/static/vendor/`. When a font file is missing, the page uses the system font. | The canvas is locked (D-17, D-18, D-19). An unattended session cannot read the canvas, so it needs the copy. Local files keep the app on one machine (NFR-03). |
| D-32 | Proposed | Log each request in `src/web/request_log.py`, a web module that `create_app` adds as an HTTP middleware. It logs the method, the path, the status and the time, and logs an error with its context. It does not log the query string. | The app factory holds no logic (`CLAUDE.md`), and the log must hold no user data. Auto-decided in M1, review. |
| D-33 | Proposed | Import `pyarrow` in `src/adapters/store.py` to give each LanceDB table an explicit schema, and list it in `requirements.txt` (pinned to the installed version). | LanceDB already installs it, and an empty table needs a schema. Auto-decided in M3, review. |
| D-34 | Proposed | Open an assignment for editing with `GET /projects/{id}?edit_assignment=<assignment id>`: the Project page shows the panel of the artboard in edit mode (the employee read-only) and the other assignments as read-only rows. `AssignmentService` in `src/services/assignments.py` adds the rows for a project and for an employee. The assignment rules (leaf, participation, duplicate) are the functions of `entry_rules.py`; the service raises `AssignmentError` with their message. | Meets FR-22 and FR-41. The route list had no way to open an edit form for an assignment. Auto-decided in M6, review. |
| D-35 | Proposed | `LanceStore` also has `list_assignment_vectors()` and `list_profile_vectors()`. They return the rows of the tables `assignment_vectors` and `profile_vectors` as the data classes `AssignmentVector(assignment_id, employee_id, text, vector)` and `ProfileVector(employee_id, text, vector)` of `src/domain/models.py`. | The route tests of M10 must read what was stored (D-13, D-27), and the store interface had no read of the vector tables. Auto-decided in M10, review. |
| D-36 | Proposed | `LanceStore` writes the vectors with `save_assignment_vectors(vectors)`, `delete_assignment_vectors(assignment_ids)`, `delete_assignment_vectors_of_employee(employee_id)`, `save_profile_vector(vector)`, `delete_profile_vector(employee_id)` and `drop_vectors()`, and the table `meta` with `get_meta()` and `set_meta(values)`. A save replaces the row of the same ID. The two vector tables have a fixed-size vector column, so the store creates each one at its first write, with the length of that vector; `drop_vectors()` deletes both before all vectors are embedded again. | `LanceStore(data_dir)` does not know the vector size of the model, and a vector search needs a fixed-size column. Auto-decided in M10, review. |
| D-37 | Proposed | `IndexingService(store, embedder)` in `src/services/indexing.py` is the only service that writes vectors. A service first calls `embed_assignments(assignments, project, nodes)` or `embed_profile(employee)` with the new values, then writes its records, then saves the vectors with `save_assignment_vectors(vectors)` or `save_profile(employee, vector)`. It embeds only a text that differs from the stored text of the vector. A changed node embeds the assignments of every leaf below it again, because the path of a leaf is in the text (D-08). `create_app` calls `sync_model()`; when the model does not answer at start, it logs a warning, keeps the vectors and leaves `meta` as it is, so the next start tries again. | Meets D-13 and D-27 at the lowest cost: a change that does not change a text (team, career level, project name) embeds nothing. Auto-decided in M10, review. |
| D-38 | Proposed | `src/web/errors.py` gives each route the message and the status of a failed save: 422 with the message of a rejected entry, or 503 with one fixed message when the embedding model does not answer. The routes that embed (save a project, add or save an assignment, add or save an employee, save a node) catch `EmbeddingUnavailable` and show their page with that message. | One place for the message of D-27, and no technical detail of Ollama on the page. Auto-decided in M10, review. |
| D-39 | Proposed | The data classes `Hit(employee_id, assignment_id, leaf_id, distance)` and `RankedEmployee(employee_id, best_assignment_id, leaf_ids)` are defined in `src/domain/ranking.py`, and a test imports them from there. `leaf_ids` is a list. | The Interfaces table names the two records but not their module, and `ranking.py` is the only module that uses them. Auto-decided in M12, review. |
| D-40 | Proposed | `LanceStore.search_assignment_vectors(query_vector, employee_ids=None)` runs the exact cosine search over the assignment vectors (all of them, or only those of the given employees, D-04) and returns `VectorMatch(assignment_id, employee_id, distance)` records of `src/domain/models.py`, nearest first. `SearchService(store, embedder, employees, result_limit)` in `src/services/search.py` has `experience(query)`: it embeds the query, joins each match with its assignment to make a `Hit`, calls `ranking.rank_employees`, and returns `SearchResult(rank, employee, reason, tags)` records; the reason is the description of the best assignment (D-14) and the tags are `EmployeeService.levels_in(employee_id, leaf_ids)`. When the model does not answer, `GET /search` shows the page with the message of `search_failure()` in `src/web/errors.py` and status 503. | The vector table has no leaf ID, so the service joins the assignments. The message of a failed save says that nothing was saved, which is wrong for a search. Auto-decided in M12, review. |

## Open Design Questions

| ID | Question |
|----|----------|

None.

## Architecture

The layers and their import rule are in D-21. `main.py` reads the settings with `src/config.py`, creates `LanceStore` and `OllamaEmbedder`, calls `create_app(store, embedder, options)` of `src/app.py`, and starts Uvicorn.

| Module | Layer | Responsibility | Requirements and decisions |
|--------|-------|----------------|----------------------------|
| `src/config.py` | entry | Reads `config/.env` and the environment. Gives the settings. | D-24 |
| `src/app.py` | entry | The app factory: connects the store, the embedder, the services and the routes. | D-21 |
| `src/domain/models.py` | domain | The data classes: Employee, Project, Node, Assignment, Flag, Threshold, AssignmentVector, ProfileVector. | Spec section 2, D-25, D-35 |
| `src/domain/levels.py` | domain | Computes the level of an employee in a leaf from counts, flags and thresholds. Holds the level names and the default thresholds. | FR-25, FR-27, FR-32, D-05 |
| `src/domain/skill_tree.py` | domain | Tree rules: the leaves, the leaves under a node, the path of a node. | Spec 2.2, FR-12, FR-13, D-06 |
| `src/domain/entry_rules.py` | domain | Decides whether an entry is valid and gives the message: Aware flag, duplicate assignment, leaf only, thresholds, node deletion, child of a leaf. | FR-24, FR-26, FR-33, FR-34, FR-35, FR-41, FR-42 |
| `src/domain/vector_text.py` | domain | Builds the text of an assignment vector and of a profile vector. | D-08, D-09 |
| `src/domain/ranking.py` | domain | Groups vector hits by employee, ranks the employees, and picks the reason and the top leaves. | FR-01, FR-05, FR-06, D-11, D-14 |
| `src/domain/seed_data.py` | domain | Builds the seed data. | NFR-04, NFR-05, NFR-06, D-26 |
| `src/services/employees.py` | services | Lists, shows, creates, edits and deletes employees. Builds the 360 view. | FR-10, FR-11, FR-20, FR-28, FR-29 |
| `src/services/projects.py` | services | Lists, creates, edits and deletes projects. | FR-21, FR-28, FR-29 |
| `src/services/assignments.py` | services | Creates, edits and deletes assignments. | FR-22, FR-28, FR-40, FR-41, FR-42 |
| `src/services/flags.py` | services | Sets and removes the Aware and Expert flags. | FR-23, FR-24, FR-26, FR-40, FR-41 |
| `src/services/skill_tree.py` | services | Reads and changes the tree. Lists the employees with a level in a leaf or under a node. | FR-12, FR-13, FR-30, FR-33, FR-34 |
| `src/services/thresholds.py` | services | Reads, saves and resets the thresholds. | FR-31, FR-32, FR-35, FR-36 |
| `src/services/indexing.py` | services | Embeds and stores the vectors after a change. Embeds all vectors again when the model changes. | D-13, D-27, D-37 |
| `src/services/search.py` | services | Runs the two search modes and the filters. | FR-01 to FR-07, D-04, D-10, D-28 |
| `src/services/seed.py` | services | Loads the seed data into an empty store. | NFR-04, D-26 |
| `src/adapters/store.py` | adapters | `LanceStore`: the only module that imports LanceDB. Reads and writes the tables. | D-01, D-15, D-25 |
| `src/adapters/embedder.py` | adapters | `OllamaEmbedder`: the only module that calls Ollama. | D-16 |
| `src/web/routes/search.py` | web | The Search page and its preview. | FR-01 to FR-07 |
| `src/web/routes/employees.py` | web | The Employees, Employee profile and Edit employee pages, and the flags. | FR-10, FR-11, FR-20, FR-23, FR-28 |
| `src/web/routes/projects.py` | web | The Project and assignments page. | FR-21, FR-22, FR-28 |
| `src/web/routes/skill_tree.py` | web | The Skill tree page. | FR-12, FR-13, FR-30 |
| `src/web/routes/settings.py` | web | The Settings page. | FR-31, FR-36 |
| `src/web/request_log.py` | web | Logs each request and each error of the app. | D-32 |
| `src/web/errors.py` | web | Gives the message and the status of a rejected entry or an unavailable embedding model. | D-27, D-38 |
| `src/web/templates/` | web | One template for each page, `base.html` for the shell, and `partials/` for the parts that HTMX swaps. | D-19, D-31 |
| `src/web/static/` | web | `app.css`, and `vendor/` with HTMX and the fonts. | D-17, D-31 |

## Settings

`config/.env.example` lists each key. A milestone adds a key there in the same change as the code that reads it.

| Setting | Default | Meaning |
|---------|---------|---------|
| `HOST` | `127.0.0.1` | The address that the server listens on. |
| `PORT` | `8000` | The port that the server listens on. |
| `DATA_DIR` | `data` | The folder of the LanceDB files, from the root of the repository. |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | The address of Ollama. |
| `EMBEDDING_MODEL` | `qwen3-embedding:0.6b` | The embedding model (D-16). |
| `EMBEDDING_TIMEOUT_SECONDS` | `60` | The longest time to wait for Ollama. |
| `SEARCH_RESULT_LIMIT` | `10` | The number of employees that a search with a query shows (D-28). |
| `PAGE_SIZE` | `10` | The number of rows on one page of the Employees list. |

## Data storage

Each table is a LanceDB table in `DATA_DIR`. Only the two vector tables have a vector column (D-15). The spec owns the data model (section 2). This section adds only what the store needs.

| Table | Fields | Notes |
|-------|--------|-------|
| `employees` | `id`, `name`, `job_title`, `career_level`, `team`, `skill_gaps` | `id` has the form `E-0001` (D-25). |
| `projects` | `id`, `name`, `description`, `year`, `process_technology` | `year` is a whole number. |
| `nodes` | `id`, `parent_id`, `name`, `description`, `position` | `parent_id` is empty for a top-level node (D-06). `position` is the order below the parent. |
| `assignments` | `id`, `employee_id`, `project_id`, `leaf_id`, `participation`, `description` | `participation` is `lead` or `member`. |
| `flags` | `employee_id`, `leaf_id`, `flag` | `flag` is `aware` or `expert`. One row for each employee and leaf. |
| `thresholds` | `level`, `lead_from`, `lead_to`, `member_from`, `member_to` | One row for each of the levels 2, 3 and 4. An empty `lead_to` or `member_to` means no upper limit. No rows: the defaults apply (FR-32). |
| `assignment_vectors` | `assignment_id`, `employee_id`, `text`, `vector` | One row for each assignment (D-08). |
| `profile_vectors` | `employee_id`, `text`, `vector` | One row for each employee with skill gaps (D-09). |
| `meta` | `key`, `value` | `embedding_model` and `vector_size` (D-27). |

The IDs of projects, nodes and assignments are random text IDs that the services make. A test does not depend on their value.

The text of an assignment vector has these lines, in this order: the leaf name, the leaf description, the path of the leaf, the participation, the assignment description, the process technology of the project (D-08). The text of a profile vector is the skill gaps (D-09).

## Interfaces

### The app, the store and the embedder

| Name | Interface |
|------|-----------|
| `create_app(store, embedder, options)` in `src/app.py` | Returns the FastAPI app. `options` is an `AppOptions` data class of `src/app.py` with `search_result_limit`, `page_size` and `load_seed`. When `load_seed` is true and `store` has no employee, the app loads the seed data. `main.py` sets `load_seed` to true. |
| `LanceStore(data_dir)` in `src/adapters/store.py` | Opens or creates the tables in the folder `data_dir`. For the table `nodes` it has `list_nodes()`, `add_node(node)`, `update_node(node_id, name, description)` and `delete_node(node_id)`. For the table `employees` it has `list_employees()`, `add_employee(employee)`, `update_employee(employee)` (changes every field of the employee with that ID) and `delete_employee(employee_id)`. For the table `assignments` it has `list_assignments()`, `add_assignment(assignment)`, `update_assignment(assignment)`, `delete_assignment(assignment_id)`, `delete_assignments_of_employee(employee_id)` and `delete_assignments_of_project(project_id)`. For the vector tables it has `list_assignment_vectors()` and `list_profile_vectors()` (D-35), and the writes of D-36, and `search_assignment_vectors(query_vector, employee_ids=None)` (D-40). For the table `meta` it has `get_meta()` and `set_meta(values)`. |
| The embedder | An object with `embed(texts)`, which takes a list of texts and returns one list of numbers for each text, and with the properties `model_name` and `vector_size`. It raises `EmbeddingUnavailable` (defined in `src/domain/models.py`) when the model does not answer. |
| `OllamaEmbedder(url, model, timeout_seconds)` in `src/adapters/embedder.py` | Calls `POST <url>/api/embed` with the fields `model` and `input` (a list of texts) and reads the field `embeddings`. `vector_size` embeds one probe text the first time it is read. |
| `IndexingService(store, embedder)` in `src/services/indexing.py` | `embed_assignments(assignments, project=None, nodes=None)`, `save_assignment_vectors(vectors)`, `delete_assignment_vectors(assignment_ids)`, `embed_profile(employee)`, `save_profile(employee, vector)`, `delete_employee_vectors(employee_id)` and `sync_model()` (D-37). The services of assignments, projects, employees and the skill tree take it as their last argument. |

### Public functions of the domain

| Function | Result |
|----------|--------|
| `levels.LEVEL_NAMES` | `{1: "Aware", 2: "Hands-on", 3: "Lead", 4: "Senior lead", 5: "Expert"}` |
| `levels.default_thresholds()` | The 3 `Threshold` records of spec section 2.5: level 2 is lead 0 to 0 and member 1 to no limit, level 3 is lead 1 to 2 and member 0 to no limit, level 4 is lead 3 to no limit and member 0 to no limit. |
| `levels.computed_level(lead_count, member_count, thresholds)` | The highest of the levels 2, 3 and 4 whose two ranges contain the counts, or `None` (FR-25). |
| `levels.effective_level(lead_count, member_count, flag, thresholds)` | `flag` is `None`, `"aware"` or `"expert"`. Expert gives 5 (FR-27). If not, one or more assignments give the computed level. If not, Aware gives 1. If not, `None`. |
| `skill_tree.is_leaf(nodes, node_id)` | `True` when no node has `node_id` as its parent. |
| `skill_tree.leaves_under(nodes, node_id)` | The leaves below the node, in tree order. A leaf gives itself. |
| `skill_tree.children_of(nodes, parent_id)` and `skill_tree.outline(nodes)` | The children of a node ordered by `position`, and every node with its depth, parents before their children. |
| `skill_tree.path(nodes, node_id)` | The names from the top-level node to the node, joined with ` / `, such as `Circuit design / Clocking / PLL`. |
| `ranking.rank_employees(hits, limit)` | `hits` is a list of `Hit(employee_id, assignment_id, leaf_id, distance)`. Returns at most `limit` `RankedEmployee(employee_id, best_assignment_id, leaf_ids)` records, the smallest best distance first. `leaf_ids` holds at most 3 leaves of the best hits, each leaf one time. |
| `vector_text.assignment_text(assignment, project, leaf, leaf_path)` | The text of an assignment vector. |
| `vector_text.profile_text(employee)` | The text of a profile vector, or an empty text for empty skill gaps. |
| `seed_data.build()` | A `SeedData` record with the lists `employees`, `projects`, `nodes`, `assignments` and `flags`. |

`Threshold` has the fields `level`, `lead_from`, `lead_to`, `member_from`, `member_to`. `None` in a `to` field means no upper limit. The other data classes have the fields of their table in "Data storage".

### Routes

A `GET` route answers with a page (status 200). A `POST` route that succeeds answers with status 303 and the address of the page that shows the result. A `POST` route that rejects an entry answers with status 422 and the page with the message. An unknown ID gives status 404. When the embedding model does not answer, a route answers with status 503 and the page with the message, and it saves nothing (D-27). A request with the header `HX-Request` gets only the part of the page that changes.

| Method and path | Fields | Result | Requirements |
|-----------------|--------|--------|--------------|
| `GET /` | | The Search page with no results. | D-18 |
| `GET /search` | `q`, `mode` (`experience` or `gaps`), `team`, `career_level`, `leaf_id`, `min_level` | The Search page with the results and the preview of the first result. | FR-01 to FR-07 |
| `GET /search/preview/{employee_id}` | `mode` | The preview part for one employee. | FR-05, D-18 |
| `GET /employees` | `filter` (a part of the name or the ID), `team`, `career_level`, `page` | The Employees page. | FR-10 |
| `GET /employees/new` | | The Edit employee page for a new employee. | FR-20 |
| `POST /employees` | `name`, `job_title`, `career_level`, `team`, `skill_gaps` | Creates the employee. Redirects to the profile. | FR-20 |
| `GET /employees/{id}` | | The Employee profile page. | FR-10, FR-11 |
| `GET /employees/{id}/edit` | | The Edit employee page. | FR-20, FR-23 |
| `POST /employees/{id}` | The fields of `POST /employees` | Saves the employee. Redirects to the profile. | FR-20 |
| `POST /employees/{id}/delete` | | Deletes the employee, the assignments and the flags. Redirects to `/employees`. | FR-28, FR-29 |
| `POST /employees/{id}/flags` | `leaf_id`, `flag` (`aware` or `expert`) | Sets the flag. Redirects to the Edit employee page. | FR-23, FR-24, FR-26, FR-41 |
| `POST /employees/{id}/flags/{leaf_id}/delete` | | Removes the flag. Redirects to the Edit employee page. | FR-23 |
| `GET /projects` | | The Project and assignments page with the first project selected. | FR-21 |
| `GET /projects/{id}` | `edit_assignment` (optional assignment ID, D-34) | The Project and assignments page with that project selected. | FR-21, FR-22 |
| `GET /projects/new` | | The Project page with the form for a new project. | FR-21 |
| `GET /projects/{id}/edit` | | The Project page with the form of that project. | FR-21 |
| `POST /projects` | `name`, `description`, `year`, `process_technology` | Creates the project. Redirects to `/projects/{id}`. | FR-21 |
| `POST /projects/{id}` | The fields of `POST /projects` | Saves the project. Redirects to `/projects/{id}`. | FR-21 |
| `POST /projects/{id}/delete` | | Deletes the project and its assignments. Redirects to `/projects`. | FR-28, FR-29 |
| `POST /projects/{id}/assignments` | `employee_id`, `leaf_id`, `participation` (`lead` or `member`), `description` | Creates the assignment. Redirects to `/projects/{id}`. | FR-22, FR-41, FR-42 |
| `POST /assignments/{id}` | `leaf_id`, `participation`, `description` | Saves the assignment. Redirects to its project. | FR-22 |
| `POST /assignments/{id}/delete` | | Deletes the assignment. Redirects to its project. | FR-28 |
| `GET /skill-tree` | | The Skill tree page with no node selected. | FR-30 |
| `GET /skill-tree/{node_id}` | | The Skill tree page with the node selected and its employees. | FR-12, FR-13 |
| `POST /skill-tree/nodes` | `parent_id` (empty for a top-level node), `name`, `description` | Adds the node. Redirects to `/skill-tree/{node_id}`. | FR-30, FR-34 |
| `POST /skill-tree/nodes/{node_id}` | `name`, `description` | Saves the node. Redirects to `/skill-tree/{node_id}`. | FR-30 |
| `POST /skill-tree/nodes/{node_id}/delete` | | Deletes the node. Redirects to `/skill-tree`. | FR-30, FR-33 |
| `GET /settings` | | The Settings page. | FR-31 |
| `POST /settings/thresholds` | For each level `n` of 2, 3 and 4: `level{n}_lead_from`, `level{n}_lead_to`, `level{n}_member_from`, `level{n}_member_to` | Saves the thresholds. Redirects to `/settings`. | FR-31, FR-35 |
| `POST /settings/thresholds/reset` | | Restores the defaults. Redirects to `/settings`. | FR-36 |

### HTML markers

A test finds content by these markers, not by the layout.

| Marker | On |
|--------|----|
| `role="alert"` | The element that holds a message for a rejected entry or an unavailable model. |
| `data-employee-id="<id>"` | Each row or card that shows one employee: a search result, a row of the Employees list, a row of the employees of a node, the preview. |
| `data-leaf-id="<id>"` with `data-level="<1 to 5>"` | Each element that shows the level of an employee in a leaf. A leaf with no level has `data-level="0"`. |
| `data-result-count="<n>"` | The element that shows the number of results. |
| `data-reason` | The element that holds the reason for the match in a search result. |
| `data-node-id="<id>"`, and `data-leaf="true"` on a leaf | Each row of the outline of the skill tree. |
| `data-project-id="<id>"` | Each row of the project list. |
| `data-assignment-id="<id>"` | Each row that shows one assignment. |
| `<select name="leaf_id">` | The list of leaves for an assignment, a flag or the search filter. It holds only leaves (FR-40). |

## Test policy

- The test tool is pytest. `python scripts/check.py` runs it over `tests/`.
- A unit test (`tests/unit/`) calls the public functions of one module of `src/domain`.
- A route test (`tests/route/`) calls the routes through the FastAPI test client. `tests/conftest.py` gives the fixtures `store` (a `LanceStore` in a temporary folder), `embedder` (a `FakeEmbedder`), `client` (the test client of `create_app(store, embedder, options)` with `load_seed` false and an empty store) and `seeded_client` (the same with `load_seed` true).
- `tests/fakes.py` holds `FakeEmbedder`. Its `vector_size` is 64. For each word of a text, in lower case, it adds 1 at the position `zlib.crc32(word) % 64`. It scales the vector to length 1. Thus two texts with the same words are near, and the result is the same on each run. It keeps the texts of each call in the list `calls`, so a test can examine what was embedded (D-13). `FakeEmbedder(available=False)` raises `EmbeddingUnavailable` on each call.
- No test calls Ollama. No test uses the folder `data/`.

| Level | Spec IDs |
|-------|----------|
| unit | FR-25, FR-27, FR-32, NFR-04, NFR-05 |
| route | FR-01, FR-03 to FR-07, FR-10 to FR-13, FR-20 to FR-24, FR-26, FR-28 to FR-31, FR-33 to FR-36, FR-40 to FR-42, NFR-02 |
| by hand | FR-02 and AC-01 (they need the live embedding model), NFR-01 (the look of the pages against the canvas), NFR-03 (the app and Ollama run on one machine), NFR-06 (the seed names are invented) |

## Sources

| Claim | Source | Date |
|-------|--------|------|
| A LanceDB vector search takes a filter with `.where("... IN (...)")`, and the filter applies before the search by default. | https://docs.lancedb.com/search/filtering | 2026-11-17 |
| LanceDB 0.41.0 keeps a table with no vector column, filters it, updates and deletes its rows, and limits a cosine search to a list of employee IDs with `IN`. This closes the check that D-15 asks for. | A test in a temporary folder with invented data: it passed. | 2026-11-17 |
| Ollama gives embeddings at `POST /api/embed` with the fields `model` and `input`, and answers with `embeddings`. | https://docs.ollama.com/api/embed | 2026-11-17 |
