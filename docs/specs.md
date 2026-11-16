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
| Skill category | A group of skills, such as circuit design, system design, coding or leadership. |
| Skill block | A skill inside a category, such as PLL or ADC. |
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

### 2.2 Skill category and skill block
- A skill block belongs to one skill category.
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
| Skill block | The one block the employee worked on. An employee who worked on 2 blocks in a project has 2 assignments. |
| Participation | Lead or member of the block design. |
| Role description | Free text. |

### 2.5 Skill level
The level is per employee per skill block.

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
| FR-03 | U | The system shall offer these optional filters: team, career level, and one skill block with a minimum level for that block. |
| FR-04 | S | While one or more filters are set, the system shall rank only the employees that meet all filters. |
| FR-05 | U | The system shall show each search result with name, job title, team, top matching skills and a short reason for the match. |

### 3.2 Profile
| ID | Type | Requirement |
|----|------|-------------|
| FR-10 | E | When the user opens an employee, the system shall show a profile page for that employee. |
| FR-11 | U | The profile page shall show all employee attributes, the skill level for each skill block, and each project with its assignment details. |

### 3.3 Data entry
| ID | Type | Requirement |
|----|------|-------------|
| FR-20 | U | The system shall allow the user to create and edit employees. |
| FR-21 | U | The system shall allow the user to create and edit projects. |
| FR-22 | U | The system shall allow the user to create and edit assignments. |
| FR-23 | U | The system shall allow the user to set the Aware flag and the Expert flag on a skill block for an employee. |
| FR-24 | X | If the user sets the Aware flag on a skill block where the employee has an assignment, then the system shall reject the change and show a message. |
| FR-25 | U | The system shall compute levels 2, 3 and 4 from assignments. |
| FR-26 | X | If the user tries to enter level 2, 3 or 4 directly, then the system shall not accept the entry. |
| FR-27 | S | While the Expert flag is set on a skill block, the system shall show level 5 for that block, whatever the computed level. |

### 3.4 Settings
| ID | Type | Requirement |
|----|------|-------------|
| FR-30 | U | The system shall allow the user to create, rename and delete skill categories and skill blocks. |
| FR-31 | U | The system shall allow the user to set the number of lead and member assignments required for each computed level (2, 3 and 4). |
| FR-32 | U | The system shall use the default thresholds in section 2.5 until the user changes them. |

## 4. Non-Functional Requirements
| ID | Type | Requirement |
|----|------|-------------|
| NFR-01 | U | The system shall provide a web UI for desktop browsers only. |
| NFR-02 | U | The system shall not require login or roles. One local user shall have full access. |
| NFR-03 | U | The system shall run on one machine. |
| NFR-04 | U | The system shall include fake seed data: 40 employees, 15 projects, 6 skill categories and about 30 skill blocks. |
| NFR-05 | U | The seed data shall give skill levels that match the assignments. |
| NFR-06 | U | The system shall contain no real employee data. |

## 5. Constraints
- The system stores data in a vector store and uses embeddings (see `design.md`).
- The data is entered manually.

## 6. Out of Scope
- Staffing engineers into projects.
- Target role profiles and computed skill gaps.
- A team skill-gap report.
- Login, roles and access control.
- Mobile support.
- Success criteria for the PoC. The product owner chose not to define them. Without them, the team cannot show that the PoC worked.

## 7. Open Items
| ID | Item | Proposed default |
|----|------|------------------|
| OI-03 | The filter set (team, career level, minimum skill level) was inferred, not confirmed. | As in FR-03. |
| OI-04 | Delete rules for employees, projects and assignments are not defined. | Allow delete. |
