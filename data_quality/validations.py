import pandas as pd
import json
import os
from datetime import datetime
import boto3


#CONFIG
FILES = {
    "GLOBAL":   "s3://data-source-52143/processed/SAU-GLOBAL-1-v48-0.parquet",
    "HighSeas": "s3://data-source-52143/processed/SAU-HighSeas-71-v48-0.parquet",
    "EEZ_Fiji": "s3://data-source-52143/processed/SAU-EEZ-242-v48-0.parquet",
    "EEZ_848":  "s3://data-source-52143/processed/SAU_EEZ_848_v50_1.parquet",
}

#LOAD FILES
print("Loading files...")
files = {name: pd.read_parquet(path) for name, path in FILES.items()}
print(f"  GLOBAL:   {files['GLOBAL'].shape}")
print(f"  HighSeas: {files['HighSeas'].shape}")
print(f"  EEZ_Fiji: {files['EEZ_Fiji'].shape}")
print(f"  EEZ_848:  {files['EEZ_848'].shape}")

#RESULTS COLLECTOR
results = []

def record(rule_id, description, file, passed, failed_count, total, severity, detail=""):
    status = "PASSED" if passed else "FAILED"
    pct = f"{failed_count / total * 100:.2f}%" if total > 0 else "N/A"
    results.append({
        "rule_id":       rule_id,
        "description":   description,
        "file":          file,
        "status":        status,
        "failed_records": failed_count,
        "total_records": total,
        "failed_pct":    pct,
        "severity":      severity,
        "detail":        detail,
    })
    icon = "✓" if passed else "✗"
    print(f"  [{icon}] {rule_id} | {file:<10} | {status} | failed={failed_count}/{total} ({pct}) | {severity}")

#DQ-01 — Temporal validity (year between 1950–2018)
print("\nDQ-01: Temporal validity...")
for name, df in files.items():
    mask = ~df['year'].between(1950, 2018)
    failed = int(mask.sum())
    detail = str(df[mask]['year'].unique().tolist()) if failed > 0 else ""
    record("DQ-01", "Year range 1950–2018", name,
           passed=(failed == 0), failed_count=failed,
           total=len(df), severity="Critical", detail=detail)

#DQ-02 — Non-negative tonnes
print("\nDQ-02: Non-negative tonnes...")
for name, df in files.items():
    mask = df['tonnes'] < 0
    failed = int(mask.sum())
    record("DQ-02", "Tonnes >= 0", name,
           passed=(failed == 0), failed_count=failed,
           total=len(df), severity="Critical")

#DQ-03 — Null rate in landed_value below 20%
print("\nDQ-03: Null rate in landed_value...")
for name, df in files.items():
    null_count = int(df['landed_value'].isnull().sum())
    pct_null = null_count / len(df) * 100
    record("DQ-03", "Nulls in landed_value < 20%", name,
           passed=(pct_null < 20), failed_count=null_count,
           total=len(df), severity="Critical",
           detail=f"{pct_null:.1f}% nulls")

#DQ-04 — Column rename correctly applied
print("\nDQ-04: Column rename validation...")
for name, df in files.items():
    bad_cols   = [c for c in ['fish_name', 'country'] if c in df.columns]
    missing    = [c for c in ['common_name', 'fishing_entity'] if c not in df.columns]
    problems   = bad_cols + missing
    passed     = len(problems) == 0
    detail     = f"Bad columns: {problems}" if problems else ""
    record("DQ-04", "Rename fish_name→common_name, country→fishing_entity", name,
           passed=passed, failed_count=len(problems),
           total=4, severity="Critical", detail=detail)

#DQ-05 — Uncertainty score within valid range
print("\nDQ-05: Uncertainty score range...")
eez_ranges = {
    "EEZ_Fiji": (0, 3),
    "EEZ_848":  (2, 4),
}
for name, (lo, hi) in eez_ranges.items():
    df    = files[name]
    valid = df['uncertainty_score'].dropna()
    mask  = ~valid.between(lo, hi)
    failed = int(mask.sum())
    detail = str(valid[mask].unique().tolist()) if failed > 0 else ""
    record("DQ-05", f"Uncertainty score in [{lo}, {hi}]", name,
           passed=(failed == 0), failed_count=failed,
           total=len(valid), severity="Warning", detail=detail)

#DQ-06 — No duplicates on key combination
print("\nDQ-06: Duplicate rows on key columns...")
keys = {
    "GLOBAL":   ['year', 'fishing_entity', 'gear_type', 'catch_type'],
    "HighSeas": ['year', 'fishing_entity', 'common_name', 'area_name'],
    "EEZ_Fiji": ['year', 'fishing_entity', 'common_name', 'area_name', 'gear_type'],
    "EEZ_848":  ['year', 'fishing_entity', 'common_name', 'area_name', 'gear_type'],
}
for name, cols in keys.items():
    df     = files[name]
    failed = int(df.duplicated(subset=cols).sum())
    record("DQ-06", "No duplicates on key combination", name,
           passed=(failed == 0), failed_count=failed,
           total=len(df), severity="Warning")

#DQ-07 — Referential integrity of fishing entities
print("\nDQ-07: Referential integrity...")
global_entities = set(files["GLOBAL"]['fishing_entity'].unique())
for name in ["HighSeas", "EEZ_Fiji", "EEZ_848"]:
    df      = files[name]
    orphans = set(df['fishing_entity'].unique()) - global_entities
    failed  = len(orphans)
    record("DQ-07", "All fishing_entity values exist in GLOBAL", name,
           passed=(failed == 0), failed_count=failed,
           total=len(df['fishing_entity'].unique()),
           severity="Warning",
           detail=str(orphans) if orphans else "")

