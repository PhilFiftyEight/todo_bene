
---

# 📖 Frequency Parser Specification (V1.0 de la doc)
Le parser renvoie uen chaine qui contient les instructions pour le moteur de répétition.

## 1. Structure de la Chaîne

Chaque retour du parser suit une structure segmentée par le symbole `@` :

> **Format :** `start_date@cadence@limit|shift!exceptions`

| Segment | Nom | Description |
| --- | --- | --- |
| **1** | `start_date` | Point de départ du calcul (valeur par défaut : `today`). |
| **2** | `cadence` | La règle de répétition technique (ex: `weekly#1mon`). |
| **3** | `limit` | La condition d'arrêt (`∞`, nombre fixe, durée `+` ou date `YYYY-MM-DD`). |
| **4** | `shift` | (Optionnel) Modificateur après ` |
| **5** | `exceptions` | (Optionnel) Jours exclus après `!`. |

---

## 2. Typologie des Limites (`limit`)

L'Engine doit interpréter le troisième segment selon ces quatre formats :

* **Infinie (`∞`)** : Pas de date de fin.
* **Fixe (`5`)** : Nombre total d'occurrences à générer.
* **Relative (`+2w`, `+6m`, `+1y`)** : Durée calendaire à partir de `today`.
* **Date (`2026-06-30`)** : Date d'arrêt absolue (incluse).

---

## 3. Table de Référence des Tests (32 Cas)

Cette section liste les correspondances exactes validées par la suite de tests unitaires et sert de référence pour le comportement attendu du système.

### A. Intervalles Simples et Séquences

| Entrée (FR/EN) | Résultat Parser | Note Engine |
| --- | --- | --- |
| "Chaque jour" | `today@daily#1d@∞` | Répétition quotidienne infinie. |
| "Toutes les 2 semaines" | `today@weekly#2w@∞` | Intervalle de 2 semaines. |
| "Every 3 weeks" | `today@weekly#3w@∞` | Saut de 3 semaines. |
| "1, 2, 3 jours" | `today@sequence#1,2,3d@3` | Séquence unitaire de 3 jours. |
| "10, 20 jours" | `today@sequence#10,20d@2` | Séquence de 2 dates spécifiques. |
| "1, 2, 4, 8, 16 jours" | `today@sequence#1,2,4,8,16d@5` | Génère 5 dates précises à J+1, J+2, etc. |
| "Les 5 prochains jours" | `today@sequence#1,2,3,4,5d@5` | Séquence unitaire de 5 jours. |
| "Les 3 prochains mois" | `today@sequence#1,2,3m@3` | 1 occurrence par mois pendant 3 mois. |

### B. Jours Spécifiques et Multiples

| Entrée | Résultat Parser | Note Engine |
| --- | --- | --- |
| "Lundi et Jeudi" | `today@weekly#1mon,thu@1` | Limite à 1 (demande implicite). |
| "Lundi, Mercredi et Vendredi" | `today@weekly#1mon,wed,fri@1` | Limite à 1. |
| "Tous les lundis" | `today@weekly#1mon@∞` | Tous les lundis sans fin. |

### C. Durées et Limites Complexes

| Entrée | Résultat Parser | Note Engine |
| --- | --- | --- |
| "Tous les lundis pour 1 mois" | `today@weekly#1mon@+1m` | Stop après 1 mois calendaire. |
| "Chaque jour pendant 15 jours" | `today@daily#1d@+15d` | Durée relative en jours. |
| "Lundi et Mercredi pendant 2 semaines" | `today@weekly#1mon,wed@+2w` | Stop après 2 semaines. |
| "Toutes les 2 semaines pour 6 mois" | `today@weekly#2w@+6m` | Arbitrage Cadence vs Durée. |
| "Les 5 prochains jours pendant 2 sem." | `today@sequence#1,2,3,4,5d@+2w` | La durée `+2w` écrase la limite `5`. |
| "Chaque jour les 2 prochaines semaines" | `today@daily#1d@+2w` | Répétition quotidienne sur durée fixe. |
| "Toutes les 2 sem. pendant 3 mois" | `today@weekly#2w@+3m` | Arbitrage d'unités mixtes. |

### D. Dates de Fin Dynamiques (Frozen Time: 2026-02-09)

| Entrée | Résultat Parser | Note Engine |
| --- | --- | --- |
| "...jusqu'à la fin du mois" | `... @2026-02-28` | Calculé sur le mois en cours. |
| "...jusqu'à la fin du semestre" | `... @2026-06-30` | Fin de S1 ou S2. |
| "...jusqu'au 15 juin" | `... @2026-06-15` | Date fixe. |
| "...jusqu'au 1er janvier" | `... @2027-01-01` | Vise l'année suivante si déjà passé. |

