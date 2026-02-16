
# Technical Documentation: Frequency Engine

The `FrequencyEngine` is the core logic for temporal calculations. Its role is to transform a normalized domain-specific language (DSL) instruction into a list of `pendulum.DateTime` objects while respecting business limits and calendar constraints such as holidays and weekends.

## 1. Instruction Structure

The engine processes strings using the following format:
`[START]@[CADENCE]@[LIMITS]![EXCLUSIONS]|[MODIFIERS]`

* **START**: The anchor date (`today`, `tomorrow`, or `YYYY-MM-DD`).
* **CADENCE**: The temporal base and interval (e.g., `monthly#1`, `weekly#mon,fri`).
* **LIMITS**: Number of occurrences (`12`), an end date (`2026-12-31`), a relative duration (`+2m`), or infinity (`∞`).
* **EXCLUSIONS**: Days or months to ignore (e.g., `!sat,sun`, `!aug`).
* **MODIFIERS**: Post-generation adjustments (e.g., `|next_workday`).

---

## 2. Generation Algorithm

The algorithm follows a linear five-step workflow:

### Step A: Initialization and Parsing

1. **Extraction**: Splitting the instruction using the `@` separator.
2. **Anchoring**: Calculating the `start_date`. If a specific month is requested (e.g., `@oct`), the cursor moves to the 1st of that month.
3. **Final Limit Calculation**:
* The engine retrieves the safety limit (`BusinessLimits`) for the chosen base (e.g., 366 for `daily`, 12 for `monthly`).
* It compares this safety limit with the user's request (`limit_attr`), and the lower value is used.



### Step B: Base Logic Branching

The engine directs the calculation toward three types of loops:

* **Weekly Logic (`weekly`)**: If specific days are provided (`#mon`), the engine increments day by day starting from `start_date + 1` until the quota is met.
* **Sequence Logic (`sequence`)**: Uses mathematical offsets to handle complex cycles (e.g., "every 1, 2, and 4 days").
* **Standard Logic (Iterative loop)**: For other bases (`daily`, `monthly`, `yearly`, etc.), the engine calculates each occurrence by adding the interval to the start date.

### Step C: Ordinal Logic (The "Monthly Brain")

For complex frequencies such as "The last Friday of the month" (`monthly#lastfri`) or "The 2nd workday" (`monthly#workday#2`):

1. It positions itself at the beginning or end of the target month.
2. It iterates (forward or backward) until it finds the day matching the predicate.
3. It validates that the found date belongs to the current month.

### Step D: Post-processing (Filtering and Pipes)

Once the raw list is generated, two filters are applied:

1. **Exclusions (`!`)**: Removes dates if the month (`aug`) or day (`sat`) matches.
2. **Modifiers (`|`)**: If `|next_workday` is present, any date falling on a weekend or holiday is shifted to the next business day via the `HolidayService`.

### Step E: Finalization

* Removal of duplicates using a `set`.
* Chronological sorting.
* Final slicing to strictly respect the requested limit.

---

## 3. Safety Limits (BusinessLimits)

To prevent infinite loops or excessive memory consumption, the engine natively caps the number of occurrences:

| Base | Max Limit |
| --- | --- |
| Daily | 366 (1 year) |
| Weekly | 52 |
| Monthly | 12 |
| Fortnight | 26 |
| Quarter | 4 |

---

## 4. Complex Instruction Examples

The engine combines different logics to meet specific business needs:

| Business Need | DSL Instruction | Behavior Analysis |
| --- | --- | --- |
| **Variable sequences** | `today@sequence#1,2,5d@10` | Generates 10 occurrences with jumps of 1 day, then 2, then 5, before restarting the cycle. |
| **Specific quarters** | `2026-01-01@quarter#lastfri@∞` | Calculates the last Friday of each quarter (March, June, Sept., Dec.) for 2026. |
| **Combined exclusion** | `today@daily#1d@30!sat,sun,aug` | Calculates 30 consecutive days but removes all weekends and the entire month of August from the final result. |
| **Workday shift** | `today@monthly#1@12|next_workday` | Calculates the 1st of each month for a year. If the 1st is a Sunday, the occurrence shifts to Monday the 2nd. |

---

## 5. Ordinal Calculation Algorithm (Details)

A key feature is the ability to handle moving anchors within a month. Here is the logic for `monthly#lastfri`:

1. **Target**: Identify the month of the current iteration.
2. **Starting Point**: Move to the last day of that month (e.g., January 31st).
3. **Search Loop**:
* Check if the current day is a Friday (`fri`).
* If not, subtract 1 day and repeat.


4. **Validation**: Once Friday is found, set the occurrence time to midnight (00:00:00).

---

## 6. Error Handling and Exceptions

The `FrequencyEngine` is designed to be "fail-fast." It validates the DSL instruction integrity before starting any generation loops to avoid inconsistent calculations.

### Raised Exceptions

The engine primarily raises a `ValueError` with an explicit message in the following cases:

* **Incomplete Format**: The instruction lacks at least the three base segments (`START@CADENCE@LIMITS`).
* **Unknown Cadence**: The base keyword (e.g., `monthly`) is not supported.
* **Invalid Segments**:
* Negative numerical limits.
* Malformed relative duration (`+...`) formats (e.g., `+2x` instead of `+2w`).
* Start or end dates that Pendulum cannot parse.


* **Calculation Errors**: Unexpected exceptions during generation are caught and wrapped in a `ValueError` to prevent the calling thread from crashing.

### Anti-Loop Protections

In addition to syntax exceptions, the engine applies **silent limits**. If a user requests an infinite frequency (`∞`) without an end date, the engine automatically stops after reaching the quota defined in `BusinessLimits`.

---

## Validation Workflow Synthesis

```python
try:
    occurrences = engine.get_occurrences("today@daily#1d@∞")
except ValueError as e:
    # Catch DSL syntax errors here ("Invalid frequency instruction")
    log.error(f"User input error: {e}")

```

---

## Appendix: Organization

### Component Description:

* **FrequencyEngine**: The main class containing the public `get_occurrences` method. It encapsulates parsing and generation logic.
* **BusinessLimits**: An immutable `dataclass` injected at initialization. It serves as a safeguard against excessive data generation.
* **HolidayService**: An injected external service used by the `|next_workday` modifier to identify non-working days.
* **Pendulum (Dependency)** : The engine relies on Pendulum for timezone manipulation and relative duration calculations.
