"""
Model Training and Scoring Module
Flexible model interface for different model types.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
import warnings
import os
warnings.filterwarnings('ignore')

# Suppress TensorFlow oneDNN messages
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress INFO and WARNING messages

# Try to import TensorFlow/Keras for CNN
try:
    import tensorflow as tf
    # Set TensorFlow logging level to suppress INFO messages
    tf.get_logger().setLevel('ERROR')
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Warning: TensorFlow not available. CNN model will not work.")
    print("Install with: pip install tensorflow")


class ScorecardModel:
    """
    Base class for scorecard models.
    Provides interface for training and scoring.
    """
    
    def __init__(self, model_type='logistic', **model_params):
        """
        Initialize scorecard model.
        
        Parameters:
        -----------
        model_type : str
            Type of model ('logistic', 'random_forest', 'gradient_boosting', 'decision_tree')
        **model_params : dict
            Additional parameters for the model
        """
        self.model_type = model_type
        self.model = self._create_model(model_type, **model_params)
        self.is_trained = False
        self.feature_names = None  # Store feature names used during training
    
    def _create_model(self, model_type, **params):
        """Create model instance based on type."""
        if model_type == 'logistic':
            return LogisticRegression(
                max_iter=params.get('max_iter', 1000),
                random_state=params.get('random_state', 42),
                **{k: v for k, v in params.items() 
                   if k not in ['max_iter', 'random_state']}
            )
        elif model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=params.get('n_estimators', 100),
                random_state=params.get('random_state', 42),
                **{k: v for k, v in params.items() 
                   if k not in ['n_estimators', 'random_state']}
            )
        elif model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=params.get('n_estimators', 100),
                random_state=params.get('random_state', 42),
                **{k: v for k, v in params.items() 
                   if k not in ['n_estimators', 'random_state']}
            )
        elif model_type == 'decision_tree':
            return DecisionTreeClassifier(
                random_state=params.get('random_state', 42),
                **{k: v for k, v in params.items() 
                   if k not in ['random_state']}
            )
        elif model_type == 'cnn':
            if not TF_AVAILABLE:
                raise ImportError(
                    "TensorFlow is required for CNN model. "
                    "Install with: pip install tensorflow"
                )
            return self._create_cnn_model(**params)
        else:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Choose from: logistic, random_forest, gradient_boosting, "
                f"decision_tree, cnn"
            )
    
    def _create_cnn_model(self, **params):
        """Create CNN model for 28x28 image input."""
        input_shape = (28, 28, 1)
        
        model = keras.Sequential([
            # First convolutional block
            layers.Conv2D(
                filters=params.get('filters_1', 32),
                kernel_size=params.get('kernel_size_1', 3),
                activation='relu',
                input_shape=input_shape
            ),
            layers.MaxPooling2D(pool_size=params.get('pool_size_1', 2)),
            layers.Dropout(params.get('dropout_1', 0.25)),
            
            # Second convolutional block
            layers.Conv2D(
                filters=params.get('filters_2', 64),
                kernel_size=params.get('kernel_size_2', 3),
                activation='relu'
            ),
            layers.MaxPooling2D(pool_size=params.get('pool_size_2', 2)),
            layers.Dropout(params.get('dropout_2', 0.25)),
            
            # Flatten and dense layers
            layers.Flatten(),
            layers.Dense(
                units=params.get('dense_units', 128),
                activation='relu'
            ),
            layers.Dropout(params.get('dropout_3', 0.5)),
            layers.Dense(units=1, activation='sigmoid')  # Binary classification
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(
                learning_rate=params.get('learning_rate', 0.001)
            ),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X, y, **fit_params):
        """
        Train the model.
        
        Parameters:
        -----------
        X : DataFrame or array
            Feature matrix (WOE transformed) or image array for CNN
        y : Series or array
            Target variable
        **fit_params : dict
            Additional parameters for training (e.g., epochs, batch_size for CNN)
        """
        if self.model_type == 'cnn':
            # CNN requires different training approach
            epochs = fit_params.get('epochs', 10)
            batch_size = fit_params.get('batch_size', 32)
            validation_split = fit_params.get('validation_split', 0.2)
            verbose = fit_params.get('verbose', 1)
            
            # Ensure y is 1D numpy array for CNN training
            if isinstance(y, pd.Series):
                y = y.values
            y = np.asarray(y)
            if y.ndim > 1:
                y = y.flatten()
            
            self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=verbose
            )
        else:
            # Standard sklearn models
            self.model.fit(X, y)
        
        self.is_trained = True
    
    def predict_proba(self, X):
        """
        Predict probabilities.
        
        Parameters:
        -----------
        X : DataFrame or array
            Feature matrix or image array
        
        Returns:
        --------
        array : Probability predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        if self.model_type == 'cnn':
            # CNN returns probabilities directly (shape: n_samples, 1)
            predictions = self.model.predict(X, verbose=0)
            # Flatten to 1D if needed, then stack for sklearn format
            if predictions.ndim > 1:
                predictions = predictions.flatten()
            # Return in same format as sklearn (2D array with probabilities)
            prob_0 = 1 - predictions
            prob_1 = predictions
            return np.column_stack([prob_0, prob_1])
        else:
            # Standard sklearn models
            return self.model.predict_proba(X)
    
    def predict(self, X):
        """
        Predict classes.
        
        Parameters:
        -----------
        X : DataFrame or array
            Feature matrix
        
        Returns:
        --------
        array : Class predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)


def train_model(df_woe, vars_to_bin, target='default_12m', 
                model_type='logistic', feature_columns=None, use_woe=True, **model_params):
    """
    Train a scorecard model.
    
    Parameters:
    -----------
    df_woe : DataFrame or tuple
        WOE transformed dataframe OR raw dataframe OR (X_images, y) tuple for CNN
    vars_to_bin : list
        List of variables that were binned (for WOE) or feature columns (for raw data)
    target : str
        Target variable name (not used for CNN if df_woe is tuple)
    model_type : str
        Type of model to use
    feature_columns : list, optional
        Feature columns for CNN (if None, uses all numeric)
    use_woe : bool
        Whether data is WOE transformed (True) or raw (False)
    **model_params : dict
        Additional parameters for the model and training
    
    Returns:
    --------
    ScorecardModel : Trained model object
    """
    if model_type == 'cnn':
        # CNN uses image data
        if isinstance(df_woe, tuple):
            # Already converted to images
            X, y = df_woe
        else:
            # Need to convert dataframe to images
            from .preprocessing import prepare_cnn_data
            X, y = prepare_cnn_data(
                df_woe, 
                feature_columns=feature_columns,
                target=target,
                grid_size=28
            )
    else:
        # Standard models - can use WOE or raw data
        if target not in df_woe.columns:
            raise ValueError(
                f"Target variable '{target}' not found in dataframe"
            )
        
        if use_woe:
            # Get WOE variable names
            woe_vars = [f'{var}_woe' for var in vars_to_bin 
                        if f'{var}_woe' in df_woe.columns]
            
            if len(woe_vars) == 0:
                raise ValueError("No WOE variables found in dataframe")
            
            # Prepare features and target
            X = df_woe[woe_vars].fillna(0).values
            y = df_woe[target].values
            
            # Store feature names for later use in scoring
            feature_names = woe_vars
        else:
            # Use raw numeric columns
            # If vars_to_bin is provided, use those columns; otherwise use all numeric
            if vars_to_bin and len(vars_to_bin) > 0:
                feature_cols = [col for col in vars_to_bin if col in df_woe.columns]
            else:
                # Use all numeric columns except target
                numeric_cols = df_woe.select_dtypes(include=[np.number]).columns.tolist()
                feature_cols = [col for col in numeric_cols if col != target]
            
            if len(feature_cols) == 0:
                raise ValueError("No feature columns found in dataframe")
            
            # Prepare features and target
            X = df_woe[feature_cols].fillna(0).values
            y = df_woe[target].values
            
            # Store feature names for later use in scoring
            feature_names = feature_cols
    
    # Create and train model
    # Separate training params from model params
    training_params = {
        k: v for k, v in model_params.items() 
        if k in ['epochs', 'batch_size', 'validation_split', 'verbose']
    }
    model_params_clean = {
        k: v for k, v in model_params.items() 
        if k not in ['epochs', 'batch_size', 'validation_split', 'verbose']
    }
    
    model = ScorecardModel(model_type=model_type, **model_params_clean)
    model.train(X, y, **training_params)
    
    # Store feature names for non-CNN models
    if model_type != 'cnn':
        model.feature_names = feature_names
    
    return model


def score_data(df_woe, model, vars_to_bin, feature_columns=None, use_woe=True):
    """
    Score data using trained model.
    
    Parameters:
    -----------
    df_woe : DataFrame or numpy array
        WOE transformed dataframe OR raw dataframe OR image array for CNN
    model : ScorecardModel
        Trained model object
    vars_to_bin : list
        List of variables that were binned (for WOE) or feature columns (for raw data)
    feature_columns : list, optional
        Feature columns for CNN (if None, uses all numeric)
    use_woe : bool
        Whether data is WOE transformed (True) or raw (False)
    
    Returns:
    --------
    DataFrame or numpy array : Data with probability predictions added
    """
    if model.model_type == 'cnn':
        # CNN uses image data
        if isinstance(df_woe, np.ndarray):
            # Already converted to images
            X = df_woe
        else:
            # Need to convert dataframe to images
            from .preprocessing import convert_to_image_grid
            X = convert_to_image_grid(
                df_woe,
                feature_columns=feature_columns,
                grid_size=28,
                normalize=True
            )
        
        # Predict probabilities
        prob_col_name = 'prob' if isinstance(df_woe, pd.DataFrame) else None
        predictions = model.predict_proba(X)
        
        # Extract probability of positive class (default) - second column
        if predictions.ndim == 2 and predictions.shape[1] == 2:
            prob_default = predictions[:, 1]
        else:
            # If already 1D, use as is
            prob_default = predictions.flatten() if predictions.ndim > 1 else predictions
        
        if isinstance(df_woe, pd.DataFrame):
            df_scored = df_woe.copy()
            df_scored[prob_col_name] = prob_default
            # Ensure all original columns are preserved (including target if it exists)
            # This is important for downstream functions that need the target column
            return df_scored
        else:
            return prob_default
    else:
        # Standard models - can use WOE or raw data
        df_scored = df_woe.copy()
        
        # Get expected feature names from model (if available)
        if model.feature_names is not None:
            expected_features = model.feature_names
        else:
            if use_woe:
                expected_features = [f'{var}_woe' for var in vars_to_bin]
            else:
                expected_features = vars_to_bin if vars_to_bin else []
        
        if use_woe:
            # Get available WOE variable names
            available_features = [f'{var}_woe' for var in vars_to_bin 
                                 if f'{var}_woe' in df_scored.columns]
            
            if len(available_features) == 0:
                raise ValueError("No WOE variables found in dataframe")
        else:
            # Get available raw feature columns
            if vars_to_bin and len(vars_to_bin) > 0:
                available_features = [col for col in vars_to_bin if col in df_scored.columns]
            else:
                # Use all numeric columns
                numeric_cols = df_scored.select_dtypes(include=[np.number]).columns.tolist()
                available_features = numeric_cols
            
            if len(available_features) == 0:
                raise ValueError("No feature columns found in dataframe")
        
        # Create feature matrix with all expected features
        # Fill missing features with 0
        X_features = []
        for feat in expected_features:
            if feat in df_scored.columns:
                X_features.append(df_scored[feat].fillna(0).values)
            else:
                # Missing feature - fill with 0
                X_features.append(np.zeros(len(df_scored)))
                print(f"   WARNING: Feature '{feat}' not found in scoring data. Using default value 0.")
        
        X = np.column_stack(X_features) if len(X_features) > 1 else X_features[0].reshape(-1, 1)
        
        # Predict probabilities
        prob_col_name = 'prob' if 'prob' not in df_scored.columns else 'prob_default'
        df_scored[prob_col_name] = model.predict_proba(X)[:, 1]
        
        return df_scored


def calculate_scores(df_scored, base_score=600, pdo=20, prob_col='prob'):
    """
    Calculate credit scores from probabilities.
    
    Parameters:
    -----------
    df_scored : DataFrame
        Dataframe with probability predictions
    base_score : int
        Base score (default: 600)
    pdo : int
        Points to Double Odds (default: 20)
    prob_col : str
        Name of probability column
    
    Returns:
    --------
    DataFrame : Dataframe with scores, risk bands, and decisions
    """
    df_final = df_scored.copy()
    
    # Calculate odds and log odds
    # Note: odds = p / (1-p), where p is probability of default
    df_final['odds'] = (
        df_final[prob_col] / (1 - df_final[prob_col] + 1e-10)
    )
    df_final['log_odds'] = np.log(df_final['odds'] + 1e-10)
    
    # Calculate score
    # Standard credit scoring: Higher probability of default = Lower score
    # Formula: score = base_score - (pdo / log(2)) * log_odds
    # This ensures: high prob → high log_odds → low score → high risk
    df_final['score'] = base_score - (pdo / np.log(2)) * df_final['log_odds']
    
    # Risk bands
    conditions = [
        df_final['score'] < 580,
        (df_final['score'] >= 580) & (df_final['score'] < 620),
        (df_final['score'] >= 620) & (df_final['score'] < 660),
        (df_final['score'] >= 660) & (df_final['score'] < 700),
        df_final['score'] >= 700
    ]
    choices = [
        'Very High Risk', 'High Risk', 'Medium Risk', 
        'Low Risk', 'Very Low Risk'
    ]
    df_final['risk_band'] = np.select(conditions, choices)
    
    # Decision
    conditions = [
        df_final['score'] < 580,
        (df_final['score'] >= 580) & (df_final['score'] < 660),
        df_final['score'] >= 660
    ]
    choices = ['Reject', 'Refer', 'Accept']
    df_final['decision'] = np.select(conditions, choices)
    
    # Binary Approve/Decline decision based on risk bands
    # Approve: Very Low Risk + Low Risk + Medium Risk
    # Decline: High Risk + Very High Risk
    approve_conditions = [
        df_final['risk_band'].isin(['Very Low Risk', 'Low Risk', 'Medium Risk'])
    ]
    df_final['approve_decision'] = np.where(
        df_final['risk_band'].isin(['Very Low Risk', 'Low Risk', 'Medium Risk']),
        'Approve',
        'Decline'
    )
    
    return df_final

