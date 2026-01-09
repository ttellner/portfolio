"""
Data Pipeline - Step-by-Step Execution
Interactive step-by-step execution of data transformation pipeline.
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

# Page configuration
st.set_page_config(
    page_title="Data Pipeline - Step by Step",
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

# Reset session state when navigating to this page (for new users)
# Track which page we were last on - if we're coming to this page fresh, reset
current_page = st.query_params.get("project", "")
last_page = st.session_state.get("last_page", "")

# If we're on this page but weren't here before, reset state
if current_page == "data_pipeline.py" and last_page != "data_pipeline.py":
    # Coming to this page fresh - reset all data pipeline state
    st.session_state.raw_data = None
    st.session_state.current_stage = 0
    st.session_state.stage_results = {}

# Update last page tracker
st.session_state.last_page = current_page

# Initialize session state (if not already set)
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 0
if 'stage_results' not in st.session_state:
    st.session_state.stage_results = {}

# Stage definitions with descriptions and code snippets
STAGES = [
    {
        'number': 1,
        'name': 'Bureau Derived Variables',
        'description': 'Creates bureau score flags, ratios, and risk bands from credit bureau data.',
        'function': stage1_bureau_vars,
        'code': '''
# Core Bureau Derived Variables
df['bureau_score_flag'] = (df['bureau_score'] < 650).astype(int)
df['overdue_to_total_ratio'] = df['overdue_accounts'] / df['total_accounts']
df['active_account_ratio'] = df['active_accounts'] / df['total_accounts']
df['enquiries_flag'] = (df['recent_enquiries_6m'] >= 3).astype(int)

# Risk score band
df['risk_score_band'] = pd.cut(
    df['bureau_score'],
    bins=[-np.inf, 600, 650, 700, 750, np.inf],
    labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
).astype(str)

# Additional derived variables...
'''
    },
    {
        'number': 2,
        'name': 'CBS Derived Variables',
        'description': 'Creates CBS-related derived variables including EMI ratios and balance flags.',
        'function': stage2_cbs_vars,
        'code': '''
# Add missing base variables
df['average_balance'] = 60000
df['minimum_balance'] = 8000
df['salary_credits_3m'] = 3
df['emi_bounce_count'] = 0
df['account_tenure_months'] = 24

# Core CBS Derived Variables
df['emi_to_income_ratio'] = df['emi_amount'] / df['monthly_income']
df['avg_balance_flag'] = (df['average_balance'] < 5000).astype(int)
df['min_balance_ratio'] = df['minimum_balance'] / df['average_balance']
# Additional derived variables...
'''
    },
    {
        'number': 3,
        'name': 'DPD Derived Variables',
        'description': 'Creates Days Past Due (DPD) related variables including counts, flags, and trends.',
        'function': stage3_dpd_vars,
        'code': '''
# Add dummy DPD values
df['dpd_m1'] = 0
df['dpd_m2'] = 30
df['dpd_m3'] = 0
df['dpd_m4'] = 60
df['dpd_m5'] = 0
df['dpd_m6'] = 90

# Core DPD Derived Variables
dpd_cols = ['dpd_m1', 'dpd_m2', 'dpd_m3', 'dpd_m4', 'dpd_m5', 'dpd_m6']
df['dpd_max_days'] = df[dpd_cols].max(axis=1)
df['dpd_avg'] = df[dpd_cols].mean(axis=1)
df['dpd_count_30_plus'] = (df[dpd_cols] >= 30).sum(axis=1)
# Additional derived variables...
'''
    },
    {
        'number': 4,
        'name': 'Collection & Recovery Variables',
        'description': 'Creates collection and recovery related flags and ratios.',
        'function': stage4_collection_vars,
        'code': '''
# Collection & Recovery Derived Variables
df['write_off_case_flag'] = (df['write_off_flag'] == 1).astype(int)
df['legal_action_taken_flag'] = (df['legal_case_flag'] == 1).astype(int)
df['broken_ptp_flag'] = (df['broken_ptp_flag'] == 1).astype(int)
df['ptp_honored_ratio'] = df['ptp_kept_ratio']
df['recovery_effectiveness_score'] = df['repayment_to_due_ratio']
'''
    },
    {
        'number': 5,
        'name': 'Disbursal Timing & Channel Analysis',
        'description': 'Creates disbursal timing, channel analysis, and tenure analytics.',
        'function': stage5_disburse_vars,
        'code': '''
# Disbursal timing
df['disbursal_gap_days'] = (df['account_open_date'] - df['application_date']).dt.days
df['disbursal_gap_category'] = df['disbursal_gap_days'].apply(
    lambda x: 'Fast' if x <= 3 else ('Moderate' if x <= 7 else 'Slow')
)

# Channel analysis
df['digital_channel_flag'] = df['channel'].isin(['Online', 'Mobile']).astype(int)
df['channel_code'] = df['channel'].apply(
    lambda x: '1' if x == 'Online' else ('2' if x == 'Mobile' else ('3' if x == 'Branch' else '0'))
)

# Tenure analytics
df['long_tenure_flag'] = (df['tenure_months'] > 60).astype(int)
df['tenure_category'] = df['tenure_months'].apply(
    lambda x: 'Short' if x <= 12 else ('Medium' if x <= 36 else 'Long')
)
'''
    },
    {
        'number': 6,
        'name': 'Credit Utilization Features',
        'description': 'Creates credit utilization and credit limit related features.',
        'function': stage6_txn_vars,
        'code': '''
# Credit Utilization Features
df['high_utilization_flag'] = (df['credit_card_utilization_pct'] >= 80).astype(int)
df['low_utilization_flag'] = (df['credit_card_utilization_pct'] <= 20).astype(int)
df['utilization_bucket'] = (df['credit_card_utilization_pct'] // 10).astype(int)

# Credit Limit Grouping
df['high_credit_limit_flag'] = (df['credit_limit'] >= 200000).astype(int)
df['credit_segment'] = df['credit_limit'].apply(
    lambda x: 'Low' if x < 25000 else ('Mid' if x < 100000 else 'High')
)
'''
    },
    {
        'number': 7,
        'name': 'Loan Size & Application Timeliness',
        'description': 'Creates loan size features, tenure features, and application timeliness flags.',
        'function': stage7_txn_vars,
        'code': '''
# Loan Size & Tenure Features
df['loan_size_flag'] = (df['requested_amount'] > 200000).astype(int)
df['loan_size_score'] = df['requested_amount'] / df['monthly_income']
df['short_term_flag'] = (df['tenure_months'] <= 12).astype(int)
df['loan_burden_ratio'] = (df['requested_amount'] / df['tenure_months']) / df['monthly_income']

# Application Timeliness
df['application_month'] = df['application_date'].dt.month
df['festive_season_flag'] = df['application_month'].isin([10, 11, 12]).astype(int)
df['financial_year_start_flag'] = df['application_month'].isin([4, 5]).astype(int)
'''
    },
    {
        'number': 8,
        'name': 'Repayment Performance & Recovery',
        'description': 'Creates repayment performance flags, recovery effectiveness, and PTP behavior indicators.',
        'function': stage8_txn_vars,
        'code': '''
# Repayment Performance Flags
df['clean_repayment_flag'] = (df['dpd_30_flag'] == 0).astype(int)
df['ever_60_plus_flag'] = (df['dpd_60_flag'] == 1).astype(int)
df['ever_90_plus_flag'] = (df['dpd_90_flag'] == 1).astype(int)

# Recovery Effectiveness
df['recovery_ratio_flag'] = (df['repayment_to_due_ratio'] >= 0.8).astype(int)
df['recovery_gap_score'] = 1 - df['repayment_to_due_ratio']
df['recovery_success_flag'] = ((df['write_off_flag'] == 0) & (df['repayment_to_due_ratio'] >= 0.8)).astype(int)

# PTP Commitment Behavior
df['ptp_compliance_flag'] = (df['ptp_kept_ratio'] >= 0.7).astype(int)
'''
    },
    {
        'number': 9,
        'name': 'Behavior Score Interactions',
        'description': 'Creates behavior score interactions, risk banding, and external flags.',
        'function': stage9_txn_vars,
        'code': '''
# Simulated Variables
df['internal_behavior_score'] = 650 + np.random.normal(0, 50, len(df))
df['risk_band_code'] = 'M'
df['behavior_stability_index'] = 75 + np.random.normal(0, 10, len(df))

# Bureau Score Buckets & Flags
df['low_bureau_score_flag'] = (df['bureau_score'] < 600).astype(int)
df['high_bureau_score_flag'] = (df['bureau_score'] >= 750).astype(int)

# Behavior Score Interactions
df['behavior_score_gap'] = df['bureau_score'] - df['internal_behavior_score']
df['behavior_agreement_flag'] = (df['behavior_score_gap'].abs() < 50).astype(int)
df['avg_combined_score'] = (df['bureau_score'] + df['internal_behavior_score']) / 2
'''
    },
    {
        'number': 10,
        'name': 'Risk Ratios & Consolidated Scores',
        'description': 'Creates final risk ratios, alert flags, and consolidated risk profile scores.',
        'function': stage10_txn_vars,
        'code': '''
# Risk Ratios
df['score_utilization_ratio'] = df['bureau_score'] / (1 + df['credit_card_utilization_pct'])
df['limit_to_income_ratio'] = df['credit_limit'] / (1 + df['monthly_income'])
df['emi_to_income_ratio'] = df['total_emi_amount'] / (1 + df['monthly_income'])

# Alert Flags
df['multiple_risk_flags'] = (
    df['high_utilization_flag'] + 
    df['low_bureau_score_flag'] + 
    df['high_behavioral_risk_flag'] + 
    df['dual_low_score_flag']
)
df['high_risk_alert'] = (df['multiple_risk_flags'] >= 3).astype(int)

# Final Risk Profile
df['risk_profile_score'] = (df['avg_combined_score'] + df['behavior_stability_index']) / 2
df['risk_band_final'] = df['risk_profile_score'].apply(
    lambda x: 'Low' if x >= 750 else ('Medium' if x >= 600 else 'High')
)
'''
    },
    {
        'number': 11,
        'name': 'Final Derived Variables & Default Flag',
        'description': 'Generates final derived variables and creates the default flag for modeling population.',
        'function': stage11_final_vars,
        'code': '''
# Stage 11.1 – Additional Derived Variables
dpd_cols_12 = [f'dpd_m{i}' for i in range(1, 13)]
df['dpd_max_days'] = df[dpd_cols_12].max(axis=1)
df['dpd_avg'] = df[dpd_cols_12].mean(axis=1)
df['dpd_count_30_plus'] = (df[dpd_cols_12] >= 30).sum(axis=1)

# Behavioural Score
df['behavioural_score'] = (df['bureau_score'] * 0.7) + ((100 - df['dpd_avg']) * 0.3)

# Stage 11.2 – Generate Default Flag
perf_dpd_cols = [f'dpd_f{i}' for i in range(1, 7)]
df['valid_obs'] = df[obs_dpd_cols].notna().all(axis=1).astype(int)
df['valid_perf'] = df[perf_dpd_cols].notna().all(axis=1).astype(int)

df['default_flag'] = np.where(
    (df['valid_obs'] == 1) & (df['valid_perf'] == 1),
    np.where(df[perf_dpd_cols].max(axis=1) >= 90, 1, 0),
    np.nan
)
df['modeling_population'] = ((df['valid_obs'] == 1) & (df['valid_perf'] == 1)).astype(int)

# Keep only valid modeling population
df_final = df[df['modeling_population'] == 1].copy()
'''
    }
]

def load_raw_data():
    """Load the raw data file."""
    data_file = current_dir / "data" / "PD_RAW_VARIABLES.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    else:
        st.error(f"Data file not found: {data_file}")
        return None

def display_stage_info(stage):
    """Display stage information and code."""
    st.markdown(f'<div class="stage-header">Stage {stage["number"]}: {stage["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Description:** {stage['description']}")
    
    st.markdown("**Python Code:**")
    st.code(stage['code'], language='python')

def display_dataframe_summary(df, stage_num):
    """Display a summary of the dataframe after each stage."""
    st.markdown("**Data Summary:**")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", f"{len(df.columns):,}")
    with col3:
        new_cols = len(df.columns) - (len(st.session_state.raw_data.columns) if st.session_state.raw_data is not None else 0)
        st.metric("New Columns", f"+{new_cols}")
    with col4:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    st.markdown("**New Columns Created in This Stage:**")
    if stage_num == 1:
        new_cols = df.columns.tolist()
    else:
        prev_cols = set(st.session_state.stage_results[stage_num - 1].columns)
        new_cols = [col for col in df.columns if col not in prev_cols]
    
    if new_cols:
        st.write(f"Total new columns: {len(new_cols)}")
        # Show first 20 new columns
        display_cols = new_cols[:20]
        st.write(", ".join(display_cols))
        if len(new_cols) > 20:
            st.write(f"... and {len(new_cols) - 20} more columns")
    else:
        st.write("No new columns created in this stage.")

def main():
    """Main application."""
    # Scroll to top on page load if scroll parameter is present
    if st.query_params.get("scroll") == "top":
        st.components.v1.html("""
        <script>
            window.scrollTo(0, 0);
        </script>
        """, height=0)
    
    st.markdown('<h1 class="main-header">Data Pipeline - Step by Step Execution</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application allows you to execute each stage of an example data pipeline 
    step-by-step, viewing the code and output at each stage. Due to storage and compute constraints,
    the "database" is a csv file with 37 primary features that are used to derive ~ 231 new features.
    Data has been created by Sameer Shaikh for his book, "SAS Credit Risk Modelling - A to Z for PD Models".
    
    Note: The data has already been split into training and testing data. All stages demonstrated in the pipeline are applied to the only training data.
    The testing data also file will be used later and all applicable engineering will have already been applied to it to align it with the training data.
    
    **Instructions:**
    1. Load the raw data file (PD_RAW_VARIABLES.csv). This data is from the "Observation period", aka the training data. 
    2. Execute each stage sequentially
    3. View the code and output for each stage
    4. Track the creation of derived variables and dummy variables
    """)
    
    st.markdown("---")
    
    # Sidebar for data loading and navigation
    with st.sidebar:
        st.header("Data Loading")
        
        if st.button("Load Raw Data", type="primary"):
            with st.spinner("Loading data..."):
                data = load_raw_data()
                if data is not None:
                    st.session_state.raw_data = data
                    st.session_state.current_stage = 0
                    st.session_state.stage_results = {}
                    st.success(f"Loaded {len(data):,} rows and {len(data.columns)} columns")
                    st.rerun()
        
        if st.session_state.raw_data is not None:
            st.success(f"Data loaded: {len(st.session_state.raw_data):,} rows")
            st.markdown("---")
            st.header("Stage Navigation")
            
            for i, stage in enumerate(STAGES):
                status = "✅" if i < st.session_state.current_stage else "⏳"
                if st.button(f"{status} Stage {stage['number']}: {stage['name']}", 
                            key=f"nav_{i}",
                            disabled=(i > st.session_state.current_stage)):
                    st.session_state.current_stage = i
                    st.rerun()
            
            st.markdown("---")
            if st.button("Reset All Stages"):
                st.session_state.current_stage = 0
                st.session_state.stage_results = {}
                st.rerun()
        else:
            st.info("Please load the raw data first")
    
    # Main content area
    if st.session_state.raw_data is None:
        st.warning("Please load the raw data file using the button in the sidebar.")
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
        is_final_stage = current_stage_idx == len(STAGES) - 1
        all_stages_completed = len(st.session_state.stage_results) == len(STAGES)
        execute_disabled = current_stage_idx in st.session_state.stage_results
        
        # Change button text for final stage when all stages are completed
        if is_final_stage and all_stages_completed:
            if st.button("Proceed to next Analysis", type="primary", disabled=False):
                # Navigate to var_metadata_analysis.py with scroll parameter
                st.query_params.update({"project": "var_metadata_analysis.py", "scroll": "top"})
                st.rerun()
        else:
            if st.button("▶️ Execute Stage", type="primary", disabled=execute_disabled):
                with st.spinner(f"Executing Stage {stage['number']}..."):
                    try:
                        # Get input data
                        if current_stage_idx == 0:
                            input_df = st.session_state.raw_data.copy()
                        else:
                            input_df = st.session_state.stage_results[current_stage_idx - 1].copy()
                        
                        # Execute stage function
                        result_df = stage['function'](input_df)
                        
                        # Store result
                        st.session_state.stage_results[current_stage_idx] = result_df
                        
                        # Save output to var_metadata_input.csv if final stage
                        if is_final_stage:
                            data_dir = current_dir / "data"
                            data_dir.mkdir(parents=True, exist_ok=True)
                            output_file = data_dir / "var_metadata_input.csv"
                            result_df.to_csv(output_file, index=False)
                        
                        st.session_state.current_stage = min(current_stage_idx + 1, len(STAGES) - 1)
                        
                        if is_final_stage:
                            st.success(f"Stage {stage['number']} executed successfully! Output saved to var_metadata_input.csv")
                        else:
                            st.success(f"Stage {stage['number']} executed successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error executing stage: {str(e)}")
                        st.exception(e)
    
    # Display results if stage has been executed
    if current_stage_idx in st.session_state.stage_results:
        result_df = st.session_state.stage_results[current_stage_idx]
        
        # Data summary
        display_dataframe_summary(result_df, stage['number'])
        
        st.markdown("---")
        
        # Data preview
        st.markdown("**Data Preview (First 10 Rows):**")
        st.dataframe(result_df.head(10), use_container_width=True)
        
        st.markdown("---")
        
        # Column information
        st.markdown("**All Columns:**")
        col_info = pd.DataFrame({
            'Column': result_df.columns,
            'Data Type': [str(dtype) for dtype in result_df.dtypes],
            'Non-Null Count': result_df.count().values,
            'Null Count': result_df.isnull().sum().values
        })
        st.dataframe(col_info, use_container_width=True, height=400)
        
        # Download button
        st.markdown("---")
        csv = result_df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download Stage {stage['number']} Results (CSV)",
            data=csv,
            file_name=f"stage_{stage['number']}_results.csv",
            mime="text/csv"
        )
    else:
        st.info("👆 Click 'Execute Stage' to run this stage and view the results.")
    
    # Progress indicator
    st.markdown("---")
    st.markdown("### 📈 Pipeline Progress")
    completed = len(st.session_state.stage_results)
    total = len(STAGES)
    progress = completed / total
    st.progress(progress)
    st.caption(f"Completed: {completed} / {total} stages ({progress*100:.1f}%)")
    
    # Network Graph Section
    st.markdown("---")
    st.markdown("### Primary Variable Network Graph")
    st.markdown("View the network graph showing relationships between primary variables. You can zoom in and click on nodes to highlight relationships.")
    
    # Initialize session state for network graph visibility
    if 'show_network_graph' not in st.session_state:
        st.session_state.show_network_graph = False
    
    # Button to show network graph
    if st.button("View Primary Variable Network", type="secondary"):
        st.session_state.show_network_graph = True
    
    # Display network graph if button was clicked
    if st.session_state.show_network_graph:
        network_file = current_dir / "files" / "network_graph_primary.html"
        if network_file.exists():
            try:
                with open(network_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # Render the HTML using Streamlit components
                st.components.v1.html(html_content, height=800)
            except Exception as e:
                st.error(f"Error loading network graph: {e}")
        else:
            st.error(f"Network graph file not found: {network_file}")

if __name__ == "__main__":
    main()

