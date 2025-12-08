"""
Data Preprocessing Module
Handles data cleaning, WOE calculation, and data transformation.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

# Try to import SMOTE from imbalanced-learn
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    # Note: Error handling is done in main.py when SMOTE is actually used


def clean_data(df, imputation_dict=None):
    """
    Clean and impute missing values in the dataset.
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe with raw data
    imputation_dict : dict, optional
        Dictionary mapping column names to imputation values.
        If None, uses default strategy (median for numeric, mode for categorical)
    
    Returns:
    --------
    DataFrame : Cleaned dataframe
    """
    df_clean = df.copy()
    
    # If imputation_dict is provided, use it
    if imputation_dict is not None:
        for col, value in imputation_dict.items():
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(value)
    else:
        # Default imputation strategy: median for numeric, mode for categorical
        for col in df_clean.columns:
            if df_clean[col].isna().any():
                if df_clean[col].dtype in ['int64', 'float64']:
                    # Use median for numeric columns
                    median_val = df_clean[col].median()
                    if pd.notna(median_val):
                        df_clean[col] = df_clean[col].fillna(median_val)
                    else:
                        # If all values are NaN, fill with 0
                        df_clean[col] = df_clean[col].fillna(0)
                else:
                    # Use mode for categorical columns
                    mode_val = df_clean[col].mode()
                    if len(mode_val) > 0:
                        df_clean[col] = df_clean[col].fillna(mode_val[0])
    
    return df_clean


def calculate_woe_iv(df, var, target='default_12m', n_bins=6):
    """
    Calculate WOE (Weight of Evidence) and IV (Information Value) for a variable.
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe
    var : str
        Variable name to calculate WOE for
    target : str
        Target variable name (default: 'default_12m')
    n_bins : int
        Number of bins for discretization (default: 6)
    
    Returns:
    --------
    tuple : (woe_table, total_iv)
        woe_table: DataFrame with WOE values by bin
        total_iv: Total Information Value
    """
    # Bin the variable
    df_binned = df.copy()
    df_binned[f'{var}_bin'] = pd.qcut(
        df_binned[var], q=n_bins, labels=False, duplicates='drop'
    )
    
    # Calculate frequencies
    freq_table = df_binned.groupby([f'{var}_bin', target]).size().unstack(
        fill_value=0
    )
    
    if 0 not in freq_table.columns:
        freq_table[0] = 0
    if 1 not in freq_table.columns:
        freq_table[1] = 1
    
    freq_table.columns = ['good', 'bad']
    
    # Calculate distributions
    total_good = freq_table['good'].sum()
    total_bad = freq_table['bad'].sum()
    
    if total_good == 0 or total_bad == 0:
        return None, 0
    
    freq_table['dist_good'] = (freq_table['good'] + 0.5) / (total_good + 3.0)
    freq_table['dist_bad'] = (freq_table['bad'] + 0.5) / (total_bad + 3.0)
    
    # Calculate WOE and IV
    freq_table['woe'] = np.log(freq_table['dist_good'] / freq_table['dist_bad'])
    freq_table['iv'] = (
        (freq_table['dist_good'] - freq_table['dist_bad']) * freq_table['woe']
    )
    
    total_iv = freq_table['iv'].sum()
    
    return freq_table, total_iv


def calculate_woe_mappings(df, vars_to_bin, target='default_12m', n_bins=6):
    """
    Calculate WOE mappings for multiple variables.
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe
    vars_to_bin : list
        List of variable names to calculate WOE for
    target : str
        Target variable name
    n_bins : int
        Number of bins for discretization
    
    Returns:
    --------
    dict : Dictionary mapping variable names to WOE tables
    """
    woe_mappings = {}
    
    for var in vars_to_bin:
        if var in df.columns:
            woe_table, iv = calculate_woe_iv(df, var, target, n_bins)
            if woe_table is not None:
                woe_mappings[var] = woe_table
                print(f"IV for {var}: {iv:.4f}")
    
    return woe_mappings


def apply_woe_transformation(df, woe_mappings, vars_to_bin, n_bins=6):
    """
    Apply WOE transformation to dataframe.
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe
    woe_mappings : dict
        Dictionary of WOE mappings (from calculate_woe_mappings)
    vars_to_bin : list
        List of variable names that were binned
    n_bins : int
        Number of bins used (for new data, use len of woe_table)
    
    Returns:
    --------
    DataFrame : Dataframe with WOE transformed columns
    """
    df_woe = df.copy()
    
    for var in vars_to_bin:
        if var in df_woe.columns and var in woe_mappings:
            woe_table = woe_mappings[var]
            # For new data, use the number of bins from the woe_table
            n_bins_actual = len(woe_table) if hasattr(woe_table, '__len__') else n_bins
            
            df_woe[f'{var}_bin'] = pd.qcut(
                df_woe[var], q=n_bins_actual, labels=False, duplicates='drop'
            )
            
            df_woe = df_woe.merge(
                woe_table[['woe']].reset_index(),
                left_on=f'{var}_bin',
                right_on=f'{var}_bin',
                how='left',
                suffixes=('', '_woe')
            )
            df_woe[f'{var}_woe'] = df_woe['woe']
            df_woe = df_woe.drop(
                columns=[f'{var}_bin', 'woe'], errors='ignore'
            )
    
    return df_woe


def prepare_training_data(df, vars_to_bin, target='default_12m', n_bins=6):
    """
    Complete preprocessing pipeline for training data.
    
    Parameters:
    -----------
    df : DataFrame
        Raw training dataframe
    vars_to_bin : list
        List of variables to bin and transform
    target : str
        Target variable name
    n_bins : int
        Number of bins for discretization
    
    Returns:
    --------
    tuple : (cleaned_df, woe_mappings, df_woe)
        cleaned_df: Cleaned dataframe
        woe_mappings: WOE transformation mappings
        df_woe: WOE transformed dataframe ready for modeling
    """
    # Clean data
    cleaned_df = clean_data(df)
    
    # Calculate WOE mappings
    woe_mappings = calculate_woe_mappings(
        cleaned_df, vars_to_bin, target, n_bins
    )
    
    # Apply WOE transformation
    df_woe = apply_woe_transformation(
        cleaned_df, woe_mappings, vars_to_bin, n_bins
    )
    
    return cleaned_df, woe_mappings, df_woe


def apply_smote(df_woe, vars_to_bin, target='default_12m', 
                random_state=42, k_neighbors=5):
    """
    Apply SMOTE oversampling to WOE-transformed data.
    This should be called AFTER WOE transformation and BEFORE model training.
    
    Parameters:
    -----------
    df_woe : DataFrame
        WOE transformed dataframe
    vars_to_bin : list
        List of variables that were binned (to find WOE columns)
    target : str
        Target variable name
    random_state : int
        Random state for reproducibility
    k_neighbors : int
        Number of nearest neighbors for SMOTE
    
    Returns:
    --------
    DataFrame : Oversampled WOE dataframe
    """
    if not SMOTE_AVAILABLE:
        raise ImportError(
            "SMOTE not available. Install imbalanced-learn: "
            "pip install imbalanced-learn"
        )
    
    # Get WOE variable names
    woe_vars = [f'{var}_woe' for var in vars_to_bin 
                if f'{var}_woe' in df_woe.columns]
    
    if len(woe_vars) == 0:
        raise ValueError("No WOE variables found in dataframe")
    
    if target not in df_woe.columns:
        raise ValueError(f"Target variable '{target}' not found in dataframe")
    
    # Extract features and target
    X = df_woe[woe_vars].fillna(0).values
    y = df_woe[target].values
    
    # Check if dataset is imbalanced
    unique, counts = np.unique(y, return_counts=True)
    class_counts = dict(zip(unique, counts))
    
    print(f"\n   Class distribution before SMOTE:")
    for cls, count in class_counts.items():
        print(f"     Class {cls}: {count} ({count/len(y)*100:.2f}%)")
    
    # Apply SMOTE - catch compatibility errors early
    try:
        smote = SMOTE(random_state=random_state, k_neighbors=k_neighbors)
        X_resampled, y_resampled = smote.fit_resample(X, y)
    except AttributeError as e:
        error_str = str(e)
        if '_validate_data' in error_str:
            # Raise a clear compatibility error that will be caught in main.py
            raise AttributeError(
                "SMOTE compatibility error (_validate_data): Version mismatch. "
                "Update packages: pip install --upgrade scikit-learn imbalanced-learn"
            ) from e
        else:
            raise
    except Exception as e:
        # Catch any other SMOTE-related errors
        error_str = str(e)
        if 'SMOTE' in error_str or 'imbalanced' in error_str.lower():
            raise AttributeError(
                f"SMOTE error: {error_str}. "
                "This may be a compatibility issue. "
                "Try: pip install --upgrade scikit-learn imbalanced-learn"
            ) from e
        else:
            raise
    
    # Check class distribution after SMOTE
    unique_after, counts_after = np.unique(y_resampled, return_counts=True)
    class_counts_after = dict(zip(unique_after, counts_after))
    
    print(f"\n   Class distribution after SMOTE:")
    for cls, count in class_counts_after.items():
        print(f"     Class {cls}: {count} ({count/len(y_resampled)*100:.2f}%)")
    
    # Create oversampled dataframe
    df_resampled = pd.DataFrame(X_resampled, columns=woe_vars)
    df_resampled[target] = y_resampled
    
    # Add any other columns from original dataframe (if needed for consistency)
    # Keep only WOE columns and target for modeling
    return df_resampled


def prepare_scoring_data(df, woe_mappings, vars_to_bin):
    """
    Preprocess data for scoring (new applicants).
    
    Parameters:
    -----------
    df : DataFrame
        Raw dataframe for scoring
    woe_mappings : dict
        WOE mappings from training data
    vars_to_bin : list
        List of variables that were binned in training
    
    Returns:
    --------
    DataFrame : WOE transformed dataframe ready for scoring
    """
    # Clean data
    cleaned_df = clean_data(df)
    
    # Apply WOE transformation using training mappings
    df_woe = apply_woe_transformation(
        cleaned_df, woe_mappings, vars_to_bin
    )
    
    return df_woe


def convert_to_image_grid(df, feature_columns=None, grid_size=28, 
                          normalize=True, fill_method='zero', exclude_columns=None):
    """
    Convert tabular data to 28x28 image grid format for CNN.
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe with features
    feature_columns : list, optional
        List of column names to use as features. If None, uses all numeric columns.
    grid_size : int
        Size of the grid (default: 28 for 28x28)
    normalize : bool
        Whether to normalize features to [0, 1] range (default: True)
    fill_method : str
        Method to fill grid if features < grid_size^2: 'zero', 'mean', 'repeat'
    exclude_columns : list, optional
        List of column names to exclude from features (e.g., target column)
    
    Returns:
    --------
    numpy.ndarray : Array of shape (n_samples, grid_size, grid_size, 1) for CNN input
    """
    # Select feature columns
    if feature_columns is None:
        # Use all numeric columns (target will be excluded in prepare_cnn_data)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_columns = numeric_cols
    
    # Exclude specified columns (e.g., target column)
    if exclude_columns:
        feature_columns = [col for col in feature_columns if col not in exclude_columns]
    
    # Filter to only columns that exist in dataframe
    feature_columns = [col for col in feature_columns if col in df.columns]
    
    if len(feature_columns) == 0:
        raise ValueError(
            "No valid feature columns found in dataframe after filtering. "
            f"Available columns: {list(df.columns)[:20]}"
        )
    
    # Extract features
    X = df[feature_columns].fillna(0).values
    
    # Normalize if requested
    if normalize:
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
    
    n_samples, n_features = X.shape
    grid_total = grid_size * grid_size
    
    # Reshape features to grid
    images = []
    for i in range(n_samples):
        features = X[i]
        
        if n_features >= grid_total:
            # Truncate if more features than grid size
            grid_data = features[:grid_total]
        else:
            # Fill if fewer features than grid size
            grid_data = np.zeros(grid_total)
            grid_data[:n_features] = features
            
            if fill_method == 'mean':
                # Fill remaining with mean of features
                grid_data[n_features:] = np.mean(features)
            elif fill_method == 'repeat':
                # Repeat features to fill
                n_repeats = (grid_total - n_features) // n_features + 1
                repeated = np.tile(features, n_repeats)
                grid_data = repeated[:grid_total]
            # 'zero' is already handled above
        
        # Reshape to grid
        grid_2d = grid_data.reshape(grid_size, grid_size)
        images.append(grid_2d)
    
    # Convert to numpy array and add channel dimension
    images_array = np.array(images)
    images_array = images_array.reshape(n_samples, grid_size, grid_size, 1)
    
    return images_array


def prepare_cnn_data(df, feature_columns=None, target='default_12m', 
                     grid_size=28, normalize=True):
    """
    Prepare data for CNN model (28x28 grid format).
    
    Parameters:
    -----------
    df : DataFrame
        Input dataframe
    feature_columns : list, optional
        List of column names to use as features
    target : str
        Target variable name
    grid_size : int
        Size of the grid (default: 28)
    normalize : bool
        Whether to normalize features
    
    Returns:
    --------
    tuple : (X_images, y)
        X_images: Image array (n_samples, grid_size, grid_size, 1)
        y: Target array
    """
    # Clean data first
    cleaned_df = clean_data(df)
    
    # Verify target column exists
    if target not in cleaned_df.columns:
        available_cols = list(cleaned_df.columns)
        raise ValueError(
            f"Target variable '{target}' not found in dataframe columns. "
            f"Available columns: {available_cols[:10]}{'...' if len(available_cols) > 10 else ''}"
        )
    
    # Ensure target is excluded from feature_columns if it's there
    if feature_columns is not None:
        feature_columns = [col for col in feature_columns if col != target]
        if len(feature_columns) == 0:
            raise ValueError(
                "No feature columns available after excluding target. "
                "Please ensure feature_columns contains columns other than the target."
            )
    
    # Convert to image grid (this should not include target)
    X_images = convert_to_image_grid(
        cleaned_df, 
        feature_columns=feature_columns,
        grid_size=grid_size,
        normalize=normalize,
        exclude_columns=[target]  # Explicitly exclude target column
    )
    
    # Extract target
    y = cleaned_df[target].values
    # Ensure y is 1D for CNN (flatten if needed)
    if y.ndim > 1:
        y = y.flatten()
    
    # Verify y has the same length as X_images
    if len(y) != len(X_images):
        raise ValueError(
            f"Target length ({len(y)}) does not match image array length ({len(X_images)})"
        )
    
    return X_images, y

