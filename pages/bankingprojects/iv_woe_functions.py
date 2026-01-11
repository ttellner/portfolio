"""
IV and WoE Calculation Functions
Contains functions for calculating Information Value (IV) and Weight of Evidence (WoE).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


def step1_get_numeric_variables(df: pd.DataFrame, exclude_vars: List[str] = None) -> List[str]:
    """
    Step 1: Get list of numeric variables excluding specified variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    exclude_vars : list, optional
        List of variable names to exclude (default: ['default_flag'])
    
    Returns:
    --------
    list : List of numeric variable names
    """
    if exclude_vars is None:
        exclude_vars = ['default_flag']
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude specified variables (case-insensitive)
    exclude_vars_upper = [var.upper() for var in exclude_vars]
    numeric_vars = [col for col in numeric_cols 
                   if col.upper() not in exclude_vars_upper]
    
    return numeric_vars


def step2_create_iv_summary_structure() -> pd.DataFrame:
    """
    Step 2: Create empty IV summary table with correct structure.
    
    Returns:
    --------
    pd.DataFrame : Empty dataframe with 'variable' and 'IV' columns
    """
    return pd.DataFrame(columns=['variable', 'IV'])


def step4_calculate_woe_iv_for_variable(df: pd.DataFrame, 
                                        var_name: str, 
                                        target_col: str = 'default_flag',
                                        n_bins: int = 10) -> Tuple[float, pd.DataFrame]:
    """
    Step 4: Calculate WoE and IV for a single variable.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    var_name : str
        Name of the variable to analyze
    target_col : str
        Name of the target variable (default: 'default_flag')
    n_bins : int
        Number of bins to create (default: 10)
    
    Returns:
    --------
    tuple : (IV value, WoE statistics dataframe)
    """
    if var_name not in df.columns or target_col not in df.columns:
        return 0.0, pd.DataFrame()
    
    df_work = df[[var_name, target_col]].copy()
    df_work = df_work.dropna(subset=[var_name])
    
    if len(df_work) == 0:
        return 0.0, pd.DataFrame()
    
    # Create bins using qcut (equivalent to proc rank groups=10)
    try:
        df_work['bin'] = pd.qcut(
            df_work[var_name],
            q=n_bins,
            labels=False,
            duplicates='drop'
        )
    except ValueError:
        # If qcut fails due to duplicates, use rank-based approach
        df_work['bin'] = pd.qcut(
            df_work[var_name].rank(method='first'),
            q=n_bins,
            labels=False,
            duplicates='drop'
        )
    
    # Fill NaN bins with -1
    df_work['bin'] = df_work['bin'].fillna(-1).astype(int)
    
    # Calculate good/bad counts by bin
    stats = df_work.groupby('bin').agg({
        target_col: ['sum', 'count']
    }).reset_index()
    
    stats.columns = ['bin', 'bad', 'total']
    stats['good'] = stats['total'] - stats['bad']
    
    # Remove invalid bins
    stats = stats[stats['bin'] >= 0]
    
    if len(stats) == 0:
        return 0.0, pd.DataFrame()
    
    # Calculate total goods/bads
    tot_good = stats['good'].sum()
    tot_bad = stats['bad'].sum()
    
    if tot_good == 0 or tot_bad == 0:
        return 0.0, stats
    
    # Calculate WoE & IV components
    stats['pct_good'] = stats['good'] / tot_good
    stats['pct_bad'] = stats['bad'] / tot_bad
    
    # Avoid division by zero
    stats['pct_good'] = stats['pct_good'].replace(0, 0.0001)
    stats['pct_bad'] = stats['pct_bad'].replace(0, 0.0001)
    
    # Calculate WoE
    stats['woe'] = np.log(stats['pct_good'] / stats['pct_bad'])
    
    # Calculate IV component
    stats['iv_component'] = (stats['pct_good'] - stats['pct_bad']) * stats['woe']
    
    # Add variable name
    stats['variable'] = var_name
    
    # Calculate total IV
    iv_value = stats['iv_component'].sum()
    
    return iv_value, stats


def step4_calculate_woe_iv_all_variables(df: pd.DataFrame,
                                        numeric_vars: List[str],
                                        target_col: str = 'default_flag',
                                        n_bins: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Step 4: Calculate WoE and IV for all numeric variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    numeric_vars : list
        List of numeric variable names to analyze
    target_col : str
        Name of the target variable (default: 'default_flag')
    n_bins : int
        Number of bins to create (default: 10)
    
    Returns:
    --------
    tuple : (IV summary dataframe, WoE statistics dataframe for all variables)
    """
    iv_summary_list = []
    woe_all_list = []
    
    for var in numeric_vars:
        if var not in df.columns:
            continue
        
        iv_value, woe_stats = step4_calculate_woe_iv_for_variable(
            df, var, target_col, n_bins
        )
        
        # Append to IV summary
        iv_summary_list.append({
            'variable': var,
            'IV': iv_value
        })
        
        # Append to WoE table if valid
        if not woe_stats.empty:
            woe_all_list.append(woe_stats)
    
    # Create IV summary dataframe
    iv_summary = pd.DataFrame(iv_summary_list)
    
    # Combine all WoE statistics
    if woe_all_list:
        woe_all = pd.concat(woe_all_list, ignore_index=True)
    else:
        woe_all = pd.DataFrame(columns=['bin', 'bad', 'good', 'total', 
                                       'pct_good', 'pct_bad', 'woe', 
                                       'iv_component', 'variable'])
    
    return iv_summary, woe_all


