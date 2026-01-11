"""
Quick script to get column list from a CSV file.

Usage:
    python get_columns.py woe_transformed_data.csv
    python get_columns.py model_data_filtered.csv
"""

import pandas as pd
import sys
from pathlib import Path

# Get the directory containing this script
current_dir = Path(__file__).parent.absolute()
data_dir = current_dir / "data"

def get_columns(filename):
    """Get and display columns from a CSV file."""
    file_path = data_dir / filename
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        print(f"\nAvailable files in {data_dir}:")
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            for f in csv_files:
                print(f"  - {f.name}")
        else:
            print("  (no CSV files found)")
        return
    
    try:
        # Read only headers (fast, no data loading)
        df = pd.read_csv(file_path, nrows=0)
        columns = df.columns.tolist()
        
        print(f"\nFile: {filename}")
        print(f"Total columns: {len(columns)}\n")
        print("Column list:")
        print("-" * 60)
        
        for i, col in enumerate(columns, 1):
            print(f"{i:3d}. {col}")
        
        print("-" * 60)
        print(f"\nTotal: {len(columns)} columns")
        
        # Also print as comma-separated list for easy copying
        print(f"\nComma-separated list:")
        print(", ".join(columns))
        
    except Exception as e:
        print(f"Error reading file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Default to woe_transformed_data.csv
        filename = "woe_transformed_data.csv"
        print(f"No filename provided, using default: {filename}")
    
    get_columns(filename)

