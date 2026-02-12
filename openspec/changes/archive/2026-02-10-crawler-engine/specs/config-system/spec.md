## ADDED Requirements

### Requirement: Crawl configuration
The `CrawlConfig` model SHALL include a `binary_extensions` field containing a set of file extensions (with leading dot) that are known binary formats. These extensions SHALL be used by the directory discovery module to skip files without reading them.

The field SHALL default to a comprehensive list of common binary extensions including image formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.ico`, `.svg`, `.webp`), audio/video (`.mp3`, `.wav`, `.mp4`, `.avi`, `.mov`), archives (`.zip`, `.tar`, `.gz`, `.bz2`, `.7z`, `.rar`), compiled (`.pyc`, `.pyo`, `.so`, `.dll`, `.dylib`, `.o`, `.a`, `.class`, `.jar`, `.wasm`), fonts (`.woff`, `.woff2`, `.ttf`, `.otf`, `.eot`), and other binary formats (`.pdf`, `.exe`, `.bin`, `.dat`, `.db`, `.sqlite`).

#### Scenario: Default binary extensions include common formats
- **WHEN** a `CrawlConfig` is created with default values
- **THEN** `binary_extensions` SHALL contain at least `.png`, `.jpg`, `.pyc`, `.zip`, `.exe`, `.pdf`

#### Scenario: Custom binary extensions override defaults
- **WHEN** a user specifies `binary_extensions` in `lexibrary.toml`
- **THEN** the configured list SHALL be used instead of defaults