def calculate_manual_binning_woe_iv(df: pd.DataFrame,
                                     var_name: str,
                                     bin_edges: List[float],
                                     target_col: str = 'default_flag') -> Tuple[float, pd.DataFrame]:
    """
    Calculate WoE and IV for a variable using manual binning.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    var_name : str
        Name of the variable to analyze
    bin_edges : list
        List of bin edges for manual binning (e.g., [400, 500, 600, 700] creates bins: <400, 400-500, 500-600, 600-700, >=700)
    target_col : str
        Name of the target variable (default: 'default_flag')
    
    Returns:
    --------
    tuple : (IV value, WoE statistics dataframe)
    """
    if var_name not in df.columns or target_col not in df.columns:
        return 0.0, pd.DataFrame()
    
    df_work = df[[var_name, target_col]].copy()
    df_work = df_work.dropna(subset=[var_name])
    
    if len(df_work) == 0:
        return 0.0, pd.DataFrame()
    
    # Create manual bins
    df_work['bin'] = pd.cut(df_work[var_name], bins=[-np.inf] + bin_edges + [np.inf], labels=False, right=False)
    df_work['bin'] = df_work['bin'] + 1  # Start from 1 instead of 0
    
    # Calculate good/bad counts by bin
    stats = df_work.groupby('bin').agg({
        target_col: ['sum', 'count']
    }).reset_index()
    
    stats.columns = ['bin', 'bad', 'total']
    stats['good'] = stats['total'] - stats['bad']
    
    if len(stats) == 0:
        return 0.0, pd.DataFrame()
    
    # Calculate total goods/bads
    tot_good = stats['good'].sum()
    tot_bad = stats['bad'].sum()
    
    if tot_good == 0 or tot_bad == 0:
        return 0.0, stats
    
    # Calculate WoE & IV components
    stats['pct_good'] = stats['good'] / tot_good
    stats['pct_bad'] = stats['bad'] / tot_bad
    
    # Avoid division by zero
    stats['pct_good'] = stats['pct_good'].replace(0, 0.0001)
    stats['pct_bad'] = stats['pct_bad'].replace(0, 0.0001)
    
    # Calculate WoE
    stats['woe'] = np.log(stats['pct_good'] / stats['pct_bad'])
    
    # Calculate IV component
    stats['iv_component'] = (stats['pct_good'] - stats['pct_bad']) * stats['woe']
    
    # Add variable name
    stats['variable'] = var_name
    
    # Calculate total IV
    iv_value = stats['iv_component'].sum()
    
    return iv_value, stats


