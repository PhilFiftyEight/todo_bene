Here is the complete and faithful English translation of your documentation, including the updated reference table with all 32 test cases translated for English-speaking readers.

---

# 📖 Frequency Parser Specification (V1.0)

The parser returns a technical string containing instructions for the repetition engine.

## 1. String Structure

Each parser output follows a segmented structure separated by the `@` symbol:

> **Format:** `start_date@cadence@limit|shift!exceptions`

| Segment | Name | Description |
| --- | --- | --- |
| **1** | `start_date` | Calculation starting point (default value: `today`). |
| **2** | `cadence` | The technical repetition rule (e.g., `weekly#1mon`). |
| **3** | `limit` | The stop condition (`∞`, fixed number, duration `+`, or date `YYYY-MM-DD`). |
| **4** | `shift` | (Optional) Modifier after ` |
| **5** | `exceptions` | (Optional) Excluded days after `!`. |

---

## 2. Limit Typology (`limit`)

The Engine must interpret the third segment according to these four formats:

* **Infinite (`∞`)**: No end date.
* **Fixed (`5`)**: Total number of occurrences to generate.
* **Relative (`+2w`, `+6m`, `+1y`)**: Calendar duration starting from `today`.
* **Date (`2026-06-30`)**: Absolute stop date (inclusive).

---

## 3. Test Reference Table (32 Cases)

This section lists the exact correspondences validated by the unit test suite and serves as a reference for expected system behavior.

### A. Simple Intervals and Sequences

| Input (FR/EN) | Parser Result | Engine Note |
| --- | --- | --- |
| "Every day" | `today@daily#1d@∞` | Infinite daily repetition. |
| "Every 2 weeks" | `today@weekly#2w@∞` | 2-week interval. |
| "Every 3 weeks" | `today@weekly#3w@∞` | 3-week jump. |
| "1, 2, 3 days" | `today@sequence#1,2,3d@3` | Unitary sequence of 3 days. |
| "10, 20 days" | `today@sequence#10,20d@2` | Sequence of 2 specific dates. |
| "1, 2, 4, 8, 16 days" | `today@sequence#1,2,4,8,16d@5` | Generates 5 specific dates at D+1, D+2, etc. |
| "Next 5 days" | `today@sequence#1,2,3,4,5d@5` | Unitary sequence of 5 days. |
| "Next 3 months" | `today@sequence#1,2,3m@3` | 1 occurrence per month for 3 months. |

### B. Specific and Multiple Days

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Monday and Thursday" | `today@weekly#1mon,thu@1` | Limited to 1 (implicit request). |
| "Monday, Wednesday and Friday" | `today@weekly#1mon,wed,fri@1` | Limited to 1. |
| "Every Monday" | `today@weekly#1mon@∞` | Every Monday indefinitely. |

### C. Durations and Complex Limits

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Every Monday for 1 month" | `today@weekly#1mon@+1m` | Stops after 1 calendar month. |
| "Every day for 15 days" | `today@daily#1d@+15d` | Relative duration in days. |
| "Monday and Wednesday for 2 weeks" | `today@weekly#1mon,wed@+2w` | Stops after 2 weeks. |
| "Every 2 weeks for 6 months" | `today@weekly#2w@+6m` | Cadence vs Duration arbitration. |
| "Next 5 days for 2 weeks" | `today@sequence#1,2,3,4,5d@+2w` | Duration `+2w` overrides limit `5`. |
| "Every day for the next 2 weeks" | `today@daily#1d@+2w` | Daily repetition on fixed duration. |
| "Every 2 weeks for 3 months" | `today@weekly#2w@+3m` | Mixed units arbitration. |

### D. Dynamic End Dates (Frozen Time: 2026-02-09)

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "...until the end of the month" | `... @2026-02-28` | Calculated on the current month. |
| "...until the end of the semester" | `... @2026-06-30` | End of S1 or S2. |
| "...until June 15th" | `... @2026-06-15` | Fixed date. |
| "...until January 1st" | `... @2027-01-01` | Targets next year if date has passed. |

### E. Relative Positions and Workdays (Ordinals)

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "135th day of the year" | `today@yearly#135thday@∞` | Absolute yearly position. |
| "27th day of the quarter" | `today@quarter#27thday@∞` | Position in the quarter cycle. |
| "2nd workday of the month" | `today@monthly#2ndworkday@∞` | Requires workday calendar. |
| "Last Friday of the quarter" | `today@quarter#lastfri@∞` | End of quarterly cycle. |
| "Last Friday of every month" | `today@monthly#lastfri@∞` | Monthly relative position. |
| "Last Friday of the year" | `today@yearly#lastfri@∞` | End of yearly cycle. |

### F. Exceptions, Shifts and Robustness

| Input | Parser Result | Engine Note |
| --- | --- | --- |
| "Every day except Monday" | `... @∞!mon` | Remove Mondays from occurrences. |
| "...except Saturday and Sunday" | `... @∞!sat,sun` | Weekend filter. |
| "Every day but not on Wed for 2 weeks" | `daily#1d@+2w!wed` | Exception on limited duration. |
| "Every Monday except in August" | `today@weekly#1mon@∞!aug` | Monthly exclusion (long name). |
| "Every Monday except in 08" | `today@weekly#1mon@∞!aug` | Monthly exclusion (numeric). |
| "1st of the month, shift if WE" | `today@monthly#1stday@∞ | next_workday` |
| "5th of the month, shift if non-workday" | `today@monthly#5thday@∞ | next_workday` |
| "1 m," (Trailing comma) | `today@monthly#1stday@∞` | Comma ignored. |
| "5 m" (Short form) | `today@monthly#5thday@∞` | Technical form understood. |

