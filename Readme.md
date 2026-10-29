# A Constraint-Based Smart University Examination Scheduling System
## with Human Resource Allocation and Resource Consumption Optimisation

> **Research Proposal README**
> Faculty of Computing — Department of Computer Science
> University of Sri Jayewardenepura (USJ)

---

## 📋 Project Metadata

| Field | Detail |
|---|---|
| **Title** | A Constraint-Based Smart University Examination Scheduling System with Human Resource Allocation and Resource Consumption Optimisation |
| **Submitted By** | A.B.Z. Hussain |
| **Index Number** | AS2022468 |
| **Programme** | B.Sc. (Hons) in Computer Science — Final Year |
| **Supervisor** | [Supervisor Name & Designation] |
| **Date of Submission** | 30 May 2026 |
| **Institution** | University of Sri Jayewardenepura, Faculty of Computing, Department of Computer Science |
| **Methodology** | Design Science Research (DSR) |
| **Target Publication Venues** | ICTER / SLAAI (contingent on results) |

---

## 1. Introduction / Background

University examination scheduling is one of the most operationally complex administrative tasks in higher education. At the University of Sri Jayewardenepura (USJ), as in most Sri Lankan public universities, the examination scheduling process is conducted **manually** by examination officers who must simultaneously account for hundreds of courses across multiple years, semesters, departments, and examination types.

This manual approach is:

- ⏱️ Time-consuming
- ❌ Error-prone
- ⚠️ Prone to scheduling conflicts
- 📉 Suboptimal in resource utilisation
- 🗑️ Wasteful

### Programme Structure Context

The BSc (Hons) programme structure at USJ provides a well-defined course hierarchy:

- **Course codes** follow the pattern `[DEPT][YEAR][SEQ]` — e.g., `CSC 201` denotes a Computer Science course in the second year.
- **Credits** directly determine examination duration.
- **Theory and practical examinations** have fundamentally different requirements (venue type, paper materials, supervision ratios, equipment).
- **Year groups** sit examinations in designated time sessions (Year 1 in the morning, Year 2 mid-morning, etc.), adding a temporal constraint layer to avoid campus logistical conflicts.

### The Gap

Despite the availability of computational approaches, **no automated, intelligent scheduling system exists at USJ or most other Sri Lankan public universities.** This research proposes a constraint-based smart examination scheduling system using algorithmic and machine learning techniques to produce conflict-free, resource-optimised examination timetables. It is designed to be generalisable beyond USJ to any university using a structured course code convention.

---

## 2. Problem Statement

Current examination scheduling practices at Sri Lankan public universities are characterised by the following critical problems:

| # | Problem | Description |
|---|---|---|
| 1 | **Student conflicts** | Students enrolled in multiple courses may be scheduled for two examinations simultaneously — occurs regularly under manual scheduling. |
| 2 | **Room over-allocation** | Examination halls assigned based on rough estimates, resulting in over-crowded venues or underutilised rooms with unnecessary allocation costs. |
| 3 | **Unbalanced schedules** | Examination load unevenly distributed across the examination period, creating peak-stress days for students and idle days for staff. |
| 4 | **Human resource inefficiency** | Supervisors, invigilators, and hall attendants assigned manually without optimisation — unfair duty distribution and scheduling gaps. |
| 5 | **Paper waste** | Answer booklets, question papers, and supplementary sheets printed without precise calculation — measurable paper and cost wastage. |
| 6 | **No differentiation between examination types** | Theory and practical examinations have entirely different requirements; current systems treat them uniformly. |
| 7 | **No fallback or generalisation** | Existing manual processes are institution-specific and cannot be transferred or scaled to other universities. |

**Collective impact:** These issues increase administrative workload, reduce examination quality, and result in preventable resource expenditure. There is a clear need for an intelligent, automated system that addresses all these dimensions systematically.

---

## 3. Research Objectives

1. To develop an **automated course code parser** that extracts year, semester, credit load, and examination type (Theory or Practical) from structured university course codes.
2. To design and implement a **constraint-based examination scheduling algorithm** (CSP with backtracking) that eliminates hard conflicts and satisfies soft constraints including year-based session assignments.
3. To develop a **human resource allocation module** that assigns chief supervisors, invigilators, and hall attendants to each examination based on student count, examination type, and staff availability constraints.
4. To implement a **resource consumption optimisation module** that precisely calculates paper, answer booklet, and stationery requirements per examination, minimising waste.
5. To build a **web-based examination management system** with role-based dashboards for examination officers, lecturers, and students.
6. To **evaluate the system** against manual scheduling using metrics including conflict rate, room utilisation efficiency, staff duty balance, and paper consumption reduction.
7. To **generalise the system** through a configuration-driven architecture enabling deployment at any university using a structured course code convention.

