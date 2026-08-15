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
  - `feature`: `fstring`, `binop_names`, `rebind_self`, `append_or_extend`, `append_call`, `remove_call`, `pop_call`, `len_call`, `boolean_and`, `boolean_or`, `unary_not`, `subscript`, `comment`, `if_statement`, `for_loop`, `while_loop`, `elif_branch`, `calls_name`, `print_names`, `print_min_calls`, `range_call`, `compares_names`, `method_call`, `function_signature`, `forbidden_call`
  - optional `name` / `names` to require specific variables
  - optional `ops` for comparison operators (`Lt`, `Eq`, …)
  - optional `in_function` to scope the check to one function body
  - optional `inside` (e.g. `"for_loop"` / `"while_loop"` for `calls_name` or `rebind_self`; `"for_iter"` for `method_call`) so a dummy construct elsewhere cannot pass
  - `method_call`: required `method`; optional `name` (receiver), `min_args`, `arg_equals`, `contributes` (`true`/`result`/`return`), `body_calls_name` / `body_method` (with `inside: "for_iter"`), `in_function`
  - `function_signature`: required `name` and ordered `parameters`; optional `defaults` map of literal values
  - `while_loop`: detects `ast.While`; honors `in_function`; optional `nonconstant` rejects `while False` / other constant tests
  - `forbidden_call`: reject calls to a named function (for example `sum`) inside an optional `in_function`

Prefer behavior checks over comparing source text. Use `source_uses` only when a hardcoded result would otherwise pass.

Optional import control (defaults to no imports):

```json
"allowed_modules": ["math"]
```

Only curated curriculum modules can be enabled. See `engine/import_policy.py`.
