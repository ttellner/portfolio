"""
IV and WoE Analysis
Calculates Information Value (IV) and Weight of Evidence (WoE) for numeric variables. Analyzes variable predictive power and creates bin-level statistics.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from iv_woe_functions import (
    step1_get_numeric_variables,
    step2_create_iv_summary_structure,
    calculate_woe_iv_with_manual_bureau_score,
    apply_woe_transformations,
    create_expanded_keep_list,
    filter_variables_by_iv,
    select_final_variables,
    create_filtered_dataset
)

# Page configuration
st.set_page_config(
    page_title="IV and WoE Analysis",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stage-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #ecf0f1;
        border-left: 4px solid #3498db;
    }
    </style>
""", unsafe_allow_html=True)

# Reset session state when navigating to this page
current_page = st.query_params.get("project", "")
last_page = st.session_state.get("last_page_iv_woe", "")

if current_page == "iv_woe_analysis.py" and last_page != "iv_woe_analysis.py":
    # Coming to this page fresh - reset state
    if 'input_data' in st.session_state:
        del st.session_state.input_data
    if 'step_results' in st.session_state:
        del st.session_state.step_results
    if 'current_step' in st.session_state:
        del st.session_state.current_step

st.session_state.last_page_iv_woe = current_page

# Initialize session state
if 'input_data' not in st.session_state:
    st.session_state.input_data = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'step_results' not in st.session_state:
    st.session_state.step_results = {}

# Step definitions with descriptions and code snippets
STEPS = [
    {
        'number': 1,
        'name': 'Get Numeric Variables',
        'description': 'Identifies all numeric variables in the dataset, excluding the target variable (default_flag).',
        'code': '''
# Get numeric variables excluding default_flag
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_vars = [col for col in numeric_cols 
                if col.upper() != 'DEFAULT_FLAG']
'''
    },
    {
        'number': 2,
        'name': 'Create Empty Base Tables',
        'description': 'Creates empty IV summary and WoE statistics tables with the correct structure.',
        'code': '''
# Create empty IV summary dataframe
iv_summary = pd.DataFrame(columns=['variable', 'IV'])

# Create empty WoE statistics dataframe
woe_all = pd.DataFrame(columns=['variable', 'bin', 'good', 'bad', 
                                'pct_good', 'pct_bad', 'woe', 'iv_component'])
'''
    },
    {
        'number': 3,
        'name': 'Calculate WoE and IV for All Variables',
        'description': 'Loops through all numeric variables, creates bins (10 bins for automatic, manual bins for bureau_score), calculates WoE and IV statistics.',
        'code': '''
# For each variable (except bureau_score):
# 1. Create 10 bins using qcut
df['bin'] = pd.qcut(df[variable], q=10, labels=False, duplicates='drop')

# 2. Calculate good/bad counts by bin
stats = df.groupby('bin').agg({
    'default_flag': ['sum', 'count']
})
stats['good'] = stats['total'] - stats['bad']

# 3. Calculate percentages and WoE
stats['pct_good'] = stats['good'] / tot_good
stats['pct_bad'] = stats['bad'] / tot_bad
stats['woe'] = np.log(stats['pct_good'] / stats['pct_bad'])
stats['iv_component'] = (stats['pct_good'] - stats['pct_bad']) * stats['woe']

# For bureau_score: Use manual binning with cutoffs <400, 400-500, 500-600, 600-700, >=700
'''
    },
    {
        'number': 4,
        'name': 'Apply WoE Transformations',
        'description': 'Applies WoE transformations to the dataset, replacing original variables with their WoE values.',
        'code': '''
# For each variable:
# 1. Create bins (same as calculation step)
# 2. Merge with WoE statistics
# 3. Replace original variable with WoE values
df[variable] = merged_woe_values
'''
    },
    {
        'number': 5,
        'name': 'Create Expanded Keep List and Filter Variables',
        'description': 'Creates expanded forced keep list, merges IV summary with keep list, and applies filtering rules (IV >= 0.015 and <= 5, or variables in keep list).',
        'code': '''
# Create keep list (forced variables to always keep)
keep_list = create_expanded_keep_list()

# Merge IV summary with keep list and apply filtering rules
iv_filtered = filter_variables_by_iv(iv_summary, keep_list, iv_min=0.015, iv_max=5.0)
'''
    },
    {
        'number': 6,
        'name': 'Create Final Filtered Dataset',
        'description': 'Selects final variables (only those that exist in dataset) and creates filtered dataset with selected variables and target.',
        'code': '''
# Get available variables from dataset
available_vars = df.columns.tolist()

# Final selection - keep only existing variables
selected_vars = select_final_variables(iv_filtered, keep_list, available_vars)

# Create filtered dataset
df_filtered = create_filtered_dataset(df, selected_vars, target_col='default_flag')
'''
    }
]


