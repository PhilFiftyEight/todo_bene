

# Documentation Technique : Frequency Engine 

Le `FrequencyEngine` est le cœur logique de calcul temporel. Son rôle est de transformer une instruction normalisée (DSL) en une liste d'objets `pendulum.DateTime` tout en respectant les limites métier et les contraintes de calendrier (jours fériés, week-ends).

## 1. Structure d'une Instruction

L'engine traite des chaînes au format suivant :
`[START]@[CADENCE]@[LIMITS]![EXCLUSIONS]|[MODIFIERS]`

* **START** : Date d'ancrage (`today`, `tomorrow` ou `YYYY-MM-DD`).
* **CADENCE** : Base temporelle et intervalle (ex: `monthly#1`, `weekly#mon,fri`).
* **LIMITS** : Nombre d'occurrences (`12`), date de fin (`2026-12-31`), durée relative (`+2m`) ou infini (`∞`).
* **EXCLUSIONS** : Jours ou mois à ignorer (ex: `!sat,sun`, `!aug`).
* **MODIFIERS** : Ajustements post-génération (ex: `|next_workday`).

---

## 2. L'Algorithme de Génération

L'algorithme suit un flux linéaire en cinq étapes :

### Étape A : Initialisation et Parsing

1. **Extraction** : Découpage de l'instruction via le séparateur `@`.
2. **Ancrage** : Calcul de la `start_date`. Si un mois spécifique est demandé (ex: `@oct`), le curseur est déplacé au 1er de ce mois.
3. **Calcul de la Limite Finale** :
* Le moteur récupère la limite de sécurité (`BusinessLimits`) pour la base choisie (ex: 366 pour `daily`, 12 pour `monthly`).
* Il compare cette sécurité avec la demande de l'utilisateur (`limit_attr`). La valeur la plus basse l'emporte.



### Étape B : Branchement de la Logique de Base

Le moteur aiguille le calcul vers trois types de boucles :

* **Logique Hebdomadaire (`weekly`)** : Si des jours sont spécifiés (`#mon`), le moteur incrémente jour par jour à partir de `start_date + 1` jusqu'à remplir le quota.
* **Logique de Séquence (`sequence`)** : Utilise des offsets mathématiques pour gérer des cycles complexes (ex: "tous les 1, 2 et 4 jours").
* **Logique Standard (Boucle itérative)** : Pour les autres bases (`daily`, `monthly`, `yearly`, etc.), le moteur calcule chaque occurrence via :



### Étape C : Gestion des Cas Ordinaux (Le "Cerveau" du mensuel)

Pour les fréquences complexes comme "Le dernier vendredi du mois" (`monthly#lastfri`) ou "Le 2ème jour ouvré" (`monthly#workday#2`) :

1. Il se positionne au début ou à la fin du mois cible.
2. Il itère (en avant ou en arrière) jusqu'à trouver le jour correspondant au prédicat.
3. Il valide que la date trouvée appartient bien au mois en cours.

### Étape D : Post-traitement (Filtrage et Pipes)

Une fois la liste brute générée, deux filtres sont appliqués :

1. **Exclusions (`!`)** : Suppression des dates si le mois (`aug`) ou le jour (`sat`) correspond.
2. **Modificateurs (`|`)** : Si `|next_workday` est présent, chaque date tombant un week-end ou jour férié est décalée au jour ouvré suivant via le `HolidayService`.

### Étape E : Finalisation

* Suppression des doublons éventuels via un `set`.
* Tri chronologique.
* Découpage (`slicing`) final pour respecter strictement la limite demandée.

---

## 3. Limites de Sécurité (BusinessLimits)

Pour éviter les boucles infinies ou les consommations de mémoire excessives, l'engine plafonne nativement le nombre d'occurrences :

| Base | Limite Max |
| --- | --- |
| Daily | 366 (1 an) |
| Weekly | 52 |
| Monthly | 12 |
| Fortnight | 26 |
| Quarter | 4 |

---
Voici le complément de documentation pour le `FrequencyEngine`, incluant des cas d'usage avancés et la modélisation UML du système.

---

## 4. Exemples d'Instructions Complexes

