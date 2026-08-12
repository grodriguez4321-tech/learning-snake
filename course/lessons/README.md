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

Prefer behavior checks over comparing source text.