---

## 4. Research Questions

1. To what extent can a **Constraint Satisfaction Problem (CSP) approach** eliminate examination scheduling conflicts compared to the current manual process at USJ?
2. How effectively can a **Genetic Algorithm optimisation layer** improve soft constraint satisfaction (schedule balance, staff duty fairness, session distribution) following initial CSP scheduling?
3. What **reduction in paper and stationery consumption** is achievable through precise algorithmic resource calculation compared to current estimation practices?
4. How usable is the developed web system for examination officers and students at a Sri Lankan public university, as measured by the **System Usability Scale (SUS)**?
5. Can the system be effectively **generalised** to function as a configurable examination planner for universities beyond USJ using synthetic or self-reported data?

---

## 5. Literature Review

Examination timetabling is a well-studied problem in operations research and computer science, classified as **NP-hard** due to its combinatorial complexity.

### 5.1 Constraint Satisfaction and Timetabling
- **Even, Itai, and Shamir (1976)** established the theoretical complexity of timetabling problems.
- **CSP formulations with backtracking and forward checking** can produce conflict-free timetables efficiently for university-scale instances.
- **Burke et al. (2004)** provided a comprehensive survey of graph colouring and CSP approaches, establishing the conceptual foundation for modern scheduling systems.
- **Key insight:** Courses sharing enrolled students must not be assigned to the same time slot — maps naturally to graph colouring (courses = nodes, shared-student conflicts = edges).

### 5.2 Metaheuristic Optimisation Approaches
- While CSP guarantees hard constraint satisfaction, soft constraint optimisation requires additional techniques.
- **Genetic Algorithms (GAs)** widely applied to optimise secondary objectives such as minimising consecutive examinations and balancing examiner workloads (Deb, 2001; Pillay, 2014).
- **Simulated Annealing** applied to improve schedule quality post-CSP (Abuhamdah, 2010).
- **Soria-Alcaraz et al. (2016):** Hyperheuristic frameworks outperform single metaheuristics on complex timetabling instances — relevant to the multi-objective nature of this research.

### 5.3 Resource Optimisation in Examination Management
- This dimension has received comparatively little attention in the literature.
- Existing studies focus primarily on conflict elimination rather than downstream physical resource implications.
- **Kahar and Kendall (2010):** Addressed examination venue assignment as a secondary optimisation problem; room capacity constraints can be satisfied alongside time slot constraints without significant performance degradation.
- **No prior study** was identified that explicitly models paper consumption minimisation as an objective in examination scheduling.

### 5.4 Human Resource Allocation in Invigilation
- **Demir and Bilge (2017):** Modelled invigilator assignment as a variant of the nurse scheduling problem, applying constraint programming to satisfy workload balance and expertise constraints.
- Demonstrated algorithmic assignment reduces duty imbalance by **up to 40%** compared to manual allocation — a benchmark this research aims to replicate in the Sri Lankan university context.

### 5.5 Web-Based Examination Systems in Developing Contexts
- Limited research addresses web-based examination management systems specifically for South/Southeast Asian public university contexts.
- Existing commercial systems (e.g., **Celcat**, **FET**) are designed for Western university structures and do not accommodate:
  - Structured course code conventions
  - Session-based year groupings
  - Resource optimisation requirements specific to Sri Lankan universities
- **This represents a significant contextual gap.**

### 5.6 Summary of Research Gap

| Research Area | Existing Work | Gap Addressed Here |
|---|---|---|
| Conflict elimination | CSP, GA, graph colouring | Applied to SL university structure with course code parsing |
| Practical vs theory exams | Not differentiated | Full differentiation: venue, ratio, paper, duration |
| Paper/stationery optimisation | Not studied | Novel module calculating sheets per exam with buffer |
| Invigilator allocation | General constraint programming | Duty fairness with role-based ratios (SL context) |
| Generalisability | Institution-specific systems | Config-driven architecture for any structured-code university |
| Sri Lankan public universities | No prior automated system | First proposed system for SL public HEI context |

