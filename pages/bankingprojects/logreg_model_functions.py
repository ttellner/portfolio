"""
Functions for Logistic Regression Model Analysis.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from scipy.stats import ks_2samp
from typing import Tuple, Dict, List, Optional


def prepare_model_data(df: pd.DataFrame, target_col: str = 'default_flag') -> pd.DataFrame:
    """
    Prepare data for modeling: standardize dpd_max, remove problematic variables,
    and adjust dpd_max to avoid quasi-separation.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target_col : str
        Target column name
        
    Returns:
    --------
    pd.DataFrame : Prepared dataframe
    """
    df_prep = df.copy()
    
    # Standardize dpd_max if it exists
    if 'dpd_max' in df_prep.columns:
        scaler = StandardScaler()
        df_prep['dpd_max'] = scaler.fit_transform(df_prep[['dpd_max']])
    
    # Remove problematic variables
    vars_to_drop = ['emi_to_income_ratio', 'dpd_count_30_plus']
    vars_to_drop = [v for v in vars_to_drop if v in df_prep.columns]
    df_prep = df_prep.drop(columns=vars_to_drop, errors='ignore')
    
    # Adjust dpd_max to avoid quasi-separation (add small random noise)
    if 'dpd_max' in df_prep.columns:
        np.random.seed(12345)
        df_prep['dpd_max_adj'] = df_prep['dpd_max'] + (np.random.uniform(size=len(df_prep)) * 0.01)
        df_prep = df_prep.drop(columns=['dpd_max'], errors='ignore')
    elif 'dpd_max_adj' not in df_prep.columns:
        # If dpd_max doesn't exist, create a placeholder
        np.random.seed(12345)
        df_prep['dpd_max_adj'] = np.random.uniform(size=len(df_prep)) * 0.01
    
    return df_prep


def split_train_validation(df: pd.DataFrame, test_size: float = 0.3, 
                           random_state: int = 12345) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and validation sets.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    test_size : float
        Proportion of data for validation (default 0.3)
    random_state : int
        Random seed
        
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame] : (train_df, valid_df)
    """
    train_df, valid_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=random_state,
        stratify=df['default_flag'] if 'default_flag' in df.columns else None
    )
    return train_df.reset_index(drop=True), valid_df.reset_index(drop=True)


def train_stepwise_logistic(train_df: pd.DataFrame, target_col: str = 'default_flag',
                            categorical_cols: Optional[List[str]] = None) -> Dict:
    """
    Train stepwise logistic regression model (using all available variables).
    Note: True stepwise selection requires specialized libraries. This function
    trains a logistic model with all available variables.
    
    Parameters:
    -----------
    train_df : pd.DataFrame
        Training dataframe
    target_col : str
        Target column name
    categorical_cols : list, optional
        List of categorical columns (not used in this simplified version)
        
    Returns:
    --------
    dict : Dictionary containing model and selected features
    """
    # Get all numeric columns except target
    feature_cols = [col for col in train_df.select_dtypes(include=[np.number]).columns 
                   if col != target_col]
    
    # Prepare features and target
    X = train_df[feature_cols].fillna(0)
    y = train_df[target_col]
    
    # Train logistic regression model
    model = LogisticRegression(max_iter=1000, random_state=12345)
    model.fit(X, y)
    
    # Get feature importance (coefficients)
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'coefficient': model.coef_[0],
        'abs_coefficient': np.abs(model.coef_[0])
    }).sort_values('abs_coefficient', ascending=False)
    
    return {
        'model': model,
        'feature_cols': feature_cols,
        'feature_importance': feature_importance
    }


def train_final_logistic(train_df: pd.DataFrame, feature_cols: List[str],
                         target_col: str = 'default_flag') -> Dict:
    """
    Train final logistic regression model with specified features.
    
    Parameters:
    -----------
    train_df : pd.DataFrame
        Training dataframe
    feature_cols : list
        List of feature columns to use
    target_col : str
        Target column name
        
    Returns:
    --------
    dict : Dictionary containing model
    """
    # Filter to only existing columns
    available_cols = [col for col in feature_cols if col in train_df.columns]
    
    if len(available_cols) == 0:
        raise ValueError("No specified features found in dataframe")
    
    # Prepare features and target
    X = train_df[available_cols].fillna(0)
    y = train_df[target_col]
    
    # Train logistic regression model
    model = LogisticRegression(max_iter=1000, random_state=12345)
    model.fit(X, y)
    
    return {
        'model': model,
        'feature_cols': available_cols
    }


