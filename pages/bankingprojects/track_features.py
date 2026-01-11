"""
Feature Tracking Script for Banking Projects Pipeline

This script tracks feature names (columns) through the analysis pipeline:
1. Data Pipeline → var_metadata_input.csv
2. Variable Metadata Analysis → feat_eng_data.csv
3. Feature Engineering Analysis → woe_ready.csv
4. IV/WoE Analysis → model_data_filtered.csv

Usage:
    python track_features.py

Output:
    Prints a detailed comparison of features at each stage, showing:
    - Number of features at each stage
    - Features added/removed between stages
    - Final feature list
"""

import pandas as pd
from pathlib import Path
import sys

# Get the directory containing this script
current_dir = Path(__file__).parent.absolute()
data_dir = current_dir / "data"

def get_features_from_file(file_path):
    """Get list of features (column names) from a CSV file."""
    if not file_path.exists():
        return None, f"File not found: {file_path}"
    
    try:
        df = pd.read_csv(file_path, nrows=0)  # Read only headers to be fast
        features = df.columns.tolist()
        return features, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"

def compare_features(prev_features, curr_features, stage_name):
    """Compare two feature lists and return differences."""
    if prev_features is None:
        return {
            'added': curr_features,
            'removed': [],
            'common': []
        }
    
    prev_set = set(prev_features)
    curr_set = set(curr_features)
    
    added = sorted(list(curr_set - prev_set))
    removed = sorted(list(prev_set - curr_set))
    common = sorted(list(prev_set & curr_set))
    
    return {
        'added': added,
        'removed': removed,
        'common': common
    }

def format_feature_list(features, max_display=20):
    """Format feature list for display."""
    if not features:
        return "None"
    
    if len(features) <= max_display:
        return ", ".join(features)
    else:
        displayed = ", ".join(features[:max_display])
        return f"{displayed} ... (+ {len(features) - max_display} more)"

def main():
    """Main tracking function."""
    print("=" * 80)
    print("FEATURE TRACKING - Banking Projects Pipeline")
    print("=" * 80)
    print()
    
    # Define the pipeline stages
    stages = [
        {
            'name': 'Data Pipeline Output',
            'file': data_dir / 'var_metadata_input.csv',
            'description': 'Output from data_pipeline.py'
        },
        {
            'name': 'Variable Metadata Analysis Output',
            'file': data_dir / 'feat_eng_data.csv',
            'description': 'Output from var_metadata_analysis.py (Step 8)'
        },
        {
            'name': 'Feature Engineering Analysis Output',
            'file': data_dir / 'woe_ready.csv',
            'description': 'Output from feat_eng_analysis.py (Step 6)'
        },
        {
            'name': 'IV/WoE Analysis - WoE Transformed',
            'file': data_dir / 'woe_transformed_data.csv',
            'description': 'Output from iv_woe_analysis.py (Step 4) - WoE transformed data'
        },
        {
            'name': 'IV/WoE Analysis - Final Filtered',
            'file': data_dir / 'model_data_filtered.csv',
            'description': 'Output from iv_woe_analysis.py (Step 6) - Final filtered dataset'
        }
    ]
    
    # Track features through pipeline
    previous_features = None
    stage_results = []
    
    for stage in stages:
        print(f"\n{'=' * 80}")
        print(f"Stage: {stage['name']}")
        print(f"File: {stage['file'].name}")
        print(f"Description: {stage['description']}")
        print(f"{'=' * 80}")
        
        features, error = get_features_from_file(stage['file'])
        
        if error:
            print(f"[!] {error}")
            stage_results.append({
                'stage': stage['name'],
                'file': stage['file'].name,
                'features': None,
                'count': 0,
                'error': error
            })
            continue

        # Compare with previous stage
        if previous_features is not None:
            comparison = compare_features(previous_features, features, stage['name'])
            
            print(f"\nFeature Count: {len(features)}")
            print(f"Change from previous stage: {len(features) - len(previous_features):+d}")
            
            if comparison['added']:
                print(f"\n[+] Features ADDED ({len(comparison['added'])}):")
                print(f"   {format_feature_list(comparison['added'])}")
            
            if comparison['removed']:
                print(f"\n[-] Features REMOVED ({len(comparison['removed'])}):")
                print(f"   {format_feature_list(comparison['removed'])}")
            
            if not comparison['added'] and not comparison['removed']:
                print(f"\n[=] No changes (all {len(comparison['common'])} features preserved)")
            
            print(f"\n[*] Common features: {len(comparison['common'])}")
        else:
            print(f"\nFeature Count: {len(features)}")
            print(f"\nAll Features:")
            print(f"   {format_feature_list(features)}")
        
        stage_results.append({
            'stage': stage['name'],
            'file': stage['file'].name,
            'features': features,
            'count': len(features) if features else 0,
            'error': None
        })
        
        previous_features = features
        print()
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print()
    
    print(f"{'Stage':<45} {'File':<35} {'Features':<10} {'Status'}")
    print("-" * 100)
    
    for result in stage_results:
        status = "[OK]" if result['error'] is None else f"[ERROR] {result['error'][:30]}"
        file_name = result['file'][:34] if len(result['file']) <= 34 else result['file'][:31] + "..."
        print(f"{result['stage']:<45} {file_name:<35} {result['count']:<10} {status}")
    
    print()
    
    # Final statistics
    valid_results = [r for r in stage_results if r['error'] is None and r['features'] is not None]
    if len(valid_results) >= 2:
        first_stage = valid_results[0]
        last_stage = valid_results[-1]
        
        print("=" * 80)
        print("OVERALL PIPELINE STATISTICS")
        print("=" * 80)
        print(f"Initial features ({first_stage['stage']}): {first_stage['count']}")
        print(f"Final features ({last_stage['stage']}): {last_stage['count']}")
        print(f"Total change: {last_stage['count'] - first_stage['count']:+d} features")
        
        if first_stage['features'] and last_stage['features']:
            first_set = set(first_stage['features'])
            last_set = set(last_stage['features'])
            
            final_only = last_set - first_set
            initial_only = first_set - last_set
            
            if final_only:
                print(f"\nFeatures in final but NOT in initial ({len(final_only)}):")
                print(f"   {format_feature_list(sorted(list(final_only)))}")
            
            if initial_only:
                print(f"\nFeatures in initial but NOT in final ({len(initial_only)}):")
                print(f"   {format_feature_list(sorted(list(initial_only)))}")
    
    print("\n" + "=" * 80)
    print("Note: On Railway, files are stored in the container filesystem.")
    print("Files are ephemeral and will be lost when the container restarts.")
    print("To persist files, consider using Railway volumes or external storage.")
    print("=" * 80)

if __name__ == "__main__":
    main()

