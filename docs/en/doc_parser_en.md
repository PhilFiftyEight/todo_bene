
---

# 📖 Frequency Parser Specification (Doc V1.0)

The parser returns a technical string containing instructions for the repetition engine.

## 1. String Structure

Each parser output follows a segmented structure using the `@` symbol:

> **Format:** `start_date@cadence@limit|shift!exceptions`

| Segment | Name | Description |
| --- | --- | --- |
| **1** | `start_date` | Calculation starting point (defaults to `today`). |
| **2** | `cadence` | Technical repetition rule (e.g., `weekly#1mon`). |
| **3** | `limit` | Stop condition (`∞`, fixed number, duration `+`, or date `YYYY-MM-DD`). |
| **4** | `shift` | (Optional) Modifier after ` |
| **5** | `exceptions` | (Optional) Excluded days after `!`. |

---

## 2. Limit Typology (`limit`)

The Engine must interpret the third segment according to these four formats:

* **Infinite (`∞`)**: No end date.
* **Fixed (`5`)**: Total number of occurrences to generate.
* **Relative (`+2w`, `+6m`, `+1y`)**: Calendar duration starting from `today`.
* **Date (`2026-06-30`)**: Absolute end date (inclusive).

---

## 3. Test Reference Table (27 Cases)

Below is the full set of behaviors validated by the test suite:

### A. Simple Intervals and Sequences

| Input (FR/EN) | Parser Result | Engine Note |
| --- | --- | --- |
| "Chaque jour" | `today@daily#1d@∞` | Infinite daily repetition. |
| "Every 3 weeks" | `today@weekly#3w@∞` | 3-week interval skip. |
| "1, 2, 4, 8, 16 jours" | `today@sequence#1,2,4,8,16d@5` | Generates 5 precise dates at D+1, D+2, etc. |
| "Les 5 prochains jours" | `today@sequence#1,2,3,4,5d@5` | Unitary sequence of 5 days. |
| "Les 3 prochains mois" | `today@sequence#1,2,3m@3` | 1 occurrence per month for 3 months. |

### B. Specific and Multiple Days

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Lundi et Jeudi" | `today@weekly#1mon,thu@1` | Limit to 1 (implicit request). |
| "Lundi, Mercredi et Vendredi" | `today@weekly#1mon,wed,fri@1` | Limit to 1. |
| "Tous les lundis" | `today@weekly#1mon@∞` | Every Monday, no end. |

### C. Complex Durations and Limits

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Tous les lundis pour 1 mois" | `today@weekly#1mon@+1m` | Stop after 1 calendar month. |
| "Toutes les 2 semaines pour 6 mois" | `today@weekly#2w@+6m` | Cadence vs Duration arbitration. |
| "Les 5 prochains jours pendant 2 sem." | `today@sequence#1,2,3,4,5d@+2w` | Duration `+2w` overrides limit `5`. |
| "Toutes les 2 sem. pendant 3 mois" | `today@weekly#2w@+3m` | **Bonus Test**: Mixed units arbitration. |

### D. Dynamic End Dates (Frozen Time: 2026-02-09)

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "...jusqu'à la fin du mois" | `... @2026-02-28` | Calculated on the current month. |
| "...jusqu'à la fin du semestre" | `... @2026-06-30` | End of H1 or H2. |
| "...jusqu'au 15 juin" | `... @2026-06-15` | Fixed date. |
| "...jusqu'au 1er janvier" | `... @2027-01-01` | Targets next year if already passed. |

### E. Relative and Working Positions (Ordinals)

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "135ème jour de l'année" | `today@yearly#135thday@∞` | Yearly absolute position. |
| "27ème jour du trimestre" | `today@quarter#27thday@∞` | Position within the quarter cycle. |
| "2ème jour ouvré du mois" | `today@monthly#2ndworkday@∞` | Requires working days calendar. |
| "The last friday of the year" | `today@yearly#lastfri@∞` | End of cycle. |

### F. Exceptions and Reports (Shifts)

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Chaque jour sauf le lundi" | `... @∞!mon` | Remove Mondays from occurrences. |
| "...sauf samedi et dimanche" | `... @∞!sat,sun` | Weekend filter. |
| "1er du mois, reporter si WE" | `today@monthly#1stday@∞ | next_workday` |
| "Le 5 du mois décaler si non ouvré" | `today@monthly#5thday@∞ | next_workday` |
| "1 m," (Trailing comma) | `today@monthly#1stday@∞` | **Robustness**: Comma ignored. |
| "5 m" (Short form) | `today@monthly#5thday@∞` | **Robustness**: Technical form understood. |

