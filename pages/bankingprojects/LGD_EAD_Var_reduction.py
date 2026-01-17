"""
LGD/EAD.1 Variable Reduction
Performs variable reduction for LGD and EAD modeling through multiple stages.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Tuple, List


# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Page configuration
st.set_page_config(
    page_title="LGD/EAD.1 Variable Reduction",
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
    .code-block {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Reset session state when navigating to this page
current_page = st.query_params.get("project", "")
last_page = st.session_state.get("last_page_lgd_ead", "")

if current_page == "LGD_EAD_Var_reduction.py" and last_page != "LGD_EAD_Var_reduction.py":
    if 'input_data' in st.session_state:
        del st.session_state.input_data
    if 'stage_results' in st.session_state:
        del st.session_state.stage_results
    if 'current_stage' in st.session_state:
        del st.session_state.current_stage

st.session_state.last_page_lgd_ead = current_page

# Initialize session state
if 'input_data' not in st.session_state:
    st.session_state.input_data = None
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 0
if 'stage_results' not in st.session_state:
    st.session_state.stage_results = {}


def load_data_from_file() -> pd.DataFrame:
    """Load default data file from /data/LGD_EAD_Modeling_240Vars_Final.csv."""
    data_dir = current_dir / "data"
    default_file = data_dir / "LGD_EAD_Modeling_240Vars_Final.csv"  # /data/LGD_EAD_Modeling_240Vars_Final.csv
    
    if default_file.exists():
        try:
            df = pd.read_csv(default_file)
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None
    else:
        return None


def save_to_csv(df: pd.DataFrame, filename: str) -> Path:
    """Save DataFrame to CSV in data directory."""
    data_dir = current_dir / "data"
    data_dir.mkdir(exist_ok=True)
    filepath = data_dir / filename
    df.to_csv(filepath, index=False)
    return filepath


def stage1_drop_unneeded_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Stage 1: Drop unneeded columns.
    """
    columns_to_drop = [
        'dpd_ever_90_flag',
        'dpd_90plus_cnt',
        'partial_recovery_flag',
        'full_recovery_flag',
        'zero_recovery_flag',
        'secured_flag',
        'lgd_model_ready_flag',
        'interest_component_ratio',
        'default_in_observation_window',
        'is_defaulter',
        'recovery_flag',
        'late_dpd_flag',
        'loan_age_months',
        'is_multiple_defaults',
        'emi_burden_flag',
        'high_risk_profile_flag',
        'zero_utilization_flag',
        'full_utilization_flag',
        'loss_flag',
        'secured_and_recovered_flag',
        'no_collateral_no_recovery_flag',
        'high_emi_score',
        'secured_or_recovered_flag',
        'emi_affordability_flag',
        'disbursement_year',
        'default_and_loss_flag',
        'secured_with_loss_flag',
        'zero_exposure_flag',
        'dpd_no_peak_flag',
        'high_loss_low_recovery_flag',
        'overdrawn_flag',
        'underutilization_flag',
        'overutilization_gap',
        'total_limit_missing_flag',
        'limit_ratio_vs_score',
        'full_drawn_and_overdue_flag',
        'high_risk_loan_flag',
        'interest_income_ratio',
        'high_emi_and_interest_flag',
        'employment_emi_risk',
        'secure_home_high_loan_flag',
        'high_interest_tenure_flag',
        'emi_vs_limit_ratio',
        'emi_vs_drawn_ratio',
        'emi_vs_ead_ratio'
    ]
    
    # Only drop columns that exist
    existing_cols_to_drop = [col for col in columns_to_drop if col in df.columns]
    df_result = df.drop(columns=existing_cols_to_drop)
    
    return df_result, existing_cols_to_drop