### E. Positions Relative et Travail (Ordinals)

| Entrée | Résultat Parser | Note Engine |
| --- | --- | --- |
| "135ème jour de l'année" | `today@yearly#135thday@∞` | Position absolue annuelle. |
| "27ème jour du trimestre" | `today@quarter#27thday@∞` | Position dans le cycle quarter. |
| "2ème jour ouvré du mois" | `today@monthly#2ndworkday@∞` | Nécessite calendrier jours ouvrés. |
| "Le dernier vendredi du trimestre" | `today@quarter#lastfri@∞` | Fin de cycle trimestriel. |
| "Le dernier vendredi de chaque mois" | `today@monthly#lastfri@∞` | Position relative mensuelle. |
| "The last friday of the year" | `today@yearly#lastfri@∞` | Fin de cycle annuel. |

### F. Exceptions, Reports et Robustesse

| Entrée | Résultat Parser | Note Engine |
| --- | --- | --- |
| "Chaque jour sauf le lundi" | `... @∞!mon` | Retirer les lundis des occurrences. |
| "...sauf samedi et dimanche" | `... @∞!sat,sun` | Filtre week-end. |
| "Every day but not on Wed for 2 weeks" | `daily#1d@+2w!wed` | Exception sur durée limitée. |
| "Tous les lundis sauf en août" | `today@weekly#1mon@∞!aug` | Exclusion mensuelle (nom long). |
| "Chaque lundi sauf en 08" | `today@weekly#1mon@∞!aug` | Exclusion mensuelle (numérique). |
| "1er du mois, reporter si WE" | `today@monthly#1stday@∞ | next_workday` |
| "Le 5 du mois décaler si non ouvré" | `today@monthly#5thday@∞ | next_workday` |
| "1 m," (Virgule traînante) | `today@monthly#1stday@∞` | Virgule ignorée. |
| "5 m" (Forme courte) | `today@monthly#5thday@∞` | Forme technique comprise. |

---

## 5. Implementation Guidelines for the Engine

Le rôle de l'Engine est de transformer la chaîne technique en une liste d'objets `pendulum.DateTime`. Voici les principes directeurs pour le développement :

### A. La Boucle de Génération (The Generator Loop)

* **Initialisation** : Toujours partir de la `start_date` (ex: `today`).
* **Itération** : Utiliser la `cadence` pour calculer l'occurrence suivante.
* **Validation de Limite** : Avant d'ajouter une date à la liste, vérifier si elle respecte la `limit` :
* Si `limit` est un **nombre** : Arrêter quand `len(dates) == limit`.
* Si `limit` est une **date** : Arrêter si `next_date > limit`.
* Si `limit` est une **durée** (ex: `+3m`) : Calculer `end_date = start_date + duration` au début, puis traiter comme une limite de date fixe.


### B. Gestion des Exceptions (`!`)

* Le filtre d'exception doit être appliqué **après** le calcul de la date de cadence mais **avant** le contrôle de limite.
* Si une date tombe sur un jour exclu (ex: `!wed`), elle est ignorée et ne compte pas dans la limite numérique (si applicable).

### C. Application du Report (`|shift`)

* Le shift est la **dernière étape** de transformation pour chaque date générée.
* Si `|next_workday` est présent :
1. Vérifier si la date est un week-end (Is Saturday/Sunday?).
2. Vérifier si la date est un jour férié (nécessite une table de jours fériés externe).
3. Tant que la condition est vraie, ajouter `+1 day` à la date.


### D. Priorité de Calcul (Order of Operations)

Pour chaque occurrence, l'Engine doit suivre cet ordre strict :

1. **Generate**: Calculer la -ième date selon la règle (ex: `monthly#1stday`).
2. **Filter**: Vérifier les exceptions `!`. Si exclu, passer à .
3. **Shift**: Appliquer le report `|` si nécessaire pour tomber sur un jour ouvré.
4. **Terminate**: Vérifier si la date finale dépasse la `@limit`.


### E. Collision de motifs.

Pour éviter les conflits entre expressions (ex: "Every month" qui pourrait voler le match de "Last Friday of every month"), le système repose sur trois piliers :

- Priorité Numérique : Les extracteurs complexes (RelativePositionExtractor) ont une priorité plus forte (valeur plus petite, ex: 10) que les extracteurs simples (ex: 15 ou 20).
La **Spécificité** `gagne` sur la **Généralité** : Un extracteur qui cherche "le dernier vendredi du mois" (RelativePositionExtractor) est plus complexe qu'un extracteur qui cherche "chaque mois" (SimpleIntervalExtractor). Il doit donc avoir une priorité numérique plus faible (ex: 10 vs 15) pour être testé en premier.