---

## 6. Research Methodology

This research follows a **Design Science Research (DSR)** methodology — an applied research paradigm emphasising the creation, evaluation, and generalisation of purposeful artefacts (systems, algorithms, models) to address real-world problems (Hevner et al., 2004).

The methodology comprises **five sequential phases**, with a **three-tier data acquisition strategy** embedded in Phase 1.

### 6.1 Phase 1: Data Acquisition — Three-Tier Strategy

Data acquisition is the most critical and potentially most challenging phase. A three-tier fallback strategy ensures the research can proceed regardless of institutional cooperation. Each tier is attempted in sequence.

#### 🥇 Tier 1 — Institutional Data (Primary, Preferred)
Obtain official examination-related data directly from USJ through a formal academic data request.

**Data to be requested:**
- **Course catalogue:** course codes, course names, credit values, department, year, semester for all active programmes
- **Student enrolment counts:** number of students registered per course per semester (anonymised — no individual student data)
- **Room inventory:** room identifiers, capacities, types (lecture hall, computer lab, examination hall)
- **Staff list:** academic and administrative staff available for examination duties (name, department, designation — no personal data beyond operational necessity)
- **Historical examination schedules** (if available): for benchmarking

**Procedure:** Formal data request letter co-signed by the research supervisor submitted to the Dean of the Faculty of Computing and the Registrar's office. Includes a data confidentiality agreement, ethics clearance documentation, and a clear scope statement that no individual student personal data is required.

**Timeline:** Weeks 2–4.

#### 🥈 Tier 2 — Student Self-Reported Registration Data (Secondary Fallback)
If institutional data access is not granted within the required timeframe, this tier activates. Collects course enrolment data through a structured Google Form distributed to students at USJ, modelled on the existing student portal examination registration process.

**Form design:** Students report current registered courses using official course codes (e.g., `CSC 201`, `CSC 209`). The form collects **no names, index numbers, or any personally identifiable information** — only course codes and the respondent's academic year. Full ethical compliance.

**Advantages:**
- No institutional permission required beyond ethical approval for survey distribution
- Provides real enrolment distribution from the actual student population
- Course codes self-reported using the official format, enabling automatic parsing
- Distributable via WhatsApp, department notice boards, and student Facebook groups
- **Target: 200–400 responses** across Year 1–4 is sufficient for scheduling a representative semester

**Limitations acknowledged:** Self-reported data may be incomplete or contain minor errors (incorrect course codes). A validation step checks all submitted codes against the known course list extracted from the USJ faculty handbook (publicly available). Invalid codes are flagged and excluded.

**Timeline:** Weeks 3–5 if Tier 1 fails.

#### 🥉 Tier 3 — Synthetic Data Generation (Final Fallback)
If both Tier 1 and Tier 2 are unsuccessful or yield insufficient data, a synthetic dataset is generated that faithfully replicates the structure of the USJ BSc (Hons) Computer Science programme and Sri Lankan public university conventions. Academically valid for proof-of-concept system evaluation; explicitly framed as the **generalisation scenario**.

**Synthetic data generation approach:**
- **Course structure:** Following observed USJ pattern — courses coded by department, year, and sequence; credit values drawn from real distribution (1.0, 1.5, 2.0, 2.5 credits); 15–20% of courses classified as Practical based on keyword matching
- **Enrolment:** Student counts drawn from realistic distributions (Year 1: 150–200; Year 2: 120–180; Year 3: 80–140; Year 4: 60–100 per department)
- **Rooms:** Modelled on typical USJ faculty building inventory (3–4 large lecture halls capacity 100–200; 4–6 medium halls capacity 50–80; 2 computer labs capacity 40–60)
- **Staff:** 30–50 academic staff with roles, departments, and availability flags

This tier also serves as the generalisation dataset — demonstrating the system running on a generic university configuration via the `config.json` architecture.

> **Note:** The final research paper will explicitly state which data tier was used and discuss implications for validity. Using Tier 2 or Tier 3 data does not diminish the research contribution, as the primary contribution is the **system and algorithm design**, not the specific dataset.

### 6.2 Phase 2: System Analysis and Design

