"""
Logistic Regression Model Analysis
Builds and evaluates logistic regression models for credit risk prediction.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Optional

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from logreg_model_functions import (
    prepare_model_data,
    split_train_validation,
    train_stepwise_logistic,
    train_final_logistic,
    score_data,
    create_deciles,
    calculate_performance_summary,
    calculate_roc_stats,
    calculate_ks_statistic
)

# Page configuration
st.set_page_config(
    page_title="Logistic Regression Model Analysis",
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

# Initialize session state
if 'input_data' not in st.session_state:
    st.session_state.input_data = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'step_results' not in st.session_state:
    st.session_state.step_results = {}


def load_data_from_file():
    """Load data from CSV file."""
    # Primary input: model_ready_data.csv (from collinear_analysis.py)
    data_file = current_dir / "data" / "model_ready_data.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    
    # If not exists, return None (error will be shown in main function)
    return None


def display_step_info(step):
    """Display step information and code."""
    st.markdown(f'<div class="stage-header">{step["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Description:** {step['description']}")
    
    st.markdown("**Python Code:**")
    st.code(step['code'], language='python')


# Step definitions
STEPS = [
    {
        'number': 1,
        'name': 'Prepare Model Data',
        'description': 'Standardizes dpd_max, removes problematic variables, and adjusts dpd_max to avoid quasi-separation.',
        'code': '''
# Standardize dpd_max
scaler = StandardScaler()
df['dpd_max'] = scaler.fit_transform(df[['dpd_max']])

# Remove problematic variables
df = df.drop(columns=['emi_to_income_ratio', 'dpd_count_30_plus'])

# Adjust dpd_max to avoid quasi-separation
df['dpd_max_adj'] = df['dpd_max'] + (np.random.uniform(size=len(df)) * 0.01)
'''
    },
    {
        'number': 2,
        'name': 'Train/Validation Split',
        'description': 'Splits data into training (70%) and validation (30%) sets.',
        'code': '''
# Split into train and validation
train_df, valid_df = train_test_split(
    df, 
    test_size=0.3, 
    random_state=12345,
    stratify=df['default_flag']
)
'''
    },
    {
        'number': 3,
        'name': 'Train Stepwise Logistic Regression',
        'description': 'Trains logistic regression model with all available variables.',
        'code': '''
# Get all numeric features
feature_cols = [col for col in train_df.select_dtypes(include=[np.number]).columns 
               if col != 'default_flag']

# Train model
model = LogisticRegression(max_iter=1000, random_state=12345)
model.fit(X_train, y_train)
'''
    },
    {
        'number': 4,
        'name': 'Train Final Model with Forced Variables',
        'description': 'Trains final logistic regression model with specified business-critical variables.',
        'code': '''
# Force-keep critical variables
final_features = [
    'amount_income_term_score', 'annual_interest_rate',
    'pos_transaction_volume', 'recovery_success_flag',
    'dpd_max_adj', 'risk_score', 'overdue_normalized', 'dpd_recent_flag'
]

# Train final model
final_model = LogisticRegression(max_iter=1000, random_state=12345)
final_model.fit(X_train[final_features], y_train)
'''
    },
    {
        'number': 5,
        'name': 'Score Training and Validation Data',
        'description': 'Applies model to generate predictions for training and validation sets.',
        'code': '''
# Score training data
train_scored = score_data(train_df, model, feature_cols)

# Score validation data
valid_scored = score_data(valid_df, model, feature_cols)
'''
    },
    {
        'number': 6,
        'name': 'Create Deciles and Performance Summary',
        'description': 'Creates deciles based on predicted probabilities and calculates performance metrics by decile.',
        'code': '''
# Create deciles
train_deciles = create_deciles(train_scored)
valid_deciles = create_deciles(valid_scored)

# Calculate performance summary
train_perf = calculate_performance_summary(train_deciles)
valid_perf = calculate_performance_summary(valid_deciles)
'''
    },
    {
        'number': 7,
        'name': 'Calculate ROC Statistics',
        'description': 'Calculates ROC curve statistics including AUC (c-statistic).',
        'code': '''
# Calculate ROC stats
roc_train = calculate_roc_stats(train_scored)
roc_valid = calculate_roc_stats(valid_scored)
'''
    },
    {
        'number': 8,
        'name': 'Calculate KS Statistic',
        'description': 'Calculates Kolmogorov-Smirnov (KS) statistic to measure model discrimination.',
        'code': '''
# Calculate KS statistic
ks_train = calculate_ks_statistic(train_scored)
ks_valid = calculate_ks_statistic(valid_scored)
'''
    }
]


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
    
    st.markdown('<h1 class="main-header">Logistic Regression Model Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application builds and evaluates logistic regression models for credit risk prediction.
    
    **Instructions:**
    1. Default data (model_ready_data.csv) is loaded automatically
    2. Execute each step sequentially
    3. View model performance metrics and summaries
    4. Review ROC and KS statistics
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
            st.caption("Default: model_ready_data.csv")
        
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
        else:
            st.info("Please load data first")
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please ensure the following exists in the data folder:\n"
                 "- model_ready_data.csv (from Collinearity Analysis)")
        st.info("💡 **Tip:** Run the previous analysis steps to generate the required input file.")
        return
    
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
                if st.button(button_text, type="primary", disabled=False):
                    # Navigate to streamlit_app.py (Credit Scorecard Models)
                    st.query_params.update({"project": "streamlit_app.py", "scroll": "top"})
                    st.rerun()
            else:
                button_text = "Execute Step"
                if st.button(button_text, type="primary", disabled=execute_disabled):
                    with st.spinner(f"Executing {step['name']}..."):
                        try:
                            input_df = st.session_state.input_data.copy()
                            
                            # Step 1: Prepare Model Data
                            if step['number'] == 1:
                                df_prep = prepare_model_data(input_df)
                                result = {
                                    'prepared_df': df_prep,
                                    'rows': len(df_prep),
                                    'columns': len(df_prep.columns)
                                }
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"{step['name']} executed successfully!")
                                st.rerun()
                            
                            # Step 2: Train/Validation Split
                            elif step['number'] == 2:
                                if 0 not in st.session_state.step_results:
                                    st.error("Please execute Step 1 first.")
                                else:
                                    step1_result = st.session_state.step_results[0]
                                    df_prep = step1_result['prepared_df']
                                    train_df, valid_df = split_train_validation(df_prep)
                                    
                                    result = {
                                        'train_df': train_df,
                                        'valid_df': valid_df,
                                        'train_rows': len(train_df),
                                        'valid_rows': len(valid_df)
                                    }
                                    st.session_state.step_results[current_step_idx] = result
                                    st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                    st.success(f"{step['name']} executed successfully! Train: {len(train_df):,} rows, Valid: {len(valid_df):,} rows")
                                    st.rerun()
                            
                            # Step 3: Train Stepwise Logistic Regression
                            elif step['number'] == 3:
                                if 1 not in st.session_state.step_results:
                                    st.error("Please execute Step 2 first.")
                                else:
                                    step2_result = st.session_state.step_results[1]
                                    train_df = step2_result['train_df']
                                    stepwise_result = train_stepwise_logistic(train_df)
                                    
                                    result = {
                                        'stepwise_model': stepwise_result['model'],
                                        'feature_cols': stepwise_result['feature_cols'],
                                        'feature_importance': stepwise_result['feature_importance']
                                    }
                                    st.session_state.step_results[current_step_idx] = result
                                    st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                    st.success(f"{step['name']} executed successfully! {len(stepwise_result['feature_cols'])} features used")
                                    st.rerun()
                            
                            # Step 4: Train Final Model
                            elif step['number'] == 4:
                                if 1 not in st.session_state.step_results:
                                    st.error("Please execute Step 2 first.")
                                else:
                                    step2_result = st.session_state.step_results[1]
                                    if not isinstance(step2_result, dict) or 'train_df' not in step2_result:
                                        st.error("Step 2 result is missing 'train_df'. Please re-execute Step 2.")
                                    else:
                                        train_df = step2_result['train_df']
                                        
                                        # Force-keep critical variables (from SAS code)
                                        final_features = [
                                            'amount_income_term_score', 'annual_interest_rate',
                                            'pos_transaction_volume', 'recovery_success_flag',
                                            'dpd_max_adj', 'risk_score', 'overdue_normalized', 'dpd_recent_flag'
                                        ]
                                        
                                        # Filter to only existing columns
                                        available_features = [f for f in final_features if f in train_df.columns]
                                        
                                        final_result = train_final_logistic(train_df, available_features)
                                        
                                        result = {
                                            'final_model': final_result['model'],
                                            'feature_cols': final_result['feature_cols']
                                        }
                                        st.session_state.step_results[current_step_idx] = result
                                        st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                        st.success(f"{step['name']} executed successfully! {len(final_result['feature_cols'])} features used")
                                        st.rerun()
                            
                            # Step 5: Score Data
                            elif step['number'] == 5:
                                if 1 not in st.session_state.step_results:
                                    st.error("Please execute Step 2 first.")
                                elif 3 not in st.session_state.step_results:
                                    st.error("Please execute Step 4 first.")
                                else:
                                    step2_result = st.session_state.step_results[1]
                                    step4_result = st.session_state.step_results[3]
                                    if 'train_df' not in step2_result or 'valid_df' not in step2_result:
                                        st.error("Step 2 result is missing required data. Please re-execute Step 2.")
                                    else:
                                        train_df = step2_result['train_df']
                                        valid_df = step2_result['valid_df']
                                    final_model = step4_result['final_model']
                                    feature_cols = step4_result['feature_cols']
                                    
                                    train_scored = score_data(train_df, final_model, feature_cols)
                                    valid_scored = score_data(valid_df, final_model, feature_cols)
                                    
                                    result = {
                                        'train_scored': train_scored,
                                        'valid_scored': valid_scored
                                    }
                                    st.session_state.step_results[current_step_idx] = result
                                    st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                    st.success(f"{step['name']} executed successfully!")
                                    st.rerun()
                            
                            # Step 6: Create Deciles and Performance Summary
                            elif step['number'] == 6:
                                if 4 not in st.session_state.step_results:
                                    st.error("Please execute Step 5 first.")
                                else:
                                    step5_result = st.session_state.step_results[4]
                                    if 'train_scored' not in step5_result or 'valid_scored' not in step5_result:
                                        st.error("Step 5 result is missing required data. Please re-execute Step 5.")
                                    else:
                                        train_scored = step5_result['train_scored']
                                        valid_scored = step5_result['valid_scored']
                                        
                                        train_deciles = create_deciles(train_scored)
                                        valid_deciles = create_deciles(valid_scored)
                                        
                                        train_perf = calculate_performance_summary(train_deciles)
                                        valid_perf = calculate_performance_summary(valid_deciles)
                                        
                                        result = {
                                            'train_deciles': train_deciles,
                                            'valid_deciles': valid_deciles,
                                            'train_perf': train_perf,
                                            'valid_perf': valid_perf
                                        }
                                        st.session_state.step_results[current_step_idx] = result
                                        st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                        st.success(f"{step['name']} executed successfully!")
                                        st.rerun()
                            
                            # Step 7: Calculate ROC Statistics
                            elif step['number'] == 7:
                                if 4 not in st.session_state.step_results:
                                    st.error("Please execute Step 5 first.")
                                else:
                                    step5_result = st.session_state.step_results[4]
                                    if 'train_scored' not in step5_result or 'valid_scored' not in step5_result:
                                        st.error("Step 5 result is missing required data. Please re-execute Step 5.")
                                    else:
                                        train_scored = step5_result['train_scored']
                                        valid_scored = step5_result['valid_scored']
                                        
                                        roc_train = calculate_roc_stats(train_scored)
                                        roc_valid = calculate_roc_stats(valid_scored)
                                        
                                        result = {
                                            'roc_train': roc_train,
                                            'roc_valid': roc_valid
                                        }
                                        st.session_state.step_results[current_step_idx] = result
                                        st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                        st.success(f"{step['name']} executed successfully!")
                                        st.rerun()
                            
                            # Step 8: Calculate KS Statistic
                            elif step['number'] == 8:
                                if 4 not in st.session_state.step_results:
                                    st.error("Please execute Step 5 first.")
                                else:
                                    step5_result = st.session_state.step_results[4]
                                    if 'train_scored' not in step5_result or 'valid_scored' not in step5_result:
                                        st.error("Step 5 result is missing required data. Please re-execute Step 5.")
                                    else:
                                        train_scored = step5_result['train_scored']
                                        valid_scored = step5_result['valid_scored']
                                        
                                        ks_train = calculate_ks_statistic(train_scored)
                                        ks_valid = calculate_ks_statistic(valid_scored)
                                        
                                        result = {
                                            'ks_train': ks_train,
                                            'ks_valid': ks_valid
                                        }
                                        st.session_state.step_results[current_step_idx] = result
                                        st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                        st.success(f"{step['name']} executed successfully!")
                                        st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error executing step: {str(e)}")
                            st.exception(e)
        
        # Display results if step is completed
        if current_step_idx in st.session_state.step_results:
            result = st.session_state.step_results[current_step_idx]
            
            st.markdown("---")
            st.success(f"✅ {step['name']} completed successfully!")
            
            # Step-specific displays
            if step['number'] == 1:
                if isinstance(result, dict):
                    st.subheader("Prepared Data Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{result.get('rows', 0):,}")
                    with col2:
                        st.metric("Columns", f"{result.get('columns', 0)}")
            
            elif step['number'] == 2:
                if isinstance(result, dict):
                    st.subheader("Train/Validation Split Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Training Rows", f"{result.get('train_rows', 0):,}")
                    with col2:
                        st.metric("Validation Rows", f"{result.get('valid_rows', 0):,}")
            
            elif step['number'] == 3:
                if isinstance(result, dict):
                    feature_importance = result.get('feature_importance', pd.DataFrame())
                    st.subheader("Feature Importance (Top 20)")
                    if not feature_importance.empty:
                        st.dataframe(feature_importance.head(20), use_container_width=True)
            
            elif step['number'] == 4:
                if isinstance(result, dict):
                    feature_cols = result.get('feature_cols', [])
                    st.subheader("Final Model Features")
                    st.write(f"**{len(feature_cols)} features used:**")
                    st.dataframe(pd.DataFrame({'feature': feature_cols}), use_container_width=True)
            
            elif step['number'] == 6:
                if isinstance(result, dict):
                    train_perf = result.get('train_perf', pd.DataFrame())
                    valid_perf = result.get('valid_perf', pd.DataFrame())
                    
                    st.subheader("Training Performance Summary")
                    if not train_perf.empty:
                        st.dataframe(train_perf, use_container_width=True)
                    
                    st.subheader("Validation Performance Summary")
                    if not valid_perf.empty:
                        st.dataframe(valid_perf, use_container_width=True)
            
            elif step['number'] == 7:
                if isinstance(result, dict):
                    roc_train = result.get('roc_train', {})
                    roc_valid = result.get('roc_valid', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Training ROC Statistics")
                        st.metric("AUC (c-statistic)", f"{roc_train.get('auc', 0):.4f}")
                    with col2:
                        st.subheader("Validation ROC Statistics")
                        st.metric("AUC (c-statistic)", f"{roc_valid.get('auc', 0):.4f}")
            
            elif step['number'] == 8:
                if isinstance(result, dict):
                    ks_train = result.get('ks_train', {})
                    ks_valid = result.get('ks_valid', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Training KS Statistic")
                        st.metric("KS Statistic", f"{ks_train.get('ks_statistic', 0):.4f}")
                        st.metric("P-value", f"{ks_train.get('p_value', 0):.6f}")
                    with col2:
                        st.subheader("Validation KS Statistic")
                        st.metric("KS Statistic", f"{ks_valid.get('ks_statistic', 0):.4f}")
                        st.metric("P-value", f"{ks_valid.get('p_value', 0):.6f}")


if __name__ == "__main__":
    main()

