# Software Requirements Specification: design-kb

Version 0.1 · 2026-11-16 · Status: Draft

## 1. Introduction

### 1.1 Purpose
This document states the requirements for `design-kb`. Design choices are in `design.md`.

### 1.2 Scope
`design-kb` is a knowledge base for an integrated circuit (IC) design team. It records who has experience in which skills. Users search it to find the right experience.

This is a proof of concept (PoC). It proves the idea. It is not a full product. It also teaches vector stores.

### 1.3 Definitions
| Term | Meaning |
|------|---------|
| Skill | The top-level group, such as circuit design, system design, coding or leadership. |
| Sub-skill | A group of blocks inside a skill, such as clock generation. |
| Block | A tag for one specific skill inside a sub-skill, such as VCO, PLL or CDR. Levels and assignments attach to blocks. |
| Assignment | The work of one employee on one project. |
| Semantic search | Search that matches meaning, not keywords. |

### 1.4 Users
One user type. The user has full access. There is no login (see NFR-02).

## 2. Data Model

### 2.1 Employee
| Attribute | Notes |
|-----------|-------|
| Employee ID | Unique. |
| Employee name | |
| Job title | |
| Career level | |
| Team/group | |
| Process technologies | List of process names, such as "TSMC 7nm". No level or count. |
| Skill gaps | Free text. Entered manually. |

### 2.2 Skill, sub-skill and block
- Hierarchy: skill, then sub-skill, then block.
- A sub-skill belongs to one skill. A block belongs to one sub-skill.
- Levels and assignments attach to blocks.
- The user manages both in Settings (FR-30).

### 2.3 Project
| Attribute | Notes |
|-----------|-------|
| Project name | |
| Description | Short text. |
| Year | |

### 2.4 Assignment (employee on a project)
| Attribute | Notes |
|-----------|-------|
| Employee | |
| Project | |
| Block | The one block the employee worked on. An employee who worked on 2 blocks in a project has 2 assignments. |
| Participation | Lead or member of the block design. |
| Role description | Free text. |

### 2.5 Skill level
The level is per employee per block.

| Level | Name | Source | Default rule |
|-------|------|--------|--------------|
| 1 | Aware | Manual flag | General knowledge from coursework or textbooks. Applies only when the employee has no assignment in the block. |
| 2 | Hands-on | Computed | Lead in 0 projects, member in 1 or more. |
| 3 | Lead | Computed | Lead in 1 to 2 projects. |
| 4 | Senior lead | Computed | Lead in 3 or more projects. |
| 5 | Expert | Manual flag | Set freely on any block. Overrides the computed level. |

## 3. Functional Requirements

Requirements use the EARS (Easy Approach to Requirements Syntax) templates. The Type column shows the template: U = ubiquitous, E = event-driven (When), S = state-driven (While), O = optional feature (Where), X = unwanted behavior (If, then).

### 3.1 Search
| ID | Type | Requirement |
|----|------|-------------|
| FR-01 | E | When the user submits a free-text query, the system shall return employees ranked by semantic match to the query. |
| FR-02 | U | The system shall match a query to employees by meaning, not by keywords. |
| FR-03 | U | The system shall offer these optional filters: team, career level, and one block with a minimum level for that block. |
| FR-04 | S | While one or more filters are set, the system shall rank only the employees that meet all filters. |
| FR-05 | U | The system shall show each search result with name, job title, team, top matching blocks and a short reason for the match. |

### 3.2 Views
| ID | Type | Requirement |
|----|------|-------------|
| FR-10 | E | When the user opens an employee, the system shall show a profile page for that employee. |
| FR-11 | U | The profile page shall give a 360 view: all employee attributes, the skill level for every block in every skill, and each project with its assignment details. |
| FR-12 | E | When the user selects a block, the system shall list all employees with a level in that block, sorted by level, highest first. |
| FR-13 | E | When the user selects a skill, the system shall list all employees with a level in any block of that skill, with their level in each block. |
| FR-14 | E | When the user selects an x-axis dimension, a y-axis dimension and a value, the system shall draw a matrix that colors each intersection by that value. Example: employees by blocks, colored by skill level. |

### 3.3 Data entry
| ID | Type | Requirement |
|----|------|-------------|
| FR-20 | U | The system shall allow the user to create and edit employees. |
| FR-21 | U | The system shall allow the user to create and edit projects. |
| FR-22 | U | The system shall allow the user to create and edit assignments. |
| FR-23 | U | The system shall allow the user to set the Aware flag and the Expert flag on a block for an employee. |
| FR-24 | X | If the user sets the Aware flag on a block where the employee has an assignment, then the system shall reject the change and show a message. |
| FR-25 | U | The system shall compute levels 2, 3 and 4 from assignments. |
| FR-26 | X | If the user tries to enter level 2, 3 or 4 directly, then the system shall not accept the entry. |
| FR-27 | S | While the Expert flag is set on a block, the system shall show level 5 for that block, whatever the computed level. |
| FR-28 | U | The system shall allow the user to delete employees, projects and assignments. |
| FR-29 | E | When the user deletes an employee or a project, the system shall also delete the assignments that refer to it. |

### 3.4 Settings
| ID | Type | Requirement |
|----|------|-------------|
| FR-30 | U | The system shall allow the user to create, rename and delete skills, sub-skills and blocks. |
| FR-31 | U | The system shall allow the user to set the number of lead and member assignments required for each computed level (2, 3 and 4). |
| FR-32 | U | The system shall use the default thresholds in section 2.5 until the user changes them. |
| FR-33 | X | If the user deletes a skill that has sub-skills, a sub-skill that has blocks, or a block that has assignments or flags, then the system shall refuse the deletion and show a message. |

## 4. Non-Functional Requirements
| ID | Type | Requirement |
|----|------|-------------|
| NFR-01 | U | The system shall provide a web UI for desktop browsers only. |
| NFR-02 | U | The system shall not require login or roles. One local user shall have full access. |
| NFR-03 | U | The system shall run on one machine. |
| NFR-04 | U | The system shall include fake seed data: 40 employees, 15 projects, 6 skills, about 12 sub-skills and about 30 blocks. |
| NFR-05 | U | The seed data shall give skill levels that match the assignments. |
| NFR-06 | U | The system shall contain no real employee data. |

## 5. Constraints
- The system stores data in a vector store and uses embeddings (see `design.md`).
- The data is entered manually.

## 6. Acceptance Criteria
| ID | Type | Criterion |
|----|------|-----------|
| AC-01 | E | When the demo runs the 3 example searches in OI-01, the system shall show the expected person in the top 5 results of each search. |

The PoC passes when AC-01 is met.

## 7. Out of Scope
- Staffing engineers into projects.
- Target role profiles and computed skill gaps.
- A team skill-gap report.
- Login, roles and access control.
- Mobile support.

## 8. Open Items
| ID | Item | Proposed default |
|----|------|------------------|
| OI-01 | The 3 example searches and the expected person for each are not yet defined. | Write them with the seed data. |
| OI-03 | FR-14 does not yet say which dimensions and values the user may pick. "Any x, any y" is open-ended. | Axes: employee, team, skill, sub-skill, block. Value: skill level only. |
