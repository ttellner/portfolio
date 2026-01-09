"""
Feature Engineering Analysis
Performs feature engineering including exclusions, feature creation, imputation, and outlier capping.
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

from feat_eng_functions import (
    step1_filter_by_dates,
    step1_apply_exclusions,
    step2_create_features,
    step3_calculate_impute_stats,
    step6_calculate_percentiles,
    step7_apply_imputation_and_capping
)

# Page configuration
st.set_page_config(
    page_title="Feature Engineering Analysis",
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
last_page = st.session_state.get("last_page_feat_eng", "")

if current_page == "feat_eng_analysis.py" and last_page != "feat_eng_analysis.py":
    # Coming to this page fresh - reset state
    if 'input_data' in st.session_state:
        del st.session_state.input_data
    if 'step_results' in st.session_state:
        del st.session_state.step_results
    if 'current_step' in st.session_state:
        del st.session_state.current_step

st.session_state.last_page_feat_eng = current_page

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
        'name': 'Filter by Date Range & Apply Exclusions',
        'description': 'Filters data by observation date range and applies exclusion rules (write-offs, invalid income, etc.).',
        'function': None,
        'code': '''
# Filter by date range
df_filtered = df[(df['snapshot_date'] >= obs_start) & 
                 (df['snapshot_date'] <= obs_end)]

# Apply exclusion rules
df = df[df['write_off_flag'] != 1]
df = df[df['monthly_income'] > 0]
df = df[df['application_date'] <= df['snapshot_date']]
df = df[df['tenure_months'] >= 3]
'''
    },
    {
        'number': 2,
        'name': 'Create Engineered Features',
        'description': 'Creates new features including DPD frequencies, flags, ratios, buckets, and derived metrics.',
        'function': step2_create_features,
        'code': '''
# DPD frequency counts
for col in dpd_cols:
    df.loc[(df[col] >= 1) & (df[col] <= 30), 'dpd_0to30_freq'] += 1
    df.loc[(df[col] >= 31) & (df[col] <= 60), 'dpd_31to60_freq'] += 1
    df.loc[df[col] >= 61, 'dpd_61plus_freq'] += 1

# Recent delinquency flag
df['dpd_recent_flag'] = (df[['dpd_m1', 'dpd_m2', 'dpd_m3']].max(axis=1) > 0).astype(int)

# Worsening DPD flag
df['dpd_worsening_flag'] = ((df['dpd_m1'] > df['dpd_m2']) & 
                             (df['dpd_m2'] > df['dpd_m3'])).astype(int)

# Average utilization
df['avg_util_3m'] = df[['util_m1', 'util_m2', 'util_m3']].mean(axis=1)

# EMI to income ratio
df['emi_to_income_ratio'] = df['total_emi'] / df['monthly_income']

# Loan tenure bucket
df['loan_tenure_bucket'] = pd.cut(df['loan_tenure'], 
                                  bins=[-np.inf, 12, 36, np.inf],
                                  labels=['Short', 'Medium', 'Long'])

# Age band
df['age_band'] = pd.cut(df['age'], 
                        bins=[-np.inf, 25, 35, 50, np.inf],
                        labels=['<25', '25-35', '36-50', '50+'])

# Salary credit flag
df['salary_credit_flag'] = (df[['salary_credit_m1', 'salary_credit_m2', 
                                 'salary_credit_m3']].sum(axis=1) > 0).astype(int)

# Bounce count
df['bounce_3m_count'] = df[['bounce_m1', 'bounce_m2', 'bounce_m3']].sum(axis=1)

# DPD to bureau ratio
df['dpd_to_bureau_ratio'] = max_dpd / (900 - df['bureau_score'])
'''
    },
    {
        'number': 3,
        'name': 'Calculate Imputation Statistics',
        'description': 'Calculates mean and median values for bureau_score, total_emi, and monthly_income for imputation.',
        'function': step3_calculate_impute_stats,
        'code': '''
# Calculate mean and median
stats = {}
vars_to_impute = ['bureau_score', 'total_emi', 'monthly_income']
for var in vars_to_impute:
    stats[f'{var}_mean'] = df[var].mean()
    stats[f'{var}_median'] = df[var].median()
'''
    },
    {
        'number': 4,
        'name': 'Calculate Percentiles for Capping',
        'description': 'Calculates 1st and 99th percentiles for bureau_score, total_emi, and monthly_income for outlier capping.',
        'function': step6_calculate_percentiles,
        'code': '''
# Calculate percentiles
percentiles = {}
vars_to_cap = ['bureau_score', 'total_emi', 'monthly_income']
for var in vars_to_cap:
    percentiles[f'{var}_p1'] = df[var].quantile(0.01)
    percentiles[f'{var}_p99'] = df[var].quantile(0.99)
'''
    },
    {
        'number': 5,
        'name': 'Apply Imputation and Outlier Capping',
        'description': 'Applies missing value imputation using medians and caps outliers using 1st and 99th percentiles.',
        'function': None,
        'code': '''
# Create missing flags
df['bureau_score_miss_flag'] = df['bureau_score'].isna().astype(int)
df['total_emi_miss_flag'] = df['total_emi'].isna().astype(int)
df['monthly_income_miss_flag'] = df['monthly_income'].isna().astype(int)

# Imputation using median
df['bureau_score'] = df['bureau_score'].fillna(bs_median)
df['total_emi'] = df['total_emi'].fillna(emi_median)
df['monthly_income'] = df['monthly_income'].fillna(inc_median)

# Outlier capping
df.loc[df['bureau_score'] < bs_p1, 'bureau_score'] = bs_p1
df.loc[df['bureau_score'] > bs_p99, 'bureau_score'] = bs_p99
df.loc[df['total_emi'] < emi_p1, 'total_emi'] = emi_p1
df.loc[df['total_emi'] > emi_p99, 'total_emi'] = emi_p99
df.loc[df['monthly_income'] < inc_p1, 'monthly_income'] = inc_p1
df.loc[df['monthly_income'] > inc_p99, 'monthly_income'] = inc_p99
'''
    }
]


def load_data_from_file():
    """Load data from CSV file."""
    data_file = current_dir / "data" / "feat_eng_data.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    else:
        st.error(f"Data file not found: {data_file}")
        return None


def display_step_info(step):
    """Display step information and code."""
    st.markdown(f'<div class="stage-header">Step {step["number"]}: {step["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Description:** {step['description']}")
    
    st.markdown("**Python Code:**")
    st.code(step['code'], language='python')


def main():
    """Main application."""
    # Scroll to top on page load if scroll parameter is present
    if st.query_params.get("scroll") == "top":
        st.components.v1.html("""
        <script>
            window.scrollTo(0, 0);
        </script>
        """, height=0)
    
    st.markdown('<h1 class="main-header">Feature Engineering Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application performs feature engineering including data filtering, exclusion rules, 
    feature creation, missing value imputation, and outlier capping.
    
    **Instructions:**
    1. Default data (feat_eng_data.csv) is loaded automatically
    2. Execute each step sequentially
    3. View the code and output for each step
    4. Review the final engineered dataset
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
            st.caption("Default: feat_eng_data.csv")
        
        st.markdown("---")
        
        if st.session_state.input_data is not None:
            st.header("Step Navigation")
            
            for i, step in enumerate(STEPS):
                status = "✅" if i < st.session_state.current_step else "⏳"
                if st.button(f"{status} Step {step['number']}: {step['name']}", 
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
            
            # Download button for output CSV (only show if Step 5 is completed)
            if 4 in st.session_state.step_results:
                st.markdown("---")
                st.header("Download Results")
                output_file = current_dir / "data" / "feat_eng_output.csv"
                if output_file.exists():
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="Download feat_eng_output.csv",
                            data=f.read(),
                            file_name="feat_eng_output.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        else:
            st.info("Please load data first")
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please check that feat_eng_data.csv exists in the data folder.")
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
    
    # Date range inputs for Step 1
    obs_start = pd.to_datetime('2022-01-01').date()
    obs_end = pd.to_datetime('2022-12-31').date()
    
    if step['number'] == 1:
        col1, col2 = st.columns(2)
        with col1:
            obs_start = st.date_input("Observation Start Date", value=obs_start)
        with col2:
            obs_end = st.date_input("Observation End Date", value=obs_end)
    
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
                with st.spinner(f"Executing Step {step['number']}..."):
                    try:
                        input_df = st.session_state.input_data.copy()
                        
                        # Step 1: Filter by dates and apply exclusions
                        if step['number'] == 1:
                            # Filter by dates
                            df_filtered = step1_filter_by_dates(
                                input_df,
                                obs_start=str(obs_start),
                                obs_end=str(obs_end)
                            )
                            
                            # Apply exclusions
                            df_result, excluded_count = step1_apply_exclusions(df_filtered)
                            
                            result = {
                                'filtered_data': df_result,
                                'excluded_count': excluded_count,
                                'initial_count': len(input_df),
                                'final_count': len(df_result)
                            }
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully! Excluded {excluded_count:,} records.")
                            st.rerun()
                        
                        # Step 2: Create features
                        elif step['number'] == 2:
                            if 0 not in st.session_state.step_results:
                            st.error("Please execute Step 1 first.")
                        else:
                            step1_result = st.session_state.step_results[0]
                            df_input = step1_result['filtered_data']
                            result = step2_create_features(df_input)
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            
                            # Count new features created
                            new_features = [col for col in result.columns if col not in df_input.columns]
                            st.success(f"Step {step['number']} executed successfully! Created {len(new_features)} new features.")
                            st.rerun()
                        
                        # Step 3: Calculate imputation statistics
                        elif step['number'] == 3:
                            if 1 not in st.session_state.step_results:
                            st.error("Please execute Step 2 first.")
                        else:
                            step2_result = st.session_state.step_results[1]
                            result = step3_calculate_impute_stats(step2_result)
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully!")
                            st.rerun()
                        
                        # Step 4: Calculate percentiles
                        elif step['number'] == 4:
                            if 1 not in st.session_state.step_results:
                            st.error("Please execute Step 2 first.")
                        else:
                            step2_result = st.session_state.step_results[1]
                            result = step6_calculate_percentiles(step2_result)
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully!")
                            st.rerun()
                        
                        # Step 5: Apply imputation and capping
                        elif step['number'] == 5:
                            if 1 not in st.session_state.step_results:
                            st.error("Please execute Step 2 first.")
                        elif 2 not in st.session_state.step_results:
                            st.error("Please execute Step 3 first.")
                        elif 3 not in st.session_state.step_results:
                            st.error("Please execute Step 4 first.")
                        else:
                            step2_result = st.session_state.step_results[1]
                            impute_stats = st.session_state.step_results[2]
                            percentiles = st.session_state.step_results[3]
                            
                            result = step7_apply_imputation_and_capping(
                                step2_result,
                                impute_stats,
                                percentiles
                            )
                            
                            # Ensure data directory exists
                            data_dir = current_dir / "data"
                            data_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Save output CSV file
                            output_file = data_dir / "feat_eng_output.csv"
                            result.to_csv(output_file, index=False)
                            
                            # Save as eda_data.csv for next step (permanent file, overwrites each run)
                            eda_file = data_dir / "eda_data.csv"
                            result.to_csv(eda_file, index=False)
                            
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully! Output saved to feat_eng_output.csv and eda_data.csv")
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
                st.subheader("Exclusion Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Initial Records", f"{result['initial_count']:,}")
                with col2:
                    st.metric("Excluded Records", f"{result['excluded_count']:,}")
                with col3:
                    st.metric("Final Records", f"{result['final_count']:,}")
                
                st.subheader("Filtered Data Preview (First 10 Rows)")
                st.dataframe(result['filtered_data'].head(10), use_container_width=True)
        
        # Step 2 special display
        elif step['number'] == 2:
            if isinstance(result, pd.DataFrame):
                st.subheader("Feature Engineering Summary")
                new_features = [col for col in result.columns 
                              if col not in st.session_state.step_results[0]['filtered_data'].columns]
                st.write(f"**New Features Created:** {len(new_features)}")
                st.write(f"**Feature Names:** {', '.join(new_features[:20])}" + 
                        (f" ... and {len(new_features) - 20} more" if len(new_features) > 20 else ""))
                
                st.subheader("Data Preview (First 10 Rows)")
                st.dataframe(result.head(10), use_container_width=True)
        
        # Step 3 special display
        elif step['number'] == 3:
            if isinstance(result, dict):
                st.subheader("Imputation Statistics")
                stats_df = pd.DataFrame({
                    'Variable': ['bureau_score', 'total_emi', 'monthly_income'],
                    'Mean': [result.get('bureau_score_mean', np.nan),
                            result.get('total_emi_mean', np.nan),
                            result.get('monthly_income_mean', np.nan)],
                    'Median': [result.get('bureau_score_median', np.nan),
                              result.get('total_emi_median', np.nan),
                              result.get('monthly_income_median', np.nan)]
                })
                st.dataframe(stats_df, use_container_width=True)
        
        # Step 4 special display
        elif step['number'] == 4:
            if isinstance(result, dict):
                st.subheader("Percentile Statistics for Capping")
                percentiles_df = pd.DataFrame({
                    'Variable': ['bureau_score', 'total_emi', 'monthly_income'],
                    '1st Percentile': [result.get('bureau_score_p1', np.nan),
                                      result.get('total_emi_p1', np.nan),
                                      result.get('monthly_income_p1', np.nan)],
                    '99th Percentile': [result.get('bureau_score_p99', np.nan),
                                       result.get('total_emi_p99', np.nan),
                                       result.get('monthly_income_p99', np.nan)]
                })
                st.dataframe(percentiles_df, use_container_width=True)
        
        # Step 5 special display
        elif step['number'] == 5:
            if isinstance(result, pd.DataFrame):
                st.subheader("Final Dataset Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows", f"{len(result):,}")
                with col2:
                    st.metric("Columns", f"{len(result.columns):,}")
                
                # Show missing flags summary
                miss_flag_cols = [col for col in result.columns if col.endswith('_miss_flag')]
                if miss_flag_cols:
                    st.subheader("Missing Value Flags Summary")
                    miss_summary = pd.DataFrame({
                        'Variable': [col.replace('_miss_flag', '') for col in miss_flag_cols],
                        'Missing Count': [result[col].sum() for col in miss_flag_cols]
                    })
                    st.dataframe(miss_summary, use_container_width=True)
                
                st.subheader("Final Data Preview (First 10 Rows)")
                st.dataframe(result.head(10), use_container_width=True)
        
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
        if 0 in st.session_state.step_results and 4 in st.session_state.step_results:
            step1_result = st.session_state.step_results[0]
            step5_result = st.session_state.step_results[4]
            
            initial_count = step1_result['initial_count']
            final_count = len(step5_result)
            excluded_count = step1_result['excluded_count']
            
            st.markdown("#### Overall Summary")
            overall_summary = pd.DataFrame({
                'Metric': ['Initial Records', 'Excluded Records', 'Final Records', 'Final Columns'],
                'Count': [initial_count, excluded_count, final_count, len(step5_result.columns)]
            })
            st.dataframe(overall_summary, use_container_width=True, hide_index=True)
        
        # Step-by-step summary
        st.markdown("---")
        st.markdown("#### Step-by-Step Summary")
        
        # Step 1 summary
        if 0 in st.session_state.step_results:
            step1_result = st.session_state.step_results[0]
            st.markdown("##### Step 1: Filter by Date Range & Apply Exclusions")
            summary_table = pd.DataFrame({
                'Metric': ['Initial Records', 'Excluded Records', 'Final Records'],
                'Count': [step1_result['initial_count'], 
                         step1_result['excluded_count'],
                         step1_result['final_count']]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 2 summary
        if 1 in st.session_state.step_results:
            step2_result = st.session_state.step_results[1]
            step1_result = st.session_state.step_results[0]
            new_features = [col for col in step2_result.columns 
                           if col not in step1_result['filtered_data'].columns]
            st.markdown("##### Step 2: Create Engineered Features")
            summary_table = pd.DataFrame({
                'Metric': ['New Features Created'],
                'Count': [len(new_features)],
                'Details': [', '.join(new_features[:30]) + 
                           (f" ... and {len(new_features) - 30} more" if len(new_features) > 30 else "")]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 3 summary
        if 2 in st.session_state.step_results:
            step3_result = st.session_state.step_results[2]
            st.markdown("##### Step 3: Calculate Imputation Statistics")
            summary_table = pd.DataFrame({
                'Variable': ['bureau_score', 'total_emi', 'monthly_income'],
                'Mean': [step3_result.get('bureau_score_mean', np.nan),
                        step3_result.get('total_emi_mean', np.nan),
                        step3_result.get('monthly_income_mean', np.nan)],
                'Median': [step3_result.get('bureau_score_median', np.nan),
                          step3_result.get('total_emi_median', np.nan),
                          step3_result.get('monthly_income_median', np.nan)]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 4 summary
        if 3 in st.session_state.step_results:
            step4_result = st.session_state.step_results[3]
            st.markdown("##### Step 4: Calculate Percentiles for Capping")
            summary_table = pd.DataFrame({
                'Variable': ['bureau_score', 'total_emi', 'monthly_income'],
                '1st Percentile': [step4_result.get('bureau_score_p1', np.nan),
                                 step4_result.get('total_emi_p1', np.nan),
                                 step4_result.get('monthly_income_p1', np.nan)],
                '99th Percentile': [step4_result.get('bureau_score_p99', np.nan),
                                  step4_result.get('total_emi_p99', np.nan),
                                  step4_result.get('monthly_income_p99', np.nan)]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 5 summary
        if 4 in st.session_state.step_results:
            step5_result = st.session_state.step_results[4]
            miss_flag_cols = [col for col in step5_result.columns if col.endswith('_miss_flag')]
            st.markdown("##### Step 5: Apply Imputation and Outlier Capping")
            summary_table = pd.DataFrame({
                'Metric': ['Final Rows', 'Final Columns', 'Missing Flags Created'],
                'Count': [len(step5_result), len(step5_result.columns), len(miss_flag_cols)]
            })
            st.dataframe(summary_table, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

