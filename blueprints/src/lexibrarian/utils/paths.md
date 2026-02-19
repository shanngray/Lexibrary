# utils/paths

**Summary:** Computes mirrored output paths inside `.lexibrary/` for design files (`.md`) and directory indexes (`.aindex`).

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `mirror_path` | `(project_root: Path, source_file: Path) -> Path` | Map `src/auth/login.py` → `.lexibrary/src/auth/login.py.md` |
| `aindex_path` | `(project_root: Path, directory: Path) -> Path` | Map `src/auth/` → `.lexibrary/src/auth/.aindex` |
| `LEXIBRARY_DIR` | `str = ".lexibrary"` | Constant for the output directory name |

## Dependents

- Will be used by artifact writers and lookup commands once implemented
