"""
Collinearity Analysis Functions
Contains functions for correlation and VIF filtering.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
import warnings
warnings.filterwarnings('ignore')


def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix for numeric variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    
    Returns:
    --------
    pd.DataFrame : Correlation matrix
    """
    numeric_df = df.select_dtypes(include=[np.number])
    return numeric_df.corr()


def find_high_correlation_pairs(corr_matrix: pd.DataFrame, threshold: float = 0.90) -> pd.DataFrame:
    """
    Find pairs of variables with correlation above threshold.
    
    Parameters:
    -----------
    corr_matrix : pd.DataFrame
        Correlation matrix
    threshold : float
        Correlation threshold (default: 0.90)
    
    Returns:
    --------
    pd.DataFrame : DataFrame with var1, var2, and corr_value columns
    """
    high_corr_pairs = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            var1 = corr_matrix.columns[i]
            var2 = corr_matrix.columns[j]
            corr_value = corr_matrix.iloc[i, j]
            
            if corr_value >= threshold:
                high_corr_pairs.append({
                    'var1': var1,
                    'var2': var2,
                    'corr_value': corr_value
                })
    
    return pd.DataFrame(high_corr_pairs)


def identify_vars_to_drop_correlation(
    high_corr_pairs: pd.DataFrame,
    iv_summary: Optional[pd.DataFrame] = None,
    corr_threshold_high: float = 0.98,
    corr_threshold_medium: float = 0.95,
    iv_threshold: float = 0.02
) -> List[str]:
    """
    Identify variables to drop based on correlation and IV values.
    Drops var2 if:
    - corr_value > 0.98, OR
    - corr_value > 0.95 AND IV < 0.02
    
    Parameters:
    -----------
    high_corr_pairs : pd.DataFrame
        DataFrame with high correlation pairs
    iv_summary : pd.DataFrame, optional
        IV summary DataFrame with 'variable' and 'IV' columns
    corr_threshold_high : float
        High correlation threshold (default: 0.98)
    corr_threshold_medium : float
        Medium correlation threshold (default: 0.95)
    iv_threshold : float
        IV threshold (default: 0.02)
    
    Returns:
    --------
    list : List of variable names to drop
    """
    vars_to_drop = []
    
    if iv_summary is not None:
        iv_dict = dict(zip(iv_summary['variable'], iv_summary['IV']))
    else:
        iv_dict = {}
    
    for _, row in high_corr_pairs.iterrows():
        var2 = row['var2']
        corr_value = row['corr_value']
        
        # Drop if correlation > high threshold
        if corr_value > corr_threshold_high:
            if var2 not in vars_to_drop:
                vars_to_drop.append(var2)
        # Drop if correlation > medium threshold AND IV < threshold
        elif corr_value > corr_threshold_medium:
            iv_value = iv_dict.get(var2, 0)
            if iv_value < iv_threshold:
                if var2 not in vars_to_drop:
                    vars_to_drop.append(var2)
    
    return vars_to_drop


def apply_correlation_filter(
    df: pd.DataFrame,
    vars_to_drop: List[str]
) -> pd.DataFrame:
    """
    Apply correlation filter by dropping specified variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    vars_to_drop : list
        List of variable names to drop
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe
    """
    return df.drop(columns=vars_to_drop, errors='ignore')


