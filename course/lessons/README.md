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
  - `feature`: `fstring`, `binop_names`, `rebind_self`, `append_or_extend`, `append_call`, `remove_call`, `pop_call`, `len_call`, `boolean_and`, `boolean_or`, `unary_not`, `subscript`, `comment`, `if_statement`, `for_loop`, `while_loop`, `elif_branch`, `calls_name`, `print_names`, `print_min_calls`, `range_call`, `compares_names`, `method_call`, `function_signature`
  - optional `name` / `names` to require specific variables (receiver for `method_call`)
  - optional `method` for `method_call` (e.g. `"items"`, `"get"`)
  - optional `min_args` for `method_call` to require a minimum number of positional arguments
  - optional `ops` for comparison operators (`Lt`, `Eq`, …)
  - optional `in_function` to scope the check to one function body
  - optional `inside`: `"for_loop"` for `calls_name`, or `"for_iter"` for `method_call` to require the call directly drives a `for` loop's iterable (dummy calls elsewhere do not count)
  - for `function_signature`, provide:
    - `name`: function name
    - `parameters`: ordered declared parameter names
    - optional `defaults`: mapping of parameter name → literal default value (e.g. `{"quantity": 1}`)
    - rejects `*args`/`**kwargs` in place of the named parameters, wrong order, missing/wrong defaults, or body-only fallbacks

Prefer behavior checks over comparing source text. Use `source_uses` only when a hardcoded result would otherwise pass.

Optional import control (defaults to no imports):

```json
"allowed_modules": ["math"]
```

Only curated curriculum modules can be enabled. See `engine/import_policy.py`.