def load_data_from_file():
    """Load data from CSV file with fallback options."""
    # Primary input: woe_ready.csv (from feat_eng_analysis.py Step 6)
    data_file = current_dir / "data" / "woe_ready.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    
    # Fallback: feat_eng_output.csv (from feat_eng_analysis.py Step 5)
    fallback_file = current_dir / "data" / "feat_eng_output.csv"
    if fallback_file.exists():
        st.info("Using fallback data file: feat_eng_output.csv (from Feature Engineering Analysis Step 5)")
        return pd.read_csv(fallback_file)
    
    # If neither exists, show error
    st.error(f"Data file not found. Please ensure one of the following exists:\n"
             f"- {data_file.name} (from Feature Engineering Analysis Step 6)\n"
             f"- {fallback_file.name} (from Feature Engineering Analysis Step 5)")
    return None


def display_step_info(step):
    """Display step information and code."""
    st.markdown(f'<div class="stage-header">{step["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Description:** {step['description']}")
    
    st.markdown("**Python Code:**")
    st.code(step['code'], language='python')


def main():
    """Main application."""
    # Scroll to top on page load if scroll parameter is present
    if st.query_params.get("scroll") == "top":
        st.markdown("""
        <script>
            (function() {
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
                setTimeout(function() {
                    window.scrollTo(0, 0);
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                }, 50);
                setTimeout(function() {
                    window.scrollTo(0, 0);
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                }, 200);
            })();
        </script>
        """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">IV and WoE Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application calculates Information Value (IV) and Weight of Evidence (WoE) 
    for numeric variables. IV measures the predictive power of variables, while WoE 
    provides transformation values for each bin.
    
    **Instructions:**
    1. Default data (woe_ready.csv) is loaded automatically
    2. Execute each step sequentially
    3. View the IV summary and WoE statistics for all variables
    4. Review variable rankings by IV value
    """)
    
    st.markdown("---")
    
    # Auto-load default data if not already loaded
    if st.session_state.input_data is None:
        data = load_data_from_file()
        if data is not None:
            st.session_state.input_data = data
            st.session_state.current_step = 0
            st.session_state.step_results = {}
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Data Information")
        if st.session_state.input_data is not None:
            st.success(f"Data loaded: {len(st.session_state.input_data):,} rows, {len(st.session_state.input_data.columns)} columns")
            # Check which file was actually loaded
            woe_file = current_dir / "data" / "woe_ready.csv"
            if woe_file.exists():
                st.caption("Default: woe_ready.csv")
            else:
                st.caption("Using: feat_eng_output.csv (fallback)")
        
        st.markdown("---")
        
        if st.session_state.input_data is not None:
            st.header("Step Navigation")
            
            for i, step in enumerate(STEPS):
                status = "✅" if i < st.session_state.current_step else "⏳"
                if st.button(f"{status} {step['name']}", 
                            key=f"nav_{i}",
                            disabled=(i > st.session_state.current_step)):
                    # Ensure index is valid before setting
                    if 0 <= i < len(STEPS):
                        st.session_state.current_step = i
                        st.rerun()
            
            st.markdown("---")
            if st.button("Reset All Steps"):
                st.session_state.current_step = 0
                st.session_state.step_results = {}
                st.rerun()
            
            # Download buttons for output CSVs
            if 2 in st.session_state.step_results:
                st.markdown("---")
                st.header("Download Results")
                output_file = current_dir / "data" / "iv_woe_output.csv"
                if output_file.exists():
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="Download iv_woe_output.csv",
                            data=f.read(),
                            file_name="iv_woe_output.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            # Download filtered dataset (only show if Step 6 is completed)
            if 5 in st.session_state.step_results:
                filtered_file = current_dir / "data" / "model_data_filtered.csv"
                if filtered_file.exists():
                    with open(filtered_file, 'rb') as f:
                        st.download_button(
                            label="Download model_data_filtered.csv",
                            data=f.read(),
                            file_name="model_data_filtered.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        else:
            st.info("Please load data first")
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please ensure one of the following exists in the data folder:\n"
                 "- woe_ready.csv (from Feature Engineering Analysis Step 6)\n"
                 "- feat_eng_output.csv (from Feature Engineering Analysis Step 5)")
        st.info("💡 **Tip:** Run the previous analysis steps to generate the required input file, or ensure the default files exist.")
        return
    
    # Display current step
    current_step_idx = st.session_state.current_step
    
    # Ensure STEPS is not empty
    if len(STEPS) == 0:
        st.error("No steps defined. Please check the STEPS configuration.")
        return
    
    # Ensure current_step_idx is within valid range
    if current_step_idx >= len(STEPS):
        current_step_idx = len(STEPS) - 1
        st.session_state.current_step = current_step_idx
    elif current_step_idx < 0:
        current_step_idx = 0
        st.session_state.current_step = current_step_idx
    
    step = STEPS[current_step_idx]
    
    # Step information
    display_step_info(step)
    
    st.markdown("---")
    
    # Execute step button
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_disabled = current_step_idx in st.session_state.step_results
        is_final_step = current_step_idx == len(STEPS) - 1
        all_steps_completed = len(st.session_state.step_results) == len(STEPS)
        
        # Change button text for final step when all steps are completed
        if is_final_step and all_steps_completed:
            button_text = "Proceed to next Analysis"
            if st.button(button_text, type="primary", disabled=True):
                pass  # Disabled for now as requested
        else:
            button_text = "Execute Step"
            if st.button(button_text, type="primary", disabled=execute_disabled):
                with st.spinner(f"Executing {step['name']}..."):
                    try:
                        input_df = st.session_state.input_data.copy()
                        
                        # Step 1: Get numeric variables
                        if step['number'] == 1:
                            numeric_vars = step1_get_numeric_variables(input_df)
                            result = {
                                'numeric_vars': numeric_vars,
                                'count': len(numeric_vars)
                            }
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"{step['name']} executed successfully! Found {len(numeric_vars)} numeric variables.")
                            st.rerun()
                        
                        # Step 2: Create empty base tables
                        elif step['number'] == 2:
                            iv_summary = step2_create_iv_summary_structure()
                            woe_all = pd.DataFrame(columns=['variable', 'bin', 'good', 'bad', 
                                                           'pct_good', 'pct_bad', 'woe', 'iv_component'])
                            result = {
                                'iv_summary': iv_summary,
                                'woe_all': woe_all
                            }
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"{step['name']} executed successfully!")
                            st.rerun()
                        
                        # Step 3: Calculate WoE and IV for all variables
                        elif step['number'] == 3:
                            if 0 not in st.session_state.step_results:
                                st.error("Please execute Step 1 first.")
                            else:
                                step1_result = st.session_state.step_results[0]
                                numeric_vars = step1_result['numeric_vars']
                                
                                iv_summary, woe_all = calculate_woe_iv_with_manual_bureau_score(
                                    input_df,
                                    numeric_vars,
                                    target_col='default_flag',
                                    n_bins=10,
                                    manual_var='bureau_score',
                                    manual_bin_edges=[400, 500, 600, 700]
                                )
                                
                                # Sort IV summary by IV value (descending)
                                iv_summary = iv_summary.sort_values('IV', ascending=False).reset_index(drop=True)
                                
                                # Ensure data directory exists
                                data_dir = current_dir / "data"
                                data_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Save IV summary
                                iv_file = data_dir / "iv_woe_output.csv"
                                iv_summary.to_csv(iv_file, index=False)
                                
                                # Save WoE statistics
                                woe_file = data_dir / "woe_statistics.csv"
                                woe_all.to_csv(woe_file, index=False)
                                
                                result = {
                                    'iv_summary': iv_summary,
                                    'woe_all': woe_all
                                }
                                
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"{step['name']} executed successfully! Calculated IV for {len(iv_summary)} variables. Output saved to iv_woe_output.csv and woe_statistics.csv")
                                st.rerun()
                        
                        # Step 4: Apply WoE transformations
                        elif step['number'] == 4:
                            if 2 not in st.session_state.step_results:
                                st.error("Please execute Step 3 first.")
                            else:
                                step1_result = st.session_state.step_results[0]
                                step3_result = st.session_state.step_results[2]
                                numeric_vars = step1_result['numeric_vars']
                                woe_all = step3_result['woe_all']
                                
                                df_woe_transformed = apply_woe_transformations(
                                    input_df,
                                    woe_all,
                                    numeric_vars,
                                    target_col='default_flag',
                                    n_bins=10,
                                    manual_var='bureau_score',
                                    manual_bin_edges=[400, 500, 600, 700]
                                )
                                
                                # Ensure data directory exists
                                data_dir = current_dir / "data"
                                data_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Save WoE transformed dataset
                                woe_transformed_file = data_dir / "woe_transformed_data.csv"
                                df_woe_transformed.to_csv(woe_transformed_file, index=False)
                                
                                # Save IV summary (equivalent to CREDIT.PD_IV_SUMMARY in SAS Step 7)
                                # This matches the SAS flow where IV summary is saved after applying WoE transformations
                                iv_summary = step3_result['iv_summary']
                                iv_file = data_dir / "iv_woe_output.csv"
                                iv_summary.to_csv(iv_file, index=False)
                                
                                result = {
                                    'woe_transformed_data': df_woe_transformed,
                                    'rows': len(df_woe_transformed),
                                    'columns': len(df_woe_transformed.columns),
                                    'iv_summary': iv_summary
                                }
                                
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"{step['name']} executed successfully! WoE transformed data saved to woe_transformed_data.csv. IV summary saved to iv_woe_output.csv (equivalent to CREDIT.PD_IV_SUMMARY)")
                                st.rerun()
                        
                        # Step 5: Create Expanded Keep List and Filter Variables
                        elif step['number'] == 5:
                            if 2 not in st.session_state.step_results:
                                st.error("Please execute Step 3 first.")
                            else:
                                step3_result = st.session_state.step_results[2]
                                iv_summary = step3_result['iv_summary']
                                
                                # Create keep list
                                keep_list = create_expanded_keep_list()
                                
                                # Filter variables by IV
                                iv_filtered = filter_variables_by_iv(
                                    iv_summary,
                                    keep_list,
                                    iv_min=0.015,
                                    iv_max=5.0
                                )
                                
                                result = {
                                    'keep_list': keep_list,
                                    'iv_filtered': iv_filtered,
                                    'vars_to_keep': iv_filtered[iv_filtered['keep_flag'] == 1]['variable'].tolist()
                                }
                                
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"{step['name']} executed successfully! Filtered {len(result['vars_to_keep'])} variables based on IV criteria and keep list.")
                                st.rerun()
                        
                        # Step 6: Create Final Filtered Dataset
                        elif step['number'] == 6:
                            if 3 not in st.session_state.step_results:
                                st.error("Please execute Step 4 first (Apply WoE Transformations).")
                            elif 4 not in st.session_state.step_results:
                                st.error("Please execute Step 5 first (Create Expanded Keep List and Filter Variables).")
                            else:
                                step4_result = st.session_state.step_results[3]
                                step5_result = st.session_state.step_results[4]
                                df_woe_transformed = step4_result['woe_transformed_data']
                                keep_list = step5_result['keep_list']
                                iv_filtered = step5_result['iv_filtered']
                                
                                # Get available variables from dataset
                                available_vars = df_woe_transformed.columns.tolist()
                                
                                # Final selection - keep only existing variables
                                selected_vars = select_final_variables(
                                    iv_filtered,
                                    keep_list,
                                    available_vars
                                )
                                
                                # Create filtered dataset
                                df_filtered = create_filtered_dataset(
                                    df_woe_transformed,
                                    selected_vars,
                                    target_col='default_flag'
                                )
                                
                                # Ensure data directory exists
                                data_dir = current_dir / "data"
                                data_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Save filtered dataset (equivalent to CREDIT.PD_MODEL_DATA_CH10_FILTERED)
                                filtered_file = data_dir / "model_data_filtered.csv"
                                df_filtered.to_csv(filtered_file, index=False)
                                
                                result = {
                                    'filtered_data': df_filtered,
                                    'selected_vars': selected_vars,
                                    'rows': len(df_filtered),
                                    'columns': len(df_filtered.columns),
                                    'vars_removed': len(df_woe_transformed.columns) - len(df_filtered.columns)
                                }
                                
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"{step['name']} executed successfully! Filtered dataset saved to model_data_filtered.csv (equivalent to CREDIT.PD_MODEL_DATA_CH10_FILTERED). Reduced from {len(df_woe_transformed.columns)} to {len(df_filtered.columns)} columns ({len(selected_vars)} selected variables + default_flag).")
                                st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error executing step: {str(e)}")
                        st.exception(e)
    
    # Display results if step has been executed
    if current_step_idx in st.session_state.step_results:
        result = st.session_state.step_results[current_step_idx]
        
        st.markdown("**Results:**")
        
        # Step 1 special display
        if step['number'] == 1:
            if isinstance(result, dict):
                st.subheader("Numeric Variables Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Numeric Variables", f"{result['count']}")
                with col2:
                    st.metric("Excluding Target", "default_flag")
                
                st.subheader("Numeric Variables List")
                numeric_vars = result['numeric_vars']
                # Display first 50 variables
                display_vars = numeric_vars[:50]
                st.write(f"**Total:** {len(numeric_vars)} variables")
                st.write(", ".join(display_vars))
                if len(numeric_vars) > 50:
                    st.write(f"... and {len(numeric_vars) - 50} more variables")
        
        # Step 2 special display
        elif step['number'] == 2:
            if isinstance(result, dict):
                st.subheader("Empty Base Tables Created")
                st.write("**IV Summary Structure:**", ", ".join(result['iv_summary'].columns.tolist()))
                st.write("**WoE Statistics Structure:**", ", ".join(result['woe_all'].columns.tolist()))
                st.dataframe(result['iv_summary'], use_container_width=True)
        
        # Step 3 special display
        elif step['number'] == 3:
            if isinstance(result, dict):
                iv_summary = result.get('iv_summary', pd.DataFrame())
                woe_all = result.get('woe_all', pd.DataFrame())
                
                st.subheader("IV Summary - All Variables (Sorted by IV)")
                if not iv_summary.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Variables Analyzed", f"{len(iv_summary)}")
                    with col2:
                        st.metric("Highest IV", f"{iv_summary['IV'].max():.4f}")
                    with col3:
                        st.metric("Average IV", f"{iv_summary['IV'].mean():.4f}")
                    
                    # IV interpretation guide
                    st.info("""
                    **IV Interpretation Guide:**
                    - < 0.02: Not useful for prediction
                    - 0.02 - 0.1: Weak predictive power
                    - 0.1 - 0.3: Medium predictive power
                    - 0.3 - 0.5: Strong predictive power
                    - > 0.5: Suspiciously high (check for overfitting)
                    """)
                    
                    # Display top 20 variables
                    st.subheader("Top 20 Variables by IV")
                    st.dataframe(iv_summary.head(20), use_container_width=True)
                    
                    # Display full IV summary
                    st.subheader("Full IV Summary")
                    st.dataframe(iv_summary, use_container_width=True, height=400)
                    
                    # WoE statistics preview
                    if not woe_all.empty:
                        st.subheader("WoE Statistics Preview (First 50 Rows)")
                        st.dataframe(woe_all.head(50), use_container_width=True)
                        
                        # Variable selector for detailed WoE view
                        st.subheader("Detailed WoE View by Variable")
                        var_options = sorted(iv_summary['variable'].tolist())
                        selected_var = st.selectbox("Select a variable to view detailed WoE statistics:", 
                                                    var_options, key="woe_var_selector")
                        
                        if selected_var:
                            var_woe = woe_all[woe_all['variable'] == selected_var].copy()
                            if not var_woe.empty:
                                var_woe = var_woe.sort_values('bin').reset_index(drop=True)
                                st.dataframe(var_woe, use_container_width=True)
                else:
                    st.warning("No IV summary calculated. Please check the data and try again.")
        
        # Step 4 special display
        elif step['number'] == 4:
            if isinstance(result, dict):
                df_woe = result.get('woe_transformed_data', pd.DataFrame())
                
                st.subheader("WoE Transformed Data Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows", f"{result.get('rows', 0):,}")
                with col2:
                    st.metric("Columns", f"{result.get('columns', 0)}")
                
                st.subheader("WoE Transformed Data Preview (First 20 Rows)")
                if not df_woe.empty:
                    st.dataframe(df_woe.head(20), use_container_width=True)
                    
                    st.subheader("Data Summary Statistics")
                    st.dataframe(df_woe.describe(), use_container_width=True)
                else:
                    st.warning("No transformed data available.")
        
        # Step 5 special display
        elif step['number'] == 5:
            if isinstance(result, dict):
                st.subheader("Filtered Variables Summary")
                iv_filtered = result.get('iv_filtered', pd.DataFrame())
                vars_to_keep = result.get('vars_to_keep', [])
                keep_list = result.get('keep_list', [])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Variables in Keep List", f"{len(keep_list)}")
                with col2:
                    st.metric("Variables to Keep", f"{len(vars_to_keep)}")
                with col3:
                    if not iv_filtered.empty:
                        st.metric("Variables with IV >= 0.015", f"{len(iv_filtered[iv_filtered['IV'] >= 0.015])}")
                
                if not iv_filtered.empty:
                    st.subheader("IV Filtered Summary (with keep_flag)")
                    st.dataframe(iv_filtered, use_container_width=True, height=400)
                    
                    st.subheader("Variables Selected to Keep")
                    st.write(f"**Total:** {len(vars_to_keep)} variables")
                    # Display first 50 variables
                    display_vars = vars_to_keep[:50]
                    st.write(", ".join(display_vars))
                    if len(vars_to_keep) > 50:
                        st.write(f"... and {len(vars_to_keep) - 50} more variables")
        
        # Step 6 special display
        elif step['number'] == 6:
            if isinstance(result, dict):
                df_filtered = result.get('filtered_data', pd.DataFrame())
                selected_vars = result.get('selected_vars', [])
                
                st.subheader("Final Filtered Dataset Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", f"{result.get('rows', 0):,}")
                with col2:
                    st.metric("Columns (After Filtering)", f"{result.get('columns', 0)}")
                with col3:
                    st.metric("Variables Removed", f"{result.get('vars_removed', 0)}")
                
                st.subheader("Selected Variables")
                st.write(f"**Total:** {len(selected_vars)} variables + default_flag = {result.get('columns', 0)} total columns")
                
                st.subheader("Filtered Dataset Preview (First 20 Rows)")
                if not df_filtered.empty:
                    st.dataframe(df_filtered.head(20), use_container_width=True)
                    
                    st.subheader("Filtered Dataset Summary Statistics")
                    st.dataframe(df_filtered.describe(), use_container_width=True)
                else:
                    st.warning("No filtered data available.")
        
        # Standard display for other steps
        else:
            if isinstance(result, pd.DataFrame):
                st.dataframe(result, use_container_width=True)
            elif isinstance(result, dict):
                for key, value in result.items():
                    st.write(f"**{key}:**")
                    if isinstance(value, pd.DataFrame):
                        st.dataframe(value, use_container_width=True)
                    else:
                        st.write(value)
            else:
                st.write(result)
    else:
        st.info("Click 'Execute Step' to run this step and view the results.")
    
    # Progress indicator
    st.markdown("---")
    st.markdown("### Analysis Progress")
    completed = len(st.session_state.step_results)
    total = len(STEPS)
    progress = completed / total
    st.progress(progress)
    st.caption(f"Completed: {completed} / {total} steps ({progress*100:.1f}%)")
    
    # Detailed Summary Tables - show when all steps are completed
    if completed == total:
        st.markdown("---")
        st.markdown("### Detailed Analysis Summary")
        
        # Overall Summary
        if 2 in st.session_state.step_results:
            step3_result = st.session_state.step_results[2]
            step1_result = st.session_state.step_results[0]
            
            if isinstance(step3_result, dict):
                iv_summary = step3_result.get('iv_summary', pd.DataFrame())
                
                # Count output files
                output_files = ["iv_woe_output.csv (IV summary)", "woe_statistics.csv (detailed WoE)", 
                               "woe_transformed_data.csv (WoE transformed data)"]
                if 5 in st.session_state.step_results:
                    output_files.append("model_data_filtered.csv (filtered dataset)")
                
                st.markdown("#### Overall Summary")
                overall_summary = pd.DataFrame({
                    'Metric': ['Variables Analyzed', 'Output Files Created'],
                    'Count': [len(iv_summary), len(output_files)],
                    'Details': [
                        f"{len(iv_summary)} numeric variables from input data",
                        ", ".join(output_files)
                    ]
                })
                st.dataframe(overall_summary, use_container_width=True, hide_index=True)
        
        # Step-by-step summary
        st.markdown("---")
        st.markdown("#### Step-by-Step Summary")
        
        # Step 1 summary
        if 0 in st.session_state.step_results:
            step1_result = st.session_state.step_results[0]
            st.markdown("##### Step 1: Get Numeric Variables")
            summary_table = pd.DataFrame({
                'Metric': ['Numeric Variables Found'],
                'Count': [step1_result['count']],
                'Details': [f"{step1_result['count']} variables (excluding default_flag)"]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 2 summary
        if 1 in st.session_state.step_results:
            st.markdown("##### Step 2: Create Empty Base Tables")
            summary_table = pd.DataFrame({
                'Metric': ['Structures Created'],
                'Count': [2],
                'Details': ["Empty IV summary and WoE statistics tables with correct structure"]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 3 summary
        if 2 in st.session_state.step_results:
            step3_result = st.session_state.step_results[2]
            if isinstance(step3_result, dict):
                iv_summary = step3_result.get('iv_summary', pd.DataFrame())
                woe_all = step3_result.get('woe_all', pd.DataFrame())
                
                st.markdown("##### Step 3: Calculate WoE and IV for All Variables")
                summary_table = pd.DataFrame({
                    'Metric': ['Variables Analyzed', 'IV Values Calculated', 'WoE Bins Created', 'Top IV Value'],
                    'Count': [
                        len(iv_summary),
                        len(iv_summary),
                        len(woe_all),
                        iv_summary['IV'].max() if not iv_summary.empty else 0
                    ],
                    'Details': [
                        f"All {len(iv_summary)} numeric variables processed (manual binning for bureau_score)",
                        f"IV calculated for {len(iv_summary)} variables",
                        f"Total bins across all variables: {len(woe_all)}",
                        f"Highest IV: {iv_summary['IV'].max():.4f}" if not iv_summary.empty else "N/A"
                    ]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 4 summary
        if 3 in st.session_state.step_results:
            step4_result = st.session_state.step_results[3]
            st.markdown("##### Step 4: Apply WoE Transformations")
            summary_table = pd.DataFrame({
                'Metric': ['Variables Transformed', 'Output Rows', 'Output Columns'],
                'Count': [
                    step1_result['count'] if 0 in st.session_state.step_results else 0,
                    step4_result.get('rows', 0),
                    step4_result.get('columns', 0)
                ],
                'Details': [
                    f"WoE transformations applied to all numeric variables",
                    f"Transformed dataset contains {step4_result.get('rows', 0):,} rows",
                    f"Transformed dataset contains {step4_result.get('columns', 0)} columns"
                ]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 5 summary
        if 4 in st.session_state.step_results:
            step5_result = st.session_state.step_results[4]
            st.markdown("##### Step 5: Create Expanded Keep List and Filter Variables")
            summary_table = pd.DataFrame({
                'Metric': ['Keep List Variables', 'Variables Selected to Keep', 'IV Filter Criteria'],
                'Count': [
                    len(step5_result.get('keep_list', [])),
                    len(step5_result.get('vars_to_keep', [])),
                    1
                ],
                'Details': [
                    f"{len(step5_result.get('keep_list', []))} forced variables in keep list",
                    f"{len(step5_result.get('vars_to_keep', []))} variables selected (keep list + IV >= 0.015 and <= 5.0)",
                    "IV >= 0.015 and <= 5.0, or variables in keep list"
                ]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 6 summary
        if 5 in st.session_state.step_results:
            step6_result = st.session_state.step_results[5]
            st.markdown("##### Step 6: Create Final Filtered Dataset")
            summary_table = pd.DataFrame({
                'Metric': ['Selected Variables', 'Final Columns', 'Variables Removed', 'Output File'],
                'Count': [
                    len(step6_result.get('selected_vars', [])),
                    step6_result.get('columns', 0),
                    step6_result.get('vars_removed', 0),
                    1
                ],
                'Details': [
                    f"{len(step6_result.get('selected_vars', []))} variables selected (only existing in dataset)",
                    f"{step6_result.get('columns', 0)} total columns ({len(step6_result.get('selected_vars', []))} variables + default_flag)",
                    f"{step6_result.get('vars_removed', 0)} variables removed during filtering",
                    "model_data_filtered.csv (equivalent to CREDIT.PD_MODEL_DATA_CH10_FILTERED)"
                ]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