---

## 5. Implementation Guidelines for the Engine

The Engine's role is to transform the technical string into a list of `pendulum.DateTime` objects. Here are the guiding principles for development:

### A. The Generator Loop

* **Initialization**: Always start from the `start_date` (e.g., `today`).
* **Iteration**: Use the `cadence` to calculate the next occurrence.
* **Limit Validation**: Before adding a date to the list, verify if it respects the `limit`:
* If `limit` is a **number**: Stop when `len(dates) == limit`.
* If `limit` is a **date**: Stop if `next_date > limit`.
* If `limit` is a **duration** (e.g., `+3m`): Calculate `end_date = start_date + duration` at the beginning, then treat it as a fixed date limit.



### B. Exceptions Management (`!`)

* The exception filter must be applied **after** calculating the cadence date but **before** checking the limit.
* If a date falls on an excluded day (e.g., `!wed`), it is ignored and does not count toward the numerical limit (if applicable).

### C. Applying the Shift (`|shift`)

* The shift is the **final transformation step** for each generated date.
* If `|next_workday` is present:
1. Check if the date is a weekend (Saturday/Sunday).
2. Check if the date is a public holiday (requires an external holiday table).
3. As long as the condition is true, add `+1 day` to the date.



### D. Order of Operations (Priority of Calculation)

For each occurrence, the Engine must follow this strict order:

1. **Generate**: Calculate the -th date according to the rule (e.g., `monthly#1stday`).
2. **Filter**: Check exceptions `!`. If excluded, move to .
3. **Shift**: Apply the report `|` if necessary to land on a workday.
4. **Terminate**: Verify if the final date exceeds the `@limit`.

### E. Pattern Collisions

To prevent conflicts between expressions (e.g., "Every month" stealing the match from "Last Friday of every month"), the system relies on three pillars:

* **Numerical Priority**: Complex extractors (`RelativePositionExtractor`) have a higher priority (smaller value, e.g., 10) than simple extractors (e.g., 15 or 20). **Specificity** wins over **Generality**.
* **Strict Anchoring**: Simple extractors use the `^` anchor to ensure they do not capture a partial string at the end of a complex command. **Anchoring** acts as a shield.
* **Exception Post-Processing**: Exclusions (after the `!`) are cleaned of stopwords, and numeric month codes are converted into technical labels (e.g., `08` -> `aug`) to ensure final format consistency.

---

## Appendix: Test Case Catalog (32 Scenarios)

This section lists the exact correspondences validated by the unit test suite.

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
* **Every day for 15 days**: `daily#1d@+15d`
* **Monday and Wednesday for 2 weeks**: `weekly#1mon,wed@+2w`
* **Every 2 weeks for 6 months**: `weekly#2w@+6m`
* **Next 5 days for 2 weeks**: `sequence#1,2,3,4,5d@+2w` (Arbitration: duration overrides count).
* **Every day for the next 2 weeks**: `daily#1d@+2w`

### 4. Calendar Limits (Reference Date: 02/09/2026)

* **Until the end of the month**: `daily#1d@2026-02-28`
* **Until the end of the semester**: `weekly#1mon@2026-06-30`
* **Until June 15th**: `weekly#1fri@2026-06-15`
* **Until January 1st**: `daily#1d@2027-01-01` (Targets next year).

### 5. Positions and Civil Calendar

* **135th day of the year**: `yearly#135thday@∞`
* **27th day of the quarter**: `quarter#27thday@∞`
* **2nd workday of the month**: `monthly#2ndworkday@∞`
* **Last Friday of the year**: `yearly#lastfri@∞`

### 6. Exceptions and Shifts (Robustness)

* **Except Monday**: `daily#1d@∞!mon`
* **Except Saturday and Sunday**: `daily#1d@∞!sat,sun`
* **Every day but not on Wed for 2 weeks**: `daily#1d@+2w!wed`
* **1st of the month, shift if weekend**: `monthly#1stday@∞|next_workday`
* **5th of the month, shift if non-workday**: `monthly#5thday@∞|next_workday`
* **Last Friday of the quarter, shift if holiday**: `quarter#lastfri@∞|next_workday`

### 7. Complex Relative Positions

Handles specific ranks within a given period, including workdays and long ordinals.

* **The 135th day of the year**: `today@yearly#135thday@∞`
* **The 2nd workday of the month**: `today@monthly#2ndworkday@∞`
* **The last Friday of the quarter**: `today@quarter#lastfri@∞`
* **The last Friday of every month**: `today@monthly#lastfri@∞`

### 8. Exclusions and Exceptions (Months)

Ability to exclude full months using long names or numeric codes.

* **Every Monday except in August**: `today@weekly#1mon@∞!aug`
* **Every Monday except in 08**: `today@weekly#1mon@∞!aug`

---