Covers:
- **Requirements engineering:** Functional requirements (scheduling, allocation, calculation, export) and non-functional requirements (usability, performance, generalisability) documented using use case diagrams and user stories following Agile methodology
- **Database schema design:** Full entity-relationship diagram covering `Courses`, `Students`, `Rooms`, `Staff`, `ExamSlots`, `ExamSchedule`, `StaffDuties`, `ExamResources`, and `Constraints` tables — normalised to **Third Normal Form (3NF)**
- **System architecture design:** Three-tier web architecture — React frontend, Python FastAPI backend (REST API), Supabase (PostgreSQL database + authentication + real-time subscriptions) — with the scheduling engine as a standalone Python module callable via API
- **Algorithm design:** Formal specification of hard and soft constraints, CSP backtracking logic, and Genetic Algorithm fitness function
- **HCI design:** Low-fidelity wireframes developed and validated with 3 potential users before implementation begins

### 6.3 Phase 3: Core Algorithm Development

The technical centrepiece — five interconnected algorithm modules:

#### Module A — Course Code Parser
A regular expression-based parser that extracts:
- Year (first digit of course code)
- Department code (alphabetic prefix)
- Sequence number
- Credit value
- Examination type (Theory/Practical via keyword matching on course name)
- Examination duration (equal to credits)
- Assigned year-session time from a structured course code and name string

#### Module B — CSP Scheduling Engine
A backtracking constraint satisfaction solver assigning each course an examination slot satisfying all **hard constraints**:
- No student conflict (no two courses sharing enrolled students in the same slot)
- Year-session compliance (Year 1 → 08:00, Year 2 → 10:00, Year 3 → 13:00, Year 4 → 15:30)
- Room type matching (theory → examination halls; practical → computer/science labs)
- Room capacity (enrolled students must not exceed room capacity)
- No lecturer simultaneously invigilating two exams

#### Module C — Genetic Algorithm Optimiser
Following CSP scheduling, a GA refines the schedule to maximise the **soft constraint score**:
- Even distribution of examinations across the examination period (no overloaded days)
- Minimum gaps between consecutive examinations for the same student cohort
- Balanced staff duty loads
- Preference for morning sessions for large-cohort examinations

The fitness function is a weighted sum of all soft constraint scores.

#### Module D — Human Resource Allocator
Assigns staff to each scheduled examination based on student count and examination type.

**Ratios applied:**
- **Theory examinations:** 1 Chief Supervisor, 1 Invigilator per 30 students, 1 Hall Attendant per 60 students
- **Practical examinations:** 1 Chief Supervisor, 1 Invigilator per 15 students, 1 Technical Officer, 1 Hall Attendant per 40 students

**Hard constraints:**
- No staff member assigned to two simultaneous examinations
- No lecturer invigilation of their own course examination
- Minimum of one rest session between consecutive duties

#### Module E — Resource Calculator
Computes precise paper requirements per examination based on student count, examination type, duration, and institutional stationery specifications.

**Outputs:** Question paper copies, answer booklet count, cover sheet count, total sheets, total reams, and waste buffer (**5% for theory, 3% for practical**). Aggregated across all examinations to produce a full resource procurement report.

### 6.4 Phase 4: Web System Development

A three-role web application:

| Role | Features |
|---|---|
| **Examination Officer (Admin)** | Data upload (CSV/manual entry), schedule generation (algorithm selection: Greedy / CSP / CSP+GA), schedule calendar view, conflict report, room allocation view, staff duty roster, resource consumption report, PDF/Excel export |
| **Lecturer** | Personal invigilation duty view, examination details per assigned session |
| **Student** | Personal examination timetable view, clash complaint submission form |

**Technology stack:**
- **Backend:** Python FastAPI (REST API)
- **Frontend:** React with Tailwind CSS
- **Database & Auth:** Supabase (managed PostgreSQL, built-in authentication with Row Level Security, real-time data subscriptions, RESTful auto-generated API)
- **Visualisation:** FullCalendar.js
- **Export:** ReportLab (PDF generation), openpyxl (Excel export)

> Supabase replaces the need for a self-managed database server and provides built-in user authentication, making deployment significantly simpler and more scalable.

### 6.5 Phase 5: Evaluation

Three evaluation dimensions:

#### Algorithm Evaluation
- **Conflict rate** (target: 0 hard conflicts)
- **Room utilisation efficiency** (%)
- **Staff duty balance index** (standard deviation of duties per staff member — lower is better)
- **Paper consumption reduction** (% compared to manual estimation baseline)
- **Schedule quality score** (weighted soft constraint fitness value)

