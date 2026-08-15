# Basilisk Master Curriculum Roadmap

**Status:** Private planning reference — Version 1.0 (August 2026)

**Subtitle:** From foundational Python reasoning to data and ML literacy — culminating in Build the Basilisk

> **Course identity:** Basilisk is a programming course first. Lore supplies continuity and meaning, but competence, retention, debugging, and independent problem solving outrank story, badges, or streaks.

This document is the long-horizon curriculum architecture for Basilisk. Detailed Phase 2 lesson specs remain in `docs/phase2-curriculum-plan.md`. Engagement and retention principles remain in `docs/engagement-retention-design.md`.

## Executive Decisions

> **Primary learner target:** A learner who can reason through Python, read and modify notebooks, manipulate data with standard libraries, follow introductory training and evaluation code, and independently build the integrated Basilisk capstone. The target is not professional software-engineering readiness or full machine-learning theory.

- Lessons 1-28 remain the committed programming foundation. OOP is one section, not the course identity.

- Practical Python, files, parsing, exceptions, modules, and testing must come before scientific libraries.

- Notebook execution and array/data-table mental models must come before ML workflows.

- ML instruction focuses on code literacy, data flow, evaluation, reproducibility, and common mistakes - not replacing mathematics or statistics courses.

- The final capstone begins as tested core logic. Persistence and GUI work are attached only after the command-line system works.

- Future lesson numbers are provisional until the Phase 2 beginner pilot; the dependency order is the commitment.

## Status Legend

| **Status**        | **Meaning**                                      | **Planning rule**                                                   |
|-------------------|--------------------------------------------------|---------------------------------------------------------------------|
| Implemented       | Present on the current curriculum path           | Preserve IDs and review changes for regressions                     |
| Active batch      | Specified and ready for Cursor implementation    | Review implementation against its contract                          |
| Approved sequence | Topic order and outcomes accepted                | Develop in bounded batches before coding                            |
| Provisional       | Master-map direction, not final lesson copy      | Validate prerequisites and pilot results before assigning final IDs |
| Optional          | Useful enrichment outside the required exit path | Never block core progression                                        |

## Course Architecture at a Glance

| **\#** | **Phase**                     | **Range**              | **Core work**                                                           | **Exit performance**                               |
|--------|-------------------------------|------------------------|-------------------------------------------------------------------------|----------------------------------------------------|
| 1      | Foundations                   | Lessons 1-8            | Output, values, decisions, lists, loops, functions                      | Build a small working Python tool                  |
| 2      | Reasoning and models          | Lessons 9-28           | Deeper control, nested data, debugging, references, basic OOP           | Build and debug a small composed program           |
| 3      | Practical Python and Archives | Provisional            | Fluency, exceptions, files, parsing, modules, testing                   | Turn messy records into dependable structured data |
| 4      | Notebooks and data analysis   | Provisional            | Jupyter, NumPy, pandas, visualization                                   | Analyze and explain an expedition dataset          |
| 5      | ML code literacy              | Provisional            | Splits, preprocessing, fit/predict, metrics, leakage                    | Read and modify an introductory ML workflow        |
| 6      | Build the Basilisk            | Provisional milestones | Game state, composition, selective inheritance, persistence, tests, GUI | Deliver a complete integrated capstone             |

# 1. Learner Promise and Scope

## The promised exit ability

- Read ordinary Python and trace how values move through a program.

- Write useful scripts using functions, collections, files, exceptions, and modules.

- Debug syntax, runtime, logical, state, shape, and data-quality problems.

- Read and modify Jupyter notebooks without being confused by cell state or execution order.

- Use NumPy and pandas to load, clean, transform, summarize, and visualize data.

- Follow an introductory scikit-learn workflow from features and targets through evaluation.

- Design a modest multi-object application using composition and selective inheritance.

- Test, save, load, and present the final Basilisk encounter.

## What the course does not claim

Completion should not be advertised as professional software-engineering readiness, data-scientist qualification, or mastery of machine-learning mathematics. Basilisk creates a durable programming foundation and the code literacy needed to enter those fields intelligently.

- Advanced algorithms and formal complexity analysis

- Production databases, distributed systems, deployment, security engineering, or cloud operations

- Deep metaprogramming, descriptors, metaclasses, or complex decorator construction

- Advanced asynchronous and concurrent programming

