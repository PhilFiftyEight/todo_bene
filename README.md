# 🌿 Todo Bene

**Todo Bene** est une application de gestion de tâches (Todo List) en ligne de commande ( CLI pour l'instant mais ouverte pour GUI ou autre). 

## ✨ Notes de conception

- **Architecture Hexagonale (Clean Architecture)** : Séparation stricte entre le métier (Domain), les cas d'usage (Application) et l'infrastructure (Persistence/CLI).
- **Stockage avec DuckDB** : Profitez de la puissance d'une base de données relationnelle et analytique locale pour une gestion instantanée des données. L'architecture permet d'ajouter votre BDD préférée.
- **Démarrage facile** : Un configurateur interactif au premier lancement pour créer ou restaurer votre profil utilisateur via votre email.
- **Arborescence de tâches** : Support des relations parents/enfants/... pour décomposer des projets complexes en sous-tâches.
- **Tests first** : Suite de tests pour éviter toute régression et garantissant la fiabilité de chaque fonctionnalité à mesure de l'ajout de nouvelles fonctionnalité.
- Python, Typer, Rich, Pendulum

---
## 🏗 Architecture & Design

Le projet s'inspire des principes de la **Clean Architecture** :

1. **Domain** : Contient les entités (`Todo`, `User`) et la logique métier pure, sans dépendance externe.
2. **Application** : Définit les contrats (Interfaces) et implémente les cas d'usage.
3. **Infrastructure** : Gère les détails techniques comme la persistence DuckDB, le stockage JSON de la session et l'interface cliente Typer/Rich.

---

## 🚀 Installation rapide

Le projet utilise `uv` pour une gestion simplifiée et ultra-rapide des dépendances et de l'environnement Python. Le fichier pyproject.toml est disponible pour ceux qui préfèrent un autre gestionnaire.

1. **Cloner le dépôt :**
    ```
    $ git clone https://github.com/PhilFiftyEight/todo_bene.git
    $ cd todo_bene
    ```

2. **Installer l'environnement et les dépendances :**
    ```bash
    $ uv sync

    ```

---

## 🛠 Utilisation

### Premier lancement

Lancez simplement n'importe quelle commande pour démarrer le Wizard de configuration :

```bash
$ uv run todo_bene list


╔═════════════════════════════════════════════════════╗
║                                                     ║
║       _____ ___  ___   ___                          ║
║      |_   _/ _ \|   \ / _ \                         ║
║        | || (_) | |) | (_) |                        ║
║        |_| \___/|___/ \___/                         ║
║       ___  ___ _  _ ___                             ║
║      | _ )| __| \| | __|                            ║
║      | _ \| _|| .` | _|                             ║
║      |___/|___|_|\_|___|                            ║
║                                                     ║
║     // Configurons votre profil pour commencer.     ║
║                                                     ║
╚═════════════════════════════════════════════════════╝


Quel est votre email ?: philippe@home
Email inconnu. Quel est votre nom ? (philippe): Philippe

Bienvenue Philippe ! Profil créé.
Aucun Todo trouvé.
```

Todo Bene utilise un fichier de configuration JSON, si celui-ci est supprimé mais que la base de données existe, votre profil sera automatiquement restauré grâce à votre email.
```
Quel est votre email ?: philippe@home
Restauration du profil existant pour : Philippe
Aucun Todo trouvé.
```


### Commandes fréquentes

| Action | Commande |
| --- | --- |
| **Lister les tâches** | `uv run tb list` |
| **Ajouter une tâche** | `uv run tb add "Titre de la tâche" --cat Travail` |
| **Ajouter une sous-tâche** | `uv run tb add "Sous-tâche" --parent <titre du parent>` |

> `--parent` le mot peut être tronqué, tb va proposer les parents possibles:
>```
>Plusieurs parents possibles trouvés :
>┏━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
>┃ N° ┃ Titre  ┃ Catégorie ┃
>┡━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
>│ 1  │ essai  │ Quotidien │
>│ 2  │ essai2 │ Quotidien │
>│ 3  │ essai3 │ Quotidien │
>└────┴────────┴───────────┘
>Choisissez le numéro du parent (0):
>```


**Le reste des commandes est mis en oeuvre par les différents menus de l'application :**
```

        ╭─────────────────────── ⏳ À FAIRE ───────────────────────╮
        │ essai                                                    │
        │                                                          │
        │ Pas de description                                       │
        │                                                          │
        │ Démarrage: 19/01/2026 22:18 - Échéance: 19/01/2026 23:59 │
        ╰──────────────────────────────────────────────────────────╯

Sous-tâches :
  1. ⏳ essai2
  2. ⏳ essai3

Actions :
  t: Terminer | s: Supprimer | n: Nouvelle sous-tâche
  r: Retour | [N°]: Voir sous-tâche

Votre choix:
```
---
### Règles Parent/Enfant (tâche/sous-tâche)

1. Si le parent a une date_due, l'enfant ne peux pas finir après, avant c'est possible
2. Un enfant peut avoir des enfants
3. Si parent supprimé l'enfant est supprimé aussi
4. L'archivage d'un parent entraîne l'archivage des enfants.
5. Les enfants étant les sous-taches d'un parents elles doivent être terminées pour pouvoir terminer (et archiver qui est la conséquence de la terminaison) un parent.
6. Lorsqu'un enfant est terminé, si le parent a d'autres enfant non terminés il ne peut pas encore être archivé : c'est l'archivage du parent qui déclenche l'archivage des enfants (Archiver = tâche complété, c'est différent de la suppression: la tâche n'est plus visible mais elle reste en BDD pour l'historique)

---
### Description
La description est optionnelle

---
### Dates
1. Création : Les dates sont optionnelles (*--date_start, --date_due*), on peut donc créer une tache sans les préciser
2. Par défaut *date_start = now()*
3. Par défaut *date_due = date_start à 23:59:59*
---
### Catégorie
Par défaut la catégorie est *quotidien*

---
## 🧪 Tests

```bash
# Le flag -s est indispensable pour permettre l'interaction avec les prompts CLI durant les tests
$ uv run pytest -s

```

---


*Développé avec passion pour un flux de travail organisé et serein.*
