"""
Variable Metadata Analysis
Analyzes variable metadata, missing values, duplicates, and data quality.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from var_meta_functions import (
    step1_extract_metadata,
    step2_transpose_missing,
    step3_calculate_pct_missing,
    step4_high_missing_vars,
    step4_categorical_frequencies,
    step5_descriptive_stats,
    step6_invalid_categories,
    step7_duplicate_columns,
    step7_get_duplicate_list,
    step8_drop_duplicates,
    step9_orphan_records
)

# Page configuration
st.set_page_config(
    page_title="Variable Metadata Analysis",
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
last_page = st.session_state.get("last_page_var_meta", "")

if current_page == "var_metadata_analysis.py" and last_page != "var_metadata_analysis.py":
    # Coming to this page fresh - reset state
    if 'input_data' in st.session_state:
        del st.session_state.input_data
    if 'step_results' in st.session_state:
        del st.session_state.step_results
    if 'current_step' in st.session_state:
        del st.session_state.current_step

st.session_state.last_page_var_meta = current_page

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
        'name': 'Extract Variable Metadata',
        'description': 'Extracts metadata for all numeric variables, calculating count and missing count.',
        'function': step1_extract_metadata,
        'code': '''
# Extract metadata for numeric variables
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

summary_data = {
    'Variable': numeric_cols,
    'N': [df[col].count() for col in numeric_cols],
    'NMiss': [df[col].isnull().sum() for col in numeric_cols]
}
result = pd.DataFrame(summary_data)
'''
    },
    {
        'number': 2,
        'name': 'Transpose Missing Summary',
        'description': 'Transposes the metadata to have variables as rows.',
        'function': step2_transpose_missing,
        'code': '''
# Transpose missing summary
result = df_metadata.rename(columns={'NMiss': 'COL1'})
result = result[['Variable', 'COL1']].copy()
'''
    },
    {
        'number': 3,
        'name': 'Calculate % Missing',
        'description': 'Calculates percentage of missing values for each variable.',
        'function': step3_calculate_pct_missing,
        'code': '''
# Calculate percentage missing
result['Pct_Missing'] = (result['COL1'] / total_n * 100).round(2)
result = result[['Variable', 'Pct_Missing']].copy()
'''
    },
    {
        'number': 4,
        'name': 'High Missing Variables & Categorical Frequencies',
        'description': 'Identifies variables with >30% missing values and generates frequency distributions for categorical variables.',
        'function': None,  # Special handling needed
        'code': '''
# High missing variables
high_missing = df_pct_missing[df_pct_missing['Pct_Missing'] > 30].copy()

# Categorical frequencies
cat_vars = ['gender', 'marital_status', 'residence_type']
freq_tables = {}
for var in cat_vars:
    freq_df = df[var].value_counts(dropna=False).reset_index()
    freq_tables[var] = freq_df
'''
    },
    {
        'number': 5,
        'name': 'Descriptive Statistics & Range Checks',
        'description': 'Calculates descriptive statistics (n, mean, std, min, max) for selected risk variables.',
        'function': step5_descriptive_stats,
        'code': '''
# Descriptive statistics
vars_list = ['bureau_score', 'emi_to_income_ratio', 'monthly_income']
stats_data = {
    'Variable': vars_list,
    'N': [df[var].count() for var in vars_list],
    'Mean': [df[var].mean() for var in vars_list],
    'Std': [df[var].std() for var in vars_list],
    'Min': [df[var].min() for var in vars_list],
    'Max': [df[var].max() for var in vars_list]
}
result = pd.DataFrame(stats_data)
'''
    },
    {
        'number': 6,
        'name': 'Invalid Categories Check',
        'description': 'Performs frequency checks on categorical variables to detect misspellings and invalid values.',
        'function': step6_invalid_categories,
        'code': '''
# Invalid categories check
cat_vars = ['gender', 'marital_status', 'residence_type']
freq_tables = {}
for var in cat_vars:
    freq_df = df[var].value_counts(dropna=False).reset_index()
    freq_tables[var] = freq_df
'''
    },
    {
        'number': 7,
        'name': 'Duplicate Column Detection',
        'description': 'Detects duplicate columns by creating MD5 hashes of column values. Returns groups of duplicate columns.',
        'function': step7_duplicate_columns,
        'code': '''
# Duplicate column detection using MD5 hashing
df_sample = df.sample(n=min(1000, len(df)))
df_transposed = df_sample.T

# Create hash digest for each column
def create_hash(row):
    row_str = ''.join([str(val) for val in row.values if pd.notna(val)])
    return hashlib.md5(row_str.encode()).hexdigest()

df_transposed['digest'] = df_transposed.apply(create_hash, axis=1)

# Group by digest to find duplicates
# Returns dataframe with group_id and column_name
'''
    },
    {
        'number': 8,
        'name': 'Drop Duplicate Columns',
        'description': 'Drops duplicate columns identified in Step 7.',
        'function': step8_drop_duplicates,
        'code': '''
# Drop duplicate columns
# Uses list from Step 7's duplicate detection
result = df.drop(columns=columns_to_drop, errors='ignore')
'''
    },
    {
        'number': 9,
        'name': 'Check for Orphan Records',
        'description': 'Finds records that don\'t have a match in customer master table (if available).',
        'function': step9_orphan_records,
        'code': '''
# Check for orphan records
# Left join with customer master
merged = df.merge(
    customer_master[['cust_id']],
    on='cust_id',
    how='left',
    indicator=True
)
orphan_records = merged[merged['_merge'] == 'left_only']
'''
    }
]


def load_data_from_file():
    """Load data from CSV file."""
    data_file = current_dir / "data" / "var_metadata_input.csv"
    if data_file.exists():
        return pd.read_csv(data_file)
    else:
        st.error(f"Default data file not found: {data_file}")
        return None


def create_metadata_dictionary(input_df, step_results):
    """
    Create a comprehensive metadata dictionary combining information from all analysis steps.
    
    Parameters:
    -----------
    input_df : pd.DataFrame
        Original input dataframe
    step_results : dict
        Dictionary containing results from all analysis steps
    
    Returns:
    --------
    pd.DataFrame : Metadata dictionary with all variable information
    """
    metadata_list = []
    
    # Get all variables from original input
    all_vars = input_df.columns.tolist()
    
    # Get metadata from Step 1
    step1_metadata = {}
    if 0 in step_results:
        step1_result = step_results[0]
        if isinstance(step1_result, pd.DataFrame):
            for _, row in step1_result.iterrows():
                if row['Variable'] != 'TOTAL':
                    step1_metadata[row['Variable']] = {
                        'N': row.get('N', 0),
                        'NMiss': row.get('NMiss', 0)
                    }
    
    # Get % missing from Step 3
    step3_pct_missing = {}
    if 2 in step_results:
        step3_result = step_results[2]
        if isinstance(step3_result, pd.DataFrame):
            for _, row in step3_result.iterrows():
                step3_pct_missing[row['Variable']] = row.get('Pct_Missing', 0)
    
    # Get descriptive stats from Step 5
    step5_stats = {}
    if 4 in step_results:
        step5_result = step_results[4]
        if isinstance(step5_result, pd.DataFrame) and 'Variable' in step5_result.columns:
            for _, row in step5_result.iterrows():
                step5_stats[row['Variable']] = {
                    'Mean': row.get('Mean', None),
                    'Std': row.get('Std', None),
                    'Min': row.get('Min', None),
                    'Max': row.get('Max', None)
                }
    
    # Get duplicate information from Step 7
    duplicate_cols = set()
    if 6 in step_results:
        step7_result = step_results[6]
        if isinstance(step7_result, pd.DataFrame):
            duplicate_cols = set(step7_get_duplicate_list(step7_result))
    
    # Get dropped columns from Step 8
    dropped_cols = set()
    if 7 in step_results:
        step8_result = step_results[7]
        if isinstance(step8_result, dict) and 'columns_dropped' in step8_result:
            dropped_cols = set(step8_result['columns_dropped'])
    
    # Get categorical frequency info from Step 4/6
    categorical_vars = set()
    if 3 in step_results:
        step4_result = step_results[3]
        if isinstance(step4_result, dict) and 'freq_tables' in step4_result:
            categorical_vars = set(step4_result['freq_tables'].keys())
    
    if 5 in step_results:
        step6_result = step_results[5]
        if isinstance(step6_result, dict):
            categorical_vars.update(step6_result.keys())
    
    # Build metadata dictionary for each variable
    for var in all_vars:
        var_metadata = {
            'Variable': var,
            'Data_Type': 'Numeric' if pd.api.types.is_numeric_dtype(input_df[var]) else 'Categorical',
            'N': step1_metadata.get(var, {}).get('N', input_df[var].count()),
            'NMiss': step1_metadata.get(var, {}).get('NMiss', input_df[var].isnull().sum()),
            'Pct_Missing': step3_pct_missing.get(var, (input_df[var].isnull().sum() / len(input_df) * 100) if len(input_df) > 0 else 0),
            'Is_Duplicate': 'Yes' if var in duplicate_cols else 'No',
            'Is_Dropped': 'Yes' if var in dropped_cols else 'No',
            'Is_Categorical': 'Yes' if var in categorical_vars else 'No'
        }
        
        # Add descriptive statistics for numeric variables
        if var in step5_stats:
            var_metadata['Mean'] = step5_stats[var].get('Mean', None)
            var_metadata['Std'] = step5_stats[var].get('Std', None)
            var_metadata['Min'] = step5_stats[var].get('Min', None)
            var_metadata['Max'] = step5_stats[var].get('Max', None)
        elif pd.api.types.is_numeric_dtype(input_df[var]):
            # Calculate basic stats if not in Step 5
            var_metadata['Mean'] = input_df[var].mean()
            var_metadata['Std'] = input_df[var].std()
            var_metadata['Min'] = input_df[var].min()
            var_metadata['Max'] = input_df[var].max()
        else:
            var_metadata['Mean'] = None
            var_metadata['Std'] = None
            var_metadata['Min'] = None
            var_metadata['Max'] = None
        
        # Add unique values count for categorical
        if var in categorical_vars or not pd.api.types.is_numeric_dtype(input_df[var]):
            var_metadata['Unique_Values'] = input_df[var].nunique()
        else:
            var_metadata['Unique_Values'] = None
        
        metadata_list.append(var_metadata)
    
    # Create DataFrame
    metadata_df = pd.DataFrame(metadata_list)
    
    # Round numeric columns
    numeric_cols = ['Pct_Missing', 'Mean', 'Std']
    for col in numeric_cols:
        if col in metadata_df.columns:
            metadata_df[col] = metadata_df[col].round(2)
    
    return metadata_df


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
    
    st.markdown('<h1 class="main-header">Variable Metadata Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    This application analyzes variable metadata, missing values, duplicates, and data quality.
    It takes the final output from the data pipeline and performs various quality checks.
    
    NOTE: This project works on the training data as engineered in Step 1: Data Pipeline. 
    
    **Instructions:**
    1. Default data (var_metadata_input.csv with 268 columns) is loaded automatically
    2. Execute each step sequentially
    3. View the code and output for each step
    4. Review duplicate column detection and removal
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
            st.caption("Default: var_metadata_input.csv (268 columns from data pipeline)")
        
        st.markdown("---")
        
        if st.session_state.input_data is not None:
            st.success(f"Data loaded: {len(st.session_state.input_data):,} rows")
            st.markdown("---")
            st.header("Step Navigation")
            
            for i, step in enumerate(STEPS):
                status = "✅" if i < st.session_state.current_step else "⏳"
                if st.button(f"{status} Step {step['number']}: {step['name']}", 
                            key=f"nav_{i}",
                            disabled=(i > st.session_state.current_step)):
                    st.session_state.current_step = i
                    st.rerun()
            
            st.markdown("---")
            if st.button("Reset All Steps"):
                st.session_state.current_step = 0
                st.session_state.step_results = {}
                st.rerun()
            
            # Download button for output CSV (only show if Step 8 is completed)
            if 7 in st.session_state.step_results:
                st.markdown("---")
                st.header("Download Results")
                output_file = current_dir / "data" / "var_metadata_output.csv"
                if output_file.exists():
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="Download var_metadata_output.csv",
                            data=f.read(),
                            file_name="var_metadata_output.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        else:
            st.info("Please load data first")
    
    # Main content area
    if st.session_state.input_data is None:
        st.error("Error: Could not load default data file. Please check that var_metadata_input.csv exists in the data folder.")
        return
    
    # Display current step
    current_step_idx = st.session_state.current_step
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
            if st.button("Proceed to next Analysis", type="primary", disabled=False):
                # Navigate to feat_eng_analysis.py with scroll parameter
                st.query_params.update({"project": "feat_eng_analysis.py", "scroll": "top"})
                st.rerun()
        else:
            if st.button("Execute Step", type="primary", disabled=execute_disabled):
                with st.spinner(f"Executing Step {step['number']}..."):
                    try:
                        input_df = st.session_state.input_data.copy()
                        
                        # Special handling for Step 4
                        if step['number'] == 4:
                            # Need results from Step 3
                            if 2 not in st.session_state.step_results:
                                st.error("Please execute Step 3 first to get missing percentage data.")
                            else:
                                step3_result = st.session_state.step_results[2]
                                high_missing = step4_high_missing_vars(step3_result, threshold=30.0)
                                
                                cat_vars = ['gender', 'marital_status', 'residence_type']
                                freq_tables = step4_categorical_frequencies(input_df, cat_vars)
                                
                                result = {
                                    'high_missing': high_missing,
                                    'freq_tables': freq_tables
                                }
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"Step {step['number']} executed successfully!")
                                st.rerun()
                        
                        # Special handling for Step 7
                        elif step['number'] == 7:
                            result = step7_duplicate_columns(input_df, sample_size=1000)
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully!")
                            st.rerun()
                        
                        # Special handling for Step 8
                        elif step['number'] == 8:
                            # Get duplicate list from Step 7
                            if 6 not in st.session_state.step_results:
                                st.error("Please execute Step 7 first to detect duplicate columns.")
                            else:
                                step7_result = st.session_state.step_results[6]
                                columns_to_drop = step7_get_duplicate_list(step7_result)
                                
                                result = step8_drop_duplicates(input_df, columns_to_drop)
                                st.session_state.step_results[current_step_idx] = {
                                    'cleaned_data': result,
                                    'columns_dropped': columns_to_drop
                                }
                                
                                # Ensure data directory exists
                                data_dir = current_dir / "data"
                                data_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Save output CSV file
                                output_file = data_dir / "var_metadata_output.csv"
                                result.to_csv(output_file, index=False)
                                
                                # Save as feat_eng_data.csv for next step
                                # This file persists and is overwritten each run to allow starting from feat_eng_analysis.py
                                feat_eng_file = data_dir / "feat_eng_data.csv"
                                result.to_csv(feat_eng_file, index=False)
                                
                                # Create and save metadata dictionary
                                metadata_dict = create_metadata_dictionary(
                                    st.session_state.input_data,
                                    st.session_state.step_results
                                )
                                metadata_file = data_dir / "var_metadata_dictionary.csv"
                                metadata_dict.to_csv(metadata_file, index=False)
                                
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"Step {step['number']} executed successfully! Dropped {len(columns_to_drop)} columns. Output saved to var_metadata_output.csv and feat_eng_data.csv. Metadata dictionary saved to var_metadata_dictionary.csv")
                                st.rerun()
                        
                        # Special handling for Step 9
                        elif step['number'] == 9:
                            # Step 9 requires customer master (optional)
                            result = step9_orphan_records(input_df, customer_master=None)
                            st.session_state.step_results[current_step_idx] = result
                            st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                            st.success(f"Step {step['number']} executed successfully!")
                            st.rerun()
                        
                        # Standard steps
                        elif step['function'] is not None:
                            # Steps 1-3 need special handling for dependencies
                            if step['number'] == 1:
                                result = step['function'](input_df)
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"Step {step['number']} executed successfully!")
                                st.rerun()
                            
                            elif step['number'] == 2:
                                if 0 not in st.session_state.step_results:
                                    st.error("Please execute Step 1 first.")
                                else:
                                    step1_result = st.session_state.step_results[0]
                                    result = step['function'](step1_result)
                                    st.session_state.step_results[current_step_idx] = result
                                    st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                    st.success(f"Step {step['number']} executed successfully!")
                                    st.rerun()
                            
                            elif step['number'] == 3:
                                if 1 not in st.session_state.step_results or 0 not in st.session_state.step_results:
                                    st.error("Please execute Steps 1 and 2 first.")
                                else:
                                    step2_result = st.session_state.step_results[1]
                                    step1_result = st.session_state.step_results[0]
                                    total_n = step1_result._total_n
                                    result = step['function'](step2_result, total_n)
                                    st.session_state.step_results[current_step_idx] = result
                                    st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                    st.success(f"Step {step['number']} executed successfully!")
                                    st.rerun()
                            
                            elif step['number'] == 5:
                                vars_list = ['bureau_score', 'emi_to_income_ratio', 'monthly_income']
                                result = step['function'](input_df, vars_list)
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"Step {step['number']} executed successfully!")
                                st.rerun()
                            
                            elif step['number'] == 6:
                                cat_vars = ['gender', 'marital_status', 'residence_type']
                                result = step['function'](input_df, cat_vars)
                                st.session_state.step_results[current_step_idx] = result
                                st.session_state.current_step = min(current_step_idx + 1, len(STEPS) - 1)
                                st.success(f"Step {step['number']} executed successfully!")
                                st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error executing step: {str(e)}")
                        st.exception(e)
    
    # Display results if step has been executed
    if current_step_idx in st.session_state.step_results:
        result = st.session_state.step_results[current_step_idx]
        
        st.markdown("**Results:**")
        
        # Step 4 special display
        if step['number'] == 4:
            st.subheader("Variables with >30% Missing")
            if isinstance(result, dict) and 'high_missing' in result:
                if not result['high_missing'].empty:
                    st.dataframe(result['high_missing'], use_container_width=True)
                else:
                    st.info("No variables with >30% missing values.")
            
            st.subheader("Categorical Variable Frequencies")
            if isinstance(result, dict) and 'freq_tables' in result:
                for var, freq_df in result['freq_tables'].items():
                    st.write(f"**{var}:**")
                    st.dataframe(freq_df, use_container_width=True)
        
        # Step 8 special display
        elif step['number'] == 8:
            if isinstance(result, dict) and 'cleaned_data' in result:
                st.subheader(f"Columns Dropped: {len(result['columns_dropped'])}")
                st.write(", ".join(result['columns_dropped']))
                
                st.subheader("Cleaned Data Summary")
                cleaned_df = result['cleaned_data']
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows", f"{len(cleaned_df):,}")
                with col2:
                    st.metric("Columns", f"{len(cleaned_df.columns):,}")
                
                st.subheader("Data Preview (First 10 Rows)")
                st.dataframe(cleaned_df.head(10), use_container_width=True)
        
        # Step 9 special display
        elif step['number'] == 9:
            if isinstance(result, pd.DataFrame):
                if not result.empty:
                    st.warning(f"Found {len(result)} orphan records.")
                    st.dataframe(result, use_container_width=True)
                else:
                    st.info("No orphan records found (or customer master not available).")
        
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
        
        # Overall Summary Table (first table)
        if 7 in st.session_state.step_results:
            step8_result = st.session_state.step_results[7]
            if isinstance(step8_result, dict) and 'cleaned_data' in step8_result:
                original_cols = len(st.session_state.input_data.columns)
                cleaned_df = step8_result['cleaned_data']
                cleaned_cols = len(cleaned_df.columns)
                columns_dropped = len(step8_result['columns_dropped'])
                
                st.markdown("#### Overall Summary")
                overall_summary = pd.DataFrame({
                    'Metric': ['Columns Input', 'Columns Output', 'Columns Deleted'],
                    'Count': [original_cols, cleaned_cols, columns_dropped]
                })
                st.dataframe(overall_summary, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("Summary tables for each step showing rows/columns affected:")
        
        # Step 1: Extract Metadata
        if 0 in st.session_state.step_results:
            step1_result = st.session_state.step_results[0]
            if isinstance(step1_result, pd.DataFrame):
                st.markdown("#### Step 1: Extract Variable Metadata")
                numeric_vars_df = step1_result[step1_result['Variable'] != 'TOTAL'].copy()
                summary_table = pd.DataFrame({
                    'Metric': ['Numeric Variables Analyzed', 'Total Rows in Dataset', 'Total Missing Values'],
                    'Count': [len(numeric_vars_df), numeric_vars_df['N'].sum(), numeric_vars_df['NMiss'].sum()],
                    'Variables/Details': [
                        f"{len(numeric_vars_df)} variables: {', '.join(numeric_vars_df['Variable'].head(10).tolist())}" + (f" ... and {len(numeric_vars_df) - 10} more" if len(numeric_vars_df) > 10 else ""),
                        f"All {numeric_vars_df['N'].sum():,} observations",
                        f"Across all {len(numeric_vars_df)} numeric variables"
                    ]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 2: Transpose Missing
        if 1 in st.session_state.step_results:
            step2_result = st.session_state.step_results[1]
            if isinstance(step2_result, pd.DataFrame):
                st.markdown("#### Step 2: Transpose Missing Summary")
                summary_table = pd.DataFrame({
                    'Metric': ['Variables Transposed'],
                    'Count': [len(step2_result)],
                    'Variables/Details': [f"{len(step2_result)} variables transposed: {', '.join(step2_result['Variable'].head(10).tolist())}" + (f" ... and {len(step2_result) - 10} more" if len(step2_result) > 10 else "")]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 3: % Missing
        if 2 in st.session_state.step_results:
            step3_result = st.session_state.step_results[2]
            if isinstance(step3_result, pd.DataFrame):
                st.markdown("#### Step 3: Calculate % Missing")
                high_missing = step3_result[step3_result['Pct_Missing'] > 30]
                summary_table = pd.DataFrame({
                    'Metric': ['Variables Analyzed', 'Variables >30% Missing'],
                    'Count': [len(step3_result), len(high_missing)],
                    'Variables/Details': [
                        f"All {len(step3_result)} numeric variables",
                        f"{len(high_missing)} variables: {', '.join(high_missing['Variable'].tolist()) if len(high_missing) <= 20 else ', '.join(high_missing['Variable'].head(20).tolist()) + f' ... and {len(high_missing) - 20} more'}"
                    ]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 4: High Missing & Categorical Frequencies
        if 3 in st.session_state.step_results:
            step4_result = st.session_state.step_results[3]
            if isinstance(step4_result, dict):
                st.markdown("#### Step 4: High Missing Variables & Categorical Frequencies")
                summary_rows = []
                
                if 'high_missing' in step4_result and not step4_result['high_missing'].empty:
                    high_missing_vars = step4_result['high_missing']['Variable'].tolist()
                    summary_rows.append({
                        'Metric': 'Variables with >30% Missing',
                        'Count': len(high_missing_vars),
                        'Variables/Details': ', '.join(high_missing_vars) if len(high_missing_vars) <= 20 else ', '.join(high_missing_vars[:20]) + f" ... and {len(high_missing_vars) - 20} more"
                    })
                else:
                    summary_rows.append({
                        'Metric': 'Variables with >30% Missing',
                        'Count': 0,
                        'Variables/Details': 'No variables with >30% missing'
                    })
                
                if 'freq_tables' in step4_result:
                    cat_vars = list(step4_result['freq_tables'].keys())
                    low_card_vars = [var for var, freq_df in step4_result['freq_tables'].items() if len(freq_df) <= 5]
                    summary_rows.append({
                        'Metric': 'Categorical Variables Analyzed',
                        'Count': len(cat_vars),
                        'Variables/Details': f"Variables: {', '.join(cat_vars)}. Low cardinality (≤5 values): {', '.join(low_card_vars) if low_card_vars else 'None'}"
                    })
                
                summary_table = pd.DataFrame(summary_rows)
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 5: Descriptive Statistics
        if 4 in st.session_state.step_results:
            step5_result = st.session_state.step_results[4]
            if isinstance(step5_result, pd.DataFrame):
                st.markdown("#### Step 5: Descriptive Statistics")
                vars_analyzed = step5_result['Variable'].tolist() if 'Variable' in step5_result.columns else []
                summary_table = pd.DataFrame({
                    'Metric': ['Variables Analyzed'],
                    'Count': [len(step5_result)],
                    'Variables/Details': [f"{len(vars_analyzed)} variables: {', '.join(vars_analyzed)}"]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 6: Invalid Categories
        if 5 in st.session_state.step_results:
            step6_result = st.session_state.step_results[5]
            if isinstance(step6_result, dict):
                st.markdown("#### Step 6: Invalid Categories Check")
                cat_vars = list(step6_result.keys())
                summary_table = pd.DataFrame({
                    'Metric': ['Categorical Variables Checked'],
                    'Count': [len(cat_vars)],
                    'Variables/Details': [f"{len(cat_vars)} variables: {', '.join(cat_vars)}"]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 7: Duplicate Columns
        if 6 in st.session_state.step_results:
            step7_result = st.session_state.step_results[6]
            if isinstance(step7_result, pd.DataFrame):
                st.markdown("#### Step 7: Duplicate Column Detection")
                duplicate_cols = step7_get_duplicate_list(step7_result)
                duplicate_groups = step7_result['group_id'].nunique() if not step7_result.empty else 0
                summary_table = pd.DataFrame({
                    'Metric': ['Duplicate Columns Found', 'Duplicate Groups'],
                    'Count': [len(duplicate_cols), duplicate_groups],
                    'Variables/Details': [
                        f"{len(duplicate_cols)} columns to drop: {', '.join(duplicate_cols[:30])}" + (f" ... and {len(duplicate_cols) - 30} more" if len(duplicate_cols) > 30 else ""),
                        f"{duplicate_groups} groups of duplicate columns"
                    ]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 8: Drop Duplicates
        if 7 in st.session_state.step_results:
            step8_result = st.session_state.step_results[7]
            if isinstance(step8_result, dict) and 'cleaned_data' in step8_result:
                st.markdown("#### Step 8: Drop Duplicate Columns")
                original_rows = len(st.session_state.input_data)
                original_cols = len(st.session_state.input_data.columns)
                cleaned_df = step8_result['cleaned_data']
                cleaned_rows = len(cleaned_df)
                cleaned_cols = len(cleaned_df.columns)
                columns_dropped = step8_result['columns_dropped']
                
                summary_table = pd.DataFrame({
                    'Metric': ['Columns Before', 'Columns Dropped', 'Columns After', 'Rows Before', 'Rows After', 'Rows Dropped'],
                    'Count': [original_cols, len(columns_dropped), cleaned_cols, original_rows, cleaned_rows, original_rows - cleaned_rows],
                    'Variables/Details': [
                        f"{original_cols} columns in original dataset",
                        f"{len(columns_dropped)} columns: {', '.join(columns_dropped[:30])}" + (f" ... and {len(columns_dropped) - 30} more" if len(columns_dropped) > 30 else ""),
                        f"{cleaned_cols} columns remaining",
                        f"{original_rows:,} rows in original dataset",
                        f"{cleaned_rows:,} rows remaining",
                        f"{original_rows - cleaned_rows:,} rows removed (if any)"
                    ]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Step 9: Orphan Records
        if 8 in st.session_state.step_results:
            step9_result = st.session_state.step_results[8]
            if isinstance(step9_result, pd.DataFrame):
                st.markdown("#### Step 9: Orphan Records Check")
                orphan_count = len(step9_result)
                if orphan_count > 0:
                    # Get row indices or IDs if available
                    if 'cust_id' in step9_result.columns:
                        orphan_ids = step9_result['cust_id'].head(50).tolist()
                        details = f"{orphan_count} orphan records found. Sample IDs: {', '.join(map(str, orphan_ids))}" + (f" ... and {orphan_count - 50} more" if orphan_count > 50 else "")
                    else:
                        orphan_indices = step9_result.index.head(50).tolist()
                        details = f"{orphan_count} orphan records found. Sample row indices: {', '.join(map(str, orphan_indices))}" + (f" ... and {orphan_count - 50} more" if orphan_count > 50 else "")
                else:
                    details = "No orphan records found (or customer master not available)"
                
                summary_table = pd.DataFrame({
                    'Metric': ['Orphan Records Found'],
                    'Count': [orphan_count],
                    'Variables/Details': [details]
                })
                st.dataframe(summary_table, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

