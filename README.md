
---

# 📝 Todo Bene

[![Version Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-219%20pass%C3%A9s-brightgreen)](#)

[Version Française](#-version-française) | [English Version](#-english-version)

## 🇫🇷 Version Française

**Todo Bene** est un gestionnaire de tâches en ligne de commande (CLI) focalisé sur l'efficacité, conçu pour lutter contre la procrastination grâce à une hiérarchie de tâches structurée et un report automatique.

---

## ✨ Fonctionnalités Clés

* **Hiérarchie Intelligente :** Créez des sous-tâches avec héritage des propriétés (catégorie, dates).
* **Report Automatique :** Les tâches en retard sont automatiquement replanifiées au lendemain même pour maintenir la pertinence de votre liste.
* **Zéro Configuration :** Un assistant de configuration interactif vous guide lors du premier lancement.
* **Interface UI Riche :** Une interface terminal avec des panneaux d'état, des tableaux et des indicateurs de progression.
* **Architecture Propre :** Conçu pour la fiabilité et la performance en utilisant DuckDB

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

### Premier Lancement et commandes CLI

Le premier lancement va générer le fichier de configuration :
l'**Assistant Interactif** vous guidera pour créer votre profil et initialiser votre base de données locale.

```
~/.config/todo_bene/config.json
~/.local/share/todo_bene/.todo_bene.db
# Noter que si vous répondez OUI à la version de développement, la base sera créer dans le répertoire `todo_bene` avec le nom `dev.db`
```

![Setup](docs/media/01setup.gif) 

---

## 🛠 Utilisation

### Ajouter des Todos

Créez une tâche principale ou une sous-tâche en toute simplicité :

```bash
tb add "Finir le rapport de projet" --category "Travail"(*) --priority
# (*) : Le passage à l'anglais est prévu ultérieurement

```

### Pour visualiser et gérer les Todos

Lancez la liste interactive pour naviguer, mettre à jour ou terminer vos tâches :

```bash
tb list
tb list -c Travail # Pour filtrer sur une catégorie (autocompletion)
# Si la catégorie n'existe pas, vous pourrez valider sa création
tb list -p [today|week|month|all] # filtrer par période
# les filtres peuvent être combinés
```

### Naviguer, Modifier, Terminer et Répéter, Supprimer

La navigation est récursive pour plonger dans les sous-tâches. 

Modifier facilement un todo à partir de la vue détails.

Terminer un Todo l' archive (il reste présents dans la bdd afin d'historique et recherche). Vous pourrez alors les répéter automatiquement en langage naturel `ex: tous les lundi pendant 2 mois`. Les sous-tâches actives bloquent la complétion à moins de forcer l'action. Un Todo terminé n'est plus visible dans la list

Supprimer définitivement un Todo (pas d'archivage)


![Demo](docs/media/02demov032.gif) 

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

**Todo Bene** is a command-line task manager (CLI) focused on efficiency, designed to fight procrastination through a structured task hierarchy and automatic rescheduling.

---

## ✨ Key Features

* **Smart Hierarchy:** Create subtasks with property inheritance (category, dates).
* **Self-Correction:** Overdue tasks are automatically rescheduled to the next day to keep your list relevant.
* **Zero Config:** An interactive setup wizard guides you through your first launch.
* **Rich UI:** A polished terminal interface featuring status panels, tables, and progress indicators.
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

### First Launch & Configuration

The first launch will generate your configuration file. The **Interactive Wizard** will guide you through creating your profile and initializing your local database.

```text
~/.config/todo_bene/config.json
~/.local/share/todo_bene/.todo_bene.db
# Note: If you choose the development version, the database will be created in the `todo_bene` directory as `dev.db`

```
![Setup](docs/media/01setup.gif)
---

## 🛠 Usage

### Adding Todos

Create a main task or a subtask with ease:

```bash
tb add "Finish project report" --category "Work" --priority

```

### Viewing and Managing Todos

Launch the interactive list to navigate, update, or complete your tasks:

```bash
tb list
tb list -c Work # Filter by category (with autocompletion)
# If the category doesn't exist, you can confirm its creation on the fly.
tb list -p [today|week|month|all] # Filter by period
# Filters can be combined.

```

### Navigate, Edit, Complete & Repeat, Delete

* **Navigation:** Recursive navigation allows you to dive deep into subtasks.
* **Edit:** Easily modify a todo from the details view.
* **Complete:** Completing a todo archives it (it remains in the database for history and search).
* **Recurrence:** You can set tasks to repeat using natural language (e.g., `every Monday for 2 months`). Active subtasks block completion unless forced.
* **Delete:** Permanently remove a todo (no archiving).

![Demo](docs/media/02demov032.gif)

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

