# Adding lessons

Drop a new `*.json` file in this directory and restart the app.
`CourseCatalog` loads every JSON file automatically — no GUI changes needed.

Minimum fields:

- `id` (unique)
- `section`
- `section_order` (integer; lower sorts earlier)
- `order` (integer within the section)
- `title`
- `content`
- `exercises` (array; may be empty)

Useful optional fields: `topics`, `concepts`, `examples`, `common_mistakes`.

Exercise checks use `tests` with kinds such as:

- `stdout_equals` / `stdout_contains`
- `globals` (`name`, optional `type_name`, optional `expected`)
- `function` (`function`, `args`, `kwargs`, `expected`)
- `expression` / `attribute`
- `class_defined`
- `raises`
- `runs_successfully`
- `source_uses` when the *construct* is the learning objective:
  - `feature`: `fstring`, `binop_names`, `rebind_self`, `append_or_extend`, `subscript`, `comment`, `if_statement`, `for_loop`, `elif_branch`
  - optional `name` / `names` to require specific variables

Prefer behavior checks over comparing source text. Use `source_uses` only when a hardcoded result would otherwise pass.

Optional import control (defaults to no imports):

```json
"allowed_modules": ["math"]
```

Only curated curriculum modules can be enabled. See `engine/import_policy.py`.
