"""
Feature Engineering Functions
Contains functions for feature engineering pipeline including exclusions, feature creation, imputation, and outlier capping.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime


def step1_filter_by_dates(df: pd.DataFrame, 
                          obs_start: str = '2022-01-01',
                          obs_end: str = '2022-12-31') -> pd.DataFrame:
    """
    Step 1: Filter data by observation date range.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    obs_start : str
        Start date in 'YYYY-MM-DD' format
    obs_end : str
        End date in 'YYYY-MM-DD' format
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe
    """
    df = df.copy()
    
    # Convert snapshot_date to datetime if it's not already
    if 'snapshot_date' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['snapshot_date']):
            df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
        
        # Filter by date range
        obs_start_dt = pd.to_datetime(obs_start)
        obs_end_dt = pd.to_datetime(obs_end)
        df = df[(df['snapshot_date'] >= obs_start_dt) & 
                (df['snapshot_date'] <= obs_end_dt)]
    
    return df


def step1_apply_exclusions(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Step 1: Apply exclusion rules to filter out invalid records.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe after exclusions
    """
    df = df.copy()
    initial_count = len(df)
    
    # Exclusion rules
    if 'write_off_flag' in df.columns:
        df = df[df['write_off_flag'] != 1]
    
    if 'monthly_income' in df.columns:
        df = df[df['monthly_income'] > 0]
    
    if 'application_date' in df.columns and 'snapshot_date' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['application_date']):
            df['application_date'] = pd.to_datetime(df['application_date'], errors='coerce')
        df = df[df['application_date'] <= df['snapshot_date']]
    
    if 'tenure_months' in df.columns:
        df = df[df['tenure_months'] >= 3]
    
    excluded_count = initial_count - len(df)
    
    return df, excluded_count


def step2_create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Create engineered features including DPD frequencies, flags, ratios, and buckets.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    pd.DataFrame : Dataframe with new features added
    """
    df = df.copy()
    
    # Initialize DPD frequency counts
    df['dpd_0to30_freq'] = 0
    df['dpd_31to60_freq'] = 0
    df['dpd_61plus_freq'] = 0
    
    # Get DPD columns (dpd_m1 through dpd_m12)
    dpd_cols = [f'dpd_m{i}' for i in range(1, 13) if f'dpd_m{i}' in df.columns]
    
    # Loop through all DPD columns
    for col in dpd_cols:
        # Count frequencies by DPD range
        df.loc[(df[col] >= 1) & (df[col] <= 30), 'dpd_0to30_freq'] += 1
        df.loc[(df[col] >= 31) & (df[col] <= 60), 'dpd_31to60_freq'] += 1
        df.loc[df[col] >= 61, 'dpd_61plus_freq'] += 1
    
    # Recent delinquency flag (last 3 months)
    dpd_recent_cols = [f'dpd_m{i}' for i in range(1, 4) if f'dpd_m{i}' in df.columns]
    if dpd_recent_cols:
        df['dpd_recent_flag'] = (df[dpd_recent_cols].max(axis=1) > 0).astype(int)
    else:
        df['dpd_recent_flag'] = 0
    
    # Worsening DPD flag
    if all(col in df.columns for col in ['dpd_m1', 'dpd_m2', 'dpd_m3']):
        df['dpd_worsening_flag'] = (
            (df['dpd_m1'] > df['dpd_m2']) & 
            (df['dpd_m2'] > df['dpd_m3'])
        ).astype(int)
    else:
        df['dpd_worsening_flag'] = 0
    
    # Average utilization (last 3 months)
    util_cols = [f'util_m{i}' for i in range(1, 4) if f'util_m{i}' in df.columns]
    if util_cols:
        df['avg_util_3m'] = df[util_cols].mean(axis=1)
    else:
        df['avg_util_3m'] = np.nan
    
    # EMI to income ratio
    if 'total_emi' in df.columns and 'monthly_income' in df.columns:
        df['emi_to_income_ratio'] = df['total_emi'] / df['monthly_income'].replace(0, np.nan)
    else:
        df['emi_to_income_ratio'] = np.nan
    
    # Loan tenure bucket
    if 'loan_tenure' in df.columns:
        df['loan_tenure_bucket'] = pd.cut(
            df['loan_tenure'],
            bins=[-np.inf, 12, 36, np.inf],
            labels=['Short', 'Medium', 'Long']
        ).astype(str)
    else:
        df['loan_tenure_bucket'] = None
    
    # Age band
    if 'age' in df.columns:
        df['age_band'] = pd.cut(
            df['age'],
            bins=[-np.inf, 25, 35, 50, np.inf],
            labels=['<25', '25-35', '36-50', '50+']
        ).astype(str)
    else:
        df['age_band'] = None
    
    # Salary credit flag
    salary_cols = [f'salary_credit_m{i}' for i in range(1, 4) if f'salary_credit_m{i}' in df.columns]
    if salary_cols:
        df['salary_credit_flag'] = (df[salary_cols].sum(axis=1) > 0).astype(int)
    else:
        df['salary_credit_flag'] = 0
    
    # Bounce count (last 3 months)
    bounce_cols = [f'bounce_m{i}' for i in range(1, 4) if f'bounce_m{i}' in df.columns]
    if bounce_cols:
        df['bounce_3m_count'] = df[bounce_cols].sum(axis=1)
    else:
        df['bounce_3m_count'] = 0
    
    # Ratio of DPD to bureau score
    if dpd_cols and 'bureau_score' in df.columns:
        max_dpd = df[dpd_cols].max(axis=1)
        df['dpd_to_bureau_ratio'] = max_dpd / (900 - df['bureau_score'].replace(0, np.nan))
    else:
        df['dpd_to_bureau_ratio'] = np.nan
    
    return df


def step3_calculate_impute_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Step 3: Calculate mean and median for imputation.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    dict : Dictionary with mean and median values for bureau_score, total_emi, monthly_income
    """
    stats = {}
    
    vars_to_impute = ['bureau_score', 'total_emi', 'monthly_income']
    
    for var in vars_to_impute:
        if var in df.columns:
            stats[f'{var}_mean'] = df[var].mean()
            stats[f'{var}_median'] = df[var].median()
        else:
            stats[f'{var}_mean'] = np.nan
            stats[f'{var}_median'] = np.nan
    
    return stats