def stage2_drop_technical_identifiers(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Stage 2: Drop Technical Identifiers & Engineered Sources.
    """
    columns_to_drop = [
        'customer_id',           # Unique ID, not predictive
        'disbursed_month',       # Seasonality, replace with tenure
        'term_score',            # Derived from loan_term
        'loan_amount_score',     # Derived from loan_amount
        'loan_interest_term_combo'  # Engineered combo; hard to interpret
    ]
    
    # Only drop columns that exist
    existing_cols_to_drop = [col for col in columns_to_drop if col in df.columns]
    df_result = df.drop(columns=existing_cols_to_drop)
    
    return df_result, existing_cols_to_drop


def stage3_drop_high_correlation(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], pd.DataFrame, pd.DataFrame]:
    """
    Stage 3: Drop variables with high correlation.
    Creates correlation matrix, finds pairs > 0.95, compares with hardcoded columns,
    but drops only hardcoded columns.
    """
    # Hardcoded columns to drop (from SAS code)
    hardcoded_columns_to_drop = [
        'dpd_mean',                      # Duplicate of dpd_avg
        'total_past_due',                # Covered by dpd_avg and dpd_m1-m12
        'utilization_to_limit_ratio',    # Same as drawn_vs_limit_ratio
        'exposure_percent_drawn',        # Same as drawn_vs_exposure_ratio
        'exposure_to_income_ratio'       # Same as emi_to_income_ratio
    ]
    
    # Get numeric columns only
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Create correlation matrix
    corr_matrix = df[numeric_cols].corr()
    
    # Find pairs with correlation > 0.95
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr_value = corr_matrix.iloc[i, j]
            if not np.isnan(corr_value) and abs(corr_value) > 0.95:
                high_corr_pairs.append({
                    'var1': col1,
                    'var2': col2,
                    'corr_value': corr_value
                })
    
    high_corr_df = pd.DataFrame(high_corr_pairs)
    
    # Identify columns that would be dropped by correlation analysis (> 0.95)
    # (typically drop var2 in each pair)
    correlation_dropped = set()
    if len(high_corr_pairs) > 0:
        for pair in high_corr_pairs:
            correlation_dropped.add(pair['var2'])
    
    # Compare with hardcoded columns
    existing_hardcoded = [col for col in hardcoded_columns_to_drop if col in df.columns]
    correlation_dropped_set = set(correlation_dropped)
    hardcoded_set = set(existing_hardcoded)
    
    # Differences
    in_correlation_not_hardcoded = sorted(list(correlation_dropped_set - hardcoded_set))
    in_hardcoded_not_correlation = sorted(list(hardcoded_set - correlation_dropped_set))
    in_both = sorted(list(correlation_dropped_set & hardcoded_set))
    
    # Create comparison DataFrame with proper handling of different lengths
    max_len = max(len(in_correlation_not_hardcoded), 
                  len(in_hardcoded_not_correlation), 
                  len(in_both)) if (in_correlation_not_hardcoded or in_hardcoded_not_correlation or in_both) else 0
    
    # Pad lists with empty strings to same length (or create empty lists if all are empty)
    if max_len > 0:
        in_corr_padded = in_correlation_not_hardcoded + [''] * (max_len - len(in_correlation_not_hardcoded))
        in_hardcoded_padded = in_hardcoded_not_correlation + [''] * (max_len - len(in_hardcoded_not_correlation))
        in_both_padded = in_both + [''] * (max_len - len(in_both))
    else:
        in_corr_padded = []
        in_hardcoded_padded = []
        in_both_padded = []
    
    comparison_df = pd.DataFrame({
        'in_correlation_not_hardcoded': in_corr_padded,
        'in_hardcoded_not_correlation': in_hardcoded_padded,
        'in_both': in_both_padded
    })
    
    # Drop only hardcoded columns
    df_result = df.drop(columns=existing_hardcoded)
    
    return df_result, existing_hardcoded, high_corr_df, comparison_df


def stage4_near_zero_variance_filtering(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], pd.DataFrame]:
    """
    Stage 4: Near-zero Variance Filtering.
    Gets frequencies for binary/flag variables, then scans and deletes columns with
    either standard deviation < 0.01 or MIN=MAX.
    """
    # First, get frequencies for binary/flag variables
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate statistics for all numeric variables
    variance_stats = []
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            std_val = col_data.std()
            min_val = col_data.min()
            max_val = col_data.max()
            
            variance_stats.append({
                'variable': col,
                'std': std_val,
                'min': min_val,
                'max': max_val,
                'n': len(col_data),
                'nmiss': df[col].isnull().sum()
            })
    
    variance_df = pd.DataFrame(variance_stats)
    
    # Identify columns to drop: std < 0.01 or MIN = MAX
    columns_to_drop = []
    for stat in variance_stats:
        if stat['std'] < 0.01 or (not np.isnan(stat['min']) and not np.isnan(stat['max']) and stat['min'] == stat['max']):
            columns_to_drop.append(stat['variable'])
    
    # Drop the identified columns
    df_result = df.drop(columns=columns_to_drop)
    
    return df_result, columns_to_drop, variance_df


def stage5_final_summary(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Stage 5: Final Summary.
    Calculate missing values, keep only variables with < 30% missing.
    """
    # Calculate N and NMISS for all columns
    missing_summary = []
    for col in df.columns:
        n = df[col].count()
        nmiss = df[col].isnull().sum()
        missing_pct = (nmiss / len(df)) * 100 if len(df) > 0 else 0
        
        missing_summary.append({
            'varname': col,
            'n': n,
            'nmiss': nmiss,
            'missing_pct': missing_pct
        })
    
    missing_df = pd.DataFrame(missing_summary)
    
    # Keep only variables with < 30% missing
    keep_vars = missing_df[missing_df['missing_pct'] < 30]['varname'].tolist()
    columns_dropped = [col for col in df.columns if col not in keep_vars]
    
    df_result = df[keep_vars].copy()
    
    return df_result, missing_df, columns_dropped


# Stage definitions
STAGES = [
    {
        'number': 1,
        'name': 'Stage 1: Drop Unneeded Columns',
        'description': 'Drops unneeded columns from the dataset.',
        'function': stage1_drop_unneeded_columns,
        'code': '''
# Drop unneeded columns
columns_to_drop = [
    'dpd_ever_90_flag', 'dpd_90plus_cnt', 'partial_recovery_flag',
    'full_recovery_flag', 'zero_recovery_flag', 'secured_flag',
    # ... (45 columns total)
]
df_result = df.drop(columns=columns_to_drop)
'''
    },
    {
        'number': 2,
        'name': 'Stage 2: Drop Technical Identifiers & Engineered Sources',
        'description': 'Drops technical identifiers and engineered source variables.',
        'function': stage2_drop_technical_identifiers,
        'code': '''
# Drop technical identifiers and engineered sources
columns_to_drop = [
    'customer_id',              # Unique ID, not predictive
    'disbursed_month',          # Seasonality, replace with tenure
    'term_score',               # Derived from loan_term
    'loan_amount_score',        # Derived from loan_amount
    'loan_interest_term_combo'  # Engineered combo; hard to interpret
]
df_result = df.drop(columns=columns_to_drop)
'''
    },
    {
        'number': 3,
        'name': 'Stage 3: Drop Variables with High Correlation',
        'description': 'Creates correlation matrix, identifies pairs with Pearson correlation > 0.95, compares with hardcoded columns, but drops only hardcoded columns.',
        'function': stage3_drop_high_correlation,
        'code': '''
# Create correlation matrix
numeric_cols = df.select_dtypes(include=[np.number]).columns
corr_matrix = df[numeric_cols].corr()

# Find pairs with correlation > 0.95
high_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if abs(corr_matrix.iloc[i, j]) > 0.95:
            high_corr_pairs.append({
                'var1': corr_matrix.columns[i],
                'var2': corr_matrix.columns[j],
                'corr_value': corr_matrix.iloc[i, j]
            })

# Compare with hardcoded columns and drop only hardcoded
hardcoded_columns = ['dpd_mean', 'total_past_due', ...]
df_result = df.drop(columns=hardcoded_columns)
'''
    },
    {
        'number': 4,
        'name': 'Stage 4: Near-zero Variance Filtering',
        'description': 'Gets frequencies for binary/flag variables, then scans and deletes columns with standard deviation < 0.01 or MIN=MAX.',
        'function': stage4_near_zero_variance_filtering,
        'code': '''
# Calculate statistics for numeric variables
variance_stats = []
for col in numeric_cols:
    std_val = df[col].std()
    min_val = df[col].min()
    max_val = df[col].max()
    # ... store stats

# Drop columns with std < 0.01 or MIN = MAX
columns_to_drop = [col for col in numeric_cols 
                   if df[col].std() < 0.01 or df[col].min() == df[col].max()]
df_result = df.drop(columns=columns_to_drop)
'''
    },
    {
        'number': 5,
        'name': 'Stage 5: Final Summary',
        'description': 'Calculates missing values and keeps only variables with < 30% missing.',
        'function': stage5_final_summary,
        'code': '''
# Calculate missing percentages
missing_summary = []
for col in df.columns:
    missing_pct = (df[col].isnull().sum() / len(df)) * 100
    # ... store stats

# Keep only variables with < 30% missing
keep_vars = [col for col in df.columns 
             if (df[col].isnull().sum() / len(df)) * 100 < 30]
df_result = df[keep_vars].copy()
'''
    }
]


def display_stage_info(stage):
    """Display information about the current stage."""
    st.markdown(f'<h2 class="stage-header">Stage {stage["number"]}: {stage["name"]}</h2>', unsafe_allow_html=True)
    st.markdown(f"**Description:** {stage['description']}")
    st.markdown("---")
    
    st.markdown("**Code:**")
    st.code(stage['code'], language='python')


def main():
    """Main application function."""
    st.markdown('<h1 class="main-header">LGD/EAD.1 Variable Reduction</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application performs variable reduction for LGD and EAD modeling through multiple stages.
    It processes the input dataset by dropping unneeded columns, technical identifiers, 
    highly correlated variables, near-zero variance variables, and variables with high missing rates.
    
    **Instructions:**
    1. Default data (LGD_EAD_Modeling_240Vars_Final.csv) is loaded automatically
    2. Execute each stage sequentially
    3. View the code and output for each stage
    4. All output tables are saved as CSV files in the data directory
    """)
    
    st.markdown("---")
    
    # Auto-load default data if not already loaded
    if st.session_state.input_data is None:
        data = load_data_from_file()
        if data is not None:
            st.session_state.input_data = data
            st.session_state.current_stage = 0
            st.session_state.stage_results = {}
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Data Information")
        if st.session_state.input_data is not None:
            st.success(f"Data loaded: {len(st.session_state.input_data):,} rows, {len(st.session_state.input_data.columns)} columns")
            st.caption("Default: LGD_EAD_Modeling_240Vars_Final.csv")
        else:
            st.info("Please load data first")
        
        st.markdown("---")
        
        if st.session_state.input_data is not None:
            st.header("Stage Navigation")
            
            for i, stage in enumerate(STAGES):
                status = "✅" if i < st.session_state.current_stage else "⏳"
                if st.button(f"{status} {stage['name']}", 
                            key=f"nav_{i}",
                            disabled=(i > st.session_state.current_stage)):
                    st.session_state.current_stage = i
                    st.rerun()
            
            st.markdown("---")
            if st.button("Reset All Stages"):
                st.session_state.current_stage = 0
                st.session_state.stage_results = {}
                st.rerun()
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please check that LGD_EAD_Modeling_240Vars_Final.csv exists in the data folder.")
        return
    
    # Display current stage
    current_stage_idx = st.session_state.current_stage
    stage = STAGES[current_stage_idx]
    
    # Stage information
    display_stage_info(stage)
    
    st.markdown("---")
    
    # Execute stage button
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_disabled = current_stage_idx in st.session_state.stage_results
        if st.button("Execute Stage", type="primary", disabled=execute_disabled):
            with st.spinner(f"Executing {stage['name']}..."):
                # Get input data for this stage
                if current_stage_idx == 0:
                    input_df = st.session_state.input_data.copy()
                else:
                    input_df = st.session_state.stage_results[current_stage_idx - 1]['output_df'].copy()
                
                # Execute stage function
                try:
                    result = stage['function'](input_df)
                    
                    if current_stage_idx == 2:  # Stage 3 returns 4 items
                        output_df, dropped_cols, high_corr_df, comparison_df = result
                        # Save outputs
                        save_to_csv(output_df, f"reduced_stage{stage['number']}.csv")
                        save_to_csv(high_corr_df, f"stage{stage['number']}_high_corr_pairs.csv")
                        save_to_csv(comparison_df, f"stage{stage['number']}_correlation_comparison.csv")
                    elif current_stage_idx == 3:  # Stage 4 returns 3 items
                        output_df, dropped_cols, variance_df = result
                        save_to_csv(output_df, f"reduced_stage{stage['number']}.csv")
                        save_to_csv(variance_df, f"stage{stage['number']}_variance_check.csv")
                    elif current_stage_idx == 4:  # Stage 5 returns 3 items
                        output_df, missing_df, dropped_cols = result
                        save_to_csv(output_df, f"reduced_stage{stage['number']}.csv")
                        save_to_csv(missing_df, f"stage{stage['number']}_missing_summary.csv")
                    else:  # Stages 1 and 2 return 2 items
                        output_df, dropped_cols = result
                        save_to_csv(output_df, f"reduced_stage{stage['number']}.csv")
                    
                    # Store results
                    stage_result = {
                        'output_df': output_df,
                        'dropped_cols': dropped_cols
                    }
                    
                    if current_stage_idx == 2:
                        stage_result['high_corr_df'] = high_corr_df
                        stage_result['comparison_df'] = comparison_df
                    elif current_stage_idx == 3:
                        stage_result['variance_df'] = variance_df
                    elif current_stage_idx == 4:
                        stage_result['missing_df'] = missing_df
                    
                    st.session_state.stage_results[current_stage_idx] = stage_result
                    st.session_state.current_stage = min(current_stage_idx + 1, len(STAGES) - 1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error executing stage: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Display results if stage has been executed
    if current_stage_idx in st.session_state.stage_results:
        result = st.session_state.stage_results[current_stage_idx]
        
        st.markdown("---")
        st.markdown("### Stage Results")
        
        # Display dropped columns
        dropped_cols = result['dropped_cols']
        st.markdown(f"**Columns Dropped:** {len(dropped_cols)}")
        if len(dropped_cols) > 0:
            st.write(f"**Dropped Columns:** {', '.join(dropped_cols)}")
            st.write(pd.DataFrame({'Dropped Columns': dropped_cols}))
        else:
            st.info("No columns were dropped in this stage.")
        
        # Display output dataframe info
        output_df = result['output_df']
        st.markdown(f"**Output Shape:** {output_df.shape[0]:,} rows × {output_df.shape[1]} columns")
        
        # Stage-specific outputs
        if current_stage_idx == 2:  # Stage 3
            st.markdown("### High Correlation Pairs (correlation > 0.95)")
            if len(result['high_corr_df']) > 0:
                st.dataframe(result['high_corr_df'])
            else:
                st.info("No high correlation pairs found (correlation > 0.95)")
            
            st.markdown("### Correlation Analysis Comparison")
            st.dataframe(result['comparison_df'])
            
            # Extract counts from comparison dataframe (non-empty values)
            in_corr_not_hard = len([x for x in result['comparison_df']['in_correlation_not_hardcoded'] if x != ''])
            in_hard_not_corr = len([x for x in result['comparison_df']['in_hardcoded_not_correlation'] if x != ''])
            in_both = len([x for x in result['comparison_df']['in_both'] if x != ''])
            
            # Print summary
            st.markdown("**Summary:**")
            st.write(f"- Variables in correlation analysis but NOT in hardcoded list: {in_corr_not_hard}")
            st.write(f"- Variables in hardcoded list but NOT in correlation analysis: {in_hard_not_corr}")
            st.write(f"- Variables in BOTH lists: {in_both}")
        
        elif current_stage_idx == 3:  # Stage 4
            st.markdown("### Variance Statistics")
            st.dataframe(result['variance_df'])
        
        elif current_stage_idx == 4:  # Stage 5
            st.markdown("### Missing Value Summary")
            st.dataframe(result['missing_df'])
        
        # Display sample of output dataframe
        st.markdown("### Output Data Preview (first 10 rows)")
        st.dataframe(output_df.head(10))
        
        # Display final dataset at the last stage
        if current_stage_idx == len(STAGES) - 1:
            st.markdown("---")
            st.markdown("### Final Dataset")
            st.write(f"**Final Shape:** {output_df.shape[0]:,} rows × {output_df.shape[1]} columns")
            st.write(f"**Final Columns:** {len(output_df.columns)} variables")
            st.dataframe(output_df)
            
            # Save final dataset
            final_path = save_to_csv(output_df, "lgd_ead_reduced_final.csv")
            st.success(f"Final dataset saved to: {final_path}")
    
    # Show next stage button
    if current_stage_idx < len(STAGES) - 1:
        if current_stage_idx in st.session_state.stage_results:
            st.markdown("---")
            if st.button("Next Stage", type="primary"):
                st.session_state.current_stage = current_stage_idx + 1
                st.rerun()


if __name__ == "__main__":
    main()