Le moteur permet de combiner plusieurs logiques pour répondre à des besoins métier précis :

| Type de besoin | Instruction DSL | Analyse du comportement |
| --- | --- | --- |
| **Séquences variables** | `today@sequence#1,2,5d@10` | Génère 10 occurrences avec un saut de 1 jour, puis 2, puis 5, avant de recommencer le cycle. |
| **Trimestres spécifiques** | `2026-01-01@quarter#lastfri@∞` | Calcule le dernier vendredi de chaque trimestre (Mars, Juin, Sept., Déc.) pour l'année 2026. |
| **Exclusion combinée** | `today@daily#1d@30!sat,sun,aug` | Calcule 30 jours consécutifs, mais retire tous les week-ends et l'intégralité du mois d'août du résultat final. |
| **Décalage ouvré** | `today@monthly#1@12|next_workday` | Calcule le 1er de chaque mois pendant un an. Si le 1er est un dimanche, l'occurrence est décalée au lundi 2. |

---

## 5. Algorithme de Calcul Ordinal (Détail)

L'un des points forts de l'engine est sa capacité à gérer les "ancres" mobiles au sein d'un mois. Voici le pseudo-code logique pour une instruction de type `monthly#lastfri` :

1. **Cible** : Identifier le mois  de l'itération .
2. **Point de départ** : Se positionner au dernier jour du mois  (ex: 31 Janvier).
3. **Boucle de recherche** :
* Vérifier si le jour actuel est un Vendredi (`fri`).
* Si non, soustraire 1 jour et recommencer.


4. **Validation** : Une fois le vendredi trouvé, fixer l'occurrence à minuit (00:00:00).

---


## 6. Gestion des Erreurs et Exceptions

Le `FrequencyEngine` est conçu pour être "fail-fast". Il valide l'intégrité de l'instruction DSL avant de lancer toute boucle de génération afin d'éviter les calculs incohérents.

### Types d'Exceptions levées

Le moteur lève principalement une `ValueError` avec un message explicite dans les cas suivants :

* **Format Incomplet** : Si l'instruction ne contient pas au moins les trois segments de base (`START@CADENCE@LIMITS`).
* **Cadence Inconnue** : Si le mot-clé de base (ex: `monthly`) ne fait pas partie de la liste des bases supportées.
* **Segments Invalides** :
* Limite numérique négative.
* Format de durée relative (`+...`) mal formé (ex: `+2x` au lieu de `+2w`).
* Date de fin ou de début impossible à parser par Pendulum.


* **Erreurs de Calcul** : Toute exception imprévue durant la génération (comme un mois inexistant) est interceptée et encapsulée dans une `ValueError` pour ne pas faire planter le thread appelant.

### Sécurités Anti-Boucle (BusinessLimits)

En plus des exceptions de syntaxe, le moteur applique des **limites silencieuses**. Si un utilisateur demande une fréquence infinie (`∞`) sans date de fin, le moteur s'arrête automatiquement après avoir atteint le quota défini dans `BusinessLimits` pour protéger la mémoire du serveur.

---

## Synthèse du Workflow de Validation

```python
try:
    occurrences = engine.get_occurrences("today@daily#1d@∞")
except ValueError as e:
    # Capturer ici les erreurs de syntaxe DSL ("Instruction de fréquence invalide")
    log.error(f"Erreur de saisie utilisateur : {e}")

```


---
## Annexe : Organisation


### Description des composants :

* **FrequencyEngine** : La classe maîtresse contenant la méthode publique `get_occurrences`. Elle encapsule la logique de parsing et de génération.
* **BusinessLimits** : Une `dataclass` immuable injectée à l'initialisation. Elle sert de "garde-fou" pour empêcher la génération de volumes de données excessifs (ex: limiter le quotidien à 366 itérations).
* **HolidayService** : Service externe injecté utilisé par le modificateur `|next_workday` pour identifier les jours non ouvrés au-delà des simples week-ends.
* **Pendulum (Dépendance)** : Le moteur s'appuie exclusivement sur Pendulum pour la manipulation complexe des fuseaux horaires et les ajouts/soustractions de durées relatives (`add(months=1)`, `end_of('month')`).

---
