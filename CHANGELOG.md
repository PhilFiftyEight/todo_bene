# Changelog

## [0.2.0] - 2026-02-01

### ✨ Features
- **Subtask Engine**: Support for hierarchical todos with `parent_id` link.
- **Smart Inheritance**: Automated copy of category and user_id to children.
- **Time Precision**: Switched to `HH:mm:ss` format for robust date inheritance.

### 🛠 Technical
- **Timezone Security**: Enforced local timezone parsing with Pendulum.
- **Recursive Navigation**: Integrated numeric index navigation between parent and child details.
- **DuckDB Refactor**: Updated repository methods for active user filtering.

## [0.2.2] - 2026-02-05

### 🌟 Key Changes:
- **Rich UI Integration**: Integrated the Rich library for clear visual feedback using success (green) and error (red) status panels.
- **Automated Setup Wizard**: No more manual configuration. An interactive wizard now triggers automatically on the first launch to set up your profile and DuckDB database.
- **Bilingual Documentation**: The README has been completely revamped and is now available in both French and English with anchor navigation.
- **Navigation Enhancements**: Optimized recursive navigation flows for managing tasks and subtasks.

### 🛠 Technical Improvements:
- **Data Validation**: Improved interactive handling of date input errors directly within the CLI.
- **Stability**: The codebase is now backed by a comprehensive suite of 86 passing tests.
- **Dependency Management**: Optimized use of uv for fast and reliable installation.

## 📝 Changelog - v0.30 (2026-02-19)

### 🚀 New Features

* **Advanced Repetition System**: Full management of recurring tasks via a DSL engine (Daily, Weekly, Monthly, "Every Tuesday", etc.).
* **Recursive Cloning**: The system now automatically duplicates the entire task tree (parent task and all its sub-tasks).
* **Time Management**: Precise preservation of original task time (hours, minutes, seconds) when creating future occurrences.
* **Safety Guardrails**: Automatic 1-year limit on repetitions to prevent database flooding.

### 🛠 Infrastructure & Persistence

* **Migration Manager**: Implementation of a database versioning system (`_migrations`) for seamless updates without data loss.
* **Schema Evolution**: Added `frequency` (VARCHAR) and `date_final` (DOUBLE) columns to the `todos` table.
* **SQL Robustness**: Transitioned to a granular migration structure (files `001`, `002`).

### 🎨 User Experience (UX)

* **Interactive Control**: Replaced fixed `sleep` timers with user validation (`click.pause`), making the CLI more responsive.
* **Enhanced Feedback**: Clearer success and error messages during task creation and completion.

### 🧪 Quality & Reliability

* **Test Coverage**: 180 unit and integration tests passed, covering complex repetition scenarios.

## [v0.3.1] - 2026-02-20

### ✨ New Features
- **Period-based filtering**: Added `--period` (`-p`) option supporting `today`, `week`, `month`, and `all`.
- **Default View**: The `list` command now defaults to `today` for enhanced daily focus and productivity.
- **Visual Grouping**: Smart display grouping by Day (for `week` view) or Week (for `month` view) with stylized separators.
- **Autocompletion**: Full Typer support for period options in the shell.

### 🛠️ Enhancements & Fixes
- **Chronological Sorting**: Fixed SQL sorting logic to correctly combine `date_start` (time) and `date_due` (deadline).
- **UI Robustness**: Implemented `Style` objects to prevent "dim" inheritance on section headers, ensuring high visibility.
- **Test Stability**: Updated the entire test suite (184 tests) to decouple CLI integration tests from UI default changes using explicit flags.


## [0.3.2] - 2026-02-22

### ✨ New Features

* **UI Redesign (Rich):** Complete interface overhaul using the `Rich` library for a nice look and feel (panels, tables, and colors).
* **Time-Based Grouping:** Added clear visual separators in `week` and `month` views to group tasks by **Day** and **Week**.

### 🛠 Improvements & Fixes

* **Justify Spacing:** Corrected display offsets to ensure perfect right-alignment in detail panels, regardless of title length.
* **Recursive Navigation:** Stabilized index handling when diving into subtasks.
* **DuckDB Robustness:** Improved connection management via the `DuckDBConnectionManager`.

### 📝 Documentation & Media

* **Animated Demos:** Integrated VHS demos (`.gif`) showcasing the initial setup and core features.
* **Bilingual README:** Complete documentation now available in both French 🇫🇷 and English 🇬🇧.
* **Demo Scripts:** Added `populate_demo.py` in `docs/media/` to generate an instant testing environment.


## [0.3.3] - 2026-02-25

### Added
- Integrated `prompt-toolkit` for a more interactive CLI experience.
- Added fish-shell-like auto-suggestions for Category and Title fields during modification.
- Implemented multiline text editing for Todo descriptions (use Esc+Enter to validate).
- Added pre-filled editable default values for Start and Due dates.

### Changed
- Refactored `_handle_action` to use `PromptSession` for task updates.
- Centralized interactive session creation in a reusable `create_session_with_history` utility.

### Fixed
- Stabilized CLI unit tests by introducing a `mock_prompt_session` fixture to handle non-interactive environments.


## [0.3.4] - 2026-03-02

### Added
- **Background Mail Processing**: The `list` command now triggers mail orchestration in a non-blocking background thread.
- **Master Key Session Cache**: Implemented an in-memory cache for the encryption master key to prevent redundant password prompts during a single execution.
- **Enhanced Security Safeguards**: Added strict validation for the system keyring; the application now prevents encryption in production if the secure storage is unreachable.
- **Mail Payload Filtering**: Optimized the mail orchestrator to skip jobs with empty task lists or for users who have already received their daily notification.

### Fixed
- **Encryption Logic**: Resolved a `NoneType` error occurring in non-interactive environments (CI/Tests) when the system keyring is unavailable.
- **Database Optimization**: Removed redundant repository calls by sharing the pre-loaded task list with the background mail thread.


## [0.3.5] - 2026-03-03

### Added
- **Waze Transformer v2**: Smart address detection now supports metric numbering (up to 5 digits), common in rural areas.
- **Address Suffix Support**: Added regex handling for street number suffixes such as `40B`, `40 Bis`, `40C`, `40 Ter`, etc.
- **Strict Line Anchoring**: Waze links now terminate strictly at the end of the address line, preventing the "consumption" of subsequent text or newlines.

### Fixed
- **Phone/Waze Collision**: Resolved a major bug where phone numbers were incorrectly identified as street numbers. Phone detection now takes priority over address matching.
- **URL Formatting**: Fixed encoding issues where newline characters (`%0A`) were being included in the generated Waze navigation URLs.

### Testing
- Added comprehensive unit tests for phone/address collision scenarios.
- Added test cases for various French address formats including suffixes and metric numbering.

---
