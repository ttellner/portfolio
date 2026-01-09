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

