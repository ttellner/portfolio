"""
Variable Metadata Analysis Functions
Contains functions for each step of the variable analysis pipeline.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import hashlib


def step1_extract_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 1: Extract Variable Metadata
    Calculates count and missing count for all numeric variables.
    Equivalent to PROC MEANS with n nmiss.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate n (count) and nmiss (missing count) for each numeric variable
    summary_data = {
        'Variable': numeric_cols,
        'N': [df[col].count() for col in numeric_cols],
        'NMiss': [df[col].isnull().sum() for col in numeric_cols]
    }
    
    result = pd.DataFrame(summary_data)
    
    # Add total row (equivalent to _STAT_='N' row in SAS output)
    total_row = pd.DataFrame({
        'Variable': ['TOTAL'],
        'N': [result['N'].sum()],
        'NMiss': [result['NMiss'].sum()]
    })
    
    # Store total separately for later use
    result._total_n = result['N'].sum()
    result._total_nmiss = result['NMiss'].sum()
    
    return result


def step2_transpose_missing(df_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Transpose Missing Summary
    Transposes the metadata to have variables as rows.
    """
    # Extract the numeric columns data (exclude TOTAL if present)
    result = df_metadata[df_metadata['Variable'] != 'TOTAL'].copy()
    result = result.rename(columns={'NMiss': 'COL1'})
    result = result[['Variable', 'COL1']].copy()
    
    return result


def step3_calculate_pct_missing(df_transposed: pd.DataFrame, total_n: int) -> pd.DataFrame:
    """
    Step 3: Calculate % Missing
    Calculates percentage of missing values for each variable.
    """
    result = df_transposed.copy()
    result['Pct_Missing'] = (result['COL1'] / total_n * 100).round(2)
    result = result[['Variable', 'Pct_Missing']].copy()
    
    return result


