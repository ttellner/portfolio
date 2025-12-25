"""Test script to compare Step 7 output with Step 8 hardcoded list"""

import sys
from pathlib import Path
import pandas as pd

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from data_pipeline_functions import stage11_final_vars
from var_meta_functions import step7_duplicate_columns, step7_get_duplicate_list, step8_get_hardcoded_list

# Load raw data
data_file = current_dir / "data" / "PD_RAW_VARIABLES.csv"
print(f"Loading data from: {data_file}")

if not data_file.exists():
    print(f"Error: Data file not found: {data_file}")
    sys.exit(1)

raw_data = pd.read_csv(data_file)
print(f"Loaded {len(raw_data)} rows and {len(raw_data.columns)} columns")

# Run all pipeline stages to get final output (simplified - just run stage 11 which includes all previous stages)
# Actually, we need to run all stages sequentially. Let me do that properly.
from data_pipeline_functions import (
    stage1_bureau_vars,
    stage2_cbs_vars,
    stage3_dpd_vars,
    stage4_collection_vars,
    stage5_disburse_vars,
    stage6_txn_vars,
    stage7_txn_vars,
    stage8_txn_vars,
    stage9_txn_vars,
    stage10_txn_vars,
    stage11_final_vars
)

print("\nRunning data pipeline stages...")
df = raw_data.copy()
df = stage1_bureau_vars(df)
print(f"After Stage 1: {len(df.columns)} columns")
df = stage2_cbs_vars(df)
print(f"After Stage 2: {len(df.columns)} columns")
df = stage3_dpd_vars(df)
print(f"After Stage 3: {len(df.columns)} columns")
df = stage4_collection_vars(df)
print(f"After Stage 4: {len(df.columns)} columns")
df = stage5_disburse_vars(df)
print(f"After Stage 5: {len(df.columns)} columns")
df = stage6_txn_vars(df)
print(f"After Stage 6: {len(df.columns)} columns")
df = stage7_txn_vars(df)
print(f"After Stage 7: {len(df.columns)} columns")
df = stage8_txn_vars(df)
print(f"After Stage 8: {len(df.columns)} columns")
df = stage9_txn_vars(df)
print(f"After Stage 9: {len(df.columns)} columns")
df = stage10_txn_vars(df)
print(f"After Stage 10: {len(df.columns)} columns")
df = stage11_final_vars(df)
print(f"After Stage 11 (final): {len(df.columns)} columns")
print(f"Final data: {len(df)} rows")

# Now run Step 7 to detect duplicate columns
print("\n" + "="*80)
print("Running Step 7: Duplicate Column Detection")
print("="*80)
step7_result = step7_duplicate_columns(df, sample_size=1000)
print(f"\nStep 7 found {len(step7_result)} duplicate columns (including first occurrence in each group)")
print("\nDuplicate groups:")
print(step7_result.to_string())

# Get the list of columns to drop from Step 7
step7_duplicate_list = step7_get_duplicate_list(step7_result)
print(f"\nStep 7 columns to drop: {len(step7_duplicate_list)} columns")
print(sorted(step7_duplicate_list))

# Get hardcoded list from Step 8
hardcoded_list = step8_get_hardcoded_list()
print(f"\nStep 8 hardcoded list: {len(hardcoded_list)} columns")
print(sorted(hardcoded_list))

# Compare
print("\n" + "="*80)
print("Comparison Results")
print("="*80)
step7_set = set(step7_duplicate_list)
hardcoded_set = set(hardcoded_list)

if step7_set == hardcoded_set:
    print("MATCH: Step 7 output MATCHES Step 8 hardcoded list!")
else:
    print("DIFFER: Step 7 output DIFFERS from Step 8 hardcoded list")
    
    only_in_step7 = step7_set - hardcoded_set
    only_in_hardcoded = hardcoded_set - step7_set
    
    if only_in_step7:
        print(f"\nOnly in Step 7 output ({len(only_in_step7)} columns):")
        print(sorted(only_in_step7))
    
    if only_in_hardcoded:
        print(f"\nOnly in Step 8 hardcoded list ({len(only_in_hardcoded)} columns):")
        print(sorted(only_in_hardcoded))
    
    print(f"\nSummary:")
    print(f"  Step 7 columns to drop: {len(step7_set)}")
    print(f"  Step 8 hardcoded columns: {len(hardcoded_set)}")
    print(f"  Intersection (common): {len(step7_set & hardcoded_set)}")
    print(f"  Only in Step 7: {len(only_in_step7)}")
    print(f"  Only in hardcoded: {len(only_in_hardcoded)}")