Where historical data is available, the proposed system output will be compared directly against the actual schedule produced manually.

#### Usability Evaluation
**System Usability Scale (SUS)** administered to **5 examination officers and 10 students** at USJ following task-based usability testing.

- **Target SUS score: > 70 (Good)**
- **Tasks tested:** generate a schedule, view personal timetable, download examination schedule, submit a clash complaint

#### Generalisation Evaluation
The system will be configured and run using a **second synthetic university configuration** (different department codes, credit structure, and session schedule) to demonstrate config-driven portability **without code changes**.

---

## 7. System Architecture

The proposed system follows a modern **cloud-native three-tier architecture** with a specialised scheduling engine layer:

### 🖥️ Presentation Tier
React single-page application with role-based views for Examination Officer, Lecturer, and Student. Communicates with the backend via REST API and with Supabase directly via the Supabase JavaScript client for real-time schedule updates. Responsive design supporting desktop and tablet access.

### ⚙️ Application Tier
Python FastAPI RESTful API handling business logic and orchestration of the scheduling engine. The scheduling engine runs as a **standalone Python module** invoked via internal API calls, ensuring modularity and testability. FastAPI's async support ensures efficient handling of concurrent schedule generation requests.

### 🗄️ Data Tier
**Supabase** — an open-source Firebase alternative built on PostgreSQL. Provides:
1. A **managed PostgreSQL database** with the full relational schema (`Courses`, `Enrollments`, `Rooms`, `Staff`, `ExamSlots`, `ExamSchedule`, `StaffDuties`, `ExamResources`, `ScheduleRuns`, `ConflictLog`)
2. **Built-in authentication** with Row Level Security (RLS) policies enforcing role-based data access at the database level
3. **Auto-generated REST and GraphQL APIs** for direct frontend access to non-sensitive data
4. **Real-time subscriptions** so the examination officer's dashboard updates live as a schedule generation run completes

### 🔧 Configuration Layer
A university-specific `config.json` file defining:
- Course code regex patterns
- Year-to-session mappings
- Practical keyword lists
- Invigilator ratios
- Paper calculation parameters

This enables **full generalisation without code modification**. Supabase's project-level environment variables store university-specific connection credentials, allowing the same codebase to serve multiple university deployments.

---

## 8. Expected Outcomes

This research is expected to produce:

1. ✅ A trained and validated constraint-based scheduling algorithm demonstrating **zero hard conflicts** on the evaluation dataset
2. 📊 A comparative algorithm study (**Greedy vs CSP vs CSP+GA**) providing a publishable contribution on scheduling quality trade-offs
3. 🌐 A fully functional web-based examination management system deployable at a Sri Lankan public university
4. 📉 A quantified resource optimisation report demonstrating measurable paper consumption reduction
5. 🔄 A generalised, config-driven system architecture suitable for adoption by other universities
6. 🎯 A usability-validated interface achieving a **SUS score above 70**
7. 📝 A final research thesis and, contingent on results, a conference publication targeting **ICTER or SLAAI**

---

## 9. Implementation Plan and Timeline

| Weeks | Phase | Key Activities & Milestones |
|---|---|---|
| **1–2** | Proposal & Setup | Supervisor meetings, proposal finalisation, ethics clearance application, literature search |
| **2–4** | Data Acquisition (Tier 1) | Submit formal data request to faculty; await institutional response; prepare Tier 2 form in parallel |
| **3–5** | Data Acquisition (Tier 2) | If Tier 1 delayed: distribute Google Form to students; validate and clean responses; proceed from Week 5 with collected data |
| **5** | Data Acquisition (Tier 3) | If both Tier 1 and Tier 2 insufficient: generate synthetic dataset; document rationale in methodology chapter |
| **4–6** | Analysis & Design | Requirements engineering, database schema, system architecture, Figma wireframes, user stories |
| **6–9** | Algorithm Development | Course code parser, CSP scheduling engine, GA optimiser, HR allocator, resource calculator — all with unit tests |
| **9–12** | Web System Development | Backend FastAPI setup, Supabase schema implementation and RLS policies, React frontend, role-based dashboards, PDF/Excel export |
| **12–13** | Integration & Testing | End-to-end integration testing, algorithm evaluation, conflict rate and resource metrics, SUS usability testing |
| **13–15** | Refinement | Bug fixes, usability improvements based on SUS feedback, generalisation config testing with second university profile |
| **14–16** | Report Writing | Full thesis write-up, chapter reviews with supervisor, formatting, submission preparation |

