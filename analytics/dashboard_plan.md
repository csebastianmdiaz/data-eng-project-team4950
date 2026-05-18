# Dashboard Plan: Global Fishing Trends (1950–2018)
## Amazon QuickSight — connected to Athena / fishdb

### Story the dashboard tells:
> "The ocean is not infinite. This dashboard traces 70 years of global fishing —
> how much we caught, who caught it, where, and at what cost to the sea."

---

## Visualization 1 — Line chart: Global catch over time
**View:** `v1_global_catch_trend`
**X axis:** year | **Y axis:** total_tonnes
**Title:** "Global Fish Catch 1950–2018"
**What it answers:** Did we catch more or less fish over time? Where is the peak?
**Expected insight:** Peak around 1990s, followed by stagnation/decline — classic overfishing signal.

---

## Visualization 2 — Horizontal bar chart: Top 10 fishing nations
**View:** `v2_top_fishing_entities`
**X axis:** total_tonnes | **Y axis:** fishing_entity
**Title:** "Top 10 Countries by Total Catch (all years)"
**What it answers:** Which nations dominate global fishing?
**Expected insight:** China, Peru, Japan historically dominate.

---

## Visualization 3 — Stacked area chart: Reported vs unreported catch
**View:** `v3_reporting_status_trend`
**X axis:** year | **Y axis:** total_tonnes | **Color:** reporting_status
**Title:** "Reported vs Unreported Catch Over Time"
**What it answers:** How much illegal/unregulated fishing exists, and is it growing?
**Expected insight:** Unreported catch is a significant and persistent share — exposes IUU fishing.

---

## Visualization 4 — Line chart: High Seas vs EEZ pressure
**View:** `v4_highseas_vs_eez`
**X axis:** year | **Y axis:** total_tonnes | **Color:** zone
**Title:** "Fishing Pressure: High Seas vs Coastal Waters"
**What it answers:** Are fishers moving further offshore as coastal stocks decline?
**Expected insight:** Shift toward high seas over decades as EEZ stocks deplete.

---

## How to connect QuickSight to Athena

1. Open QuickSight → **Datasets** → **New dataset**
2. Select **Athena** as data source
3. Name it `fishdb-athena`, select workgroup `primary`
4. Select database `fishdb`
5. For each visualization, select the corresponding view as the dataset
6. Build each chart as described above

---

## Files to submit

| File | Status |
|------|--------|
| `analytics/v1_global_catch_trend.sql` | ✅ Ready |
| `analytics/v2_top_fishing_entities.sql` | ✅ Ready |
| `analytics/v3_reporting_status_trend.sql` | ✅ Ready |
| `analytics/v4_highseas_vs_eez.sql` | ✅ Ready |
| `analytics/v5_gear_efficiency.sql` | ✅ Ready |
| `analytics/v6_top_species_trend.sql` | ✅ Ready |
| `analytics/benchmark.md` | ✅ Ready (fill numbers after running) |
| `analytics/dashboard.pdf` | ⏳ After QuickSight screenshots |
