# config/defaults

**Summary:** Holds the default `config.yaml` template string written by `lexi init` to `.lexibrary/config.yaml`.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `DEFAULT_PROJECT_CONFIG_TEMPLATE` | `str` | YAML template with all config keys and inline comments, including `scope_root` and `max_file_size_kb` |

## Dependents

- `lexibrarian.config.__init__` -- re-exports it
- `lexibrarian.init.scaffolder` -- writes it to `.lexibrary/config.yaml` on init
