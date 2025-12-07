"""
Output and Visualization Module
Handles summarization, visualization, and output formatting.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix,
    precision_score, recall_score, f1_score,
    accuracy_score, classification_report
)
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


def generate_decision_explanations(scored_df, model=None, feature_columns=None, 
                                  max_features=3, prob_col='prob'):
    """
    Generate text explanations for each approval/denial decision.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with score, risk_band, approve_decision columns
    model : ScorecardModel, optional
        Trained model object (for feature importance)
    feature_columns : list, optional
        List of feature column names
    max_features : int
        Maximum number of top features to mention in explanation
    prob_col : str
        Name of probability column
    
    Returns:
    --------
    DataFrame : DataFrame with 'decision_explanation' column added
    """
    df = scored_df.copy()
    
    # Initialize explanations
    explanations = []
    
    # Get feature importance if model is available
    feature_importance = None
    if model is not None and hasattr(model, 'model'):
        try:
            if model.model_type == 'logistic' and hasattr(model.model, 'coef_'):
                # Logistic regression coefficients
                coef = model.model.coef_[0]
                if feature_columns and len(feature_columns) == len(coef):
                    feature_importance = dict(zip(feature_columns, coef))
                elif hasattr(model, 'feature_names') and model.feature_names:
                    feature_importance = dict(zip(model.feature_names, coef))
            elif hasattr(model.model, 'feature_importances_'):
                # Tree-based models
                importances = model.model.feature_importances_
                if feature_columns and len(feature_columns) == len(importances):
                    feature_importance = dict(zip(feature_columns, importances))
                elif hasattr(model, 'feature_names') and model.feature_names:
                    feature_importance = dict(zip(model.feature_names, importances))
        except Exception as e:
            print(f"  Warning: Could not extract feature importance: {e}")
    
    # Generate explanation for each row
    for idx, row in df.iterrows():
        decision = row.get('approve_decision', row.get('decision', 'Unknown'))
        risk_band = row.get('risk_band', 'Unknown')
        score = row.get('score', 0)
        prob = row.get(prob_col, row.get('prob_default', 0))
        
        # Start building explanation
        if decision == 'Approve' or decision == 'Accept':
            explanation = f"APPROVED: "
        elif decision == 'Decline' or decision == 'Reject':
            explanation = f"DECLINED: "
        else:
            explanation = f"DECISION ({decision}): "
        
        # Add risk band and score
        explanation += f"Applicant assigned to '{risk_band}' category "
        explanation += f"with a credit score of {score:.0f} "
        explanation += f"(default probability: {prob:.1%}). "
        
        # Add reasoning based on risk band
        if risk_band == 'Very Low Risk':
            explanation += "The applicant demonstrates excellent creditworthiness with minimal default risk. "
        elif risk_band == 'Low Risk':
            explanation += "The applicant shows strong creditworthiness with low default risk. "
        elif risk_band == 'Medium Risk':
            explanation += "The applicant presents moderate creditworthiness with acceptable default risk. "
        elif risk_band == 'High Risk':
            explanation += "The applicant shows elevated default risk indicators. "
        elif risk_band == 'Very High Risk':
            explanation += "The applicant demonstrates significant default risk concerns. "
        
        # Add key factors if feature importance is available
        if feature_importance:
            # Get top contributing features for this applicant
            top_factors = []
            
            # Try to find feature values in the row
            for feat_name, importance in sorted(feature_importance.items(), 
                                                key=lambda x: abs(x[1]), 
                                                reverse=True)[:max_features]:
                # Check if feature exists in row (could be original or WOE version)
                feat_value = None
                if feat_name in row.index:
                    feat_value = row[feat_name]
                elif feat_name.replace('_woe', '') in row.index:
                    feat_value = row[feat_name.replace('_woe', '')]
                
                if feat_value is not None and not pd.isna(feat_value):
                    # Determine if this feature contributes positively or negatively
                    contribution = "positively" if importance > 0 else "negatively"
                    feat_display = feat_name.replace('_woe', '').replace('_', ' ').title()
                    top_factors.append(f"{feat_display} ({feat_value:.2f})")
            
            if top_factors:
                explanation += f"Key factors considered: {', '.join(top_factors)}. "
        
        # Add final decision rationale
        if decision == 'Approve' or decision == 'Accept':
            explanation += "Based on the risk assessment, this application is approved."
        elif decision == 'Decline' or decision == 'Reject':
            explanation += "Based on the risk assessment, this application is declined."
        else:
            explanation += "This application requires further review."
        
        explanations.append(explanation)
    
    df['decision_explanation'] = explanations
    return df


def analyze_feature_impact(model, X, y=None, feature_names=None, 
                          method='auto', n_repeats=5, random_state=42,
                          scoring='roc_auc', return_plot=True):
    """
    Quantify how each feature impacts the probability calculated by the model.
    
    This function provides multiple methods to analyze feature impact:
    1. **Model-specific methods** (fast, model-dependent):
       - Logistic Regression: Uses coefficients directly
       - Tree-based models: Uses feature_importances_
    2. **Permutation Importance** (model-agnostic, slower but more reliable):
       - Measures how much model performance drops when a feature is permuted
       - Works for all model types including CNN
    
    Parameters:
    -----------
    model : ScorecardModel or sklearn model
        Trained model object
    X : array-like or DataFrame
        Feature matrix (n_samples, n_features)
    y : array-like, optional
        True labels (required for permutation importance)
    feature_names : list, optional
        List of feature names. If None, will try to extract from model or use indices.
    method : str
        Method to use: 'auto', 'coefficients', 'importances', or 'permutation'
        - 'auto': Uses model-specific method if available, else permutation
        - 'coefficients': Uses logistic regression coefficients (logistic only)
        - 'importances': Uses tree-based feature importances (tree models only)
        - 'permutation': Uses permutation importance (all models, requires y)
    n_repeats : int
        Number of times to permute each feature (for permutation importance)
    random_state : int
        Random state for reproducibility
    scoring : str or callable
        Scoring metric for permutation importance ('roc_auc', 'accuracy', or callable)
    return_plot : bool
        Whether to create and return a visualization plot
    
    Returns:
    --------
    dict : Dictionary containing:
        - 'feature_impact': DataFrame with feature names and impact scores
        - 'method_used': String indicating which method was used
        - 'plot': matplotlib figure (if return_plot=True)
        - 'raw_scores': Dictionary of raw impact scores
    """
    print("\n" + "=" * 60)
    print("FEATURE IMPACT ANALYSIS")
    print("=" * 60)
    
    # Get the underlying model
    if hasattr(model, 'model'):
        underlying_model = model.model
        model_type = getattr(model, 'model_type', 'unknown')
    else:
        underlying_model = model
        model_type = 'unknown'
    
    # Get feature names
    if feature_names is None:
        if hasattr(model, 'feature_names') and model.feature_names:
            feature_names = model.feature_names
        elif isinstance(X, pd.DataFrame):
            feature_names = X.columns.tolist()
        else:
            # Try to infer from X shape
            n_features = X.shape[1] if hasattr(X, 'shape') else len(X[0])
            feature_names = [f'Feature_{i}' for i in range(n_features)]
    
    # Convert X to numpy array if needed
    # For CNN models, we need to keep X as DataFrame for image conversion
    is_cnn = (model_type == 'cnn')
    if isinstance(X, pd.DataFrame):
        X_df = X.copy()
        X_array = X.values
    else:
        X_array = np.array(X)
        # Convert to DataFrame for CNN if needed
        if is_cnn and feature_names:
            X_df = pd.DataFrame(X_array, columns=feature_names)
        else:
            X_df = None
    
    # Determine method
    if method == 'auto':
        if model_type == 'logistic' and hasattr(underlying_model, 'coef_'):
            method = 'coefficients'
        elif hasattr(underlying_model, 'feature_importances_'):
            method = 'importances'
        elif y is not None:
            method = 'permutation'
        else:
            raise ValueError(
                "Cannot determine method automatically. "
                "Please specify method='permutation' and provide y, or use a model "
                "with coefficients (logistic) or feature_importances_ (tree-based)."
            )
    
    impact_scores = {}
    method_used = method
    
    # Method 1: Logistic Regression Coefficients
    if method == 'coefficients':
        if not hasattr(underlying_model, 'coef_'):
            raise ValueError(
                "Coefficients method only works for logistic regression models. "
                "Use method='permutation' or method='importances'."
            )
        print(f"\nUsing Logistic Regression Coefficients")
        print(f"  Coefficients represent log-odds impact on probability")
        
        coef = underlying_model.coef_[0]
        intercept = underlying_model.intercept_[0] if hasattr(underlying_model, 'intercept_') else 0
        
        for i, feat_name in enumerate(feature_names):
            if i < len(coef):
                # Coefficient represents change in log-odds per unit change in feature
                # To convert to probability impact, we need to consider the sigmoid transformation
                # For small changes: Δlog_odds ≈ Δprob / (prob * (1 - prob))
                # So: Δprob ≈ coef * prob * (1 - prob) for a unit change in feature
                impact_scores[feat_name] = coef[i]
        
        method_used = 'logistic_coefficients'
    
    # Method 2: Tree-based Feature Importances
    elif method == 'importances':
        if not hasattr(underlying_model, 'feature_importances_'):
            raise ValueError(
                "Feature importances method only works for tree-based models. "
                "Use method='permutation' or method='coefficients'."
            )
        print(f"\nUsing Tree-based Feature Importances")
        print(f"  Importances represent relative contribution to model predictions")
        
        importances = underlying_model.feature_importances_
        
        for i, feat_name in enumerate(feature_names):
            if i < len(importances):
                impact_scores[feat_name] = importances[i]
        
        method_used = 'tree_importances'
    
    # Method 3: Permutation Importance (Model-agnostic)
    elif method == 'permutation':
        if y is None:
            raise ValueError("Permutation importance requires y (true labels)")
        
        print(f"\nUsing Permutation Importance (model-agnostic)")
        print(f"  This measures how much model performance drops when a feature is permuted")
        print(f"  Scoring metric: {scoring}")
        print(f"  Number of repeats: {n_repeats}")
        print(f"  This may take a while...")
        
        # Convert scoring string to callable
        if scoring == 'roc_auc':
            def score_func(model, X, y):
                y_pred_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)
                return roc_auc_score(y, y_pred_proba)
        elif scoring == 'accuracy':
            def score_func(model, X, y):
                y_pred = model.predict(X)
                return accuracy_score(y, y_pred)
        else:
            score_func = scoring
        
        # Use sklearn's permutation_importance if available
        # Note: For CNN models, we skip sklearn's permutation_importance and go straight to manual
        # because sklearn expects 2D arrays but CNN needs image conversion
        if is_cnn:
            # Skip sklearn permutation_importance for CNN, go directly to manual calculation
            print(f"  CNN model detected - using manual permutation calculation")
            use_sklearn_perm = False
        else:
            use_sklearn_perm = True
        
        if use_sklearn_perm:
            try:
                # For ScorecardModel wrapper, we need to create a compatible interface
                if hasattr(model, 'predict_proba'):
                    # Model is already a ScorecardModel
                    perm_result = permutation_importance(
                        model, X_array, y, 
                        n_repeats=n_repeats, 
                        random_state=random_state,
                        scoring=scoring,
                        n_jobs=-1
                    )
                else:
                    # Need to wrap the underlying model
                    class ModelWrapper:
                        def __init__(self, model_obj):
                            self.model_obj = model_obj
                        def predict_proba(self, X):
                            if hasattr(self.model_obj, 'predict_proba'):
                                return self.model_obj.predict_proba(X)
                            else:
                                # For other models
                                pred = self.model_obj.predict(X, verbose=0) if hasattr(self.model_obj, 'predict') else self.model_obj(X)
                                if pred.ndim == 1:
                                    return np.column_stack([1 - pred, pred])
                                return pred
                        def predict(self, X):
                            if hasattr(self.model_obj, 'predict'):
                                return self.model_obj.predict(X)
                            else:
                                proba = self.predict_proba(X)
                                return (proba[:, 1] > 0.5).astype(int)
                    
                    wrapped_model = ModelWrapper(underlying_model)
                    perm_result = permutation_importance(
                        wrapped_model, X_array, y,
                        n_repeats=n_repeats,
                        random_state=random_state,
                        scoring=scoring,
                        n_jobs=-1
                    )
                
                # Extract importance scores
                for i, feat_name in enumerate(feature_names):
                    if i < len(perm_result.importances_mean):
                        # Higher importance = larger drop in performance when permuted
                        impact_scores[feat_name] = perm_result.importances_mean[i]
                
                method_used = 'permutation_importance'
                print(f"  Permutation importance calculation completed")
                
            except Exception as e:
                print(f"  Warning: sklearn permutation_importance failed: {e}")
                print(f"  Falling back to manual permutation calculation...")
                use_sklearn_perm = False
        
        if not use_sklearn_perm:
            
            # Helper function to prepare data for prediction (handles CNN)
            def prepare_for_prediction(X_data, feature_cols=None):
                """Convert data to appropriate format for model prediction."""
                if is_cnn:
                    # For CNN, convert DataFrame to images
                    if isinstance(X_data, pd.DataFrame):
                        from .preprocessing import convert_to_image_grid
                        X_images = convert_to_image_grid(
                            X_data,
                            feature_columns=feature_cols if feature_cols else feature_names,
                            grid_size=28,
                            normalize=True
                        )
                        return X_images
                    else:
                        # If already array, convert back to DataFrame first
                        if X_df is not None:
                            X_temp_df = pd.DataFrame(X_data, columns=feature_names)
                            from .preprocessing import convert_to_image_grid
                            X_images = convert_to_image_grid(
                                X_temp_df,
                                feature_columns=feature_names,
                                grid_size=28,
                                normalize=True
                            )
                            return X_images
                        else:
                            raise ValueError("Cannot convert array to images without feature names")
                else:
                    # For non-CNN models, return as-is
                    return X_data
            
            # Calculate baseline
            X_baseline = prepare_for_prediction(X_df if is_cnn else X_array, feature_names if is_cnn else None)
            baseline_pred = model.predict_proba(X_baseline)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X_baseline)
            baseline_score = score_func(model, X_baseline, y) if callable(score_func) else roc_auc_score(y, baseline_pred)
            
            print(f"  Baseline {scoring}: {baseline_score:.4f}")
            
            for i, feat_name in enumerate(feature_names):
                if i >= X_array.shape[1]:
                    continue
                
                print(f"  Processing feature {i+1}/{len(feature_names)}: {feat_name}")
                scores = []
                
                for repeat in range(n_repeats):
                    # Permute the feature
                    if is_cnn:
                        # For CNN, work with DataFrame
                        X_permuted_df = X_df.copy()
                        np.random.seed(random_state + repeat)
                        permuted_indices = np.random.permutation(len(X_permuted_df))
                        X_permuted_df.iloc[:, i] = X_permuted_df.iloc[permuted_indices, i].values
                        X_permuted = prepare_for_prediction(X_permuted_df, feature_names)
                    else:
                        # For non-CNN, work with array
                        X_permuted = X_array.copy()
                        np.random.seed(random_state + repeat)
                        permuted_indices = np.random.permutation(len(X_permuted))
                        X_permuted[:, i] = X_permuted[permuted_indices, i]
                    
                    # Predict with permuted feature
                    permuted_pred = model.predict_proba(X_permuted)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X_permuted)
                    permuted_score = score_func(model, X_permuted, y) if callable(score_func) else roc_auc_score(y, permuted_pred)
                    
                    # Importance = drop in score (higher drop = more important)
                    scores.append(baseline_score - permuted_score)
                
                impact_scores[feat_name] = np.mean(scores)
            
            method_used = 'permutation_importance_manual'
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'auto', 'coefficients', 'importances', or 'permutation'")
    
    # Create DataFrame with results
    impact_df = pd.DataFrame({
        'feature': list(impact_scores.keys()),
        'impact_score': list(impact_scores.values())
    })
    
    # Sort by absolute impact (descending)
    impact_df['abs_impact'] = impact_df['impact_score'].abs()
    impact_df = impact_df.sort_values('abs_impact', ascending=False).reset_index(drop=True)
    impact_df = impact_df.drop('abs_impact', axis=1)
    
    # Add interpretation
    if method_used == 'logistic_coefficients':
        impact_df['interpretation'] = impact_df['impact_score'].apply(
            lambda x: f"Increases probability" if x > 0 else "Decreases probability"
        )
        impact_df['magnitude'] = impact_df['impact_score'].abs()
    elif method_used in ['tree_importances', 'permutation_importance', 'permutation_importance_manual']:
        impact_df['interpretation'] = "Higher importance = larger impact on predictions"
        impact_df['magnitude'] = impact_df['impact_score']
    else:
        impact_df['interpretation'] = "Feature impact on model predictions"
        impact_df['magnitude'] = impact_df['impact_score'].abs()
    
    print(f"\nTop 10 Most Impactful Features:")
    print(impact_df.head(10).to_string(index=False))
    
    # Create visualization if requested
    fig = None
    if return_plot:
        fig, ax = plt.subplots(figsize=(10, max(6, len(impact_df) * 0.3)))
        
        # Plot top 20 features
        top_n = min(20, len(impact_df))
        plot_df = impact_df.head(top_n)
        
        colors = ['red' if x < 0 else 'green' for x in plot_df['impact_score']]
        
        y_pos = np.arange(len(plot_df))
        ax.barh(y_pos, plot_df['impact_score'], color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(plot_df['feature'])
        ax.set_xlabel('Impact Score', fontsize=12)
        
        if method_used == 'logistic_coefficients':
            ax.set_title('Feature Impact on Probability (Logistic Regression Coefficients)', fontsize=14, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
        elif method_used == 'tree_importances':
            ax.set_title('Feature Impact on Probability (Tree-based Importances)', fontsize=14, fontweight='bold')
        else:
            ax.set_title('Feature Impact on Probability (Permutation Importance)', fontsize=14, fontweight='bold')
        
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
    
    return {
        'feature_impact': impact_df,
        'method_used': method_used,
        'plot': fig,
        'raw_scores': impact_scores
    }


def summarize_scores(scored_df, target_col=None):
    """
    Create summary statistics for scored data.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with score, risk_band, decision columns
    target_col : str, optional
        Target column name if available for performance metrics
    
    Returns:
    --------
    dict : Dictionary with summary statistics
    """
    summary = {
        'total_applicants': len(scored_df),
        'score_stats': {
            'mean': scored_df['score'].mean(),
            'median': scored_df['score'].median(),
            'std': scored_df['score'].std(),
            'min': scored_df['score'].min(),
            'max': scored_df['score'].max(),
            'q25': scored_df['score'].quantile(0.25),
            'q75': scored_df['score'].quantile(0.75)
        },
        'risk_band_distribution': scored_df['risk_band'].value_counts().to_dict(),
        'decision_distribution': scored_df['decision'].value_counts().to_dict()
    }
    
    # Add performance metrics if target is available
    if target_col and target_col in scored_df.columns:
        summary['performance'] = {
            'default_rate': scored_df[target_col].mean(),
            'default_rate_by_risk_band': (
                scored_df.groupby('risk_band')[target_col].mean().to_dict()
            ),
            'default_rate_by_decision': (
                scored_df.groupby('decision')[target_col].mean().to_dict()
            )
        }
        
        # Calculate classification metrics if target is binary
        if scored_df[target_col].nunique() == 2:
            try:
                # Check if we should use approve_decision (for CNN models)
                use_approve_decision = 'approve_decision' in scored_df.columns
                
                # Try to get probability column
                if 'prob' in scored_df.columns:
                    prob_col = scored_df['prob']
                elif 'prob_default' in scored_df.columns:
                    prob_col = scored_df['prob_default']
                else:
                    prob_col = None
                
                y_true = scored_df[target_col].values
                
                # Determine predictions based on method
                if use_approve_decision:
                    # Use approve_decision: Approve=0 (No Default), Decline=1 (Default)
                    y_pred = (scored_df['approve_decision'] == 'Decline').astype(int)
                elif prob_col is not None:
                    # Use probability threshold
                    y_pred = (prob_col >= 0.5).astype(int)
                else:
                    y_pred = None
                
                if y_pred is not None:
                    # Calculate AUC-ROC (only if we have probabilities)
                    if prob_col is not None:
                        summary['performance']['auc'] = roc_auc_score(y_true, prob_col)
                    
                    # Calculate TP, TN, FP, FN manually to ensure correctness
                    # Definitions (based on user requirements):
                    # - TP = True Positive = (actual=0, predicted=0) = Correctly predicted no default
                    # - TN = True Negative = (actual=1, predicted=1) = Correctly predicted default
                    # - FP = False Positive = (actual=0, predicted=1) = Incorrectly predicted default
                    # - FN = False Negative = (actual=1, predicted=0) = Incorrectly predicted no default
                    tp = int(np.sum((y_true == 0) & (y_pred == 0)))  # Actual No Default, Predicted No Default
                    tn = int(np.sum((y_true == 1) & (y_pred == 1)))  # Actual Default, Predicted Default
                    fp = int(np.sum((y_true == 0) & (y_pred == 1)))  # Actual No Default, Predicted Default
                    fn = int(np.sum((y_true == 1) & (y_pred == 0)))  # Actual Default, Predicted No Default
                    
                    # Build confusion matrix in sklearn format for consistency
                    # [[TP, FP],   # Actual=0: TP (predicted 0), FP (predicted 1)
                    #  [FN, TN]]   # Actual=1: FN (predicted 0), TN (predicted 1)
                    cm = np.array([[tp, fp], [fn, tn]], dtype=int)
                    summary['performance']['confusion_matrix'] = cm.tolist()
                    
                    # Calculate metrics
                    # With new definitions: 
                    # TP = (Actual No Default, Predicted No Default)
                    # TN = (Actual Default, Predicted Default)
                    # FP = (Actual No Default, Predicted Default)
                    # FN = (Actual Default, Predicted No Default)
                    
                    # Sensitivity (Recall) = TP / (TP + FN) 
                    # = correctly predicted no default / (correctly predicted no default + incorrectly predicted no default)
                    # = correctly predicted no default / all actual no default
                    summary['performance']['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
                    
                    # Precision = TP / (TP + FP)
                    # = correctly predicted no default / (correctly predicted no default + incorrectly predicted default)
                    # = correctly predicted no default / all predicted no default
                    summary['performance']['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0
                    
                    # Specificity = TN / (TN + FP)
                    # = correctly predicted default / (correctly predicted default + incorrectly predicted default)
                    # = correctly predicted default / all predicted default
                    summary['performance']['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
                    
                    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
                    precision = summary['performance']['precision']
                    recall = summary['performance']['sensitivity']
                    summary['performance']['f1_score'] = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                    
                    # Accuracy = (TP + TN) / (TP + TN + FP + FN)
                    summary['performance']['accuracy'] = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
                    
                    # Store confusion matrix components - ensure correct mapping
                    summary['performance']['true_positives'] = int(tp)
                    summary['performance']['true_negatives'] = int(tn)
                    summary['performance']['false_positives'] = int(fp)
                    summary['performance']['false_negatives'] = int(fn)
                    
                    # Store which method was used
                    if use_approve_decision:
                        summary['performance']['prediction_method'] = 'approve_decision'
                    else:
                        summary['performance']['prediction_method'] = 'probability_threshold'
            except Exception as e:
                print(f"  Warning: Could not calculate performance metrics: {e}")
                summary['performance'] = {}
    
    return summary


def plot_score_distribution(scored_df, target_col=None, figsize=(15, 10)):
    """
    Create comprehensive scorecard visualization dashboard.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with score, risk_band, decision columns
    target_col : str, optional
        Target column name if available for performance metrics
    figsize : tuple
        Figure size (width, height)
    
    Returns:
    --------
    matplotlib.figure.Figure : Figure object
    """
    fig, axes = plt.subplots(2, 3, figsize=figsize)
    fig.suptitle('Scorecard Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Score distribution histogram
    axes[0, 0].hist(scored_df['score'], bins=30, edgecolor='black', alpha=0.7)
    axes[0, 0].set_title('Score Distribution')
    axes[0, 0].set_xlabel('Credit Score')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].grid(alpha=0.3)
    
    # 2. Risk band distribution
    risk_counts = scored_df['risk_band'].value_counts()
    axes[0, 1].bar(range(len(risk_counts)), risk_counts.values)
    axes[0, 1].set_xticks(range(len(risk_counts)))
    axes[0, 1].set_xticklabels(risk_counts.index, rotation=45, ha='right')
    axes[0, 1].set_title('Risk Band Distribution')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].grid(alpha=0.3, axis='y')
    
    # 3. Decision distribution
    decision_counts = scored_df['decision'].value_counts()
    axes[0, 2].bar(range(len(decision_counts)), decision_counts.values)
    axes[0, 2].set_xticks(range(len(decision_counts)))
    axes[0, 2].set_xticklabels(decision_counts.index, rotation=45, ha='right')
    axes[0, 2].set_title('Decision Distribution')
    axes[0, 2].set_ylabel('Count')
    axes[0, 2].grid(alpha=0.3, axis='y')
    
    # 4. Score by risk band box plot
    risk_bands = scored_df['risk_band'].unique()
    box_data = [scored_df[scored_df['risk_band'] == band]['score'].values 
                for band in risk_bands]
    axes[1, 0].boxplot(box_data, labels=risk_bands)
    axes[1, 0].set_title('Score by Risk Band')
    axes[1, 0].set_ylabel('Credit Score')
    axes[1, 0].tick_params(axis='x', rotation=45)
    axes[1, 0].grid(alpha=0.3, axis='y')
    
    # 5. Default rate by risk band (if target available)
    if target_col and target_col in scored_df.columns:
        default_rates = scored_df.groupby('risk_band')[target_col].mean()
        axes[1, 1].bar(range(len(default_rates)), default_rates.values * 100)
        axes[1, 1].set_xticks(range(len(default_rates)))
        axes[1, 1].set_xticklabels(default_rates.index, rotation=45, ha='right')
        axes[1, 1].set_title('Default Rate by Risk Band')
        axes[1, 1].set_ylabel('Default Rate (%)')
        axes[1, 1].grid(alpha=0.3, axis='y')
    else:
        axes[1, 1].text(0.5, 0.5, 'Target column not available', 
                        ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Default Rate by Risk Band')
    
    # 6. ROC curve (if target available)
    if target_col and target_col in scored_df.columns:
        prob_col = scored_df.get('prob', scored_df.get('prob_default', None))
        if prob_col is not None:
            y_true = scored_df[target_col].values
            fpr, tpr, _ = roc_curve(y_true, prob_col)
            auc_score = roc_auc_score(y_true, prob_col)
            axes[1, 2].plot(fpr, tpr, label=f'ROC Curve (AUC = {auc_score:.3f})')
            axes[1, 2].plot([0, 1], [0, 1], 'k--', label='Random')
            axes[1, 2].set_xlabel('False Positive Rate')
            axes[1, 2].set_ylabel('True Positive Rate')
            axes[1, 2].set_title('ROC Curve')
            axes[1, 2].legend()
            axes[1, 2].grid(alpha=0.3)
        else:
            axes[1, 2].text(0.5, 0.5, 'Probability column not available', 
                           ha='center', va='center', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('ROC Curve')
    else:
        axes[1, 2].text(0.5, 0.5, 'Target column not available', 
                        ha='center', va='center', transform=axes[1, 2].transAxes)
        axes[1, 2].set_title('ROC Curve')
    
    plt.tight_layout()
    return fig


def create_summary_table(scored_df, target_col=None):
    """
    Create summary table by risk band.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with score, risk_band, decision columns
    target_col : str, optional
        Target column name if available for performance metrics
    
    Returns:
    --------
    DataFrame : Summary table by risk band
    """
    summary_data = []
    
    for risk_band in scored_df['risk_band'].unique():
        band_data = scored_df[scored_df['risk_band'] == risk_band]
        
        row = {
            'Risk Band': risk_band,
            'Count': len(band_data),
            'Percentage': len(band_data) / len(scored_df) * 100,
            'Mean Score': band_data['score'].mean(),
            'Min Score': band_data['score'].min(),
            'Max Score': band_data['score'].max(),
        }
        
        # Add decision breakdown
        if 'decision' in band_data.columns:
            decisions = band_data['decision'].value_counts()
            for decision in decisions.index:
                row[f'{decision} Count'] = decisions[decision]
                row[f'{decision} %'] = decisions[decision] / len(band_data) * 100
        
        # Add default rate if target available
        if target_col and target_col in band_data.columns:
            row['Default Rate'] = band_data[target_col].mean()
            row['Default Rate %'] = band_data[target_col].mean() * 100
        
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    return summary_df


def plot_confusion_matrix(scored_df, target_col, prob_col_name='prob', 
                          use_approve_decision=False):
    """
    Plot confusion matrix for classification results.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with predictions and target
    target_col : str
        Target column name
    prob_col_name : str
        Name of probability column
    use_approve_decision : bool
        Whether to use approve_decision column for predictions
    
    Returns:
    --------
    matplotlib.figure.Figure : Figure object
    """
    y_true = scored_df[target_col].values
    
    if use_approve_decision and 'approve_decision' in scored_df.columns:
        # Use approve_decision: Approve=0 (No Default), Decline=1 (Default)
        y_pred = (scored_df['approve_decision'] == 'Decline').astype(int)
        labels = ['Approve (No Default)', 'Decline (Default)']
    else:
        # Use probability threshold
        prob_col = scored_df[prob_col_name]
        y_pred = (prob_col >= 0.5).astype(int)
        labels = ['No Default', 'Default']
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels)
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig


def print_classification_metrics(summary):
    """
    Print classification metrics from summary dictionary.
    
    Parameters:
    -----------
    summary : dict
        Summary dictionary from summarize_scores()
    """
    if 'performance' not in summary:
        print("   No performance metrics available (target column not provided)")
        return
    
    perf = summary['performance']
    
    print(f"\n   Classification Metrics:")
    print(f"   {'='*50}")
    
    # Display stored TP/TN/FP/FN if available
    if 'true_positives' in perf:
        print(f"   True Positives (TP):  {perf['true_positives']}")
        print(f"   True Negatives (TN):  {perf['true_negatives']}")
        print(f"   False Positives (FP): {perf['false_positives']}")
        print(f"   False Negatives (FN): {perf['false_negatives']}")
        print(f"   {'-'*50}")
    
    # Display confusion matrix if available
    if 'confusion_matrix' in perf:
        cm = np.array(perf['confusion_matrix'])
        print(f"\n   Confusion Matrix:")
        print(f"   {'':>15} {'Predicted No Default':>25} {'Predicted Default':>25}")
        print(f"   {'Actual No Default':>15} {cm[0,0]:>25} {cm[0,1]:>25}")
        print(f"   {'Actual Default':>15} {cm[1,0]:>25} {cm[1,1]:>25}")
        print(f"   {'-'*50}")
    
    # Display metrics
    if 'accuracy' in perf:
        print(f"   Accuracy:            {perf['accuracy']:.4f}")
    if 'precision' in perf:
        print(f"   Precision:           {perf['precision']:.4f}")
    if 'sensitivity' in perf:
        print(f"   Sensitivity (Recall): {perf['sensitivity']:.4f}")
    if 'specificity' in perf:
        print(f"   Specificity:         {perf['specificity']:.4f}")
    if 'f1_score' in perf:
        print(f"   F1-Score:            {perf['f1_score']:.4f}")
    if 'auc' in perf:
        print(f"   AUC-ROC:             {perf['auc']:.4f}")
    if 'default_rate' in perf:
        print(f"   Overall Default Rate: {perf['default_rate']:.4f}")
    
    print(f"   {'='*50}")


def get_false_predictions(scored_df, target_col, prob_col_name='prob',
                         use_approve_decision=False):
    """
    Get false positive and false negative predictions.
    
    Parameters:
    -----------
    scored_df : DataFrame
        DataFrame with predictions and target
    target_col : str
        Target column name
    prob_col_name : str
        Name of probability column
    use_approve_decision : bool
        Whether to use approve_decision column for predictions
    
    Returns:
    --------
    dict : Dictionary with false_positives and false_negatives DataFrames
    """
    y_true = scored_df[target_col].values
    
    if use_approve_decision and 'approve_decision' in scored_df.columns:
        # Use approve_decision: Approve=0 (No Default), Decline=1 (Default)
        y_pred = (scored_df['approve_decision'] == 'Decline').astype(int)
    else:
        # Use probability threshold
        prob_col = scored_df[prob_col_name]
        y_pred = (prob_col >= 0.5).astype(int)
    
    # False Positives: Actual No Default (0), Predicted Default (1)
    fp_mask = (y_true == 0) & (y_pred == 1)
    false_positives = scored_df[fp_mask].copy()
    
    # False Negatives: Actual Default (1), Predicted No Default (0)
    fn_mask = (y_true == 1) & (y_pred == 0)
    false_negatives = scored_df[fn_mask].copy()
    
    return {
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'fp_count': len(false_positives),
        'fn_count': len(false_negatives)
    }


def save_results(training_scored, new_applicant_scored, output_path):
    """
    Save scored dataframes to CSV files.
    
    Parameters:
    -----------
    training_scored : DataFrame
        Scored training data
    new_applicant_scored : DataFrame
        Scored new applicant data (can be None)
    output_path : str
        Base path for output files (without extension)
    """
    # Save training data
    if training_scored is not None:
        training_file = f"{output_path}_training_scored.csv"
        training_scored.to_csv(training_file, index=False)
        print(f"   Training data saved to: {training_file}")
    
    # Save new applicant data
    if new_applicant_scored is not None:
        new_applicant_file = f"{output_path}_new_applicants_scored.csv"
        new_applicant_scored.to_csv(new_applicant_file, index=False)
        print(f"   New applicant data saved to: {new_applicant_file}")
