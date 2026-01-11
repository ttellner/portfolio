"""
Collinearity Analysis
Performs correlation and VIF filtering to remove collinear variables.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import List, Optional

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from collinear_functions import (
    calculate_correlation_matrix,
    find_high_correlation_pairs,
    identify_vars_to_drop_correlation,
    apply_correlation_filter,
    calculate_vif,
    identify_vars_to_drop_vif,
    apply_vif_filter,
    run_full_collinearity_analysis
)
from iv_woe_functions import create_expanded_keep_list

# Page configuration
st.set_page_config(
    page_title="Collinearity Analysis",
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
last_page = st.session_state.get("last_page_collinear", "")

if current_page == "collinear_analysis.py" and last_page != "collinear_analysis.py":
    # Coming to this page fresh - reset state
    if 'input_data' in st.session_state:
        del st.session_state.input_data
    if 'step_results' in st.session_state:
        del st.session_state.step_results
    if 'current_step' in st.session_state:
        del st.session_state.current_step

st.session_state.last_page_collinear = current_page

    # Initialize session state
if 'input_data' not in st.session_state:
    st.session_state.input_data = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'step_results' not in st.session_state:
    st.session_state.step_results = {}
if 'starting_columns' not in st.session_state:
    st.session_state.starting_columns = []

# Step definitions with descriptions and code snippets
STEPS = [
    {
        'number': 1,
        'name': 'Correlation Filtering',
        'description': 'Calculates correlation matrix, identifies high correlation pairs (>=0.90), and drops variables with correlation > 0.98 or (correlation > 0.95 and IV < 0.02).',
        'code': '''
# Calculate correlation matrix
corr_matrix = calculate_correlation_matrix(df)

# Find high correlation pairs (>=0.90)
high_corr_pairs = find_high_correlation_pairs(corr_matrix, threshold=0.90)

# Identify variables to drop based on correlation and IV
vars_to_drop = identify_vars_to_drop_correlation(
    high_corr_pairs, iv_summary=iv_summary,
    corr_threshold_high=0.98,
    corr_threshold_medium=0.95,
    iv_threshold=0.02
)

# Apply correlation filter
df_filtered = apply_correlation_filter(df, vars_to_drop)
'''
    },
    {
        'number': 2,
        'name': 'VIF Filtering',
        'description': 'Calculates Variance Inflation Factor (VIF) for all variables, identifies variables with VIF > 10 (excluding key variables), and drops them.',
        'code': '''
# Calculate VIF for all variables
vif_df = calculate_vif(df_filtered, target_col='default_flag')

# Identify variables with VIF > 10 (excluding key variables)
vars_to_drop_vif = identify_vars_to_drop_vif(
    vif_df, vif_threshold=10.0,
    exclude_vars=['bureau_score', 'salary_credit_3m', ...]
)

# Apply VIF filter
df_vif_filtered = apply_vif_filter(df_filtered, vars_to_drop_vif)
'''
    },
    {
        'number': 3,
        'name': 'Apply Final Keep List Filter',
        'description': 'Filters to only keep columns that are in the keep list from IV/WoE Analysis. Only columns from model_data_filtered.csv that are in the IV/WoE keep list are retained.',
        'code': '''
# Get keep list from IV/WoE Analysis
keep_list = create_expanded_keep_list()

# Filter to only columns in keep list (and target)
columns_to_keep = [col for col in df_vif_filtered.columns 
                   if col in keep_list or col == 'default_flag']
df_final = df_vif_filtered[columns_to_keep].copy()
'''
    }
]


def load_data_from_file():
    """Load data from CSV file with fallback options."""
    # Primary input: model_data_filtered.csv (from iv_woe_analysis.py Step 6)
    data_file = current_dir / "data" / "model_data_filtered.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    
    # Fallback: woe_transformed_data.csv (from iv_woe_analysis.py Step 4)
    fallback_file = current_dir / "data" / "woe_transformed_data.csv"
    if fallback_file.exists():
        st.info("Using fallback data file: woe_transformed_data.csv (from IV/WoE Analysis Step 4)")
        return pd.read_csv(fallback_file)
    
    # If neither exists, show error
    st.error(f"Data file not found. Please ensure one of the following exists:\n"
             f"- {data_file.name} (from IV/WoE Analysis Step 6)\n"
             f"- {fallback_file.name} (from IV/WoE Analysis Step 4)")
    return None


def load_iv_summary():
    """Load IV summary if available."""
    iv_file = current_dir / "data" / "iv_woe_output.csv"
    if iv_file.exists():
        try:
            iv_df = pd.read_csv(iv_file)
            if 'variable' in iv_df.columns and 'IV' in iv_df.columns:
                return iv_df[['variable', 'IV']]
        except Exception:
            pass
    return None


def create_column_summary(
    starting_columns: List[str],
    keep_list: List[str],
    vars_dropped_corr: List[str],
    vars_dropped_vif: List[str],
    vars_dropped_final: List[str],
    final_columns: List[str],
    iv_summary: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Create a summary of column categorization and filtering.
    
    Parameters:
    -----------
    starting_columns : list
        List of columns in the starting dataset
    keep_list : list
        List of business critical columns (from IV/WoE keep list)
    vars_dropped_corr : list
        Variables dropped due to correlation filtering
    vars_dropped_vif : list
        Variables dropped due to VIF filtering
    vars_dropped_final : list
        Variables dropped in final step (not in keep list)
    final_columns : list
        Final columns in the dataset
    iv_summary : pd.DataFrame, optional
        IV summary DataFrame with 'variable' and 'IV' columns
    
    Returns:
    --------
    pd.DataFrame : Summary DataFrame with columns: variable, category, reason, status
    """
    summary_data = []
    iv_dict = {}
    if iv_summary is not None and not iv_summary.empty:
        iv_dict = dict(zip(iv_summary['variable'], iv_summary['IV']))
    
    # Categorize all starting columns
    for col in starting_columns:
        if col == 'default_flag':
            category = 'Target'
            reason = 'Target variable'
            status = 'Kept'
        elif col in keep_list:
            category = 'Business Critical'
            reason = 'In keep list from IV/WoE Analysis'
            if col in vars_dropped_corr:
                status = f'Dropped (Correlation)'
            elif col in vars_dropped_vif:
                status = f'Dropped (VIF)'
            elif col in vars_dropped_final:
                status = f'Dropped (Not in keep list)'
            elif col in final_columns:
                status = 'Kept'
            else:
                status = 'Dropped (Other)'
        else:
            # Not in keep list - categorize by IV if available
            iv_value = iv_dict.get(col, None)
            if iv_value is not None:
                category = 'IV Filtered'
                reason = f'IV = {iv_value:.4f}'
            else:
                category = 'Other'
                reason = 'Not in keep list'
            
            if col in vars_dropped_corr:
                status = 'Dropped (Correlation)'
            elif col in vars_dropped_vif:
                status = 'Dropped (VIF)'
            elif col in vars_dropped_final:
                status = 'Dropped (Not in keep list)'
            elif col in final_columns:
                status = 'Kept'
            else:
                status = 'Dropped (Other)'
        
        summary_data.append({
            'variable': col,
            'category': category,
            'reason': reason,
            'status': status
        })
    
    return pd.DataFrame(summary_data)


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
    
    st.markdown('<h1 class="main-header">Collinearity Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application performs collinearity analysis by filtering out highly correlated 
    variables and variables with high Variance Inflation Factor (VIF). This helps 
    reduce multicollinearity in the dataset.
    
    **Instructions:**
    1. Default data (model_data_filtered.csv) is loaded automatically
    2. Execute each step sequentially
    3. View correlation pairs and VIF values
    4. Download the final model_ready_data.csv
    """)
    
    st.markdown("---")
    
    # Auto-load default data if not already loaded
    if st.session_state.input_data is None:
        data = load_data_from_file()
        if data is not None:
            st.session_state.input_data = data
            st.session_state.current_step = 0
            st.session_state.step_results = {}
            st.session_state.starting_columns = list(data.columns)
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Data Information")
        if st.session_state.input_data is not None:
            st.success(f"Data loaded: {len(st.session_state.input_data):,} rows, {len(st.session_state.input_data.columns)} columns")
            # Check which file was actually loaded
            filtered_file = current_dir / "data" / "model_data_filtered.csv"
            if filtered_file.exists():
                st.caption("Default: model_data_filtered.csv")
            else:
                st.caption("Using: woe_transformed_data.csv (fallback)")
        
        st.markdown("---")
        
        if st.session_state.input_data is not None:
            st.header("Step Navigation")
            
            for i, step in enumerate(STEPS):
                status = "✅" if i < st.session_state.current_step else "⏳"
                if st.button(f"{status} {step['name']}", 
                            key=f"nav_{i}",
                            disabled=(i > st.session_state.current_step)):
                    if 0 <= i < len(STEPS):
                        st.session_state.current_step = i
                        st.rerun()
            
            st.markdown("---")
            if st.button("Reset All Steps"):
                st.session_state.current_step = 0
                st.session_state.step_results = {}
                st.rerun()
            
            # Download button for final output
            if 2 in st.session_state.step_results:
                st.markdown("---")
                st.header("Download Results")
                output_file = current_dir / "data" / "model_ready_data.csv"
                if output_file.exists():
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="Download model_ready_data.csv",
                            data=f.read(),
                            file_name="model_ready_data.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        else:
            st.info("Please load data first")
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please ensure one of the following exists in the data folder:\n"
                 "- model_data_filtered.csv (from IV/WoE Analysis Step 6)\n"
                 "- woe_transformed_data.csv (from IV/WoE Analysis Step 4)")
        st.info("💡 **Tip:** Run the previous analysis steps to generate the required input file, or ensure the default files exist.")
        return
    
    # Load IV summary if available
    iv_summary = load_iv_summary()
    
    # Display current step
    if st.session_state.current_step < len(STEPS):
        step = STEPS[st.session_state.current_step]
        current_step_idx = st.session_state.current_step
        
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
                    pass  # Disabled for now
            else:
                button_text = "Execute Step"
                if st.button(button_text, type="primary", disabled=execute_disabled):
                    with st.spinner(f"Executing {step['name']}..."):
                        try:
                            input_df = st.session_state.input_data.copy()
                            
                            # Step 1: Correlation Filtering
                            if step['number'] == 1:
                                corr_matrix = calculate_correlation_matrix(input_df)
                                high_corr_pairs = find_high_correlation_pairs(corr_matrix, threshold=0.90)
                                vars_to_drop_corr = identify_vars_to_drop_correlation(
                                    high_corr_pairs, iv_summary=iv_summary
                                )
                                df_corr_filtered = apply_correlation_filter(input_df, vars_to_drop_corr)
                                
                                result = {
                                    'corr_matrix': corr_matrix,
                                    'high_corr_pairs': high_corr_pairs,
                                    'vars_dropped': vars_to_drop_corr,
                                    'filtered_df': df_corr_filtered,
                                    'rows': len(df_corr_filtered),
                                    'columns': len(df_corr_filtered.columns)
                                }
                                
                                # Update input_data for next step
                                st.session_state.input_data = df_corr_filtered
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.rerun()
                            
                            # Step 2: VIF Filtering
                            elif step['number'] == 2:
                                vif_df = calculate_vif(input_df, target_col='default_flag')
                                vars_to_drop_vif = identify_vars_to_drop_vif(vif_df, vif_threshold=10.0)
                                df_vif_filtered = apply_vif_filter(input_df, vars_to_drop_vif)
                                
                                result = {
                                    'vif_df': vif_df,
                                    'vars_dropped': vars_to_drop_vif,
                                    'filtered_df': df_vif_filtered,
                                    'rows': len(df_vif_filtered),
                                    'columns': len(df_vif_filtered.columns)
                                }
                                
                                # Update input_data for next step
                                st.session_state.input_data = df_vif_filtered
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.rerun()
                            
                            # Step 3: Apply Final Keep List Filter
                            elif step['number'] == 3:
                                # Get keep list from IV/WoE Analysis
                                keep_list = create_expanded_keep_list()
                                
                                # Filter to only columns in keep list (and target)
                                columns_to_keep = [col for col in input_df.columns 
                                                   if col in keep_list or col == 'default_flag']
                                
                                # Identify columns NOT in keep list
                                columns_not_in_keep_list = [col for col in input_df.columns 
                                                            if col not in keep_list and col != 'default_flag']
                                
                                df_final = input_df[columns_to_keep].copy()
                                
                                # Get variables dropped in previous steps
                                vars_dropped_corr = []
                                vars_dropped_vif = []
                                if 0 in st.session_state.step_results:
                                    vars_dropped_corr = st.session_state.step_results[0].get('vars_dropped', [])
                                if 1 in st.session_state.step_results:
                                    vars_dropped_vif = st.session_state.step_results[1].get('vars_dropped', [])
                                
                                # Variables dropped in final step (not in keep list)
                                vars_dropped_final = columns_not_in_keep_list
                                
                                # Create column summary
                                column_summary = create_column_summary(
                                    starting_columns=st.session_state.starting_columns,
                                    keep_list=keep_list,
                                    vars_dropped_corr=vars_dropped_corr,
                                    vars_dropped_vif=vars_dropped_vif,
                                    vars_dropped_final=vars_dropped_final,
                                    final_columns=list(df_final.columns),
                                    iv_summary=iv_summary
                                )
                                
                                # Save to CSV
                                output_file = current_dir / "data" / "model_ready_data.csv"
                                df_final.to_csv(output_file, index=False)
                                
                                result = {
                                    'keep_list': keep_list,
                                    'final_df': df_final,
                                    'rows': len(df_final),
                                    'columns': len(df_final.columns),
                                    'variables': list(df_final.columns),
                                    'columns_not_in_keep_list': columns_not_in_keep_list,
                                    'input_columns': list(input_df.columns),
                                    'column_summary': column_summary,
                                    'vars_dropped_corr': vars_dropped_corr,
                                    'vars_dropped_vif': vars_dropped_vif,
                                    'vars_dropped_final': vars_dropped_final
                                }
                                
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = len(STEPS)  # Mark as complete
                                st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error executing step: {str(e)}")
                            st.exception(e)
        
        # Display results if step is completed
        if current_step_idx in st.session_state.step_results:
            result = st.session_state.step_results[current_step_idx]
            
            st.markdown("---")
            st.success(f"✅ {step['name']} completed successfully!")
            
            # Step 1 special display
            if step['number'] == 1:
                if isinstance(result, dict):
                    high_corr_pairs = result.get('high_corr_pairs', pd.DataFrame())
                    vars_dropped = result.get('vars_dropped', [])
                    filtered_df = result.get('filtered_df', pd.DataFrame())
                    
                    st.subheader("Correlation Filtering Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("High Correlation Pairs", f"{len(high_corr_pairs)}")
                    with col2:
                        st.metric("Variables Dropped", f"{len(vars_dropped)}")
                    with col3:
                        st.metric("Remaining Variables", f"{len(filtered_df.columns)}")
                    
                    if len(vars_dropped) > 0:
                        st.subheader("Variables Dropped")
                        st.write(f"**Total:** {len(vars_dropped)} variables")
                        st.dataframe(pd.DataFrame({'variable': vars_dropped}), use_container_width=True)
                    
                    if not high_corr_pairs.empty:
                        st.subheader("High Correlation Pairs (>=0.90)")
                        st.dataframe(high_corr_pairs, use_container_width=True, height=400)
                    
                    st.subheader("Filtered Data Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{result.get('rows', 0):,}")
                    with col2:
                        st.metric("Columns", f"{result.get('columns', 0)}")
            
            # Step 2 special display
            elif step['number'] == 2:
                if isinstance(result, dict):
                    vif_df = result.get('vif_df', pd.DataFrame())
                    vars_dropped = result.get('vars_dropped', [])
                    filtered_df = result.get('filtered_df', pd.DataFrame())
                    
                    st.subheader("VIF Filtering Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Variables Analyzed", f"{len(vif_df)}")
                    with col2:
                        st.metric("Variables Dropped (VIF > 10)", f"{len(vars_dropped)}")
                    with col3:
                        st.metric("Remaining Variables", f"{len(filtered_df.columns)}")
                    
                    if len(vars_dropped) > 0:
                        st.subheader("Variables Dropped (VIF > 10)")
                        st.dataframe(pd.DataFrame({'variable': vars_dropped}), use_container_width=True)
                    
                    if not vif_df.empty:
                        st.subheader("VIF Values (Sorted by VIF, Descending)")
                        vif_sorted = vif_df.sort_values('VIF', ascending=False)
                        st.dataframe(vif_sorted, use_container_width=True, height=400)
                        
                        st.info("**VIF Interpretation:** Values > 10 indicate high multicollinearity")
                    
                    st.subheader("Filtered Data Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{result.get('rows', 0):,}")
                    with col2:
                        st.metric("Columns", f"{result.get('columns', 0)}")
            
            # Step 3 special display
            elif step['number'] == 3:
                if isinstance(result, dict):
                    keep_list = result.get('keep_list', [])
                    final_df = result.get('final_df', pd.DataFrame())
                    variables = result.get('variables', [])
                    columns_not_in_keep_list = result.get('columns_not_in_keep_list', [])
                    input_columns = result.get('input_columns', [])
                    column_summary = result.get('column_summary', pd.DataFrame())
                    vars_dropped_corr = result.get('vars_dropped_corr', [])
                    vars_dropped_vif = result.get('vars_dropped_vif', [])
                    vars_dropped_final = result.get('vars_dropped_final', [])
                    
                    st.subheader("Final Dataset Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Starting Columns", f"{len(st.session_state.starting_columns)}")
                    with col2:
                        st.metric("Business Critical (Keep List)", f"{len(keep_list)}")
                    with col3:
                        st.metric("Variables in Final Dataset", f"{len(variables)}")
                    with col4:
                        st.metric("Rows", f"{result.get('rows', 0):,}")
                    
                    # Column Summary Table
                    if not column_summary.empty:
                        st.subheader("Column Summary by Category")
                        
                        # Summary statistics
                        summary_stats = column_summary.groupby(['category', 'status']).size().reset_index(name='count')
                        summary_pivot = summary_stats.pivot_table(
                            index='category', 
                            columns='status', 
                            values='count', 
                            fill_value=0
                        )
                        
                        st.dataframe(summary_pivot, use_container_width=True)
                        
                        st.subheader("Detailed Column Summary")
                        
                        # Filter options
                        col1, col2 = st.columns(2)
                        with col1:
                            category_filter = st.multiselect(
                                "Filter by Category",
                                options=sorted(column_summary['category'].unique()),
                                default=sorted(column_summary['category'].unique())
                            )
                        with col2:
                            status_filter = st.multiselect(
                                "Filter by Status",
                                options=sorted(column_summary['status'].unique()),
                                default=sorted(column_summary['status'].unique())
                            )
                        
                        filtered_summary = column_summary[
                            (column_summary['category'].isin(category_filter)) &
                            (column_summary['status'].isin(status_filter))
                        ].copy()
                        
                        st.dataframe(
                            filtered_summary.sort_values(['category', 'status', 'variable']),
                            use_container_width=True,
                            height=400
                        )
                        
                        # Breakdown by category
                        st.subheader("Breakdown by Category")
                        
                        # Business Critical columns
                        business_critical = filtered_summary[filtered_summary['category'] == 'Business Critical']
                        if not business_critical.empty:
                            st.markdown("**Business Critical Columns (From Keep List):**")
                            kept_bc = business_critical[business_critical['status'] == 'Kept']
                            dropped_bc = business_critical[business_critical['status'] != 'Kept']
                            st.write(f"- Kept: {len(kept_bc)} columns")
                            if len(dropped_bc) > 0:
                                st.write(f"- Dropped: {len(dropped_bc)} columns (due to correlation/VIF filtering)")
                                st.dataframe(dropped_bc[['variable', 'status']], use_container_width=True)
                        
                        # IV Filtered columns
                        iv_filtered = filtered_summary[filtered_summary['category'] == 'IV Filtered']
                        if not iv_filtered.empty:
                            st.markdown("**IV Filtered Columns (Not in Keep List):**")
                            kept_iv = iv_filtered[iv_filtered['status'] == 'Kept']
                            dropped_iv = iv_filtered[iv_filtered['status'] != 'Kept']
                            st.write(f"- Kept: {len(kept_iv)} columns (good IV but dropped in final step if not in keep list)")
                            if len(dropped_iv) > 0:
                                st.write(f"- Dropped: {len(dropped_iv)} columns")
                    
                    # Show columns NOT in keep list (if any)
                    if len(columns_not_in_keep_list) > 0:
                        st.subheader("Columns Dropped in Final Step (Not in Keep List)")
                        st.info(f"**{len(columns_not_in_keep_list)} columns** from the input file were NOT in the IV/WoE keep list and were excluded from the final dataset:")
                        st.dataframe(pd.DataFrame({'variable': columns_not_in_keep_list}), use_container_width=True)
                    else:
                        st.success("All columns in the input file were in the keep list from IV/WoE Analysis.")
                    
                    st.subheader("Final Variables (From Keep List)")
                    st.dataframe(pd.DataFrame({'variable': variables}), use_container_width=True)
                    
                    st.subheader("Final Dataset Preview (First 20 Rows)")
                    if not final_df.empty:
                        st.dataframe(final_df.head(20), use_container_width=True)
                    
                    st.success(f"✅ Final dataset saved to model_ready_data.csv with {len(variables)} variables")


if __name__ == "__main__":
    main()

