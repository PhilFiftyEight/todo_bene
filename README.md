
---

# 📝 Todo Bene

[![Version Python](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/)
[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-180%20pass%C3%A9s-brightgreen)](#)

[Version Française](#-version-française) | [English Version](#-english-version)

## 🇫🇷 Version Française

**Todo Bene** est un gestionnaire de tâches en ligne de commande (CLI) focalisé sur l'efficacité, conçu pour lutter contre la procrastination grâce à une hiérarchie de tâches structurée et un report intelligent automatique.

---

## ✨ Fonctionnalités Clés

* **Hiérarchie Intelligente :** Créez des sous-tâches avec héritage des propriétés (catégorie, dates).
* **Report Automatique :** Les tâches en retard sont automatiquement replanifiées au soir même pour maintenir la pertinence de votre liste.
* **Zéro Configuration :** Un assistant de configuration interactif vous guide lors du premier lancement.
* **Interface UI Riche :** Une superbe interface terminal avec des panneaux d'état, des tableaux et des indicateurs de progression.
* **Architecture Propre :** Conçu pour la fiabilité et la performance en utilisant DuckDB.

---

## 🚀 Mise en Route

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-nom-utilisateur/todo-bene.git
cd todo-bene

# Installer les dépendances et le package
uv pip install -e .

```

### Premier Lancement

Oubliez les fichiers de configuration complexes. Tapez simplement :

```bash
. .venv/bin/activate?(.bat|.csh|.fish|.nu|.ps1)
tb

```

L'**Assistant Interactif** vous guidera pour créer votre profil et initialiser votre base de données locale.

```
# exemple de structure :
~/.config/todo_bene/config.json
~/.local/share/todo_bene/.todo_bene.db

```

---

## 🛠 Utilisation

### Ajouter des tâches

Créez une tâche principale ou une sous-tâche en toute simplicité :

```bash
tb add "Finir le rapport de projet" --category "Travail" --priority (*)
# (*) : Le passage à l'anglais est prévu ultérieurement

```

### Gérer les tâches

Lancez la liste interactive pour naviguer, mettre à jour ou terminer vos tâches :

```bash
tb list

```

* **Naviguer :** Navigation récursive pour plonger dans les sous-tâches.
* **Terminer :** Marquez les tâches comme faites. Les sous-tâches actives bloquent la complétion à moins de forcer l'action.
* **Refactoriser :** Modifiez les titres, descriptions, priorités ou dates directement depuis la vue détaillée.

### Vue Debug & Dev

Visualisez l'état brut de votre base de données locale :

```bash
tb list-dev

```

---

## 🧪 Tests

Nous prenons la fiabilité au sérieux. Le projet est livré avec une suite de tests complète couvrant la logique métier, les cas d'utilisation et les interactions CLI.

```bash
pytest -s

```

---

## 📄 Licence

Distribué sous licence MIT. Voir le fichier `LICENSE` pour plus d'informations.

Développé avec ❤️ par **PhilFiftyEight** (2026).


---

# 📝 Todo Bene

## 🇬🇧 English Version

**Todo Bene** is a focused, CLI-based task manager designed to fight procrastination through structured task hierarchy and automated smart rescheduling.

---

## ✨ Key Features

* **Smart Hierarchy:** Create subtasks with inherited properties (category, dates).
* **Automatic Postponing:** Overdue tasks are automatically rescheduled to the current evening to keep your list relevant.
* **Zero Configuration:** Interactive setup wizard on first launch.
* **Rich UI:** Beautiful terminal interface with status panels, tables, and progress indicators.
* **Clean Architecture:** Built for reliability and performance using DuckDB.

---

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/todo-bene.git
cd todo-bene

# Install dependencies and the package
uv pip install -e .

```

### First Launch

Forget complex configuration files. Just type:

```bash
. .venv/bin/activate?(.bat|.csh|.fish|.nu|.ps1)
tb

```

The **Interactive Wizard** will guide you through creating your profile and initializing your local database.

```
# example:
~/.config/todo_bene/config.json
~/.local/share/todo_bene/.todo_bene.db

```

---

## 🛠 Usage

### Adding Tasks

Create a main task or a subtask with ease:

```bash
tb add "Finish project report" --category "Travail" --priority (*)
# (*) : Translation to English is planned for later

```

### Managing Tasks

Launch the interactive list to navigate, update, or complete tasks:

```bash
tb list

```

* **Navigate:** Recursive navigation to dive into subtasks.
* **Complete:** Mark tasks as done. Active subtasks will block completion unless forced.
* **Refactor:** Modify titles, descriptions, priority or dates directly from the detail view.

### Debug & Dev View

View the raw state of your local database:

```bash
tb list-dev

```

---

## 🧪 Testing

We take reliability seriously. The project comes with a comprehensive test suite covering domain logic, use cases, and CLI interactions.

```bash
pytest -s

```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

Developed with ❤️ by **PhilFiftyEight** (2026).