def score_data(df: pd.DataFrame, model: LogisticRegression, feature_cols: List[str],
               target_col: str = 'default_flag', prior_event: float = 0.07) -> pd.DataFrame:
    """
    Score data using trained model.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe to score
    model : LogisticRegression
        Trained model
    feature_cols : list
        Feature columns
    target_col : str
        Target column name
    prior_event : float
        Prior event probability (used for calibration, default 0.07)
        
    Returns:
    --------
    pd.DataFrame : Scored dataframe with predictions
    """
    df_scored = df.copy()
    
    # Prepare features
    available_cols = [col for col in feature_cols if col in df_scored.columns]
    X = df_scored[available_cols].fillna(0)
    
    # Get predictions (probability of class 1)
    prob_default = model.predict_proba(X)[:, 1]
    df_scored['P_1'] = prob_default
    
    return df_scored


def create_deciles(df_scored: pd.DataFrame, prob_col: str = 'P_1') -> pd.DataFrame:
    """
    Create deciles based on predicted probability.
    
    Parameters:
    -----------
    df_scored : pd.DataFrame
        Scored dataframe
    prob_col : str
        Probability column name
        
    Returns:
    --------
    pd.DataFrame : Dataframe with decile column
    """
    df_deciles = df_scored.copy()
    df_deciles['decile'] = pd.qcut(df_deciles[prob_col], q=10, labels=False, duplicates='drop')
    return df_deciles


def calculate_performance_summary(df_deciles: pd.DataFrame, target_col: str = 'default_flag',
                                  prob_col: str = 'P_1') -> pd.DataFrame:
    """
    Calculate performance summary by decile.
    
    Parameters:
    -----------
    df_deciles : pd.DataFrame
        Dataframe with deciles
    target_col : str
        Target column name
    prob_col : str
        Probability column name
        
    Returns:
    --------
    pd.DataFrame : Performance summary by decile
    """
    perf_summary = df_deciles.groupby('decile').agg({
        target_col: ['count', 'sum', 'mean'],
        prob_col: 'mean'
    }).reset_index()
    
    perf_summary.columns = ['decile', 'total_obs', 'defaults', 'default_rate', 'avg_pred_prob']
    
    return perf_summary.sort_values('decile')


def calculate_roc_stats(df_scored: pd.DataFrame, target_col: str = 'default_flag',
                        prob_col: str = 'P_1') -> Dict:
    """
    Calculate ROC statistics (AUC).
    
    Parameters:
    -----------
    df_scored : pd.DataFrame
        Scored dataframe
    target_col : str
        Target column name
    prob_col : str
        Probability column name
        
    Returns:
    --------
    dict : Dictionary with ROC statistics
    """
    y_true = df_scored[target_col]
    y_pred = df_scored[prob_col]
    
    auc = roc_auc_score(y_true, y_pred)
    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    
    return {
        'auc': auc,
        'fpr': fpr,
        'tpr': tpr,
        'thresholds': thresholds
    }


def calculate_ks_statistic(df_scored: pd.DataFrame, target_col: str = 'default_flag',
                           prob_col: str = 'P_1') -> Dict:
    """
    Calculate Kolmogorov-Smirnov (KS) statistic.
    
    Parameters:
    -----------
    df_scored : pd.DataFrame
        Scored dataframe
    target_col : str
        Target column name
    prob_col : str
        Probability column name
        
    Returns:
    --------
    dict : Dictionary with KS statistics
    """
    good = df_scored[df_scored[target_col] == 0][prob_col]
    bad = df_scored[df_scored[target_col] == 1][prob_col]
    
    ks_statistic, p_value = ks_2samp(good, bad)
    
    return {
        'ks_statistic': ks_statistic,
        'p_value': p_value
    }

