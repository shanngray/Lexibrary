# ignore/matcher

**Summary:** `IgnoreMatcher` combines config patterns and hierarchical `.gitignore` specs via pathspec to decide whether files/directories should be ignored or descended into.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `IgnoreMatcher` | class | Unified ignore checker for files and directories |
| `IgnoreMatcher.__init__` | `(root: Path, config_spec: PathSpec, gitignore_specs: list[tuple[Path, PathSpec]])` | Accept pre-built specs |
| `IgnoreMatcher.is_ignored` | `(path: Path) -> bool` | True if path matches any ignore pattern |
| `IgnoreMatcher.should_descend` | `(directory: Path) -> bool` | True if directory should be traversed (inverse of ignored) |

## Dependencies

- `pathspec` (third-party)

## Dependents

- `lexibrarian.ignore.__init__` — `create_ignore_matcher` instantiates this
- `lexibrarian.crawler.discovery` — passes to traversal functions
- `lexibrarian.daemon.watcher` — used to filter events

## Key Concepts

- Config patterns checked first (cheap); gitignore specs checked in reverse depth order (most specific wins)
- Directory paths use trailing slash for pathspec directory matching
- `"gitignore"` pattern style — NOT `"gitwildmatch"`