def step4_high_missing_vars(df_pct_missing: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    """
    Step 4: Identify Variables with High Missing Percentage
    Returns variables with >threshold% missing values.
    Also includes frequency distributions for categorical variables (handled in Streamlit app).
    """
    high_missing = df_pct_missing[df_pct_missing['Pct_Missing'] > threshold].copy()
    return high_missing


def step4_categorical_frequencies(df: pd.DataFrame, cat_vars: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Step 4 (part 2): Frequency Distributions for Categorical Variables
    Returns frequency tables for specified categorical variables.
    """
    freq_tables = {}
    
    for var in cat_vars:
        if var in df.columns:
            freq_df = df[var].value_counts(dropna=False).reset_index()
            freq_df.columns = [var, 'Count']
            freq_df['Frequency'] = freq_df['Count']
            freq_tables[var] = freq_df
        else:
            freq_tables[var] = pd.DataFrame({var: [], 'Count': [], 'Frequency': []})
    
    return freq_tables


def step5_descriptive_stats(df: pd.DataFrame, vars_list: List[str]) -> pd.DataFrame:
    """
    Step 5: Descriptive Statistics and Range Checks
    Calculates descriptive statistics (n, mean, std, min, max) for specified variables.
    """
    available_vars = [v for v in vars_list if v in df.columns]
    
    if not available_vars:
        return pd.DataFrame()
    
    stats_data = {
        'Variable': available_vars,
        'N': [df[var].count() for var in available_vars],
        'Mean': [df[var].mean() for var in available_vars],
        'Std': [df[var].std() for var in available_vars],
        'Min': [df[var].min() for var in available_vars],
        'Max': [df[var].max() for var in available_vars]
    }
    
    result = pd.DataFrame(stats_data)
    # Round to 2 decimal places
    for col in ['Mean', 'Std']:
        if col in result.columns:
            result[col] = result[col].round(2)
    
    return result


def step6_invalid_categories(df: pd.DataFrame, cat_vars: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Step 6: Invalid Categories Check
    Performs frequency checks on categorical variables to detect misspellings and invalid values.
    Same as Step 4 part 2, but specifically for validation purposes.
    """
    return step4_categorical_frequencies(df, cat_vars)


def step7_duplicate_columns(df: pd.DataFrame, sample_size: Optional[int] = 1000) -> pd.DataFrame:
    """
    Step 7: Duplicate Column Detection
    Detects duplicate columns by creating MD5 hashes of column values.
    Returns a dataframe with group_id and column_name for duplicate groups.
    Excludes dpd_m1 through dpd_m12 columns from duplicate detection.
    """
    # Columns to exclude from duplicate detection
    exclude_columns = [f'dpd_m{i}' for i in range(1, 13)]
    
    # Sample data if specified
    df_sample = df.sample(n=min(sample_size, len(df))) if sample_size and len(df) > sample_size else df.copy()
    
    # Exclude specified columns from duplicate detection
    columns_to_check = [col for col in df_sample.columns if col not in exclude_columns]
    df_sample = df_sample[columns_to_check].copy()
    
    # Transpose: columns become rows
    df_transposed = df_sample.T
    df_transposed.reset_index(inplace=True)
    df_transposed.rename(columns={'index': 'column_name'}, inplace=True)
    
    # Create hash digest for each column (row in transposed dataframe)
    # Hash only the data values, excluding the column_name
    def create_hash(row):
        # Get all values except the first one (column_name)
        row_values = row.iloc[1:].values
        # Convert to string and concatenate
        row_str = ''.join([str(val) for val in row_values if pd.notna(val)])
        return hashlib.md5(row_str.encode()).hexdigest()
    
    df_transposed['digest'] = df_transposed.apply(create_hash, axis=1)
    
    # Keep only column_name and digest
    hashed_columns = df_transposed[['column_name', 'digest']].copy()
    
    # Sort by digest to group duplicates together
    hashed_columns = hashed_columns.sort_values('digest').reset_index(drop=True)
    
    # Assign group_id to duplicates
    hashed_columns['group_id'] = 0
    current_group = 0
    prev_digest = None
    
    for idx, row in hashed_columns.iterrows():
        if prev_digest is None or row['digest'] != prev_digest:
            current_group += 1
        hashed_columns.at[idx, 'group_id'] = current_group
        prev_digest = row['digest']
    
    # Keep only columns that have duplicates (group_id appears more than once)
    group_counts = hashed_columns['group_id'].value_counts()
    duplicate_groups = group_counts[group_counts > 1].index.tolist()
    duplicate_columns_final = hashed_columns[hashed_columns['group_id'].isin(duplicate_groups)].copy()
    
    return duplicate_columns_final[['group_id', 'column_name']].copy()


def step7_get_duplicate_list(df_duplicates: pd.DataFrame) -> List[str]:
    """
    Step 7 (helper): Extract list of duplicate columns to drop.
    Returns list of column names that are duplicates (keeping first in each group).
    """
    if df_duplicates.empty:
        return []
    
    # Group by group_id and keep all but the first column in each group
    columns_to_drop = []
    for group_id in df_duplicates['group_id'].unique():
        group_cols = df_duplicates[df_duplicates['group_id'] == group_id]['column_name'].tolist()
        # Keep first, drop rest
        columns_to_drop.extend(group_cols[1:])
    
    return columns_to_drop


def step8_drop_duplicates(df: pd.DataFrame, columns_to_drop: List[str]) -> pd.DataFrame:
    """
    Step 8: Drop Duplicate Columns
    Drops the specified columns from the dataframe.
    """
    # Filter to only columns that exist in the dataframe
    existing_cols = [col for col in columns_to_drop if col in df.columns]
    
    if not existing_cols:
        return df.copy()
    
    result = df.drop(columns=existing_cols, errors='ignore')
    return result


def step8_get_hardcoded_list() -> List[str]:
    """
    Step 8 (helper): Returns the hardcoded list of columns to drop from SAS code.
    This is used to compare with Step 7's output.
    """
    hardcoded_list = [
        'repayment_rate_flag',
        'recovery_effectiveness_score',
        'low_credit_limit_flag',
        'low_loan_flag',
        'ptp_honored_ratio',
        'ptp_ratio_score',
        'ptp_kept_score',
        'combined_score_flag',
        'loan_weighted_score',
        'dpd_variance',
        'emi_income_flag',
        'dpd_avg',
        'credit_limit_bucket',
        'requested_amount_bucket',
        'dpd_max_days',
        'dpd_last_month',
        'max_dpd_days',
        'recent_dpd_score',
        'fast_funding_flag',
        'account_ratio_active',
        'dpd_3m_total',
        'affordability_flag',
        'dpd_ratio',
        'high_credit_limit_flag',
        'limit_score_flag',
        'loan_size_flag',
        'size_bucket_flag',
        'enquiry_below650_flag',
        'dpd_f2',
        'dpd_f3',
        'dpd_f4',
        'dpd_f5',
        'dpd_f6',
        'credit_limit',
        'requested_amt',
        'high_risk_band_flag',
        'bureau_score_low_flag',
        'write_off_case_flag',
        'writeoff_flag_combined',
        'writeoff_recovery_flag',
        'legal_action_taken_flag',
        'legal_case_escalated_flag',
        'legal_initiated_flag',
        'legal_escalation_score',
        'legal_action_flag',
        'score_agreement_flag',
        'dpd_count_30_plus',
        'recovery_bucket_score',
        'emi_ratio_buffer',
        'loan_request_score',
        'avg_balance_flag',
        'emi_bounce_flag',
        'high_balance_flag',
        'bounce_flag',
        'high_avg_bal_flag',
        'dpd_m1',
        'dpd_m3',
        'dpd_m5'
    ]
    return hardcoded_list


def step9_orphan_records(df: pd.DataFrame, customer_master: Optional[pd.DataFrame] = None, 
                         customer_id_col: str = 'cust_id') -> pd.DataFrame:
    """
    Step 9: Check for Orphan Records
    Finds records in df that don't have a match in customer_master.
    If customer_master is None, returns empty dataframe with appropriate columns.
    """
    if customer_master is None:
        # No customer master available - return empty dataframe with same columns as input
        return pd.DataFrame(columns=df.columns)
    
    if customer_id_col not in df.columns:
        return pd.DataFrame(columns=df.columns)
    
    if customer_id_col not in customer_master.columns:
        return pd.DataFrame(columns=df.columns)
    
    # Left join to find orphans
    merged = df.merge(
        customer_master[[customer_id_col]],
        on=customer_id_col,
        how='left',
        indicator=True
    )
    
    # Filter to records that don't have a match
    orphan_records = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    return orphan_records