- Full statistical learning theory, calculus, or linear-algebra instruction

- A web-development framework track

## Required versus optional breadth

| **Required core**                                       | **Required for target**                               | **Optional enrichment**                                 |
|---------------------------------------------------------|-------------------------------------------------------|---------------------------------------------------------|
| Python reasoning, data structures, functions, debugging | Notebooks, NumPy, pandas, plots, ML workflow literacy | Live web scraping, SQL companion track                  |
| Exceptions, files, JSON/CSV, modules, tests             | Reproducibility, leakage awareness, metrics           | Generators in depth, advanced dunder methods            |
| Basic classes, methods, references, composition         | Ability to use object-oriented library APIs           | Deep inheritance hierarchies, advanced GUI architecture |

# 2. Teaching and Learning Operating System

> **Central rule:** The course must teach programming reasoning, not merely expose learners to Python syntax.

| **Rule**                       | **Authoring implication**                                                                                                             |
|--------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| One major new idea             | A lesson may use related syntax, but its cognitive center must be clear. Retrieve no more than two meaningful prior concepts at once. |
| Read before blank-page writing | Use worked examples, prediction, and debugging before independent construction.                                                       |
| Fade scaffolding               | Move from recognition and guided repair toward low-scaffold building within each lesson and across the course.                        |
| Retrieve across distance       | Reuse earlier skills two or more lessons later without re-teaching them. Retrieval should advance the current problem.                |
| Debug everywhere               | Every phase includes real failures and wrong outputs. Observe, form a hypothesis, change one thing, run, and evaluate.                |
| Behavior first                 | Grade observable behavior. Require exact constructs only when the construct is the learning objective.                                |
| Transfer matters               | Each batch includes at least one context shift so competence is not trapped inside Expedition vocabulary.                             |
| Capstones integrate            | A capstone introduces no major new syntax. It combines already-practiced capabilities under reduced scaffolding.                      |
| Hints support learning         | Hints progress from concept to structure to near-solution. Asking for help is diagnostic, not punitive.                               |
| Pilot before expansion         | A real beginner pass, delayed retrieval check, and manual interface review are required before locking the next phase.                |

## Standard lesson rhythm

1.  Observe or recall: connect the new capability to a familiar program state.

2.  Predict: mentally execute a small example before running it.

3.  Investigate or repair: identify what changed, failed, or produced the wrong result.

4.  Apply: complete a guided implementation with focused feedback.

5.  Build: solve a more independent task using the new idea and retrieved skills.

6.  Retrieve later: reuse the concept in a different lesson and, periodically, a different context.

## Evidence of learning

A green check proves that submitted code met an assessment contract. It does not by itself prove durable understanding. Course-level claims require multiple signals:

- Correct prediction or trace before relying on Run

- Behavior that generalizes across hidden and non-obvious cases

- Successful debugging with progressively limited help

- A transfer task in a different surface context

- Delayed retrieval after intervening lessons or a later session

- Independent capstone integration and explanation of design choices

# 3. Committed Curriculum: Lessons 1-28

> **Boundary:** This section records the accepted curriculum architecture. Lessons 1-18 are implemented, Lessons 19-28 have an approved sequence that still requires detailed batch specifications.

**PHASE 1 - LESSONS 1-8**

# Expedition 17: Programming Foundations

**Status: Implemented - 28 exercises**

> **Phase promise:** I can combine output, stored data, decisions, collections, repetition, and a function into a small working Python tool.

| **Lesson** | **Title**                   | **Concept center**         | **Why it exists**                                         |
|------------|-----------------------------|----------------------------|-----------------------------------------------------------|
| 1          | Leave a Trace               | print(), strings, comments | Programs execute in order and can reveal what they did.   |
| 2          | Store the Record            | Variables and expressions  | Programs can remember and transform values.               |
| 3          | Assemble the Report         | f-strings                  | Stored values can become readable, dynamic output.        |
| 4          | Make a Decision             | if/else and comparisons    | Program behavior can depend on data.                      |
| 5          | Organize the Expedition     | Lists and indexing         | Related values can be modeled as one collection.          |
| 6          | Record New Evidence         | append() and mutation      | Collections can change while a program runs.              |
| 7          | Search Every Entry          | for loops                  | One instruction pattern can process an entire collection. |
| 8          | Build an Investigation Tool | Functions and return       | Behavior can be named, reused, tested, and composed.      |