def calculate_woe_iv_with_manual_bureau_score(df: pd.DataFrame,
                                              numeric_vars: List[str],
                                              target_col: str = 'default_flag',
                                              n_bins: int = 10,
                                              manual_var: str = 'bureau_score',
                                              manual_bin_edges: List[float] = [400, 500, 600, 700]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate WoE and IV for all numeric variables, with manual binning for a specific variable.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    numeric_vars : list
        List of numeric variable names to analyze
    target_col : str
        Name of the target variable (default: 'default_flag')
    n_bins : int
        Number of bins to create for automatic binning (default: 10)
    manual_var : str
        Variable name to use manual binning for (default: 'bureau_score')
    manual_bin_edges : list
        Bin edges for manual binning (default: [400, 500, 600, 700])
    
    Returns:
    --------
    tuple : (IV summary dataframe, WoE statistics dataframe for all variables)
    """
    iv_summary_list = []
    woe_all_list = []
    
    for var in numeric_vars:
        if var not in df.columns:
            continue
        
        # Use manual binning for specified variable, automatic for others
        if var == manual_var:
            iv_value, woe_stats = calculate_manual_binning_woe_iv(
                df, var, manual_bin_edges, target_col
            )
        else:
            iv_value, woe_stats = step4_calculate_woe_iv_for_variable(
                df, var, target_col, n_bins
            )
        
        # Append to IV summary
        iv_summary_list.append({
            'variable': var,
            'IV': iv_value
        })
        
        # Append to WoE table if valid
        if not woe_stats.empty:
            woe_all_list.append(woe_stats)
    
    # Create IV summary dataframe
    iv_summary = pd.DataFrame(iv_summary_list)
    
    # Combine all WoE statistics
    if woe_all_list:
        woe_all = pd.concat(woe_all_list, ignore_index=True)
    else:
        woe_all = pd.DataFrame(columns=['bin', 'bad', 'good', 'total', 
                                       'pct_good', 'pct_bad', 'woe', 
                                       'iv_component', 'variable'])
    
    return iv_summary, woe_all


def apply_woe_transformations(df: pd.DataFrame,
                              woe_all: pd.DataFrame,
                              numeric_vars: List[str],
                              target_col: str = 'default_flag',
                              n_bins: int = 10,
                              manual_var: str = 'bureau_score',
                              manual_bin_edges: List[float] = [400, 500, 600, 700]) -> pd.DataFrame:
    """
    Apply WoE transformations to the dataset, replacing original variables with WoE values.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    woe_all : pd.DataFrame
        DataFrame containing WoE statistics for all variables
    numeric_vars : list
        List of numeric variable names to transform
    target_col : str
        Name of the target variable (default: 'default_flag')
    n_bins : int
        Number of bins for automatic binning (default: 10)
    manual_var : str
        Variable name that uses manual binning (default: 'bureau_score')
    manual_bin_edges : list
        Bin edges for manual binning (default: [400, 500, 600, 700])
    
    Returns:
    --------
    pd.DataFrame : Dataframe with WoE transformed variables
    """
    df_transformed = df.copy()
    
    for var in numeric_vars:
        if var not in df_transformed.columns:
            continue
        
        # Get WoE statistics for this variable
        var_woe = woe_all[woe_all['variable'] == var].copy()
        
        if var_woe.empty:
            continue
        
        # Get non-null indices for this variable
        non_null_mask = df_transformed[var].notna()
        non_null_indices = df_transformed.index[non_null_mask]
        
        if len(non_null_indices) == 0:
            continue
        
        # Extract values for binning
        var_values = df_transformed.loc[non_null_indices, var]
        
        # Use manual binning for specified variable, automatic for others
        if var == manual_var:
            bins = pd.cut(var_values, bins=[-np.inf] + manual_bin_edges + [np.inf], 
                         labels=False, right=False)
            bins = bins + 1  # Start from 1 instead of 0
            bins = bins.astype(int)
        else:
            try:
                bins = pd.qcut(
                    var_values,
                    q=n_bins,
                    labels=False,
                    duplicates='drop'
                )
            except ValueError:
                bins = pd.qcut(
                    var_values.rank(method='first'),
                    q=n_bins,
                    labels=False,
                    duplicates='drop'
                )
            bins = bins.fillna(-1).astype(int)
            # Only process valid bins (>= 0)
            valid_bin_mask = bins >= 0
            bins = bins[valid_bin_mask]
            non_null_indices = non_null_indices[valid_bin_mask]
        
        # Create a dataframe for merging
        bin_df = pd.DataFrame({'bin': bins.values}, index=non_null_indices)
        
        # Merge with WoE values
        merged = bin_df.merge(
            var_woe[['bin', 'woe']],
            on='bin',
            how='left'
        )
        
        # Replace original variable with WoE values (only where we have valid WoE)
        df_transformed.loc[merged.index, var] = merged['woe'].values
    
    return df_transformed


def create_expanded_keep_list() -> List[str]:
    """
    Create expanded forced keep list of variables that should always be kept.
    
    Returns:
    --------
    list : List of variable names to always keep
    """
    keep_list = [
        'bureau_score',
        'bureau_score_bucket',
        'bureau_score_bucket_50',
        'bureau_enquiries_1m',
        'bureau_enquiries_3m',
        'bureau_enquiries_6m',
        'bureau_enquiries_12m',
        'salary_credit_3m',
        'salary_credit_6m',
        'salary_credit_12m',
        'emi_to_income_ratio',
        'requested_amount',
        'minimum_balance',
        'dpd_max',
        'dpd_count_30_plus',
        'dpd_count_60_plus',
        'dpd_sum_total',
        'last_payment_gap',
        'num_loans_active',
        'num_loans_closed',
        'num_credit_cards_active',
        'utilization_score',
        'balance_utilization_score',
        'credit_card_utilization_pct',
        'amount_income_term_score',
        'behavior_bureau_interaction',
        'age',
        'employment_type',
        'education_level',
        'marital_status',
        'gender',
        'city_category',
        'customer_vintage_months',
        'avg_monthly_spend',
        'loan_to_income_ratio',
        'installment_to_balance_ratio',
        'cash_txn_ratio',
        'pos_txn_volume',
        'risk_score',
        'credit_limit_usage_ratio',
        'income_variability_score',
        'overdue_amount_ratio',
        'account_open_date',
        'monthly_income',
        'monthly_interest_rate',
        'emi_income_ratio',
        'emi_normalized',
        'recovery_success_flag',
        'request_term_ratio_flag'
    ]
    return keep_list


def filter_variables_by_iv(iv_summary: pd.DataFrame,
                           keep_list: List[str],
                           iv_min: float = 0.015,
                           iv_max: float = 5.0) -> pd.DataFrame:
    """
    Merge IV summary with keep list and apply filtering rules.
    
    Parameters:
    -----------
    iv_summary : pd.DataFrame
        IV summary dataframe with 'variable' and 'IV' columns
    keep_list : list
        List of variables to always keep
    iv_min : float
        Minimum IV value for filtering (default: 0.015)
    iv_max : float
        Maximum IV value for filtering (default: 5.0)
    
    Returns:
    --------
    pd.DataFrame : Filtered IV summary with 'keep_flag' column
    """
    # Create keep list dataframe
    keep_df = pd.DataFrame({'variable': keep_list})
    
    # Merge IV summary with keep list
    iv_filtered = iv_summary.merge(
        keep_df,
        on='variable',
        how='left',
        indicator=True
    )
    
    # Apply filtering rules
    iv_filtered['keep_flag'] = (
        (iv_filtered['_merge'] == 'both') |  # Always keep forced variables
        ((iv_filtered['IV'] >= iv_min) & (iv_filtered['IV'] <= iv_max))  # IV cutoff
    ).astype(int)
    
    # Drop merge indicator
    iv_filtered = iv_filtered.drop(columns=['_merge'])
    
    return iv_filtered


def select_final_variables(iv_filtered: pd.DataFrame,
                           keep_list: List[str],
                           available_variables: List[str]) -> List[str]:
    """
    Final selection - keep only variables that exist in the dataset.
    
    Parameters:
    -----------
    iv_filtered : pd.DataFrame
        Filtered IV summary with 'keep_flag' column
    keep_list : list
        List of variables to always keep
    available_variables : list
        List of variables that exist in the dataset
    
    Returns:
    --------
    list : Final list of selected variables
    """
    # Get variables with keep_flag = 1
    vars_from_iv = iv_filtered[iv_filtered['keep_flag'] == 1]['variable'].tolist()
    
    # Combine with keep list
    combined_vars = list(set(vars_from_iv + keep_list))
    
    # Keep only variables that exist in the dataset
    selected_vars = [var for var in combined_vars if var in available_variables]
    
    return selected_vars


def create_filtered_dataset(df: pd.DataFrame,
                           selected_vars: List[str],
                           target_col: str = 'default_flag') -> pd.DataFrame:
    """
    Create final filtered dataset with only selected variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    selected_vars : list
        List of variables to keep
    target_col : str
        Target variable name (default: 'default_flag')
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe with only selected variables and target
    """
    # Always include target column
    cols_to_keep = [target_col] + [var for var in selected_vars if var in df.columns]
    
    # Filter dataframe
    df_filtered = df[cols_to_keep].copy()
    
    return df_filtered