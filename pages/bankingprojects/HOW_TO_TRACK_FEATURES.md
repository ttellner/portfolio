# How to Track Features and View Outputs

## Quick Start

### Option 1: Track Features Locally (Recommended for Analysis)

1. **Run the tracking script:**
   ```bash
   cd pages/bankingprojects
   python track_features.py
   ```

2. **View the output** - The script will show:
   - Feature count at each stage
   - Features added/removed between stages
   - Complete pipeline summary

**Example output:**
```
================================================================================
FEATURE TRACKING - Banking Projects Pipeline
================================================================================

Stage: Data Pipeline Output
File: var_metadata_input.csv
Feature Count: 268

Stage: Variable Metadata Analysis Output
File: feat_eng_data.csv
Feature Count: 268
Change from previous stage: +0
[=] No changes (all 268 features preserved)

...
```

### Option 2: View Outputs in Streamlit UI (On Railway)

1. **Navigate to the analysis pages:**
   - Data Pipeline
   - Variable Metadata Analysis
   - Feature Engineering Analysis
   - IV/WoE Analysis

2. **Run the analyses** (execute each step)

3. **Download files from the sidebar:**
   - Each analysis page has download buttons in the sidebar
   - Click "Download [filename].csv" to download
   - Files download to your local machine

4. **View downloaded files:**
   - Open in Excel, pandas, or any CSV viewer
   - Check column names to see features

### Option 3: View Feature Lists in Streamlit UI

Many analysis pages show feature information directly:

1. **Variable Metadata Analysis:**
   - Shows duplicate columns detected
   - Shows final column list after deduplication

2. **Feature Engineering Analysis:**
   - Shows which features were created/modified
   - Shows feature counts

3. **IV/WoE Analysis:**
   - Shows variables in keep list
   - Shows variables selected to keep
   - Shows breakdown: keep list vs IV-only variables
   - Shows final filtered feature count

## Detailed Steps

### Track Features Locally (After Running Analyses)

**Prerequisites:** You need to have run the analyses first (either locally or downloaded files from Railway)

1. **Ensure files exist:**
   ```bash
   # Check if files exist
   ls pages/bankingprojects/data/*.csv
   ```

2. **Run tracking script:**
   ```bash
   cd pages/bankingprojects
   python track_features.py
   ```

3. **Interpret the output:**
   - `Feature Count:` - Number of columns/features
   - `Change from previous stage:` - How many features were added/removed
   - `Features ADDED:` - New features created in this stage
   - `Features REMOVED:` - Features dropped in this stage
   - `Common features:` - Features that exist in both stages

### View Outputs on Railway

1. **Access your Railway app:**
   - Go to your Railway URL (e.g., `https://your-app.up.railway.app`)
   - Or use your custom domain

2. **Navigate to Banking Projects:**
   - Click on "Banking Projects" in the sidebar
   - Select the analysis you want to view

3. **Run the analysis steps:**
   - Execute each step sequentially
   - Wait for each step to complete

4. **Download outputs:**
   - Look for download buttons in the sidebar
   - Download the CSV files you need

5. **View downloaded files:**
   ```python
   # In Python/Jupyter
   import pandas as pd
   df = pd.read_csv('model_data_filtered.csv')
   print(f"Features: {len(df.columns)}")
   print(f"Column names: {list(df.columns)}")
   ```

### Compare Features Between Stages

After downloading files from Railway:

1. **Download all intermediate files:**
   - `var_metadata_input.csv` (from Data Pipeline)
   - `feat_eng_data.csv` (from Variable Metadata Analysis)
   - `woe_ready.csv` (from Feature Engineering Analysis)
   - `woe_transformed_data.csv` (from IV/WoE Analysis)
   - `model_data_filtered.csv` (from IV/WoE Analysis)

2. **Put them in the data directory:**
   ```bash
   # Copy downloaded files to:
   pages/bankingprojects/data/
   ```

3. **Run tracking script:**
   ```bash
   cd pages/bankingprojects
   python track_features.py
   ```

4. **View the comparison:**
   - See exactly which features were added/removed at each stage
   - See the final feature list
   - Understand the pipeline flow

## View Features in Python

If you want to programmatically inspect features:

```python
import pandas as pd
from pathlib import Path

data_dir = Path("pages/bankingprojects/data")

# Read a file
file_path = data_dir / "model_data_filtered.csv"
if file_path.exists():
    df = pd.read_csv(file_path, nrows=0)  # Read headers only
    features = df.columns.tolist()
    
    print(f"Total features: {len(features)}")
    print(f"\nFeature list:")
    for i, feat in enumerate(features, 1):
        print(f"{i:3d}. {feat}")
else:
    print(f"File not found: {file_path}")
```

## View Features in Excel/Spreadsheet

1. **Download the CSV file** from Railway UI
2. **Open in Excel/Google Sheets**
3. **First row shows all feature names**
4. **Count columns** to see total feature count

## Tips

- **Run analyses first** - Files are only created after you run the analyses
- **Download files promptly** - On Railway, files are lost when container restarts
- **Use tracking script locally** - Most convenient for comparing stages
- **Check Streamlit UI** - Some pages show feature information directly
- **Save downloaded files** - Keep copies locally for reference

## Troubleshooting

**"File not found" errors:**
- Make sure you've run the analysis steps first
- Files are only created after executing the steps
- Check that files exist in the data directory

**Script doesn't run:**
```bash
# Make sure you're in the right directory
cd pages/bankingprojects
python track_features.py
```

**Can't see download buttons:**
- Make sure you've executed the analysis steps
- Download buttons appear after steps are completed
- Check the sidebar (not the main content area)

## Summary

**Best approach:**
1. Run analyses in Streamlit UI (on Railway)
2. Download CSV files using sidebar download buttons
3. Save files to `pages/bankingprojects/data/`
4. Run `python track_features.py` locally to see comparison
5. Or view files directly in Excel/Python

This gives you both the interactive UI experience and detailed local analysis capabilities.

