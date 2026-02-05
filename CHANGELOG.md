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

