# llm-context-builder-py

Compose LLM system prompts from named, prioritized sections. Supports variable interpolation and enable/disable toggles.

Zero runtime dependencies, fully type-hinted (ships a `py.typed` marker), and works on Python 3.9+.

## Install

```bash
pip install llm-context-builder-py
```

## Usage

```python
from llm_context_builder import ContextBuilder

builder = ContextBuilder()
builder.add("role",      "You are a helpful coding assistant.", priority=100)
builder.add("format",   "Always respond in markdown.", priority=50)
builder.add("tool_hint","Use tools when needed.", priority=10)

system_prompt = builder.build()

# As a message dict
msg = builder.as_message()   # {"role": "system", "content": "..."}

# Variable interpolation
builder.add("greeting", "Hello, {user_name}!", priority=20)
prompt = builder.build(variables={"user_name": "Alice"})

# Dynamic control
builder.disable("tool_hint")
builder.enable("tool_hint")
builder.update("role", "You are a strict code reviewer.")
builder.remove("format")

# Clone for per-request variants
variant = builder.clone()
variant.add("extra", "Be concise.", priority=5)
```

## API

`ContextBuilder(separator="\n\n")` — sections are joined with `separator` when rendered.

- `.add(name, content, priority=0, enabled=True)` — add or replace a section
- `.update(name, content)` — update content, keeping the existing priority/enabled (adds the section if it does not exist)
- `.enable(name)` / `.disable(name)` — toggle a section on/off (no-op if the name is unknown)
- `.remove(name)` — drop a section (no-op if the name is unknown)
- `.has(name)` — whether a section with that name exists
- `.build(variables=None)` — render enabled sections in descending priority order, joined by the separator; if `variables` is given, each section is interpolated with `str.format_map`
- `.as_message(variables=None)` — same as `.build()` but wrapped as `{"role": "system", "content": "..."}`
- `.section_names()` — section names in priority order
- `.clone()` — return an independent deep copy

All mutating methods return `self`, so calls can be chained.

### Notes on behavior

- Sections render in **descending priority** (highest first). Sections with equal priority keep their insertion order.
- Section content is `.strip()`ped before joining.
- Interpolation is **best-effort**: if a section references a missing variable, a bad index/attribute, or an incompatible format spec, that section is rendered verbatim instead of raising — so one malformed section never breaks the whole prompt.

## Development

The test suite uses only the standard library (`unittest`), so no extra installs are needed:

```bash
python3 -m unittest discover -s tests
```

## License

MIT
