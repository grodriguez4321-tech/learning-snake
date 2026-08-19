# Basilisk V3.2 Production Curriculum Handoff

This branch is a **source-only handoff branch** for the canonical Basilisk V3.2 production curriculum. It is not an implementation PR and should not be merged directly.

Authority:

- Curriculum revision: **3.2**
- Core scope: **28 lessons / 214 learner interactions**
- Project spine: **23 multi-concept project tasks**
- Every exercise has three progressive hints; every runnable exercise has a reference solution and grader contract.
- Curriculum is Python-first. Lore supports examples/data and never replaces the programming explanation.

Integration policy:

1. Cursor owns the implementation branch, code changes, test updates, PR, and CI.
2. Materialize the staged production lesson JSON exactly unless an incompatibility with the real app is demonstrated.
3. Do not silently rewrite pedagogy, reduce exercise counts, weaken projects, or substitute the older Lessons 19–28 specifications.
4. Preserve the V3.2 lesson sequence and section/order metadata because `CourseCatalog` sorts by `(section_order, order, id)`.
5. Treat the existing older curriculum PR #25 and Issues #24/#29 as superseded for curriculum content by the V3.2 replacement. Do not merge those old lesson branches into this work.
6. PR #36 is a separate UI redesign and must not be edited from the curriculum integration branch. Rebase the final curriculum PR onto the then-current `main` after any approved PR #36 merge and rerun all UI/learner-loop tests.
7. Keep the integration PR draft and unmerged until independent review and owner Windows/manual QA.

Batches will be staged under this directory as exact production JSON source. The integration issue is the binding implementation contract.