- Ancrage Strict : Les extracteurs simples utilisent l'ancrage ^ pour s'assurer qu'ils ne capturent pas une fin de phrase appartenant à une structure plus large.
L'**Ancrage** est le bouclier : En utilisant ^ (début de chaîne) pour les extracteurs simples, on les empêche de "voler" un morceau de texte situé à la fin d'une commande complexe. Cela force l'extracteur complexe à traiter la phrase dans sa globalité.

- Post-Processing des Exceptions : Les exclusions (après le !) sont nettoyées des stopwords et les codes mois numériques sont convertis en étiquettes techniques (ex: 08 -> aug) pour assurer la cohérence du format final

---

## Annexe : Catalogue des Cas de Tests (32 scénarios)

Cette section liste les correspondances exactes validées par la suite de tests unitaires. Elle sert de référence pour le comportement attendu du système.

### 1. Configuration et Fallbacks

* **Langue Inconnue** : Si `language="de"`, le système bascule par défaut sur `"en"`.
* **Contextes multilingues** : "Toutes les 3 semaines" (FR) et "Every 3 weeks" (EN) produisent tous deux `weekly#3w@∞`.

### 2. Intervalles et Séquences (Simple & Multi)

* **Chaque jour** : `daily#1d@∞`
* **Toutes les 2 semaines** : `weekly#2w@∞`
* **Lundi et Jeudi** : `weekly#1mon,thu@1`
* **Lundi, Mercredi et Vendredi** : `weekly#1mon,wed,fri@1`
* **1, 2, 3 jours** : `sequence#1,2,3d@3`
* **10, 20 jours** : `sequence#10,20d@2`
* **1, 2, 4, 8, 16 jours** : `sequence#1,2,4,8,16d@5`

### 3. Durées et Limites Explicites

* **Les 5 prochains jours** : `sequence#1,2,3,4,5d@5`
* **3 prochaines semaines** : `sequence#1,2,3w@3`
* **Tous les lundis pour 1 mois** : `weekly#1mon@+1m`
* **Chaque jour pendant 15 jours** : `daily#1d@+15d`
* **Lundi et Mercredi pendant 2 semaines** : `weekly#1mon,wed@+2w`
* **Toutes les 2 semaines pour 6 mois** : `weekly#2w@+6m`
* **Les 5 prochains jours pendant 2 semaines** : `sequence#1,2,3,4,5d@+2w` (Arbitrage : la durée l'emporte sur le compte).
* **Chaque jour les 2 prochaines semaines** : `daily#1d@+2w`

### 4. Limites Calendaires (Date Figée au 09/02/2026)

* **Jusqu'à la fin du mois** : `daily#1d@2026-02-28`
* **Jusqu'à la fin du semestre** : `weekly#1mon@2026-06-30`
* **Jusqu'au 15 juin** : `weekly#1fri@2026-06-15`
* **Jusqu'au 1er janvier** (déjà passé) : `daily#1d@2027-01-01` (Vise l'année suivante).

### 5. Positions et Calendrier Civil

* **135ème jour de l'année** : `yearly#135thday@∞`
* **27ème jour du trimestre** : `quarter#27thday@∞`
* **2ème jour ouvré du mois** : `monthly#2ndworkday@∞`
* **Last Friday of the year** : `yearly#lastfri@∞`

### 6. Exceptions et Reports (Robustesse)

* **Sauf le lundi** : `daily#1d@∞!mon`
* **Sauf samedi et dimanche** : `daily#1d@∞!sat,sun`
* **Every day but not on Wed for 2 weeks** : `daily#1d@+2w!wed`
* **Le 1er du mois, reporter si week-end** : `monthly#1stday@∞|next_workday`
* **Le 5 du mois décaler si jour non ouvré** : `monthly#5thday@∞|next_workday`
* **Le dernier vendredi du trimestre, si férié décaler** : `quarter#lastfri@∞|next_workday`

### 7. Positions Relatives Complexes
Gère les rangs spécifiques au sein d'une période donnée, incluant les jours ouvrés et les ordinaux longs.

* **Le 135ème jour de l'année** :  `today@yearly#135thday@∞`
* **Le 2ème jour ouvré du mois** :  `today@monthly#2ndworkday@∞`
* **Le dernier vendredi du trimestre** :  `today@quarter#lastfri@∞`
* **Le dernier vendredi de chaque mois** :  `today@monthly#lastfri@∞`

### 8. Exclusions et Exceptions (Mois)
Capacité à exclure des mois complets via leur nom long ou leur code numérique.

* **Tous les lundis sauf en août** : `today@weekly#1mon@∞!aug`
* **Chaque lundi sauf en 08** : `today@weekly#1mon@∞!aug`

---