def step6_calculate_percentiles(df: pd.DataFrame) -> Dict[str, float]:
    """
    Step 6: Calculate 1st and 99th percentiles for outlier capping.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    dict : Dictionary with 1st and 99th percentile values
    """
    percentiles = {}
    
    vars_to_cap = ['bureau_score', 'total_emi', 'monthly_income']
    
    for var in vars_to_cap:
        if var in df.columns:
            p1 = df[var].quantile(0.01)
            p99 = df[var].quantile(0.99)
            percentiles[f'{var}_p1'] = p1
            percentiles[f'{var}_p99'] = p99
        else:
            percentiles[f'{var}_p1'] = np.nan
            percentiles[f'{var}_p99'] = np.nan
    
    return percentiles


def step7_apply_imputation_and_capping(df: pd.DataFrame,
                                       impute_stats: Dict[str, float],
                                       percentiles: Dict[str, float]) -> pd.DataFrame:
    """
    Step 7: Apply missing value imputation and outlier capping.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    impute_stats : dict
        Dictionary with mean and median values for imputation
    percentiles : dict
        Dictionary with 1st and 99th percentile values for capping
    
    Returns:
    --------
    pd.DataFrame : Dataframe with imputation and capping applied
    """
    df = df.copy()
    
    vars_to_process = ['bureau_score', 'total_emi', 'monthly_income']
    
    for var in vars_to_process:
        if var not in df.columns:
            continue
        
        # Create missing flags before imputation
        miss_flag_col = f'{var}_miss_flag'
        df[miss_flag_col] = df[var].isna().astype(int)
        
        # Imputation using median
        median_key = f'{var}_median'
        if median_key in impute_stats and not pd.isna(impute_stats[median_key]):
            df[var] = df[var].fillna(impute_stats[median_key])
        
        # Outlier capping
        p1_key = f'{var}_p1'
        p99_key = f'{var}_p99'
        
        if p1_key in percentiles and not pd.isna(percentiles[p1_key]):
            df.loc[df[var] < percentiles[p1_key], var] = percentiles[p1_key]
        
        if p99_key in percentiles and not pd.isna(percentiles[p99_key]):
            df.loc[df[var] > percentiles[p99_key], var] = percentiles[p99_key]
    
    return df


def step8_calculate_eda_measures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 8: Calculate EDA measures including descriptive statistics, deciles, and good/bad counts.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    pd.DataFrame : Dataframe with additional measures calculated
    """
    df = df.copy()
    
    # Create bureau_score deciles if bureau_score exists
    if 'bureau_score' in df.columns:
        # Create deciles (10 groups) using qcut
        try:
            df['bureau_decile'] = pd.qcut(
                df['bureau_score'],
                q=10,
                labels=False,
                duplicates='drop'
            )
        except ValueError:
            # If qcut fails due to duplicates, use rank-based approach
            df['bureau_decile'] = pd.qcut(
                df['bureau_score'].rank(method='first'),
                q=10,
                labels=False,
                duplicates='drop'
            )
        
        # Fill any NaN values with -1 (for cases where qcut fails)
        df['bureau_decile'] = df['bureau_decile'].fillna(-1).astype(int)
    
    return df


def calculate_iv_by_decile(df: pd.DataFrame, decile_col: str = 'bureau_decile', 
                           target_col: str = 'default_flag') -> pd.DataFrame:
    """
    Calculate Information Value (IV) statistics by decile.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    decile_col : str
        Column name for decile grouping
    target_col : str
        Column name for target variable (default flag)
    
    Returns:
    --------
    pd.DataFrame : Summary table with decile, bad count, good count
    """
    if decile_col not in df.columns or target_col not in df.columns:
        return pd.DataFrame()
    
    # Calculate good/bad counts by decile
    iv_data = []
    for decile in sorted(df[decile_col].dropna().unique()):
        if decile == -1:  # Skip invalid deciles
            continue
        decile_data = df[df[decile_col] == decile]
        bad_count = int(decile_data[target_col].sum()) if target_col in decile_data.columns else 0
        good_count = len(decile_data) - bad_count
        
        iv_data.append({
            decile_col: int(decile),
            'bad': bad_count,
            'good': good_count
        })
    
    return pd.DataFrame(iv_data)

