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