def calculate_vif(
    df: pd.DataFrame,
    target_col: str = 'default_flag',
    exclude_vars: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target_col : str
        Target column name (default: 'default_flag')
    exclude_vars : list, optional
        List of variables to exclude from VIF calculation
    
    Returns:
    --------
    pd.DataFrame : DataFrame with 'variable' and 'VIF' columns
    """
    # Get numeric variables excluding target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col != target_col]
    
    # Further exclude specified variables
    if exclude_vars:
        exclude_vars_upper = [var.upper() for var in exclude_vars]
        feature_cols = [col for col in feature_cols 
                       if col.upper() not in exclude_vars_upper]
    
    # Prepare data for VIF calculation
    X = df[feature_cols].copy()
    
    # Handle missing values
    X = X.fillna(X.mean())
    
    # Add constant for statsmodels
    try:
        X_const = add_constant(X)
        vif_data = pd.DataFrame()
        vif_data['variable'] = X.columns
        vif_data['VIF'] = [variance_inflation_factor(X_const.values, i + 1) 
                          for i in range(len(X.columns))]
    except Exception as e:
        # If VIF calculation fails, return empty DataFrame
        vif_data = pd.DataFrame(columns=['variable', 'VIF'])
    
    return vif_data


def identify_vars_to_drop_vif(
    vif_df: pd.DataFrame,
    vif_threshold: float = 10.0,
    exclude_vars: Optional[List[str]] = None
) -> List[str]:
    """
    Identify variables with VIF above threshold to drop.
    Excludes specified key variables from dropping.
    
    Parameters:
    -----------
    vif_df : pd.DataFrame
        DataFrame with 'variable' and 'VIF' columns
    vif_threshold : float
        VIF threshold (default: 10.0)
    exclude_vars : list, optional
        List of key variables to exclude from dropping
    
    Returns:
    --------
    list : List of variable names to drop
    """
    if exclude_vars is None:
        exclude_vars = [
            'bureau_score', 'salary_credit_3m', 'emi_to_income_ratio',
            'dpd_max', 'dpd_count_30_plus', 'utilization_score',
            'balance_utilization_score', 'age', 'employment_type',
            'education_level', 'marital_status', 'risk_score'
        ]
    
    exclude_vars_upper = [var.upper() for var in exclude_vars]
    
    vars_to_drop = vif_df[
        (vif_df['VIF'] > vif_threshold) &
        (~vif_df['variable'].str.upper().isin(exclude_vars_upper))
    ]['variable'].tolist()
    
    return vars_to_drop


def apply_vif_filter(
    df: pd.DataFrame,
    vars_to_drop: List[str]
) -> pd.DataFrame:
    """
    Apply VIF filter by dropping specified variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    vars_to_drop : list
        List of variable names to drop
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe
    """
    return df.drop(columns=vars_to_drop, errors='ignore')


def create_final_keep_list() -> List[str]:
    """
    Create final keep list of variables.
    
    Returns:
    --------
    list : List of variable names to keep
    """
    keep_list = [
        "account_open_date", "account_tenure_months", "age",
        "amount_income_term_score", "annual_interest_rate",
        "application_date", "avg_combined_score",
        "balance_utilization_score", "behavior_score_gap", "bureau_score",
        "credit_card_utilization_pct", "default_flag", "dpd_count_30_plus",
        "dpd_max", "dpd_recent_flag", "emi_to_income_ratio", "employment_type",
        "loan_size_score", "overdue_normalized", "pos_transaction_volume",
        "recovery_success_flag", "risk_score", "tenure_months"
    ]
    return keep_list


def apply_final_keep_list_filter(
    df: pd.DataFrame,
    keep_list: List[str]
) -> pd.DataFrame:
    """
    Apply final keep list filter - keep only variables in the keep list
    that exist in the dataframe, plus the target variable.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    keep_list : list
        List of variable names to keep
    
    Returns:
    --------
    pd.DataFrame : Filtered dataframe with only kept variables
    """
    # Find variables in keep_list that exist in dataframe
    available_vars = [var for var in keep_list if var in df.columns]
    
    # Always include target if it exists
    target_col = 'default_flag'
    if target_col in df.columns and target_col not in available_vars:
        available_vars.append(target_col)
    
    return df[available_vars].copy()


def run_full_collinearity_analysis(
    df: pd.DataFrame,
    iv_summary: Optional[pd.DataFrame] = None,
    target_col: str = 'default_flag'
) -> Tuple[pd.DataFrame, dict]:
    """
    Run full collinearity analysis pipeline.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    iv_summary : pd.DataFrame, optional
        IV summary DataFrame with 'variable' and 'IV' columns
    target_col : str
        Target column name (default: 'default_flag')
    
    Returns:
    --------
    tuple : (filtered_dataframe, results_dict)
        filtered_dataframe: Final filtered dataframe
        results_dict: Dictionary with intermediate results
    """
    results = {}
    
    # Step 1: Correlation filtering
    corr_matrix = calculate_correlation_matrix(df)
    high_corr_pairs = find_high_correlation_pairs(corr_matrix, threshold=0.90)
    vars_to_drop_corr = identify_vars_to_drop_correlation(
        high_corr_pairs, iv_summary=iv_summary
    )
    df_corr_filtered = apply_correlation_filter(df, vars_to_drop_corr)
    
    results['correlation'] = {
        'corr_matrix': corr_matrix,
        'high_corr_pairs': high_corr_pairs,
        'vars_dropped': vars_to_drop_corr,
        'filtered_df': df_corr_filtered
    }
    
    # Step 2: VIF filtering
    vif_df = calculate_vif(df_corr_filtered, target_col=target_col)
    vars_to_drop_vif = identify_vars_to_drop_vif(vif_df, vif_threshold=10.0)
    df_vif_filtered = apply_vif_filter(df_corr_filtered, vars_to_drop_vif)
    
    results['vif'] = {
        'vif_df': vif_df,
        'vars_dropped': vars_to_drop_vif,
        'filtered_df': df_vif_filtered
    }
    
    # Step 3: Final keep list filter
    keep_list = create_final_keep_list()
    df_final = apply_final_keep_list_filter(df_vif_filtered, keep_list)
    
    results['final'] = {
        'keep_list': keep_list,
        'final_df': df_final
    }
    
    return df_final, results