---

## 5. Implementation Guidelines for the Engine

The Engine's role is to transform the technical string into a list of `pendulum.DateTime` objects. Here are the guiding principles for development:

### A. The Generator Loop

* **Initialization**: Always start from the `start_date` (e.g., `today`).
* **Iteration**: Use the `cadence` to calculate the next occurrence.
* **Limit Validation**: Before adding a date to the list, check if it respects the `limit`:
* If `limit` is a **number**: Stop when `len(dates) == limit`.
* If `limit` is a **date**: Stop if `next_date > limit`.
* If `limit` is a **duration** (e.g., `+3m`): Calculate `end_date = start_date + duration` at the beginning, then treat as a fixed end date.



### B. Exception Handling (`!`)

* The exception filter must be applied **after** calculating the cadence date but **before** checking the limit.
* If a date falls on an excluded day (e.g., `!wed`), it is ignored and does not count toward the numeric limit (if applicable).

### C. Shift Application (`|shift`)

* The shift is the **final step** of transformation for each generated date.
* If `|next_workday` is present:
1. Check if the date is a weekend (Saturday/Sunday).
2. Check if the date is a public holiday (requires an external holiday table).
3. As long as the condition is true, add `+1 day` to the date.



### D. Order of Operations

For each occurrence, the Engine must follow this strict order:

1. **Generate**: Calculate the -th date based on the rule (e.g., `monthly#1stday`).
2. **Filter**: Check exceptions `!`. If excluded, proceed to .
3. **Shift**: Apply the `|` shift if necessary to land on a working day.
4. **Terminate**: Verify if the final date exceeds the `@limit`.

---

## Annex: Test Case Catalog (27 Scenarios)

This section lists the exact mappings validated by the unit test suite. It serves as a reference for expected system behavior.

### 1. Configuration and Fallbacks

* **Unknown Language**: If `language="de"`, the system defaults to `"en"`.
* **Multilingual Contexts**: "Toutes les 3 semaines" (FR) and "Every 3 weeks" (EN) both produce `weekly#3w@∞`.

### 2. Intervals and Sequences (Simple & Multi)

* **Every day**: `daily#1d@∞`
* **Every 2 weeks**: `weekly#2w@∞`
* **Monday and Thursday**: `weekly#1mon,thu@1`
* **Monday, Wednesday and Friday**: `weekly#1mon,wed,fri@1`
* **1, 2, 3 days**: `sequence#1,2,3d@3`
* **10, 20 days**: `sequence#10,20d@2`
* **1, 2, 4, 8, 16 days**: `sequence#1,2,4,8,16d@5`

### 3. Durations and Explicit Limits

* **Next 5 days**: `sequence#1,2,3,4,5d@5`
* **Next 3 weeks**: `sequence#1,2,3w@3`
* **Every Monday for 1 month**: `weekly#1mon@+1m`
* **Daily for 15 days**: `daily#1d@+15d`
* **Monday and Wednesday for 2 weeks**: `weekly#1mon,wed@+2w`
* **Every 2 weeks for 6 months**: `weekly#2w@+6m`
* **Next 5 days for 2 weeks**: `sequence#1,2,3,4,5d@+2w` (Arbitration: duration wins over count).
* **Daily for the next 2 weeks**: `daily#1d@+2w`

### 4. Calendar Limits (Frozen Time: 2026-02-09)

* **Until end of month**: `daily#1d@2026-02-28`
* **Until end of semester**: `weekly#1mon@2026-06-30`
* **Until June 15th**: `weekly#1fri@2026-06-15`
* **Until January 1st** (already passed): `daily#1d@2027-01-01` (Targets following year).

### 5. Positions and Civil Calendar

* **135th day of the year**: `yearly#135thday@∞`
* **27th day of the quarter**: `quarter#27thday@∞`
* **2nd working day of the month**: `monthly#2ndworkday@∞`
* **Last Friday of the year**: `yearly#lastfri@∞`

### 6. Exceptions and Reports (Robustness)

* **Except Monday**: `daily#1d@∞!mon`
* **Except Saturday and Sunday**: `daily#1d@∞!sat,sun`
* **Every day but not on Wed for 2 weeks**: `daily#1d@+2w!wed`
* **1st of the month, shift if weekend**: `monthly#1stday@∞|next_workday`
* **5th of the month shift if non-working day**: `monthly#5thday@∞|next_workday`
* **Last Friday of the quarter, shift if holiday**: `quarter#lastfri@∞|next_workday`

---