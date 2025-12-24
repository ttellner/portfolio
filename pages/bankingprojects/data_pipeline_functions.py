"""
Python conversion of SAS data pipeline code.
Contains functions for each stage of the data transformation pipeline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Optional


def stage1_bureau_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 1: Bureau Derived Variables
    Creates bureau score flags, ratios, and risk bands.
    """
    df = df.copy()
    
    # Core Bureau Derived Variables
    df['bureau_score_flag'] = (df['bureau_score'] < 650).astype(int)
    df['overdue_to_total_ratio'] = df['overdue_accounts'] / df['total_accounts']
    df['active_account_ratio'] = df['active_accounts'] / df['total_accounts']
    df['enquiries_flag'] = (df['recent_enquiries_6m'] >= 3).astype(int)
    
    # Risk score band
    df['risk_score_band'] = pd.cut(
        df['bureau_score'],
        bins=[-np.inf, 600, 650, 700, 750, np.inf],
        labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
    ).astype(str)
    
    df['high_enquiry_interaction'] = ((df['bureau_score'] < 650) & (df['recent_enquiries_6m'] >= 3)).astype(int)
    df['overdue_flag'] = (df['overdue_accounts'] >= 2).astype(int)
    df['total_account_bucket'] = 'B' + df['total_accounts'].astype(int).astype(str)
    df['low_risk_band_flag'] = df['risk_score_band'].isin(['High', 'Very High']).astype(int)
    df['high_risk_band_flag'] = df['risk_score_band'].isin(['Very Low', 'Low']).astype(int)
    df['bureau_score_bucket'] = (df['bureau_score'] // 50) * 50
    df['score_enquiry_score'] = df['bureau_score'] * df['recent_enquiries_6m']
    df['accounts_gap'] = df['total_accounts'] - df['active_accounts']
    df['enquiry_to_account_ratio'] = df['recent_enquiries_6m'] / df['total_accounts']
    df['overdue_normalized'] = df['overdue_accounts'] / (1 + df['recent_enquiries_6m'])
    
    # Intentionally Created Duplicates
    df['bureau_score_low_flag'] = df['bureau_score_flag']
    df['enquiry_3plus_flag'] = df['enquiries_flag']
    df['dpd_ratio'] = df['overdue_to_total_ratio']
    df['account_ratio_active'] = df['active_account_ratio']
    df['enquiry_below650_flag'] = df['high_enquiry_interaction']
    
    return df


def stage2_cbs_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 2: CBS Derived Variables
    Creates CBS-related derived variables.
    """
    df = df.copy()
    
    # Add missing base variables manually for Stage 2
    df['average_balance'] = 60000
    df['minimum_balance'] = 8000
    df['salary_credits_3m'] = 3
    df['emi_bounce_count'] = 0
    df['account_tenure_months'] = 24
    
    # Core CBS Derived Variables
    df['emi_to_income_ratio'] = df['emi_amount'] / df['monthly_income']
    df['avg_balance_flag'] = (df['average_balance'] < 5000).astype(int)
    df['min_balance_ratio'] = df['minimum_balance'] / df['average_balance']
    df['low_balance_month_flag'] = (df['min_balance_ratio'] < 0.2).astype(int)
    df['salary_credit_flag'] = (df['salary_credits_3m'] >= 2).astype(int)
    df['emi_bounce_flag'] = (df['emi_bounce_count'] >= 1).astype(int)
    df['tenure_bucket'] = (df['account_tenure_months'] // 12).astype(int)
    df['high_balance_flag'] = (df['average_balance'] >= 100000).astype(int)
    df['emi_high_flag'] = (df['emi_amount'] > 0.5 * df['monthly_income']).astype(int)
    df['low_income_flag'] = (df['monthly_income'] < 20000).astype(int)
    df['emi_normalized'] = df['emi_amount'] / (1 + df['emi_bounce_count'])
    df['balance_utilization_score'] = df['average_balance'] / df['emi_amount']
    df['salary_to_emi_ratio'] = df['monthly_income'] / df['emi_amount']
    
    # Intentionally Created Duplicates
    df['emi_income_ratio'] = df['emi_to_income_ratio']
    df['bounce_flag'] = df['emi_bounce_flag']
    df['emi_income_flag'] = df['emi_high_flag']
    df['high_avg_bal_flag'] = df['high_balance_flag']
    df['emi_ratio_buffer'] = df['salary_to_emi_ratio']
    
    return df


def stage3_dpd_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 3: DPD Derived Variables
    Creates Days Past Due (DPD) related variables.
    """
    df = df.copy()
    
    # Add dummy DPD values (replace later with real data if needed)
    df['dpd_m1'] = 0
    df['dpd_m2'] = 30
    df['dpd_m3'] = 0
    df['dpd_m4'] = 60
    df['dpd_m5'] = 0
    df['dpd_m6'] = 90
    
    df['dpd_month1'] = 'JAN'
    df['dpd_month2'] = 'FEB'
    df['dpd_month3'] = 'MAR'
    df['dpd_month4'] = 'APR'
    df['dpd_month5'] = 'MAY'
    df['dpd_month6'] = 'JUN'
    
    # Core DPD Derived Variables
    dpd_cols = ['dpd_m1', 'dpd_m2', 'dpd_m3', 'dpd_m4', 'dpd_m5', 'dpd_m6']
    df['dpd_max_days'] = df[dpd_cols].max(axis=1)
    df['dpd_sum_total'] = df[dpd_cols].sum(axis=1)
    df['dpd_avg'] = df[dpd_cols].mean(axis=1)
    df['dpd_std_dev'] = df[dpd_cols].std(axis=1)
    
    # Count logic
    df['dpd_count_30_plus'] = (df[dpd_cols] >= 30).sum(axis=1)
    df['dpd_count_60_plus'] = (df[dpd_cols] >= 60).sum(axis=1)
    df['dpd_count_90_plus'] = (df[dpd_cols] >= 90).sum(axis=1)
    
    df['dpd_30_flag'] = (df['dpd_count_30_plus'] >= 1).astype(int)
    df['dpd_60_flag'] = (df['dpd_count_60_plus'] >= 1).astype(int)
    df['dpd_90_flag'] = (df['dpd_count_90_plus'] >= 1).astype(int)
    
    # Latest and recency
    df['dpd_last_month'] = df['dpd_m6']
    df['months_since_last_dpd'] = (df['dpd_m6'] == 0).astype(int)
    
    # Rolling 3-month and trend
    df['dpd_rolling_3_months'] = df[['dpd_m4', 'dpd_m5', 'dpd_m6']].sum(axis=1)
    df['dpd_escalation_flag'] = ((df['dpd_m4'] < df['dpd_m5']) & (df['dpd_m5'] < df['dpd_m6'])).astype(int)
    
    # Peak month logic
    month_map = {0: 'JAN', 1: 'FEB', 2: 'MAR', 3: 'APR', 4: 'MAY', 5: 'JUN'}
    df['dpd_peak_month'] = df.apply(
        lambda row: month_map[np.argmax([row[f'dpd_m{i+1}'] for i in range(6)])],
        axis=1
    )
    
    # Duplicate / Renamed Variables
    df['dpd_high_flag'] = df['dpd_90_flag']
    df['max_dpd_days'] = df['dpd_max_days']
    df['dpd_variance'] = df['dpd_std_dev']
    df['dpd_3m_total'] = df['dpd_rolling_3_months']
    df['recent_dpd_score'] = df['dpd_last_month']
    
    return df


def stage4_collection_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 4: Collection & Recovery Derived Variables
    """
    df = df.copy()
    
    df['write_off_case_flag'] = (df['write_off_flag'] == 1).astype(int)
    df['legal_action_taken_flag'] = (df['legal_case_flag'] == 1).astype(int)
    df['broken_ptp_flag'] = (df['broken_ptp_flag'] == 1).astype(int)
    df['ptp_honored_ratio'] = df['ptp_kept_ratio']
    df['recovery_effectiveness_score'] = df['repayment_to_due_ratio']
    
    # Duplicates / Renamed
    df['repayment_rate_flag'] = df['recovery_effectiveness_score']
    df['legal_case_escalated_flag'] = df['legal_action_taken_flag']
    df['ptp_failure_flag'] = df['broken_ptp_flag']
    df['ptp_ratio_score'] = df['ptp_honored_ratio']
    
    return df


def stage5_disburse_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 5: Disbursal timing, channel analysis, and tenure analytics
    """
    df = df.copy()
    
    # Convert date columns if they're strings
    if df['application_date'].dtype == 'object':
        df['application_date'] = pd.to_datetime(df['application_date'])
    if df['account_open_date'].dtype == 'object':
        df['account_open_date'] = pd.to_datetime(df['account_open_date'])
    
    # Disbursal timing
    df['disbursal_gap_days'] = (df['account_open_date'] - df['application_date']).dt.days
    df['disbursal_gap_weeks'] = (df['account_open_date'] - df['application_date']).dt.days // 7
    df['disbursal_gap_category'] = df['disbursal_gap_days'].apply(
        lambda x: 'Fast' if x <= 3 else ('Moderate' if x <= 7 else 'Slow')
    )
    df['quick_disbursal_flag'] = (df['disbursal_gap_days'] <= 3).astype(int)
    df['very_slow_disbursal_flag'] = (df['disbursal_gap_days'] > 10).astype(int)
    
    # Channel analysis
    df['digital_channel_flag'] = df['channel'].isin(['Online', 'Mobile']).astype(int)
    df['in_branch_flag'] = (df['channel'] == 'Branch').astype(int)
    df['channel_code'] = df['channel'].apply(
        lambda x: '1' if x == 'Online' else ('2' if x == 'Mobile' else ('3' if x == 'Branch' else '0'))
    )
    
    # Tenure analytics
    df['long_tenure_flag'] = (df['tenure_months'] > 60).astype(int)
    df['short_term_loan_flag'] = (df['tenure_months'] <= 12).astype(int)
    df['ultra_short_flag'] = (df['tenure_months'] <= 6).astype(int)
    df['tenure_bucket'] = (df['tenure_months'] // 12).astype(int)
    df['tenure_category'] = df['tenure_months'].apply(
        lambda x: 'Short' if x <= 12 else ('Medium' if x <= 36 else 'Long')
    )
    
    # Requested amount analysis
    df['requested_amt'] = df['requested_amount']
    df['requested_bucket'] = (df['requested_amt'] // 50000).astype(int)
    df['high_requested_flag'] = (df['requested_amt'] > 200000).astype(int)
    df['low_requested_flag'] = (df['requested_amt'] <= 25000).astype(int)
    
    # Loan lifecycle status
    today = pd.Timestamp.now()
    df['active_tenure_months'] = ((today - df['account_open_date']).dt.days / 30).astype(int)
    df['account_age_bucket'] = (df['active_tenure_months'] // 6).astype(int)
    df['account_fresh_flag'] = (df['active_tenure_months'] <= 3).astype(int)
    df['account_mature_flag'] = (df['active_tenure_months'] > 24).astype(int)
    df['loan_cycle_position'] = (df['active_tenure_months'] < (df['tenure_months'] / 2)).apply(
        lambda x: 'Early' if x else 'Late'
    )
    
    # Duplicate / Renamed Variables
    df['fast_funding_flag'] = df['quick_disbursal_flag']
    df['channel_online_flag'] = df['digital_channel_flag']
    df['tenure_category_flag'] = df['long_tenure_flag']
    
    return df


def stage6_txn_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 6: Credit Utilization Features
    """
    df = df.copy()
    
    # Credit Utilization Features
    df['high_utilization_flag'] = (df['credit_card_utilization_pct'] >= 80).astype(int)
    df['low_utilization_flag'] = (df['credit_card_utilization_pct'] <= 20).astype(int)
    df['moderate_utilization_flag'] = ((df['credit_card_utilization_pct'] > 20) & 
                                        (df['credit_card_utilization_pct'] < 80)).astype(int)
    df['utilization_bucket'] = (df['credit_card_utilization_pct'] // 10).astype(int)
    df['utilization_score'] = df['credit_card_utilization_pct'] / 100
    
    # Credit Limit Grouping
    # Note: credit_limit may not exist in raw data, creating dummy if needed
    if 'credit_limit' not in df.columns:
        df['credit_limit'] = df['requested_amount'] * 1.2  # Dummy calculation
    
    df['high_credit_limit_flag'] = (df['credit_limit'] >= 200000).astype(int)
    df['low_credit_limit_flag'] = (df['credit_limit'] < 25000).astype(int)
    df['credit_limit_bucket'] = (df['credit_limit'] // 50000).astype(int)
    df['credit_segment'] = df['credit_limit'].apply(
        lambda x: 'Low' if x < 25000 else ('Mid' if x < 100000 else 'High')
    )
    
    # Interaction-Based Features
    df['utilization_to_limit_ratio'] = df['credit_card_utilization_pct'] / df['credit_limit']
    df['utilization_weighted_score'] = df['credit_card_utilization_pct'] * df['utilization_bucket']
    
    # Duplicates / Renamed
    df['util_flag'] = df['high_utilization_flag']
    df['utilization_band'] = df['utilization_bucket']
    df['limit_score_flag'] = df['high_credit_limit_flag']
    
    return df


def stage7_txn_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 7: Loan Size & Tenure Features, Application Timeliness
    """
    df = df.copy()
    
    # Loan Size & Tenure Features
    df['loan_size_flag'] = (df['requested_amount'] > 200000).astype(int)
    df['low_loan_flag'] = (df['requested_amount'] <= 25000).astype(int)
    df['requested_amount_bucket'] = (df['requested_amount'] // 50000).astype(int)
    df['loan_size_score'] = df['requested_amount'] / df['monthly_income']
    df['short_term_flag'] = (df['tenure_months'] <= 12).astype(int)
    df['long_term_flag'] = (df['tenure_months'] > 60).astype(int)
    df['tenure_bucket'] = (df['tenure_months'] // 12).astype(int)
    df['requested_per_tenure'] = df['requested_amount'] / (df['tenure_months'] + 1)
    df['loan_burden_ratio'] = (df['requested_amount'] / df['tenure_months']) / df['monthly_income']
    
    # Application Timeliness
    if df['application_date'].dtype == 'object':
        df['application_date'] = pd.to_datetime(df['application_date'])
    df['application_month'] = df['application_date'].dt.month
    df['application_year'] = df['application_date'].dt.year
    df['festive_season_flag'] = df['application_month'].isin([10, 11, 12]).astype(int)
    df['financial_year_start_flag'] = df['application_month'].isin([4, 5]).astype(int)
    df['end_of_year_push_flag'] = (df['application_month'] == 3).astype(int)
    
    # Interaction Features
    df['tenure_to_income_ratio'] = df['tenure_months'] / (df['monthly_income'] + 1)
    df['amount_income_term_score'] = (df['requested_amount'] * df['tenure_months']) / (df['monthly_income'] + 1)
    df['size_bucket_flag'] = (df['requested_amount_bucket'] >= 4).astype(int)
    df['high_stress_combination'] = ((df['loan_burden_ratio'] > 0.8) & (df['long_term_flag'] == 1)).astype(int)
    
    # Duplicates / Renamed
    df['loan_request_score'] = df['loan_size_score']
    df['short_loan_flag'] = df['short_term_flag']
    df['long_loan_flag'] = df['long_term_flag']
    df['bucketed_tenure_group'] = df['tenure_bucket']
    df['disbursal_load_flag'] = df['high_stress_combination']
    df['request_term_ratio_flag'] = df['requested_per_tenure']
    df['loan_weighted_score'] = df['amount_income_term_score']
    
    return df


def stage8_txn_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 8: Repayment Performance Flags, Recovery Effectiveness, PTP Behavior
    """
    df = df.copy()
    
    # Repayment Performance Flags
    df['clean_repayment_flag'] = (df['dpd_30_flag'] == 0).astype(int)
    df['ever_60_plus_flag'] = (df['dpd_60_flag'] == 1).astype(int)
    df['ever_90_plus_flag'] = (df['dpd_90_flag'] == 1).astype(int)
    df['recent_dpd_flag'] = (df['dpd_last_month'] > 0).astype(int)
    df['dpd_escalation_stress_flag'] = df['dpd_escalation_flag']
    
    # Recovery Effectiveness
    df['recovery_ratio_flag'] = (df['repayment_to_due_ratio'] >= 0.8).astype(int)
    df['poor_recovery_flag'] = (df['repayment_to_due_ratio'] < 0.5).astype(int)
    df['recovery_gap_score'] = 1 - df['repayment_to_due_ratio']
    df['effective_recovery_bucket'] = (df['repayment_to_due_ratio'] * 10).astype(int)
    df['recovery_success_flag'] = ((df['write_off_flag'] == 0) & (df['repayment_to_due_ratio'] >= 0.8)).astype(int)
    
    # PTP Commitment Behavior
    df['ptp_broken_flag'] = (df['broken_ptp_flag'] == 1).astype(int)
    df['ptp_kept_score'] = df['ptp_kept_ratio']
    df['ptp_compliance_flag'] = (df['ptp_kept_ratio'] >= 0.7).astype(int)
    df['ptp_failure_history_flag'] = ((df['broken_ptp_flag'] == 1) & (df['dpd_30_flag'] == 1)).astype(int)
    
    # Write-Off & Legal Indicators
    df['writeoff_flag_combined'] = df['write_off_flag']
    df['legal_initiated_flag'] = df['legal_case_flag']
    df['legal_escalation_score'] = df['legal_case_flag'] * df['dpd_90_flag']
    df['writeoff_recovery_flag'] = ((df['write_off_flag'] == 1) & (df['repayment_to_due_ratio'] >= 0.3)).astype(int)
    
    # Duplicates / Renamed
    df['clean_pay_flag'] = df['clean_repayment_flag']
    df['ptp_repayment_flag'] = df['ptp_compliance_flag']
    df['dpd_escalation_flag_alias'] = df['dpd_escalation_stress_flag']
    df['legal_case_escalated_flag'] = df['legal_escalation_score']
    df['recovery_bucket_score'] = df['effective_recovery_bucket']
    df['ptp_gap_flag'] = df['ptp_failure_history_flag']
    df['legal_action_flag'] = df['legal_initiated_flag']
    
    return df


def stage9_txn_vars(df: pd.DataFrame, random_seed: int = 42) -> pd.DataFrame:
    """
    Stage 9: Behavior Score Interactions, Risk Banding
    """
    df = df.copy()
    
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Simulated Variables – For Testing Purposes
    df['internal_behavior_score'] = 650 + np.random.normal(0, 50, len(df))
    df['risk_band_code'] = 'M'
    df['manual_override_flag'] = 0
    df['behavior_stability_index'] = 75 + np.random.normal(0, 10, len(df))
    
    # Bureau Score Buckets & Flags
    df['low_bureau_score_flag'] = (df['bureau_score'] < 600).astype(int)
    df['high_bureau_score_flag'] = (df['bureau_score'] >= 750).astype(int)
    df['bureau_score_bucket_50'] = (df['bureau_score'] // 50) * 50
    df['bureau_score_bucket_100'] = (df['bureau_score'] // 100) * 100
    df['score_band_segment'] = df['bureau_score'].apply(
        lambda x: 'Low' if x < 600 else ('Medium' if x < 700 else 'High')
    )
    
    # Behavior Score Interactions
    df['behavior_score_gap'] = df['bureau_score'] - df['internal_behavior_score']
    df['behavior_agreement_flag'] = (df['behavior_score_gap'].abs() < 50).astype(int)
    df['high_behavioral_risk_flag'] = (df['internal_behavior_score'] < 550).astype(int)
    df['behavior_bureau_interaction'] = df['bureau_score'] * df['internal_behavior_score']
    df['avg_combined_score'] = (df['bureau_score'] + df['internal_behavior_score']) / 2
    
    # Risk Banding & External Flags
    df['internal_risk_band_flag'] = df['risk_band_code'].isin(['H', 'VH']).astype(int)
    df['dual_low_score_flag'] = ((df['bureau_score'] < 600) & (df['internal_behavior_score'] < 550)).astype(int)
    df['risk_segment_score_flag'] = ((df['risk_band_code'].isin(['H', 'VH'])) & (df['bureau_score'] < 600)).astype(int)
    df['external_override_flag'] = (df['manual_override_flag'] == 1).astype(int)
    df['stable_behavior_flag'] = (df['behavior_stability_index'] >= 70).astype(int)
    
    # Duplicates / Renamed
    df['risk_band_indicator'] = df['internal_risk_band_flag']
    df['behavior_risk_score'] = df['internal_behavior_score']
    df['score_agreement_flag'] = df['behavior_agreement_flag']
    df['combined_score_flag'] = df['avg_combined_score']
    df['override_manual_flag'] = df['external_override_flag']
    df['dual_risk_flag'] = df['dual_low_score_flag']
    df['score_seg_flag'] = df['risk_segment_score_flag']
    
    return df


def stage10_txn_vars(df: pd.DataFrame, random_seed: int = 42) -> pd.DataFrame:
    """
    Stage 10: Risk Ratios & Final Consolidated Scores
    """
    df = df.copy()
    
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Simulate total EMI amount if missing in source
    df['total_emi_amount'] = 15000 + np.random.normal(0, 2000, len(df))
    
    # Risk Ratios & Final Consolidated Scores
    df['score_utilization_ratio'] = df['bureau_score'] / (1 + df['credit_card_utilization_pct'])
    df['limit_to_income_ratio'] = df['credit_limit'] / (1 + df['monthly_income'])
    df['emi_to_income_ratio'] = df['total_emi_amount'] / (1 + df['monthly_income'])
    df['request_to_limit_ratio'] = df['requested_amount'] / (1 + df['credit_limit'])
    df['score_to_tenure_ratio'] = df['bureau_score'] / (1 + df['tenure_months'])
    
    # Alert Flags – High-Risk Conditions
    df['multiple_risk_flags'] = (
        df['high_utilization_flag'] + 
        df['low_bureau_score_flag'] + 
        df['high_behavioral_risk_flag'] + 
        df['dual_low_score_flag']
    )
    df['high_risk_alert'] = (df['multiple_risk_flags'] >= 3).astype(int)
    df['critical_pd_trigger'] = ((df['ever_90_plus_flag'] == 1) & (df['behavior_score_gap'] < -100)).astype(int)
    df['low_affordability_flag'] = (df['emi_to_income_ratio'] > 0.6).astype(int)
    
    # Final Risk Profile Buckets
    df['risk_profile_score'] = (df['avg_combined_score'] + df['behavior_stability_index']) / 2
    df['risk_band_final'] = df['risk_profile_score'].apply(
        lambda x: 'Low' if x >= 750 else ('Medium' if x >= 600 else 'High')
    )
    df['final_pd_flag'] = ((df['high_risk_alert'] == 1) | (df['critical_pd_trigger'] == 1)).astype(int)
    
    # Duplicates / Alternate Versions
    df['alert_flag'] = df['high_risk_alert']
    df['affordability_flag'] = df['low_affordability_flag']
    df['risk_bucket'] = df['risk_band_final']
    
    return df


def stage11_final_vars(df: pd.DataFrame, random_seed: int = 42) -> pd.DataFrame:
    """
    Stage 11: Generate Final Derived Variables and Default Flag
    Includes Stage 11.1 (additional derived variables) and Stage 11.2 (default flag)
    """
    df = df.copy()
    
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Stage 11.1 – Generate Additional Derived Variables
    # Add missing DPD months if needed (dpd_m7 to dpd_m12)
    for i in range(7, 13):
        if f'dpd_m{i}' not in df.columns:
            df[f'dpd_m{i}'] = np.random.randint(0, 120, len(df))
    
    # DPD Behaviour Variables
    dpd_cols_12 = [f'dpd_m{i}' for i in range(1, 13)]
    df['dpd_max_days'] = df[dpd_cols_12].max(axis=1)
    df['dpd_avg'] = df[dpd_cols_12].mean(axis=1)
    df['dpd_variance'] = df[dpd_cols_12].var(axis=1)
    
    # Count of 30+, 60+, 90+ months
    df['dpd_count_30_plus'] = (df[dpd_cols_12] >= 30).sum(axis=1)
    df['dpd_count_60_plus'] = (df[dpd_cols_12] >= 60).sum(axis=1)
    df['dpd_count_90_plus'] = (df[dpd_cols_12] >= 90).sum(axis=1)
    
    # Last 3 months total DPD
    df['dpd_3m_total'] = df[['dpd_m10', 'dpd_m11', 'dpd_m12']].sum(axis=1)
    
    # EMI & Affordability
    df['emi_bounce_flag'] = (df['emi_bounce_count'] >= 1).astype(int)
    df['emi_income_flag'] = (df['emi_amount'] > 0.5 * df['monthly_income']).astype(int)
    df['emi_ratio_buffer'] = df['monthly_income'] / df['emi_amount']
    df['limit_to_income_ratio'] = df['credit_limit'] / (1 + df['monthly_income'])
    df['low_affordability_flag'] = (df['emi_amount'] / (1 + df['monthly_income']) > 0.6).astype(int)
    
    # Risk & Alerts
    df['high_risk_alert'] = ((df['dpd_count_60_plus'] >= 2) | (df['emi_income_flag'] == 1)).astype(int)
    df['affordability_flag'] = (df['emi_ratio_buffer'] < 2).astype(int)
    df['critical_pd_trigger'] = (df['dpd_max_days'] >= 120).astype(int)
    
    if 'application_date' in df.columns and 'account_open_date' in df.columns:
        if df['application_date'].dtype == 'object':
            df['application_date'] = pd.to_datetime(df['application_date'])
        if df['account_open_date'].dtype == 'object':
            df['account_open_date'] = pd.to_datetime(df['account_open_date'])
        df['fast_funding_flag'] = ((df['account_open_date'] - df['application_date']).dt.days <= 7).astype(int)
    else:
        df['fast_funding_flag'] = 0
    
    # Salary Credit Behaviour
    df['salary_credit_regular'] = (df['salary_credits_3m'] >= 3).astype(int)
    
    # Behavioural Score
    df['behavioural_score'] = (df['bureau_score'] * 0.7) + ((100 - df['dpd_avg']) * 0.3)
    
    # Risk score band (using score_band format logic)
    df['risk_score_band'] = df['bureau_score'].apply(
        lambda x: 'Low' if x < 650 else ('Medium' if x < 700 else 'High')
    )
    
    # Account Ratios
    df['account_ratio_active'] = df['active_accounts'] / df['total_accounts']
    df['overdue_to_total_ratio'] = df['overdue_accounts'] / df['total_accounts']
    df['active_account_ratio'] = df['active_accounts'] / df['total_accounts']
    
    # Enquiry Behaviour
    df['enquiries_flag'] = (df['recent_enquiries_6m'] > 2).astype(int)
    df['high_enquiry_interaction'] = ((df['recent_enquiries_6m'] >= 4) & (df['bureau_score'] < 650)).astype(int)
    
    # Loan Flags
    df['loan_size_flag'] = (df['requested_amount'] >= 500000).astype(int)
    df['limit_score_flag'] = (df['credit_limit'] > 3 * df['monthly_income']).astype(int)
    
    # POS & Mobile Behaviour (simulated)
    df['pos_transaction_volume'] = np.random.randint(50, 501, len(df))
    df['mobile_login_frequency'] = np.random.randint(1, 31, len(df))
    
    # Stage 11.2 – Generate Final Default Flag
    # Add missing performance DPD columns if needed (dpd_f1 to dpd_f6)
    for i in range(1, 7):
        if f'dpd_f{i}' not in df.columns:
            df[f'dpd_f{i}'] = np.random.randint(0, 120, len(df))
    
    # Check for complete observation window
    obs_dpd_cols = [f'dpd_m{i}' for i in range(1, 13)]
    df['valid_obs'] = df[obs_dpd_cols].notna().all(axis=1).astype(int)
    
    # Check for complete performance window
    perf_dpd_cols = [f'dpd_f{i}' for i in range(1, 7)]
    df['valid_perf'] = df[perf_dpd_cols].notna().all(axis=1).astype(int)
    
    # Generate default_flag
    df['default_flag'] = np.where(
        (df['valid_obs'] == 1) & (df['valid_perf'] == 1),
        np.where(df[perf_dpd_cols].max(axis=1) >= 90, 1, 0),
        np.nan
    )
    df['modeling_population'] = ((df['valid_obs'] == 1) & (df['valid_perf'] == 1)).astype(int)
    
    # Keep only valid modeling population for final dataset
    df_final = df[df['modeling_population'] == 1].copy()
    
    return df_final

