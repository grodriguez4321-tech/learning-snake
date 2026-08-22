# Basilisk V3.2 — Remaining 20 Production Lessons

This bundle contains the exact production JSON for Lessons 9–28. Do not rewrite, regenerate, or infer curriculum content from older lessons.

## Reconstruct

From `docs/curriculum-v3.2-handoff/source_bundle/`:

```bash
cat remaining20.production.tar.xz.b64.part0* | base64 -d > remaining20.production.tar.xz
sha256sum remaining20.production.tar.xz
tar -xJf remaining20.production.tar.xz
```

Expected SHA-256:

`9053839e712bbbf7021c6243ea23d44c4f8e2b794a1bccf2697e0140fdba0ed6`

The archive expands to `course/lessons/` and contains exactly these 20 files:

- `decisions_09_elif.json`
- `decisions_10_boolean_logic.json`
- `collections_11_len_range.json`
- `collections_12_list_methods.json`
- `collections_13_dictionaries.json`
- `collections_14_dict_iteration.json`
- `collections_15_while.json`
- `functions_16_parameters.json`
- `functions_17_defaults.json`
- `functions_18_returning_data.json`
- `collections_19_nested_data.json`
- `functions_20_scope.json`
- `strings_21_methods.json`
- `errors_22_tracebacks.json`
- `errors_23_logic_debugging.json`
- `data_24_shared_references.json`
- `oop_25_classes_objects.json`
- `oop_26_init_self.json`
- `oop_27_methods.json`
- `oop_28_composition.json`

Together with the eight direct lesson JSON files already staged under `docs/curriculum-v3.2-handoff/course/lessons/`, this supplies the full 28-lesson V3.2 production curriculum source.

Integration rule: materialize/copy these JSON files exactly onto the integration branch, preserve their contents and ordering metadata, then run the real application/test suite against them. Curriculum edits require explicit review rather than silent reconstruction.
