# Data quality rules

## Overview

| ID | Rule | Files | Severity |
|---|---|---|---|
| DQ-01 | Year range 1950–2018 | All (EEZ-848 fails) | Critical |
| DQ-02 | Tonnes ≥ 0 | All | Critical |
| DQ-03 | Nulls in landed_value < 20% | EEZ-848 at limit | Critical |
| DQ-04 | Column rename applied correctly | EEZ-242, EEZ-848 | Critical |
| DQ-05 | Uncertainty score in valid range | EEZ-242, EEZ-848 | Warning |
| DQ-06 | Consistency between tonnes and landed_value | All | Warning |
| DQ-07 | Referential integrity of countries | HighSeas, EEZs | Warning |
| DQ-08 | No ghost tonnes (< 1e-6) | EEZ-848 mainly | Info |

---

## DQ-01 — Temporal validity

**Columns:** `year`  
**Files:** All four  
**Severity:** Critical

**Business justification:** The Sea Around Us dataset covers fishing activity from 1950 to 2018 according to the official source documentation. Any year outside this range indicates data corruption or use of an incorrect file version. During profiling, EEZ-848 was found to contain rows with `year = 2019`, which falls outside the documented range.

```python
for name, df in files.items():
    invalid = df[~df['year'].between(1950, 2018)]
    assert len(invalid) == 0, \
        f"[{name}] Years out of range: {invalid['year'].unique()}"
```

---

## DQ-02 — Non-negative tonnes

**Columns:** `tonnes`  
**Files:** All four  
**Severity:** Critical

**Business justification:** Tonnes represent physical fish catch weight. A negative value has no physical meaning and would indicate a data entry or transformation error. Profiling showed the minimum observed value is `1.6e-9` (near zero but valid) across all files — no negatives were found, but this rule enforces that guarantee going forward.

```python
for name, df in files.items():
    assert (df['tonnes'] >= 0).all(), \
        f"[{name}] Negative tonnes found: {df[df['tonnes'] < 0].shape[0]} rows"
```

---

## DQ-03 — Null rate in landed_value below threshold

**Columns:** `landed_value`  
**Files:** All four  
**Severity:** Critical

**Business justification:** `landed_value` is the primary economic metric in US dollars (2010 baseline). GLOBAL and HighSeas have 0 nulls. EEZ-848 has 15,289 nulls out of 83,175 rows (18.4%), which is documented and accepted as it reflects unreported catches in the source data. Any file exceeding 20% nulls would indicate a pipeline ingestion failure rather than expected missing data.

```python
for name, df in files.items():
    pct = df['landed_value'].isnull().mean() * 100
    assert pct < 20, \
        f"[{name}] landed_value has {pct:.1f}% nulls — exceeds 20% threshold"
```

---

## DQ-04 — Column rename correctly applied by Role 1

**Columns:** `fish_name`, `country`, `common_name`, `fishing_entity`  
**Files:** EEZ-242, EEZ-848  
**Severity:** Critical

**Business justification:** The EEZ files originally use `fish_name` and `country` instead of `common_name` and `fishing_entity`. Role 1 is responsible for renaming these columns before Parquet conversion. If the rename was not applied, all Athena queries that reference `common_name` or `fishing_entity` will silently return empty results instead of raising an error. This rule explicitly validates that the upstream transformation was executed correctly.

```python
for name, df in files.items():
    assert 'fish_name' not in df.columns, \
        f"[{name}] Column 'fish_name' was not renamed by Role 1"
    assert 'country' not in df.columns, \
        f"[{name}] Column 'country' was not renamed by Role 1"
    assert 'common_name' in df.columns, \
        f"[{name}] Missing expected column 'common_name'"
    assert 'fishing_entity' in df.columns, \
        f"[{name}] Missing expected column 'fishing_entity'"
```

---

## DQ-05 — Uncertainty score within valid range

**Columns:** `uncertainty_score`  
**Files:** EEZ-242, EEZ-848  
**Severity:** Warning

**Business justification:** `uncertainty_score` represents the confidence level assigned to each catch estimate. Profiling confirmed different valid ranges per file: EEZ-242 uses a 0–3 scale and EEZ-848 uses a 2–4 scale. A value outside the expected range for its file indicates either data corruption or a version mismatch. This rule is a Warning rather than Critical because the column is nullable (EEZ-242 has 18,781 nulls; EEZ-848 has 5,771 nulls), and nulls are expected and accepted.

```python
eez_ranges = {
    "EEZ_Fiji": (0, 3),
    "EEZ_848":  (2, 4),
}
for name, (lo, hi) in eez_ranges.items():
    valid = files[name]['uncertainty_score'].dropna()
    invalid = valid[~valid.between(lo, hi)]
    assert len(invalid) == 0, \
        f"[{name}] uncertainty_score out of [{lo}, {hi}]: {invalid.unique()}"
```

---

## DQ-06 — Consistency between tonnes and landed_value

**Columns:** `tonnes`, `landed_value`  
**Files:** All four  
**Severity:** Warning

**Business justification:** If a fishing entity reports a non-zero catch weight 
(tonnes > 0), it should also report a non-zero economic value (landed_value > 0). 
A row with measurable catch but zero landed value is suspicious — it either indicates 
a data entry error, a transformation issue in the pipeline, or an unreported valuation. 
While some catches may genuinely have near-zero value, an exact zero paired with a 
positive tonnage warrants investigation before being used in economic aggregations in 
Athena views and QuickSight dashboards. 

```python
for name, df in files.items():
    mask = (df['tonnes'] > 0) & (df['landed_value'] == 0)
    assert mask.sum() == 0, \
        f"[{name}] {mask.sum()} rows with tonnes > 0 but landed_value == 0"
```

---

## DQ-07 — Referential integrity of fishing entities

**Columns:** `fishing_entity`  
**Files:** HighSeas, EEZ-242, EEZ-848 validated against GLOBAL  
**Severity:** Warning

**Business justification:** The GLOBAL file contains catch data for all fishing nations worldwide and serves as the authoritative reference for entity names. Any country appearing in the HighSeas or EEZ files but absent from GLOBAL suggests a naming inconsistency (e.g. `"Fiji"` vs `"Fji"`). Such inconsistencies would silently break JOIN operations in Athena and produce incomplete results in cross-source queries.

```python
global_entities = set(files["GLOBAL"]['fishing_entity'].unique())

for name in ["HighSeas", "EEZ_Fiji", "EEZ_848"]:
    entities = set(files[name]['fishing_entity'].unique())
    orphans = entities - global_entities
    assert len(orphans) == 0, \
        f"[{name}] Entities not found in GLOBAL: {orphans}"
```

---

## DQ-08 — No ghost values in tonnes

**Columns:** `tonnes`  
**Files:** All four, primarily EEZ-848  
**Severity:** Info

**Business justification:** Profiling revealed a minimum tonnes value of `1.6e-9` in EEZ-848. Values below `1e-6` tonnes are physically negligible (less than one milligram of fish) and are likely the result of floating-point approximation errors in the source data. While not blocking, a high proportion of such rows would distort averages and percentile calculations in analytical queries. This rule logs a warning when more than 1% of rows fall below the threshold.

```python
threshold = 1e-6
for name, df in files.items():
    ghost = df[df['tonnes'] < threshold]
    pct = len(ghost) / len(df) * 100
    if pct > 1:
        print(f"WARNING [{name}] {pct:.2f}% of rows have tonnes < {threshold}")
```