---

## 10. Resources Required

| Resource | Details |
|---|---|
| **Institutional data** | Course catalogue, enrolment counts, room inventory from USJ (Tier 1 — formal request) |
| **Survey platform** | Google Forms (free) for Tier 2 student self-reporting; Google Sheets for data collection |
| **Software (all free)** | Python 3.x, FastAPI, React, Supabase (free tier), scikit-learn (if needed), Git, VS Code, Figma (wireframes) |
| **Compute** | Personal laptop (8GB+ RAM). Google Colab for any GPU-intensive processing if required |
| **Academic access** | USJ library access to IEEE Xplore, ACM Digital Library, Scopus for literature review |
| **Supervisor access** | Bi-weekly meetings for guidance, chapter reviews, and data access facilitation |
| **Participants (HCI)** | 5 examination officers / admin staff and 10 students at USJ for usability testing (SUS) |

---

## 11. Limitations and Risks

### 11.1 Identified Risks and Mitigations

| Risk | Likelihood | Mitigation Strategy |
|---|---|---|
| **Institutional data not granted (Tier 1 fails)** | Medium | Three-tier data strategy activated; Tier 2 Google Form proceeds in parallel from Week 3 |
| **Insufficient Tier 2 survey responses** | Low-Medium | Wide distribution via WhatsApp groups, department notice boards, faculty social media; minimum 200 responses targeted |
| **Algorithm scalability for large datasets** | Low | CSP with forward checking is proven to scale to 500+ courses; GA population size capped at 100 to control runtime |
| **Staff unavailability for HCI testing** | Medium | Recruit examination officer participants early (Week 10); use students as secondary testers; minimum 5 participants acceptable |
| **Scope expansion beyond feasible timeline** | Medium | Fixed MVP feature set defined in Week 4; additional features treated as future work; supervised weekly check-ins |
| **Real-time scheduling demand exceeding prototype performance** | Low | System is a scheduling planner, not real-time; schedule generation runs offline (batch). Performance target: **<60 seconds per full schedule run** |

### 11.2 Research Limitations

The following limitations are acknowledged and will be explicitly discussed in the final thesis:

1. **Data tier dependency:** If Tier 2 or Tier 3 data is used, system evaluation is based on representative rather than actual USJ data. Results should be interpreted as **proof-of-concept validation** rather than operational deployment evidence.
2. **Stationery assumptions:** The paper consumption optimisation module assumes standard stationery specifications. Actual requirements may vary by department or examination type and would require institution-specific calibration.
3. **Course code convention:** The system is designed for universities using structured, hierarchical course codes. Universities with flat or unstructured course code conventions would require modification of the parser module.
4. **Small sample size:** Usability testing is conducted with a small participant sample (5 staff, 10 students) which, while standard for HCI research at this level, limits statistical generalisability.
5. **No system integration:** The research prototype does not include integration with existing university management systems (student information systems, LMS platforms). Full integration is identified as **future work**.
6. **GA stochasticity:** The Genetic Algorithm optimisation may produce different schedules on different runs due to stochastic initialisation. The system reports the **best result from five independent runs** to mitigate this.

---

## 12. References