*Narrative role: Expedition 17 appears through records, names, and evidence. The learner never needs lore knowledge to solve a programming problem.*

**PHASE 2A - LESSONS 9-13**

# Expedition Intake: Deeper Decisions and Collections

**Status: Implemented - 26 exercises; 54 cumulative**

> **Phase promise:** I can model an expedition record, update its collections, and make realistic decisions using several conditions.

| **Lesson** | **Title**                              | **Concept center**          | **Why it exists**                                                 |
|------------|----------------------------------------|-----------------------------|-------------------------------------------------------------------|
| 9          | More Than Two Paths                    | elif and ordered branches   | Real decisions often have more than two outcomes.                 |
| 10         | Decisions With More Than One Condition | and, or, not                | A decision can depend on the whole situation.                     |
| 11         | Count What You Have                    | len(), range(), boundaries  | Collection sizes and repetition counts introduce index reasoning. |
| 12         | Lists That Change                      | membership, remove(), pop() | Learners manage changing data rather than only adding to it.      |
| 13         | One Record, Many Facts                 | Dictionaries                | Labeled data replaces fragile parallel variables and lists.       |

**PHASE 2B - LESSONS 14-18**

# Expedition Dispatch: Repetition and Structured Functions

**Status: Implemented - 25 exercises (Issue #18)**

> **Phase promise:** I can process complete records, write terminating condition-driven loops, design flexible functions, and return fresh structured results.

| **Lesson** | **Title**                          | **Concept center**                     | **Why it exists**                                                           |
|------------|------------------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| 14         | Read the Whole Ledger              | Dictionary iteration, .items(), .get() | Learners move from creating a record to safely processing the whole record. |
| 15         | Repeat Until the Condition Changes | while, progress, termination           | Condition-driven repetition must be understood before stateful systems.     |
| 16         | Give a Function the Full Situation | Multiple parameters and argument order | Useful functions need enough explicit input to make a complete decision.    |
| 17         | Defaults for the Common Case       | Default and keyword arguments          | Function interfaces can be convenient without hiding their inputs.          |
| 18         | Return a Whole Dispatch            | Lists/dicts as results, copying inputs | Functions begin producing structured data for later program stages.         |

> **Review watchpoint:** Lesson 15 must explain that for is usually clearer for simply visiting a known collection. Lesson 18 should teach copying through observable caller-preservation behavior without requiring formal alias terminology before Lesson 24.

**PHASE 2C - LESSONS 19-23**

# Realistic Data and Debugging

**Status: Approved sequence - detailed specifications pending**

> **Phase promise:** I can navigate nested data, reason about scope, normalize text, read tracebacks, and systematically repair logic errors.

| **Lesson** | **Title**          | **Concept center**                                                         | **Why it exists**                                                               |
|------------|--------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| 19         | Nested Data        | Lists of dictionaries, dictionaries containing lists, enumerate in context | Real records combine smaller structures; this bridges data modeling to objects. |
| 20         | Scope              | Local and global names; prefer return over global mutation                 | Learners must know where values live before programs become larger.             |
| 21         | String Methods     | strip(), lower(), split(), immutability                                    | Text normalization prepares parsing and robust comparisons.                     |
| 22         | Reading Tracebacks | Syntax and runtime error families                                          | Learners need a method for reading failures rather than fearing them.           |
| 23         | Logic Debugging    | Tracing wrong output and testing assumptions                               | Many important bugs do not crash; they must be found by reasoning.              |

**PHASE 2D - LESSONS 24-28**

# References, Objects, and Composition

**Status: Approved sequence - detailed specifications pending**

> **Phase promise:** I can predict shared mutable state and construct a small multi-object program using classes, methods, and has-a composition.

| **Lesson** | **Title**             | **Concept center**                                  | **Why it exists**                                                                             |
|------------|-----------------------|-----------------------------------------------------|-----------------------------------------------------------------------------------------------|
| 24         | Shared References     | Aliasing, mutation versus rebinding, shallow copies | The memory model is taught before classes so object state is not magical.                     |
| 25         | Classes and Objects   | Blueprint versus instance; attributes               | Objects become another way to organize related state.                                         |
| 26         | \_\_init\_\_ and self | Initialization and independent instance containers  | Each object receives explicit, safe initial state.                                            |
| 27         | Methods               | Behavior that reads and changes instance state      | Functions and state are combined intentionally.                                               |
| 28         | Composition Capstone  | Character has inventory; Party has members          | Previously learned concepts are organized into a small program; inheritance remains deferred. |

> **Phase 2 exit level:** Strong beginner approaching early-intermediate Python: able to build and debug small multi-function and multi-object scripts. Not yet ready to claim file, library, notebook, data-analysis, or ML workflow competence.

# 4. Provisional Phase 3: Practical Python and Expedition Archives

This phase is required. It closes the gap between lesson-controlled Python and ordinary scripts that interact with files, external libraries, and imperfect data. Final global lesson numbers should be assigned only after the Phase 2 pilot.

> **Phase promise:** I can organize a dependable Python script that reads imperfect records, validates and parses them, writes structured results, and proves important behavior with tests.

| **Unit** | **Capability**                               | **Core content**                                            | **Why now**                                                  |
|----------|----------------------------------------------|-------------------------------------------------------------|--------------------------------------------------------------|
| P3.1     | Slicing and unpacking                        | Subsequences, first/rest patterns, multiple assignment      | Common Python fluency used throughout data code              |
| P3.2     | Tuples and sets                              | Fixed records, uniqueness, membership, set operations       | Select a structure by behavior rather than habit             |
| P3.3     | Comprehensions                               | Transform and filter lists/dicts/sets                       | Read compact idiomatic Python after loop reasoning is secure |
| P3.4     | Iteration tools and sorting                  | zip(), sorted(), key functions, limited lambda              | Coordinate data and control ordering explicitly              |
| P3.5     | None, optional values, and type hints        | Missing values, sentinel patterns, readable signatures      | Prepare real APIs and safer function contracts               |
| P3.6     | Imports, modules, packages, and environments | import, module boundaries, pip/venv concepts, documentation | Use libraries without treating them as magic                 |
| P3.7     | Exceptions and validation                    | try/except, raising errors, useful messages                 | Handle expected failure without hiding bugs                  |
| P3.8     | Paths, files, and context managers           | pathlib, with open, encodings                               | Read and write durable data safely                           |
| P3.9     | Parsing semi-structured logs                 | Tokenization, normalization, field extraction               | Turn adventurer prose-like records into data                 |
| P3.10    | CSV records                                  | csv module, headers, types, malformed rows                  | Work with common tabular exchange data                       |
| P3.11    | JSON archives                                | Nested serialization, schema expectations                   | Persist structured findings and game configuration           |
| P3.12    | HTML records                                 | DOM structure and supplied offline pages                    | Teach scraping mechanics without network instability         |
| P3.13    | Assertions and automated tests               | Normal, edge, malformed, and regression cases               | Make correctness repeatable                                  |
| P3.C     | Expedition Archive Analyzer                  | Files + parsing + validation + JSON + tests                 | Integrate the phase without introducing new syntax           |

## Optional responsible retrieval extension

Live HTTP retrieval and web scraping should be optional enrichment after deterministic local HTML. It must cover status codes, timeouts, rate limits, site terms, robots guidance, attribution, and the fact that page structure changes. Core progress must never depend on an external website remaining available.

# 5. Provisional Phase 4: Notebooks and Data Analysis

> **Phase promise:** I can open an unfamiliar notebook, restore a trustworthy execution state, inspect data shapes and types, clean and transform a dataset, calculate summaries, and create an honest visualization.

| **Unit** | **Capability**                         | **Core content**                                                    | **Why now**                                                |
|----------|----------------------------------------|---------------------------------------------------------------------|------------------------------------------------------------|
| P4.1     | Notebook mental model                  | Cells, state, execution order, restart/run-all, Markdown            | Notebook behavior must be understood before library work   |
| P4.2     | NumPy arrays                           | shape, ndim, dtype, array construction                              | ML data is organized by dimensions and types               |
| P4.3     | Indexing, slicing, and masks           | Rows, columns, boolean selection                                    | Select data without procedural loops                       |
| P4.4     | Vectorization and broadcasting         | Element-wise operations and compatible shapes                       | Read efficient scientific Python and diagnose shape errors |
| P4.5     | Axes, aggregation, and reproducibility | sum/mean by axis, random generators and seeds                       | Understand summaries and repeatable experiments            |
| P4.6     | Series and DataFrames                  | Labels, columns, indexes, object methods                            | Move from arrays to labeled tabular data                   |
| P4.7     | Load, inspect, and select              | read_csv, head, info, columns, loc/iloc                             | Establish a disciplined first look at data                 |
| P4.8     | Filter, sort, and derive               | Boolean filters, sort_values, new columns                           | Answer questions and construct useful features             |
| P4.9     | Missing values and types               | isna, fill/drop choices, conversion                                 | Prevent silent analytical errors                           |
| P4.10    | Group, aggregate, and combine          | groupby, summaries, merge                                           | Move from individual records to evidence                   |
| P4.11    | Visualization                          | Matplotlib/Seaborn basics, labels, scales, distributions            | Inspect patterns and communicate findings responsibly      |
| P4.C     | Basilisk Research Notebook             | Clean and analyze expedition outcomes; export basilisk_profile.json | Create a data artifact used by the final capstone          |

## Data-analysis habits assessed throughout

> **Why these habits matter:** Analytical fluency is not merely knowing method names. The learner must establish a trustworthy starting state, make transformation choices explicit, and distinguish observed evidence from interpretation.

- Inspect shape, columns, types, and missingness before transformation.

- Preserve raw data and make transformations explicit and repeatable.

- Label charts and choose a view that matches the question.

- Distinguish an observed pattern from a causal claim.

- Restart and run the notebook from top to bottom before submission.

# 6. Provisional Phase 5: Machine-Learning Code Literacy

This phase prepares learners to understand and modify introductory coursework. It deliberately avoids claiming to replace statistics, linear algebra, or a full ML class.

> **Phase promise:** I can trace an introductory supervised-learning workflow, explain where data enters and changes, modify common parameters, evaluate predictions, and identify obvious leakage or reproducibility problems.

| **Unit** | **Capability**                      | **Core content**                                             | **Why now**                                         |
|----------|-------------------------------------|--------------------------------------------------------------|-----------------------------------------------------|
| P5.1     | Features, targets, and task framing | X/y, rows/columns, classification versus regression          | Connect code objects to the prediction question     |
| P5.2     | Train/validation/test separation    | Splitting before learning from data                          | Protect evaluation from contamination               |
| P5.3     | Preprocessing                       | Scaling, encoding, imputation concepts                       | Prepare data without hand-waving transformations    |
| P5.4     | Estimator interface                 | Construct, fit, predict, inspect parameters                  | Use object-oriented library APIs confidently        |
| P5.5     | Metrics and baselines               | Accuracy plus task-appropriate alternatives                  | A model result needs a meaningful comparison        |
| P5.6     | Overfitting and leakage             | Train versus test behavior, forbidden information            | Recognize misleading success                        |
| P5.7     | Pipelines and reproducibility       | Repeatable preprocessing/model chains, random_state          | Reduce accidental mismatch and hidden state         |
| P5.8     | Read and modify a training script   | Trace imports, data, transformations, model, metrics         | Demonstrate code literacy in an unfamiliar workflow |
| P5.C     | Expedition Risk Model               | Predict a defined expedition outcome and explain limitations | Integrate the phase and export a documented result  |

> **Assessment honesty:** Passing this phase means the learner can follow and modify introductory ML code. It does not mean they can select any model for any domain, prove statistical validity, or deploy a production system.

# 7. Final Integration: Build the Basilisk

The capstone is a sequence of project milestones, not one giant blank-page exercise. Every milestone must remain runnable, tested, and explainable. The learner builds the system; the course does not hand over large completed class definitions.

> **Capstone promise:** I can turn requirements and data artifacts into a tested, persistent, multi-object application with a working command-line experience and an attached graphical presentation layer.

| **Milestone** | **Build step**                | **Required result**                                                              | **Capabilities integrated**             |
|---------------|-------------------------------|----------------------------------------------------------------------------------|-----------------------------------------|
| M1            | Read the battle specification | Identify state, responsibilities, inputs, outputs, and invariants                | Planning and decomposition              |
| M2            | Build the domain model        | Hero, Basilisk, Ability, Item, Status, Party through composition                 | Classes, references, composition        |
| M3            | Use inheritance selectively   | Hero subclasses only where a genuine is-a relationship and shared behavior exist | Inheritance, super(), polymorphism      |
| M4            | Create the turn engine        | Turn order, actions, targeting, victory/defeat, boss phases                      | Loops, state machines, functions        |
| M5            | Add interacting systems       | Randomness, status effects, environmental hazards, resource rules                | Probability, mutation, compound logic   |
| M6            | Integrate research artifacts  | Load basilisk_profile.json and documented analysis outputs                       | Files, JSON, validation, provenance     |
| M7            | Protect and prove behavior    | Custom errors where useful, unit/regression tests, deterministic seeded cases    | Exceptions, tests, reproducibility      |
| M8            | Deliver a command-line battle | Complete playable encounter with clear state and feedback                        | End-to-end integration                  |
| M9            | Attach the GUI                | Event-driven interface that calls the existing engine rather than duplicating it | Separation of logic and presentation    |
| M10           | Final defense and reflection  | Explain architecture, tradeoffs, bugs fixed, tests, and next improvements        | Metacognition and independent ownership |

## How the full course converges

| **Source** | **Knowledge brought forward**                                | **Capstone use**                                              |
|------------|--------------------------------------------------------------|---------------------------------------------------------------|
| Phase 1-2  | Variables, decisions, loops, collections, functions, objects | Combat rules, party state, actions, and methods               |
| Phase 3    | Files, parsing, JSON, exceptions, tests                      | Archive import, configuration, saves, and dependable behavior |
| Phase 4    | NumPy, pandas, visualization                                 | Research notebook and evidence-based Basilisk profile         |
| Phase 5    | ML workflow literacy                                         | Optional documented expedition-risk prediction artifact       |
| Capstone   | Architecture, inheritance, state, randomness, GUI            | The complete playable and explainable encounter               |

# 8. Learner Levels at Major Checkpoints

| **Checkpoint**  | **Honest level**                               | **Can reliably do**                                                                                 | **Still not claimed**                                       |
|-----------------|------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| After Lesson 8  | Foundational beginner                          | Build a small function-based script using output, decisions, lists, and loops                       | Nested data, files, errors, classes, libraries              |
| After Lesson 18 | Developing beginner                            | Process dictionaries, write terminating loops, design flexible functions, return structured results | Nested traversal, systematic debugging, references, classes |
| After Lesson 28 | Strong beginner / early-intermediate bridge    | Build and debug a small composed multi-object program                                               | Files, modules, testing, notebooks, data libraries          |
| After Phase 3   | Practical Python beginner                      | Write dependable scripts that parse and persist real records                                        | Scientific arrays, DataFrames, ML workflows                 |
| After Phase 4   | Beginning data analyst in Python               | Clean, summarize, combine, and visualize a dataset in a reproducible notebook                       | Model training and evaluation literacy                      |
| After Phase 5   | ML-code literate beginner                      | Trace and modify an introductory supervised-learning workflow                                       | Independent model selection and advanced theory             |
| After capstone  | Practical early-intermediate Python programmer | Design, test, debug, persist, and present a modest integrated application                           | Professional engineering breadth and production systems     |

# 9. Assessment Architecture

## Within each lesson

- A low-scaffold trace, recognition, or retrieval task first

- A guided application or repair task

- At least one predict, debug, or architecture decision

- A final task requiring the most independent construction

- Three progressive hints for every runnable task

- Behavioral cases including at least one non-obvious input

- Learner-facing failure messages that name the failed behavior

## At each batch gate

| **Gate**             | **Evidence required**                                                                  |
|----------------------|----------------------------------------------------------------------------------------|
| Reference validity   | All official solutions pass; alternative valid approaches remain accepted              |
| Bypass resistance    | Hardcoding and dummy constructs fail without turning hidden tests into arbitrary traps |
| Learning loop        | Run, fail, feedback, hints, fix, pass, unlock, restart, and restored progress all work |
| Transfer             | At least one task changes context while preserving the same capability                 |
| Retention            | A prior concept reappears after spacing; later pilot includes delayed recall           |
| Platform             | Automated suite, Windows-native CI, and human Windows visual QA pass                   |
| Beginner observation | At least one learner-facing pass records confusion, attempts, hint use, and time       |

## Mastery claims

Completion and mastery must remain distinct. A lesson can unlock after correct work, while course reporting should use capability statements and qualitative bands rather than false-precision percentages. Hints inform support needs; they do not punish the learner.

# 10. Plan of Action

> **Ownership:** Cursor implements, merges, and closes completed GitHub work. ChatGPT independently reviews curriculum, implementation, tests, CI, and learner experience, filing a consolidated defect issue only when confirmed problems exist.

| **Step** | **Action**                                    | **Scope**                                                        | **Exit condition**                                  |
|----------|-----------------------------------------------|------------------------------------------------------------------|-----------------------------------------------------|
| 1        | Complete Lessons 14-18                        | Issue \#18 implementation from current main                      | 18 lessons / 79 exercises; full CI and learner pass |
| 2        | Independent Batch 2 review                    | Pedagogy, validator scope, bypass tests, Windows CI              | Ready/not-ready judgment without merging            |
| 3        | Design Lessons 19-23                          | Nested data through logic debugging                              | One bounded implementation contract                 |
| 4        | Pilot gate                                    | Manual beginner pass plus neutral transfer and delayed retrieval | Corrections before OOP work                         |
| 5        | Design Lessons 24-28                          | References through composition capstone                          | Second bounded implementation contract              |
| 6        | Validate Phase 2                              | Complete learner pilot, Windows visual QA, capstone review       | Evidence that the foundation works                  |
| 7        | Freeze Phase 3 architecture                   | Reconcile future map with pilot evidence and engine needs        | Final Phase 3 IDs, batch sizes, and prerequisites   |
| 8        | Implement future phases in 4-6 lesson batches | Curriculum first, minimal reusable engine work second            | Controlled scope and reviewable PRs                 |
| 9        | Build capstone by milestones                  | CLI core before persistence and GUI                              | A runnable, tested program at every step            |

## Decisions deliberately deferred

- Exact future global lesson numbers and exercise counts

- Final GUI toolkit choice

- Whether the live-scraping extension is enabled by default

- The precise testing framework after assertions are taught

- Whether SQL becomes a separate companion track

- Whether the ML capstone prediction is required for all learners or a target-specific extension

## Do not do next

- Do not implement Lessons 19-28 inside the Lessons 14-18 pull request.

- Do not build notebook, NumPy, pandas, ML, or GUI systems before the corresponding curriculum contract exists.

- Do not force every Python feature into the course merely because Python supports it.

- Do not let the RPG project displace the learner's data and ML code-literacy target.

- Do not claim mastery from catalog completion alone.

# 11. Definition of Ready for Any Future Curriculum Batch

- The batch has one sentence explaining why it must occur at this point in the dependency chain.

- Every lesson has one learner-facing capability statement.

- Prerequisites are already taught and explicitly listed.

- Each lesson introduces one major concept cluster and retrieves no more than two substantial prior concepts.

- Exercise order moves from trace/recognition toward independent construction.

- Examples teach the shape without duplicating exercise solutions.

- Behavior matrices include normal, boundary, and non-obvious cases implied by the prompt.

- Source checks protect only the construct being taught and are scoped against dummy constructs.

- Every failure message tells the learner what behavior failed without giving away the solution.

- The batch contains a transfer task and a later retrieval plan.

- Any engine or UI prerequisite is reusable and narrowly justified.

- Automated tests, Windows CI, manual learner flow, and saved-progress behavior have acceptance criteria.

- The lore budget is explicit: names, data, and short consequences, never required exposition.

- The batch ends with a measurable exit performance rather than a list of syntax seen.

# 12. Governing References

**Internal Basilisk sources**

- `docs/phase2-curriculum-plan.md` — committed Lessons 9–28 sequence and exit criteria

- `docs/engagement-retention-design.md` — retrieval, debugging, hints, exposure budget, and capstone rules

- Pedagogy Rules — sequencing, cognitive load, reasoning, OOP, and feedback

- Exercise Quality Rules — behavioral grading, hidden tests, hints, and regression standards

- Testing Standards — learning loop, platform behavior, timeouts, GUI, and progress persistence

**External teaching references**

- Sentance, Waite, and Kallia - Teaching computer programming with PRIMM: Predict, Run, Investigate, Modify, Make.

- Roediger and Karpicke (2006) - retrieval practice and long-term retention.

- Shin, Jung, Zumbach, and Yi (2023) - faded worked examples and metacognitive scaffolding in Python problem solving.

> **Final roadmap decision:** Proceed with the committed Lessons 14-28 plan, validate the entire foundation with real learner evidence, then freeze and implement the Practical Python -\> Data Analysis -\> ML Literacy sequence before the milestone-based Build the Basilisk capstone.