#DQ-08 — Ghost values in tonnes (< 1e-6)
print("\nDQ-08: Ghost values in tonnes...")
GHOST_THRESHOLD = 1e-6
for name, df in files.items():
    failed = int((df['tonnes'] < GHOST_THRESHOLD).sum())
    pct    = failed / len(df) * 100
    # Only fails if > 1% of rows are ghost values
    record("DQ-08", f"Tonnes ghost values (< {GHOST_THRESHOLD}) below 1%", name,
           passed=(pct <= 1), failed_count=failed,
           total=len(df), severity="Info",
           detail=f"{pct:.4f}% ghost rows")

#SUMMARY
total_rules  = len(results)
passed_rules = sum(1 for r in results if r['status'] == 'PASSED')
failed_rules = total_rules - passed_rules

print(f"\n{'─'*60}")
print(f"  Rules run : {total_rules}")
print(f"  Passed    : {passed_rules}")
print(f"  Failed    : {failed_rules}")
print(f"{'─'*60}")

#SAVE json
os.makedirs("data_quality", exist_ok=True)
with open("data_quality/results.json", "w") as f:
    json.dump({
        "run_timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_rules,
            "passed": passed_rules,
            "failed": failed_rules,
        },
        "results": results
    }, f, indent=2)
print("\nResults saved to data_quality/results.json")

#GENERATE report.html
df_results = pd.DataFrame(results)

rows_html = ""
for _, row in df_results.iterrows():
    color = (
        "#d4edda" if row['status'] == "PASSED"
        else "#f8d7da" if row['severity'] == "Critical"
        else "#fff3cd"
    )
    rows_html += f"""
    <tr style="background-color:{color}">
        <td>{row['rule_id']}</td>
        <td>{row['description']}</td>
        <td>{row['file']}</td>
        <td><b>{row['status']}</b></td>
        <td>{row['failed_records']}</td>
        <td>{row['total_records']}</td>
        <td>{row['failed_pct']}</td>
        <td>{row['severity']}</td>
        <td style="font-size:0.85em;color:#555">{row['detail']}</td>
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Data Quality Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; }}
    h1   {{ color: #333; }}
    .meta {{ color: #666; font-size: 0.9em; margin-bottom: 24px; }}
    .summary {{ display: flex; gap: 20px; margin-bottom: 32px; }}
    .card {{ padding: 16px 28px; border-radius: 8px; text-align: center; }}
    .card h2 {{ margin: 0; font-size: 2em; }}
    .card p  {{ margin: 4px 0 0; font-size: 0.9em; color: #555; }}
    .total  {{ background: #e9ecef; }}
    .passed {{ background: #d4edda; }}
    .failed {{ background: #f8d7da; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9em; }}
    th    {{ background: #343a40; color: white; padding: 10px 12px; text-align: left; }}
    td    {{ padding: 8px 12px; border-bottom: 1px solid #dee2e6; }}
  </style>
</head>
<body>
  <h1>Data Quality Report</h1>
  <p class="meta">Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp; Sea Around Us — Fisheries Dataset</p>

  <div class="summary">
    <div class="card total">
      <h2>{total_rules}</h2><p>Rules run</p>
    </div>
    <div class="card passed">
      <h2>{passed_rules}</h2><p>Passed</p>
    </div>
    <div class="card failed">
      <h2>{failed_rules}</h2><p>Failed</p>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Description</th>
        <th>File</th>
        <th>Status</th>
        <th>Failed records</th>
        <th>Total records</th>
        <th>Failed %</th>
        <th>Severity</th>
        <th>Detail</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>"""

with open("data_quality/report.html", "w") as f:
    f.write(html)
print("Report saved to data_quality/report.html")

s3 = boto3.client('s3')
BUCKET = 'data-source-52143'

#UPLOAD results and report
try:
    s3.upload_file('data_quality/results.json', BUCKET, 'reports/results.json')
    s3.upload_file('data_quality/report.html', BUCKET, 'reports/report.html')
    print("Reports uploaded to S3.")
except Exception as e:
    print(f"WARNING: Could not upload reports to S3: {e}")

#GROUP critical failures by file
critical_failures_by_file = {}
for r in results:
    if r['status'] == 'FAILED' and r['severity'] == 'Critical':
        file = r['file']
        if file not in critical_failures_by_file:
            critical_failures_by_file[file] = []
        critical_failures_by_file[file].append(r['rule_id'])

#MOVE to curated the files that passed
print("\nMoving validated files to curated zone...")
any_moved = False
for name, s3_path in FILES.items():
    filename = s3_path.split('/')[-1]
    if name in critical_failures_by_file:
        print(f"  SKIPPED {filename} — failed: {critical_failures_by_file[name]}")
    else:
        copy_source = {'Bucket': BUCKET, 'Key': f'processed/{filename}'}
        s3.copy(copy_source, BUCKET, f'curated/{filename}')
        print(f"  Copied {filename} → curated/")
        any_moved = True

#FAIL pipeline if not even a single file passed
if not any_moved:
    raise Exception("DQ failed — no files passed Critical rules, curated zone not updated.")
else:
    if critical_failures_by_file:
        print(f"\nWARNING: {len(critical_failures_by_file)} file(s) excluded from curated: {list(critical_failures_by_file.keys())}")
    print("Curated zone updated with validated files.")

