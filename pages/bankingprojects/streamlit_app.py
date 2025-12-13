"""
Credit Scorecard Models
Provides web interface for the scorecard pipeline.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os
import sys
from pathlib import Path

# Add the directory containing this file to Python path for imports
# This ensures scorecard module can be found when loaded via importlib
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from scorecard.preprocessing import (
    prepare_training_data,
    prepare_scoring_data,
    prepare_cnn_data,
    apply_smote,
    clean_data
)
from scorecard.models import (
    train_model, 
    score_data, 
    calculate_scores
)
from scorecard.output import (
    summarize_scores,
    plot_score_distribution,
    create_summary_table,
    save_results,
    plot_confusion_matrix,
    print_classification_metrics,
    get_false_predictions,
    generate_decision_explanations,
    analyze_feature_impact
)

# Default data file paths - use absolute paths based on file location
DEFAULT_TRAINING_FILE = str(current_dir / "data" / "Application_Scorecard_Full_Table__25_Vars_.csv")
DEFAULT_NEW_APPLICANT_FILE = str(current_dir / "data" / "New_Applicant_Dataset__500_Records_.csv")

# Page configuration
st.set_page_config(
    page_title="Credit Scorecard Application",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'training_data' not in st.session_state:
    st.session_state.training_data = None
if 'new_applicant_data' not in st.session_state:
    st.session_state.new_applicant_data = None
if 'columns_to_exclude' not in st.session_state:
    st.session_state.columns_to_exclude = []
if 'target_column' not in st.session_state:
    st.session_state.target_column = None
if 'original_training_data' not in st.session_state:
    st.session_state.original_training_data = None
if 'original_new_applicant_data' not in st.session_state:
    st.session_state.original_new_applicant_data = None
if 'using_uploaded_training' not in st.session_state:
    st.session_state.using_uploaded_training = False
if 'using_uploaded_testing' not in st.session_state:
    st.session_state.using_uploaded_testing = False


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Credit Scorecard Application</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Data deletion notice
    st.warning("⚠️ **Notice:** If you choose to upload your own data, that data will be deleted when you exit this page or click the 'Delete Uploaded Data' button.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Data upload section
        st.subheader("📁 Upload Data Files")
        
        # Training data upload
        training_file = st.file_uploader(
            "Upload Training Data (CSV)",
            type=['csv'],
            help="Upload your training dataset in CSV format"
        )
        
        # Handle training file upload
        if training_file is not None:
            try:
                training_data = pd.read_csv(training_file)
                # Store original data
                st.session_state.original_training_data = training_data.copy()
                st.session_state.training_data = training_data
                st.session_state.using_uploaded_training = True  # Mark as uploaded
                # Reset target column if it's not in the new data
                if st.session_state.target_column not in training_data.columns:
                    st.session_state.target_column = None
                st.success(f"✅ {len(training_data)} records loaded")
            except Exception as e:
                st.error(f"Error loading training data: {e}")
        elif st.session_state.original_training_data is None:
            # Fallback to default file if no upload and no data in session
            if os.path.exists(DEFAULT_TRAINING_FILE):
                try:
                    training_data = pd.read_csv(DEFAULT_TRAINING_FILE)
                    st.session_state.original_training_data = training_data.copy()
                    st.session_state.training_data = training_data
                    st.session_state.using_uploaded_training = False  # Mark as default
                    
                    # Set default target column and excluded columns for default data
                    if st.session_state.target_column is None or st.session_state.target_column not in training_data.columns:
                        if 'delinq_12m' in training_data.columns:
                            st.session_state.target_column = 'delinq_12m'
                    
                    if not st.session_state.columns_to_exclude or len(st.session_state.columns_to_exclude) == 0:
                        default_exclude = []
                        if 'cust_id' in training_data.columns:
                            default_exclude.append('cust_id')
                        if 'application_date' in training_data.columns:
                            default_exclude.append('application_date')
                        if default_exclude:
                            st.session_state.columns_to_exclude = default_exclude
                    
                    st.info(f"📁 Using default training data: {DEFAULT_TRAINING_FILE} ({len(training_data)} records)")
                except Exception as e:
                    st.warning(f"Could not load default training file: {e}")
        
        # Testing/scoring data upload
        testing_file = st.file_uploader(
            "Upload Testing/Scoring Data (CSV)",
            type=['csv'],
            help="Upload your testing/scoring dataset in CSV format (optional)"
        )
        
        # Handle testing file upload
        if testing_file is not None:
            try:
                new_applicant_data = pd.read_csv(testing_file)
                # Store original data
                st.session_state.original_new_applicant_data = new_applicant_data.copy()
                st.session_state.new_applicant_data = new_applicant_data
                st.session_state.using_uploaded_testing = True  # Mark as uploaded
                st.success(f"✅ {len(new_applicant_data)} records loaded")
            except Exception as e:
                st.error(f"Error loading testing data: {e}")
        elif st.session_state.original_new_applicant_data is None:
            # Fallback to default file if no upload and no data in session
            if os.path.exists(DEFAULT_NEW_APPLICANT_FILE):
                try:
                    new_applicant_data = pd.read_csv(DEFAULT_NEW_APPLICANT_FILE)
                    st.session_state.original_new_applicant_data = new_applicant_data.copy()
                    st.session_state.new_applicant_data = new_applicant_data
                    st.session_state.using_uploaded_testing = False  # Mark as default
                    st.info(f"📁 Using default testing data: {DEFAULT_NEW_APPLICANT_FILE} ({len(new_applicant_data)} records)")
                except Exception as e:
                    st.warning(f"Could not load default testing file: {e}")
        
        st.markdown("---")
        
        # Column selection (only show if data is uploaded)
        if st.session_state.original_training_data is not None:
            st.subheader("🔧 Column Selection")
            
            # Get all columns from original training data (before exclusions)
            all_columns = st.session_state.original_training_data.columns.tolist()
            
            # Target column selection
            # Determine default index: prefer stored value, then 'delinq_12m' if using default data, else 0
            default_target_index = 0
            if st.session_state.target_column and st.session_state.target_column in all_columns:
                default_target_index = all_columns.index(st.session_state.target_column)
            elif not st.session_state.using_uploaded_training and 'delinq_12m' in all_columns:
                # Use 'delinq_12m' as default when using default data
                default_target_index = all_columns.index('delinq_12m')
                st.session_state.target_column = 'delinq_12m'
            
            target = st.selectbox(
                "Select Target Column",
                options=all_columns,
                index=default_target_index,
                help="Select the binary target variable column"
            )
            st.session_state.target_column = target
            
            # Columns to exclude
            # Determine default excluded columns: prefer stored value, then defaults if using default data
            default_excluded = st.session_state.columns_to_exclude if st.session_state.columns_to_exclude else []
            if not st.session_state.using_uploaded_training and not default_excluded:
                # Set defaults for default data: cust_id and application_date
                default_excluded = []
                if 'cust_id' in all_columns and 'cust_id' != target:
                    default_excluded.append('cust_id')
                if 'application_date' in all_columns and 'application_date' != target:
                    default_excluded.append('application_date')
                if default_excluded:
                    st.session_state.columns_to_exclude = default_excluded
                    default_excluded = st.session_state.columns_to_exclude
            
            columns_to_exclude = st.multiselect(
                "Select Columns to Exclude",
                options=[col for col in all_columns if col != target],
                default=default_excluded,
                help="Select columns to exclude from the model"
            )
            st.session_state.columns_to_exclude = columns_to_exclude
            
            st.markdown("---")
        
        # Model selection
        st.subheader("🤖 Model Selection")
        model_type = st.selectbox(
            "Select Model Type",
            ['logistic_regression', 'random_forest', 'gradient_boosting', 'decision_tree', 'cnn'],
            index=0,
            help="Choose the machine learning model"
        )
        
        # Model-specific parameters
        st.subheader("🔧 Model Parameters")
        
        if model_type == 'logistic_regression':
            max_iter = st.number_input("Max Iterations", min_value=100, max_value=10000, value=1000, step=100)
            model_params = {'max_iter': max_iter}
        
        elif model_type == 'random_forest':
            n_estimators = st.number_input("Number of Estimators", min_value=10, max_value=500, value=100, step=10)
            max_depth = st.number_input("Max Depth", min_value=1, max_value=50, value=10, step=1)
            model_params = {'n_estimators': n_estimators, 'max_depth': max_depth}
        
        elif model_type == 'gradient_boosting':
            n_estimators = st.number_input("Number of Estimators", min_value=10, max_value=500, value=100, step=10)
            learning_rate = st.number_input("Learning Rate", min_value=0.001, max_value=1.0, value=0.1, step=0.01)
            model_params = {'n_estimators': n_estimators, 'learning_rate': learning_rate}
        
        elif model_type == 'decision_tree':
            model_params = {}
        
        elif model_type == 'cnn':
            filters_1 = st.number_input("First Conv Filters", min_value=8, max_value=128, value=32, step=8)
            filters_2 = st.number_input("Second Conv Filters", min_value=8, max_value=128, value=64, step=8)
            dense_units = st.number_input("Dense Units", min_value=32, max_value=512, value=128, step=32)
            learning_rate = st.number_input("Learning Rate", min_value=0.0001, max_value=0.01, value=0.001, step=0.0001, format="%.4f")
            epochs = st.number_input("Epochs", min_value=1, max_value=100, value=20, step=1)
            batch_size = st.number_input("Batch Size", min_value=8, max_value=128, value=32, step=8)
            validation_split = st.number_input("Validation Split", min_value=0.1, max_value=0.5, value=0.2, step=0.1)
            model_params = {
                'filters_1': filters_1,
                'filters_2': filters_2,
                'dense_units': dense_units,
                'learning_rate': learning_rate,
                'epochs': epochs,
                'batch_size': batch_size,
                'validation_split': validation_split
            }
        
        st.markdown("---")
        
        # Data transformation options
        st.subheader("🔄 Data Transformation")
        use_woe = st.radio(
            "Data Transformation",
            ["Use WOE (Weight of Evidence)", "Use Raw Numeric Data"],
            index=0,
            help="Choose between WOE transformation or raw numeric data"
        )
        use_woe = use_woe == "Use WOE (Weight of Evidence)"
        
        # SMOTE options
        use_smote = st.checkbox("Apply SMOTE Oversampling", value=True, help="Balance the dataset using SMOTE")
        if use_smote:
            smote_k_neighbors = st.number_input("SMOTE K Neighbors", min_value=1, max_value=10, value=5, step=1)
        else:
            smote_k_neighbors = 5
        
        st.markdown("---")
        
        # Run button
        run_button = st.button("🚀 Run Scorecard Pipeline", type="primary", use_container_width=True)
        
        st.markdown("---")
        
        # Delete data button (only show if there's uploaded data)
        has_uploaded_data = st.session_state.using_uploaded_training or st.session_state.using_uploaded_testing
        if has_uploaded_data:
            delete_button = st.button("🗑️ Delete Uploaded Data", type="secondary", use_container_width=True)
        else:
            delete_button = False
    
    # Handle delete button
    if delete_button:
        # Only delete uploaded data, preserve default data
        if st.session_state.using_uploaded_training:
            st.session_state.training_data = None
            st.session_state.original_training_data = None
            st.session_state.using_uploaded_training = False
        
        if st.session_state.using_uploaded_testing:
            st.session_state.new_applicant_data = None
            st.session_state.original_new_applicant_data = None
            st.session_state.using_uploaded_testing = False
        
        # Clear results and selections
        st.session_state.results = None
        st.session_state.columns_to_exclude = []
        st.session_state.target_column = None
        
        # Reload default files if they exist
        if os.path.exists(DEFAULT_TRAINING_FILE) and not st.session_state.using_uploaded_training:
            try:
                training_data = pd.read_csv(DEFAULT_TRAINING_FILE)
                st.session_state.original_training_data = training_data.copy()
                st.session_state.training_data = training_data
                st.session_state.using_uploaded_training = False
            except Exception as e:
                st.warning(f"Could not reload default training file: {e}")
        
        if os.path.exists(DEFAULT_NEW_APPLICANT_FILE) and not st.session_state.using_uploaded_testing:
            try:
                new_applicant_data = pd.read_csv(DEFAULT_NEW_APPLICANT_FILE)
                st.session_state.original_new_applicant_data = new_applicant_data.copy()
                st.session_state.new_applicant_data = new_applicant_data
                st.session_state.using_uploaded_testing = False
            except Exception as e:
                st.warning(f"Could not reload default testing file: {e}")
        
        st.success("✅ All uploaded data and results have been deleted. Default data files are preserved.")
        st.rerun()
    
    # Apply column exclusions to data when columns_to_exclude changes
    if st.session_state.original_training_data is not None:
        # Apply exclusions
        training_data = st.session_state.original_training_data.drop(
            columns=st.session_state.columns_to_exclude, 
            errors='ignore'
        )
        st.session_state.training_data = training_data
        
        if st.session_state.original_new_applicant_data is not None:
            new_applicant_data = st.session_state.original_new_applicant_data.drop(
                columns=st.session_state.columns_to_exclude,
                errors='ignore'
            )
            st.session_state.new_applicant_data = new_applicant_data
    
    # Main content area
    if run_button:
        # Check if training data is available
        if st.session_state.training_data is None or len(st.session_state.training_data) == 0:
            st.error("❌ Please upload training data first.")
            return
        
        # Get target column
        if st.session_state.target_column is None:
            st.error("❌ Please select a target column.")
            return
        
        target = st.session_state.target_column
        
        # Verify target column exists in data
        if target not in st.session_state.training_data.columns:
            st.error(f"❌ Target column '{target}' not found in data. Please select a valid column.")
            return
        
        # Run pipeline
        try:
            with st.spinner("Running scorecard pipeline..."):
                results = run_scorecard_pipeline_streamlit(
                    training_data=st.session_state.training_data,
                    new_applicant_data=st.session_state.new_applicant_data,
                    target=target,
                    model_type=model_type,
                    model_params=model_params,
                    use_woe=use_woe,
                    use_smote=use_smote,
                    smote_k_neighbors=smote_k_neighbors
                )
                st.session_state.results = results
                st.success("✅ Pipeline completed successfully!")
        except Exception as e:
            st.error(f"Error running pipeline: {e}")
            st.exception(e)
    
    # Display results if available
    if st.session_state.results is not None:
        display_results(st.session_state.results)


def run_scorecard_pipeline_streamlit(
    training_data,
    new_applicant_data=None,
    vars_to_bin=None,
    target='default_12m',
    model_type='logistic',
    model_params=None,
    use_woe=True,
    use_smote=True,
    smote_k_neighbors=5
):
    """
    Run scorecard pipeline for Streamlit.
    
    Parameters:
    -----------
    training_data : DataFrame
        Training dataset
    new_applicant_data : DataFrame, optional
        New applicant dataset
    vars_to_bin : list, optional
        Variables to bin for WOE
    target : str
        Target variable name
    model_type : str
        Model type
    model_params : dict
        Model parameters
    use_woe : bool
        Whether to use WOE transformation
    use_smote : bool
        Whether to use SMOTE
    smote_k_neighbors : int
        SMOTE k neighbors
    
    Returns:
    --------
    dict : Results dictionary
    """
    # Validate target column exists
    if target not in training_data.columns:
        raise ValueError(f"Target column '{target}' not found in training data")
    
    # Validate and clean target to be binary (0 and 1 only)
    target_values = training_data[target].dropna().unique()
    non_binary_values = [v for v in target_values if v not in [0, 1]]
    if len(non_binary_values) > 0:
        # Filter to only binary values (0 and 1) and warn user
        st.warning(
            f"Target column '{target}' contains non-binary values: {non_binary_values}. "
            f"Filtering to only binary values (0 and 1) for WOE calculation."
        )
        training_data = training_data[training_data[target].isin([0, 1])].copy()
    if model_params is None:
        model_params = {}
    
    # Map 'logistic_regression' to 'logistic' for scorecard modules
    internal_model_type = 'logistic' if model_type == 'logistic_regression' else model_type
    
    # Auto-detect numeric columns for binning if vars_to_bin is None
    if vars_to_bin is None:
        leftmost_col = training_data.columns[0]
        numeric_cols = training_data.select_dtypes(include=[np.number]).columns.tolist()
        vars_to_bin = [col for col in numeric_cols if col != target and col != leftmost_col]
        if not vars_to_bin:
            vars_to_bin = ['monthly_income', 'bureau_score', 'residence_tenure']
    
    # Preprocess training data
    status_text = st.empty()
    
    status_text.text("Preprocessing training data...")
    
    # Verify target column exists in training data
    if target not in training_data.columns:
        available_cols = list(training_data.columns)
        raise ValueError(
            f"Target variable '{target}' not found in training data columns. "
            f"Available columns: {available_cols[:20]}{'...' if len(available_cols) > 20 else ''}"
        )
    
    if model_type == 'cnn':
        leftmost_col = training_data.columns[0]
        feature_columns = [
            col for col in training_data.select_dtypes(include=[np.number]).columns
            if col != target and col != leftmost_col
        ]
        
        # Ensure we have feature columns
        if len(feature_columns) == 0:
            raise ValueError(
                f"No feature columns available for CNN model. "
                f"Please ensure training data has numeric columns other than target '{target}'."
            )
        
        X_train_images, y_train = prepare_cnn_data(
            training_data,
            feature_columns=feature_columns,
            target=target,
            grid_size=28
        )
        df_woe_train = (X_train_images, y_train)
        woe_mappings = None
        cleaned_df = training_data
    else:
        cleaned_df = clean_data(training_data)
        
        if use_woe:
            cleaned_df, woe_mappings, df_woe_train = prepare_training_data(
                training_data, vars_to_bin, target
            )
            
            if use_smote:
                try:
                    df_woe_train = apply_smote(
                        df_woe_train, 
                        vars_to_bin, 
                        target=target,
                        k_neighbors=smote_k_neighbors
                    )
                except Exception as e:
                    st.warning(f"SMOTE not applied: {e}")
        else:
            woe_mappings = None
            leftmost_col = cleaned_df.columns[0]
            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [col for col in numeric_cols if col != target and col != leftmost_col]
            
            if vars_to_bin:
                feature_cols = [col for col in vars_to_bin if col in feature_cols]
            
            if not feature_cols:
                feature_cols = [col for col in numeric_cols if col != target and col != leftmost_col]
            
            df_woe_train = cleaned_df[feature_cols + [target]].copy()
            
            if use_smote:
                try:
                    from imblearn.over_sampling import SMOTE
                    X = df_woe_train[feature_cols].fillna(0).values
                    y = df_woe_train[target].values
                    smote = SMOTE(random_state=42, k_neighbors=smote_k_neighbors)
                    X_resampled, y_resampled = smote.fit_resample(X, y)
                    df_resampled = pd.DataFrame(X_resampled, columns=feature_cols)
                    df_resampled[target] = y_resampled
                    df_woe_train = df_resampled
                except Exception as e:
                    st.warning(f"SMOTE not applied: {e}")
    
    # Train model
    status_text.text("Training model...")
    
    try:
        if model_type == 'cnn':
            leftmost_col = training_data.columns[0]
            feature_columns = [
                col for col in training_data.select_dtypes(include=[np.number]).columns
                if col != target and col != leftmost_col
            ]
            model = train_model(
                df_woe_train,
                vars_to_bin=[],
                target=target,
                model_type=internal_model_type,
                feature_columns=feature_columns,
                **model_params
            )
        else:
            model = train_model(
                df_woe_train, 
                vars_to_bin, 
                target, 
                model_type=internal_model_type,
                use_woe=use_woe,
                **model_params
            )
    except Exception as e:
        st.error(f"Error training model: {e}")
        raise
    
    # Score training data
    status_text.text("Scoring training data...")
    
    if model_type == 'cnn':
        df_scored_train = score_data(
            cleaned_df, model, vars_to_bin=[], 
            feature_columns=feature_columns
        )
        # Ensure target column is preserved for CNN models
        # score_data should preserve all columns, but verify and add if missing
        if isinstance(df_scored_train, pd.DataFrame):
            if target not in df_scored_train.columns and target in cleaned_df.columns:
                # Ensure lengths match
                if len(df_scored_train) == len(cleaned_df):
                    df_scored_train[target] = cleaned_df[target].values
                else:
                    st.warning(f"Length mismatch: scored data ({len(df_scored_train)}) vs original ({len(cleaned_df)})")
    else:
        df_scored_train = score_data(
            df_woe_train, model, vars_to_bin, use_woe=use_woe
        )
    
    df_scored_train = calculate_scores(df_scored_train, prob_col='prob')
    
    # Generate decision explanations
    status_text.text("Generating decision explanations...")
    try:
        df_scored_train = generate_decision_explanations(
            df_scored_train, 
            model=model, 
            feature_columns=feature_columns if model_type == 'cnn' else None,
            prob_col='prob'
        )
    except Exception as e:
        st.warning(f"Could not generate decision explanations: {e}")
    
    # Create summary for training data
    status_text.text("Creating summaries...")
    
    training_summary = summarize_scores(df_scored_train, target_col=target)
    
    # Score new applicants if available
    new_applicant_scored = None
    new_applicant_summary = None
    
    if new_applicant_data is not None:
        status_text.text("Scoring new applicants...")
        
        if model_type == 'cnn':
            df_woe_new = new_applicant_data
        else:
            if use_woe:
                df_woe_new = prepare_scoring_data(
                    new_applicant_data, woe_mappings, vars_to_bin
                )
            else:
                df_woe_new = clean_data(new_applicant_data)
        
        if model_type == 'cnn':
            df_scored_new = score_data(
                new_applicant_data, model, vars_to_bin=[],
                feature_columns=feature_columns
            )
        else:
            df_scored_new = score_data(
                df_woe_new, model, vars_to_bin, use_woe=use_woe
            )
        
        prob_col_name = 'prob_default' if 'prob_default' in df_scored_new.columns else 'prob'
        new_applicant_scored = calculate_scores(
            df_scored_new, prob_col=prob_col_name
        )
        
        # Generate decision explanations for new applicants
        try:
            new_applicant_scored = generate_decision_explanations(
                new_applicant_scored, 
                model=model, 
                feature_columns=feature_columns if model_type == 'cnn' else None,
                prob_col=prob_col_name
            )
        except Exception as e:
            st.warning(f"Could not generate decision explanations for new applicants: {e}")
        
        new_applicant_summary = summarize_scores(new_applicant_scored, target_col=target if target in new_applicant_scored.columns else None)
    
    # Analyze feature impact
    feature_impact_results = None
    status_text.text("Analyzing feature impact...")
    try:
        # Prepare feature matrix and labels for analysis
        if model_type == 'cnn':
            # For CNN, use original feature DataFrame
            # Filter to only binary target values (0 and 1) for feature impact analysis
            binary_mask = cleaned_df[target].isin([0, 1])
            X_for_impact = cleaned_df.loc[binary_mask, feature_columns].copy()
            y_for_impact = cleaned_df.loc[binary_mask, target].values
            feature_names_for_impact = feature_columns
            
            # Warn if non-binary values were filtered out
            if not binary_mask.all():
                non_binary_count = (~binary_mask).sum()
                st.warning(
                    f"Filtered out {non_binary_count} rows with non-binary target values "
                    f"for feature impact analysis (CNN requires binary classification)."
                )
        else:
            # For other models, use WOE features if available
            if use_woe:
                # Get WOE variable names
                woe_vars = [f'{var}_woe' for var in vars_to_bin 
                           if f'{var}_woe' in df_woe_train.columns]
                if woe_vars:
                    X_for_impact = df_woe_train[woe_vars].copy()
                    feature_names_for_impact = woe_vars
                else:
                    # Fallback to original features
                    X_for_impact = cleaned_df[vars_to_bin].copy()
                    feature_names_for_impact = vars_to_bin
            else:
                # Use raw features
                if vars_to_bin:
                    X_for_impact = cleaned_df[vars_to_bin].copy()
                    feature_names_for_impact = vars_to_bin
                else:
                    # Use all numeric features
                    leftmost_col = cleaned_df.columns[0]
                    numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
                    feature_names_for_impact = [col for col in numeric_cols 
                                               if col != target and col != leftmost_col]
                    X_for_impact = cleaned_df[feature_names_for_impact].copy()
            
            # Filter to only binary target values (0 and 1) for feature impact analysis
            binary_mask = cleaned_df[target].isin([0, 1])
            X_for_impact = X_for_impact.loc[binary_mask].copy()
            y_for_impact = cleaned_df.loc[binary_mask, target].values
            
            # Warn if non-binary values were filtered out
            if not binary_mask.all():
                non_binary_count = (~binary_mask).sum()
                st.warning(
                    f"Filtered out {non_binary_count} rows with non-binary target values "
                    f"for feature impact analysis (requires binary classification)."
                )
        
        # Run feature impact analysis
        feature_impact_results = analyze_feature_impact(
            model=model,
            X=X_for_impact,
            y=y_for_impact,
            feature_names=feature_names_for_impact,
            method='auto',
            n_repeats=5,
            scoring='roc_auc',
            return_plot=True
        )
    except Exception as e:
        st.warning(f"Could not analyze feature impact: {e}")
        feature_impact_results = None
    
    status_text.text("Complete!")
    
    results = {
        'training_scored': df_scored_train,
        'new_applicant_scored': new_applicant_scored,
        'model': model,
        'woe_mappings': woe_mappings,
        'training_summary': training_summary,
        'new_applicant_summary': new_applicant_summary,
        'model_type': model_type,
        'vars_to_bin': vars_to_bin,
        'target': target,
        'feature_impact': feature_impact_results
    }
    
    return results


def display_results(results):
    """Display results in Streamlit."""
    
    st.markdown("---")
    st.header("📈 Results")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Training Data Summary", 
        "📋 New Applicants Summary",
        "📉 Visualizations",
        "🔍 Feature Impact Analysis",
        "💾 Download Results"
    ])
    
    with tab1:
        st.subheader("Training Data Summary")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Records",
                f"{results['training_summary']['total_applicants']:,}"
            )
        
        with col2:
            mean_score = results['training_summary']['score_stats']['mean']
            st.metric("Mean Score", f"{mean_score:.2f}")
        
        with col3:
            if 'performance' in results['training_summary']:
                default_rate = results['training_summary']['performance']['default_rate']
                st.metric("Default Rate", f"{default_rate:.2%}")
            else:
                st.metric("Default Rate", "N/A")
        
        with col4:
            if 'performance' in results['training_summary'] and 'auc' in results['training_summary']['performance']:
                auc = results['training_summary']['performance']['auc']
                st.metric("AUC-ROC", f"{auc:.4f}")
            else:
                st.metric("AUC-ROC", "N/A")
        
        # Score statistics
        st.subheader("Score Statistics")
        score_stats = results['training_summary']['score_stats']
        stats_df = pd.DataFrame({
            'Statistic': ['Mean', 'Median', 'Std Dev', 'Min', 'Max', 'Q25', 'Q75'],
            'Value': [
                score_stats['mean'],
                score_stats['median'],
                score_stats['std'],
                score_stats['min'],
                score_stats['max'],
                score_stats['q25'],
                score_stats['q75']
            ]
        })
        st.dataframe(stats_df, use_container_width=True)
        
        # Risk band distribution
        st.subheader("Risk Band Distribution")
        risk_dist = results['training_summary']['risk_band_distribution']
        risk_df = pd.DataFrame({
            'Risk Band': list(risk_dist.keys()),
            'Count': list(risk_dist.values())
        })
        risk_df['Percentage'] = (risk_df['Count'] / risk_df['Count'].sum() * 100).round(2)
        st.dataframe(risk_df, use_container_width=True)
        
        # Decision distribution
        st.subheader("Decision Distribution")
        decision_dist = results['training_summary']['decision_distribution']
        decision_df = pd.DataFrame({
            'Decision': list(decision_dist.keys()),
            'Count': list(decision_dist.values())
        })
        decision_df['Percentage'] = (decision_df['Count'] / decision_df['Count'].sum() * 100).round(2)
        st.dataframe(decision_df, use_container_width=True)
        
        # Classification metrics
        if 'performance' in results['training_summary']:
            st.subheader("Classification Metrics")
            perf = results['training_summary']['performance']
            
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                if 'accuracy' in perf:
                    st.metric("Accuracy", f"{perf['accuracy']:.4f}")
                if 'precision' in perf:
                    st.metric("Precision", f"{perf['precision']:.4f}")
                if 'sensitivity' in perf:
                    st.metric("Sensitivity (Recall)", f"{perf['sensitivity']:.4f}")
            
            with metrics_col2:
                if 'specificity' in perf:
                    st.metric("Specificity", f"{perf['specificity']:.4f}")
                if 'f1_score' in perf:
                    st.metric("F1-Score", f"{perf['f1_score']:.4f}")
                if 'auc' in perf:
                    st.metric("AUC-ROC", f"{perf['auc']:.4f}")
            
            # Confusion matrix
            if 'confusion_matrix' in perf:
                st.subheader("Confusion Matrix")
                cm = np.array(perf['confusion_matrix'])
                cm_df = pd.DataFrame(
                    cm,
                    index=['Actual: No Default', 'Actual: Default'],
                    columns=['Predicted: No Default', 'Predicted: Default']
                )
                st.dataframe(cm_df, use_container_width=True)
        
        # Summary table
        st.subheader("Summary by Risk Band")
        summary_table = create_summary_table(
            results['training_scored'], 
            target_col=results['target']
        )
        st.dataframe(summary_table, use_container_width=True)
        
        # Decision explanations if available
        if 'decision_explanation' in results['training_scored'].columns:
            st.subheader("Decision Explanations Sample")
            explanation_cols = ['score', 'risk_band', 'approve_decision', 'decision_explanation']
            available_expl_cols = [col for col in explanation_cols if col in results['training_scored'].columns]
            if available_expl_cols:
                st.dataframe(
                    results['training_scored'][available_expl_cols].head(20),
                    use_container_width=True
                )
    
    with tab2:
        if results['new_applicant_scored'] is not None:
            st.subheader("New Applicants Summary")
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Records",
                    f"{results['new_applicant_summary']['total_applicants']:,}"
                )
            
            with col2:
                mean_score = results['new_applicant_summary']['score_stats']['mean']
                st.metric("Mean Score", f"{mean_score:.2f}")
            
            with col3:
                min_score = results['new_applicant_summary']['score_stats']['min']
                max_score = results['new_applicant_summary']['score_stats']['max']
                st.metric("Score Range", f"{min_score:.0f} - {max_score:.0f}")
            
            # Risk band distribution
            st.subheader("Risk Band Distribution")
            risk_dist = results['new_applicant_summary']['risk_band_distribution']
            risk_df = pd.DataFrame({
                'Risk Band': list(risk_dist.keys()),
                'Count': list(risk_dist.values())
            })
            risk_df['Percentage'] = (risk_df['Count'] / risk_df['Count'].sum() * 100).round(2)
            st.dataframe(risk_df, use_container_width=True)
            
            # Decision distribution
            st.subheader("Decision Distribution")
            decision_dist = results['new_applicant_summary']['decision_distribution']
            decision_df = pd.DataFrame({
                'Decision': list(decision_dist.keys()),
                'Count': list(decision_dist.values())
            })
            decision_df['Percentage'] = (decision_df['Count'] / decision_df['Count'].sum() * 100).round(2)
            st.dataframe(decision_df, use_container_width=True)
            
            # Summary table
            st.subheader("Summary by Risk Band")
            summary_table = create_summary_table(results['new_applicant_scored'])
            st.dataframe(summary_table, use_container_width=True)
            
            # Display scored data
            st.subheader("Scored Data Preview")
            display_cols = ['score', 'risk_band', 'decision', 'prob', 'approve_decision', 'decision_explanation']
            available_cols = [col for col in display_cols if col in results['new_applicant_scored'].columns]
            st.dataframe(
                results['new_applicant_scored'][available_cols].head(100),
                use_container_width=True
            )
            
            # Display decision explanations if available
            if 'decision_explanation' in results['new_applicant_scored'].columns:
                st.subheader("Decision Explanations Sample")
                explanation_cols = ['score', 'risk_band', 'approve_decision', 'decision_explanation']
                available_expl_cols = [col for col in explanation_cols if col in results['new_applicant_scored'].columns]
                if available_expl_cols:
                    st.dataframe(
                        results['new_applicant_scored'][available_expl_cols].head(20),
                        use_container_width=True
                    )
        else:
            st.info("No new applicant data was provided. Upload new applicant data to see results here.")
    
    with tab3:
        st.subheader("Visualizations")
        
        # Training data visualizations
        st.subheader("Training Data Visualizations")
        try:
            fig = plot_score_distribution(
                results['training_scored'],
                target_col=results['target']
            )
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            st.error(f"Error creating training visualizations: {e}")
        
        # New applicant visualizations
        if results['new_applicant_scored'] is not None:
            st.subheader("New Applicants Visualizations")
            try:
                fig = plot_score_distribution(results['new_applicant_scored'])
                st.pyplot(fig)
                plt.close(fig)
            except Exception as e:
                st.error(f"Error creating new applicant visualizations: {e}")
            
            # Confusion matrix for new applicants if target available
            if results['target'] in results['new_applicant_scored'].columns:
                prob_col_name = 'prob' if 'prob' in results['new_applicant_scored'].columns else 'prob_default'
                if prob_col_name in results['new_applicant_scored'].columns:
                    try:
                        # Use approve_decision for CNN models
                        use_approve_decision = (
                            results['model_type'] == 'cnn' and
                            'approve_decision' in results['new_applicant_scored'].columns
                        )
                        
                        cm_fig = plot_confusion_matrix(
                            results['new_applicant_scored'],
                            results['target'],
                            prob_col_name=prob_col_name,
                            use_approve_decision=use_approve_decision
                        )
                        st.pyplot(cm_fig)
                        plt.close(cm_fig)
                        
                        # Display False Positives and False Negatives
                        st.subheader("Prediction Errors Analysis")
                        false_predictions = get_false_predictions(
                            results['new_applicant_scored'],
                            results['target'],
                            prob_col_name=prob_col_name,
                            use_approve_decision=use_approve_decision
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("False Positives", false_predictions['fp_count'])
                        with col2:
                            st.metric("False Negatives", false_predictions['fn_count'])
                        
                        # Display False Positives
                        if false_predictions['fp_count'] > 0:
                            st.subheader("False Positives (Predicted Default, Actual No Default)")
                            fp_df = false_predictions['false_positives']
                            # Select key columns for display
                            display_cols = ['score', 'prob', 'risk_band', 'decision', 'actual', 'predicted', 'probability']
                            available_cols = [col for col in display_cols if col in fp_df.columns]
                            if available_cols:
                                st.dataframe(fp_df[available_cols], use_container_width=True)
                            else:
                                st.dataframe(fp_df.head(100), use_container_width=True)
                            
                            # Download button for False Positives
                            fp_csv = fp_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download False Positives (CSV)",
                                data=fp_csv,
                                file_name="false_positives.csv",
                                mime="text/csv"
                            )
                        
                        # Display False Negatives
                        if false_predictions['fn_count'] > 0:
                            st.subheader("False Negatives (Predicted No Default, Actual Default)")
                            fn_df = false_predictions['false_negatives']
                            # Select key columns for display
                            display_cols = ['score', 'prob', 'risk_band', 'decision', 'actual', 'predicted', 'probability']
                            available_cols = [col for col in display_cols if col in fn_df.columns]
                            if available_cols:
                                st.dataframe(fn_df[available_cols], use_container_width=True)
                            else:
                                st.dataframe(fn_df.head(100), use_container_width=True)
                            
                            # Download button for False Negatives
                            fn_csv = fn_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download False Negatives (CSV)",
                                data=fn_csv,
                                file_name="false_negatives.csv",
                                mime="text/csv"
                            )
                    except Exception as e:
                        st.error(f"Error creating confusion matrix: {e}")
    
    with tab4:
        st.subheader("Feature Impact Analysis")
        
        if results['feature_impact'] is not None:
            impact_data = results['feature_impact']
            
            # Display method used
            st.info(f"**Method Used:** {impact_data['method_used']}")
            
            # Display feature impact table
            st.subheader("Feature Impact Scores")
            impact_df = impact_data['feature_impact']
            st.dataframe(impact_df, use_container_width=True)
            
            # Display plot if available
            if impact_data['plot'] is not None:
                st.subheader("Feature Impact Visualization")
                st.pyplot(impact_data['plot'])
                plt.close(impact_data['plot'])
            
            # Display top features
            st.subheader("Top 10 Most Impactful Features")
            top_features = impact_df.head(10)
            for idx, row in top_features.iterrows():
                st.write(f"**{idx+1}. {row['feature']}**: {row['impact_score']:.6f}")
            
            # Download feature impact results
            st.subheader("Download Feature Impact Results")
            impact_csv = impact_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Feature Impact Analysis (CSV)",
                data=impact_csv,
                file_name="feature_impact_analysis.csv",
                mime="text/csv"
            )
        else:
            st.info("Feature impact analysis was not performed or is not available.")
    
    with tab5:
        st.subheader("Download Results")
        
        # Download training results
        st.subheader("Training Data Results")
        training_csv = results['training_scored'].to_csv(index=False)
        st.download_button(
            label="📥 Download Training Scored Data (CSV)",
            data=training_csv,
            file_name="training_scored.csv",
            mime="text/csv"
        )
        
        # Download new applicant results
        if results['new_applicant_scored'] is not None:
            st.subheader("New Applicants Results")
            new_applicant_csv = results['new_applicant_scored'].to_csv(index=False)
            st.download_button(
                label="📥 Download New Applicants Scored Data (CSV)",
                data=new_applicant_csv,
                file_name="new_applicants_scored.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()

