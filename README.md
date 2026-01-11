
---

# 📝 Todo Bene

**Todo Bene** est un gestionnaire de tâches en ligne de commande (CLI) puissant, conçu pour être simple, rapide et respectueux de vos habitudes locales.

## 🚀 Installation

Assurez-vous d'avoir Python 3.10+ installé, puis installez les dépendances :

```bash
pip install -r requirements.txt

```

## 🛠️ Configuration Initiale

Avant de créer votre première tâche, enregistrez-vous pour configurer votre profil utilisateur :

```bash
python -m todo_bene.infrastructure.cli.main register --email votre@email.com

```

---

## 📋 Guide d'utilisation

### 1. Créer une tâche

La commande `create` est flexible. Elle gère automatiquement les dates et les priorités.

* **Tâche simple (automatique) :**
```bash
python -m todo_bene.infrastructure.cli.main create "Acheter du pain"

```


*Par défaut : La date de début est l'heure actuelle, et l'échéance est fixée à ce soir 23h59.*
* **Tâche avec date précise (Format Français) :**
```bash
python -m todo_bene.infrastructure.cli.main create "Réunion Client" --start "25/01/2026 14:00"

```


* **Tâche prioritaire :**
```bash
python -m todo_bene.infrastructure.cli.main create "Urgent : Rapport" --priority

```



### 2. Lister vos tâches

Affichez vos tâches dans un tableau lisible et localisé :

```bash
python -m todo_bene.infrastructure.cli.main list

```

### 3. Gestion des dates (Formats supportés)

L'application est intelligente et accepte plusieurs formats de saisie pour votre confort :

| Type | Exemples acceptés |
| --- | --- |
| **Français (Slashs)** | `11/01/2026`, `11/01/2026 15:30` |
| **Français (Tirets)** | `11-01-2026`, `11-01-2026 13:00` |
| **Standard ISO** | `2026-01-11` |

---

## 💡 Règles Métier automatiques

Pour vous faire gagner du temps, **Todo Bene** applique les règles suivantes :

1. **Date de début absente :** L'application utilise l'heure exacte à laquelle vous tapez la commande.
2. **Date d'échéance absente :** Elle est automatiquement fixée à **23h59** le jour du début de la tâche.
3. **Saisie de date seule :** Si vous tapez `15/01/2026` sans préciser l'heure, le début est mis à **00h00** et l'échéance à **23h59**.

---

## 🛠️ Développement et Tests

Si vous souhaitez contribuer ou lancer les tests :

```bash
# Lancer tous les tests
pytest

# Lancer les tests avec détails
pytest -v

```

---

**C'est tout bon ! Prêt à passer à l'étape suivante : la gestion de la Fréquence (tâches répétitives) ?**