1. **Abuhamdah, A.** (2010). Experimental result of late acceptance randomised descent algorithm for solving course timetabling problems. *International Journal of Computer Science and Network Security*, 10(1).
2. **Burke, E. K., Elliman, D. G., Ford, P. H., & Weare, R. F.** (2004). Examination timetabling in British universities: A survey. *Practice and Theory of Automated Timetabling*. Springer, Berlin.
3. **Deb, K.** (2001). *Multi-objective optimization using evolutionary algorithms*. Wiley.
4. **Demir, Y., & Bilge, U.** (2017). An invigilator assignment problem: A constraint programming approach. *Computers & Industrial Engineering*, 102, 1–15.
5. **Even, S., Itai, A., & Shamir, A.** (1976). On the complexity of timetable and multicommodity flow problems. *SIAM Journal of Computing*, 5(4), 691–703.
6. **Hevner, A. R., March, S. T., Park, J., & Ram, S.** (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.
7. **Kahar, M. N. M., & Kendall, G.** (2010). The examination timetabling problem at the Universiti Malaysia Pahang: Comparison of a graph colouring and a random iterative approach. *Journal of the Operational Research Society*, 61(4), 596–605.
8. **Pillay, N.** (2014). A survey of school timetabling research. *Annals of Operations Research*, 218(1), 261–293.
9. **Soria-Alcaraz, J. A., Ochoa, G., Sotelo-Figeroa, M. A., & Burke, E. K.** (2016). A methodology for determining an effective subset of heuristics in selection hyper-heuristics. *European Journal of Operational Research*, 260(3), 972–983.

---

## 13. Quick Reference — Key Design Parameters

### Examination Session Mapping (USJ)
| Year | Session Time |
|---|---|
| Year 1 | 08:00 |
| Year 2 | 10:00 |
| Year 3 | 13:00 |
| Year 4 | 15:30 |

### Invigilation Ratios
| Exam Type | Chief Supervisor | Invigilator | Other | Hall Attendant |
|---|---|---|---|---|
| **Theory** | 1 | 1 per 30 students | — | 1 per 60 students |
| **Practical** | 1 | 1 per 15 students | 1 Technical Officer | 1 per 40 students |

### Resource Waste Buffers
| Exam Type | Waste Buffer |
|---|---|
| Theory | 5% |
| Practical | 3% |

### Performance Target
- Full schedule generation: **< 60 seconds**
- Hard conflicts: **0 (zero)**
- SUS target: **> 70 (Good)**
- GA runs reported: **best of 5 independent runs**

---

## 14. Repository / Project Structure (Planned)

```
exam-scheduling-system/
├── backend/
│   ├── api/                  # FastAPI route handlers
│   ├── core/                 # Config, security, dependencies
│   ├── engine/
│   │   ├── parser.py         # Module A — Course Code Parser
│   │   ├── csp_solver.py     # Module B — CSP Scheduling Engine
│   │   ├── ga_optimiser.py   # Module C — Genetic Algorithm Optimiser
│   │   ├── hr_allocator.py   # Module D — Human Resource Allocator
│   │   └── resource_calc.py  # Module E — Resource Calculator
│   ├── models/               # SQLAlchemy / Pydantic models
│   ├── tests/                # Unit + integration tests
│   └── config.json           # University-specific configuration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── admin/        # Examination Officer dashboard
│   │   │   ├── lecturer/     # Lecturer duty view
│   │   │   └── student/      # Student timetable view
│   │   └── lib/              # Supabase client, API helpers
│   └── public/
├── supabase/
│   ├── migrations/           # SQL schema migrations
│   └── policies/             # Row Level Security policies
├── data/
│   ├── tier1/                # Institutional data (if granted)
│   ├── tier2/                # Survey responses
│   └── tier3/                # Synthetic datasets
├── docs/
│   ├── wireframes/
│   ├── er-diagrams/
│   └── thesis/
└── README.md
```

---

## 15. Glossary

| Term | Definition |
|---|---|
| **CSP** | Constraint Satisfaction Problem — a mathematical problem defined by variables, domains, and constraints |
| **GA** | Genetic Algorithm — a metaheuristic optimisation technique inspired by natural selection |
| **DSR** | Design Science Research — a research paradigm emphasising artefact creation and evaluation |
| **SUS** | System Usability Scale — a standardised 10-item questionnaire for measuring usability |
| **RLS** | Row Level Security — PostgreSQL feature enforcing access control at the row level |
| **3NF** | Third Normal Form — a database normalisation standard eliminating transitive dependencies |
| **Hard constraint** | A constraint that must not be violated (e.g., no student conflicts) |
| **Soft constraint** | A constraint that should be satisfied where possible (e.g., balanced staff duties) |
| **USJ** | University of Sri Jayewardenepura |
| **HEI** | Higher Education Institution |
| **ICTER** | International Conference on Technology for Education (target venue) |
| **SLAAI** | Sri Lanka Association for Artificial Intelligence (target venue) |

---

> **Document Status:** Research Proposal v2 — Submitted 30 May 2026
> **Next Steps:** Supervisor review → Ethics clearance → Phase 1 data acquisition begins Week 1–2
> **Contact:** A.B.Z. Hussain (Index: AS2022468), Department of Computer Science, Faculty of Computing, University of Sri Jayewardenepura

---

*This README is a faithful reconstruction of the research proposal content for repository documentation purposes. All sections, tables, parameters, and references from the original document are preserved.*