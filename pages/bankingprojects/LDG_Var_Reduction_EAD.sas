* Stage 1: Drop unneeded columns;

data credit.reduced_stage1;
    set credit.lgd_ead_raw;
    drop 
        dpd_ever_90_flag
        dpd_90plus_cnt
        partial_recovery_flag
        full_recovery_flag
        zero_recovery_flag
        secured_flag
        lgd_model_ready_flag
        interest_component_ratio
        default_in_observation_window
        is_defaulter
        recovery_flag
        late_dpd_flag
        loan_age_months
        is_multiple_defaults
        emi_burden_flag
        high_risk_profile_flag
        zero_utilization_flag
        full_utilization_flag
        loss_flag
        secured_and_recovered_flag
        no_collateral_no_recovery_flag
        high_emi_score
        secured_or_recovered_flag
        emi_affordability_flag
        disbursement_year
        default_and_loss_flag
        secured_with_loss_flag
        zero_exposure_flag
        dpd_no_peak_flag
        high_loss_low_recovery_flag
        overdrawn_flag
        underutilization_flag
        overutilization_gap
        total_limit_missing_flag
        limit_ratio_vs_score
        full_drawn_and_overdue_flag
        high_risk_loan_flag
        interest_income_ratio
        high_emi_and_interest_flag
        employment_emi_risk
        secure_home_high_loan_flag
        high_interest_tenure_flag
        emi_vs_limit_ratio
        emi_vs_drawn_ratio
        emi_vs_ead_ratio;
run;

* Stage 2: Drop Technical Identifiers & Engineered Sources;

data credit.reduced_stage2;
    set credit.reduced_stage1;

    * Drop only valid variables found in the dataset;
    drop 
        customer_id               * Unique ID, not predictive;
        disbursed_month           * Seasonality, replace with tenure;
        term_score                * Derived from loan_term;
        loan_amount_score         * Derived from loan_amount;
        loan_interest_term_combo; * Engineered combo; hard to interpret;
run;

* Stage 3: Drop variables with high correlation;

data credit.reduced_stage3;
    set credit.reduced_stage2;

    drop 
        dpd_mean                        * Duplicate of dpd_avg;
        total_past_due                  * Covered by dpd_avg and dpd_m1-m12;
        utilization_to_limit_ratio      * Same as drawn_vs_limit_ratio;
        exposure_percent_drawn          * Same as drawn_vs_exposure_ratio;
        exposure_to_income_ratio;       * Same as emi_to_income_ratio;
run;

proc means data=credit.reduced_stage3 noprint nmiss n mean std min max;
    var _numeric_;
    output out=credit.variance_check(drop=_type_ _freq_);
run;

* Stage 4: Near-zero Variance Filtering;
* Get frequencies for binary/flag variables, then manually scan the input vars with std = 0 or very low, e.g., , 0.01;

proc means data = credit.reduced_stage3 noprint nmiss n mean std min max;
    var_numeric_;
    output out = credit.variance_check(drop=_type_ _freq_);
run;

* Stage 5: Final Summary;

* Step 1: Calculate N and NMISS, drop _TYPE_ and _FREQ_;

proc means data=credit.reduced_stage4 n nmiss noprint;
    output out=missing_summary(drop=_type_ _freq_);
run;

* Step 2: Keep only numeric variables and calculate missing %;

data credit.missing_final;
    set missing_summary;
    array nums {*} _numeric_;
    do i = 1 to dim(nums)/2;   * Half for NMISS, half for N;
        varname = vname(nums[i]);
        nmiss = nums[i];
        n = nums[i + dim(nums)/2];
        if n > 0 then missing_pct = (nmiss / n) * 100;
        output;
    end;
    keep varname nmiss n missing_pct;
run;

* Step 3: Create function variable with vars < 30% missing;

proc sql noprint;
    select varname into :keep_vars separated by ' '
    from credit.missing_final
    where missing_pct < 30;
quit;

* Step 4: Create reduced_stage5 dataset;

data credit.reduced_stage5;
    set credit.reduced_stage4(keep=&keep_vars);
run;

* Step 5: No columns dropped since credit.reduced_stage3 so copy it forward;

data credit.reduced_stage4;
    set credit.reduced_stage3;
run;

* Stage 6: Variable Screening and Creation of Main LGD/EAD Datasets;

* Step 1: Ensure EAD target var exists, if not, create it;

data.credit.reduced_stage5;
    set credit.reduced_stage5;
    if missing(ead_utlilized_ratio) then
        ead_utilized_ratio = amount_drawn / exposure_at_default;
run;

* Step 2: Identify numeric predictors;

proc contents data=credit.reduced_stage5 out=_vars(keep=name type) noprint;
run;

proc sql noprint;
    select name into :num_vars separated by ' '
    from _vars
    where type=1 
      and upcase(name) not in ('LGD_OBSERVED','EAD_UTILIZED_RATIO');
quit;

* Step 3: Select top-N predictors for each target;

%macro topN_vars(target=, outlist=, outdata=, N=25);
    proc corr data=credit.reduced_stage5 noprint outp=_corr;
        var &num_vars &target;
    run;

    data _scores;
        set _corr;
        where _type_='CORR' and upcase(_name_) ne %upcase("&target");
        length var $32;
        var = _name_;
        abs_r = abs(&target);
        keep var abs_r;
    run;

    proc sort data=_scores out=_topN; by descending abs_r; run;
    data _topN; set _topN(obs=&N); run;

    proc sql noprint;
        select var into :&outlist separated by ' '
        from _topN;
    quit;

    data &outdata;
        set credit.reduced_stage5(keep=&target &&&outlist);
    run;

    %put NOTE: &target top-&N vars = &&&outlist;
%mend;

* Step 4: Create Stage 6 datasets;

%topN_vars(target=lgd_observed, outlist = lgd_vars, outdata=credit.stage6_lgd, N=25);
%topN_vars(target=ead_utlilized_ratio, outlist = ead_vars, outdata = credit.stage6_ead, N=25);

* Step 5: Create LGD & EAD datasets with unique vars and join keys;
* Step 5.1: Add Dummy IDs if missing;

data credit.reduced_stage5;
    set credit.reduced_stage5;
    if missing(customer_id) then customer_id = cats("CUST", put(_n_, z3.));
    if missing(application_id) then application_id = cats("APP", put(_n_, z3.));
run;

* Step 5.2: Define variable lists;

%let lgd_vars = lgd_observed amount_drawn avg_dpd_first_6_months dpd_consistency_flag 
    dpd_ever_30_flag dpd_ever_60_flag dpd_growth_rate dpd_m1 dpd_m2 dpd_m3 dpd_m4 
    dpd_m5 dpd_m6 dpd_m7 dpd_m8 dpd_m9 dpd_m10 dpd_m11 dpd_m12 dpd_max dpd_recent_flag 
    dpd_slope dpd_std dpd_weighted_score dpd_zero_months early_dpd_flag 
    emi_to_income_ratio exposure_at_default high_tenure_flag high_utilization_flag 
    interest_rate loan_amount loan_disbursed_in_festive_period 
    loan_disbursed_in_first_half loan_term loss_to_limit_ratio 
    over_collateralization_ratio recovery_amount recovery_started_within_90days 
    sector_risk_flag secured_type_flag unutilized_limit_ratio;

%let ead_vars = exposure_at_default amount_drawn avg_dpd_first_6_months dpd_consistency_flag 
    dpd_ever_30_flag dpd_ever_60_flag dpd_growth_rate dpd_m1 dpd_m2 dpd_m3 dpd_m4 
    dpd_m5 dpd_m6 dpd_m7 dpd_m8 dpd_m9 dpd_m10 dpd_m11 dpd_m12 dpd_max dpd_recent_flag 
    dpd_slope dpd_std dpd_weighted_score dpd_zero_months early_dpd_flag 
    emi_to_income_ratio high_tenure_flag high_utilization_flag 
    interest_rate loan_amount loan_disbursed_in_festive_period 
    loan_disbursed_in_first_half loan_term loss_to_limit_ratio 
    over_collateralization_ratio sector_risk_flag secured_type_flag 
    unutilized_limit_ratio;

* Step 5.3: Remove duplicates so each table keeps unique variables;

proc sql noprint;
    create table _lgd_unique as
    select distinct name
    from dictionary.columns
    where libname='CREDIT' and memname='REDUCED_STAGE5' 
          and upcase(name) in (%upcase("%sysfunc(tranwrd(&lgd_vars,%str( ),%str(' , ')))"));
    
    create table _ead_unique as
    select distinct name
    from dictionary.columns
    where libname='CREDIT' and memname='REDUCED_STAGE5' 
          and upcase(name) in (%upcase("%sysfunc(tranwrd(&ead_vars,%str( ),%str(' , ')))"));
quit;

* Step 5.4: Build final LGD table;

data credit.stage6_lgd;
    set credit.reduced_stage5;
    keep customer_id application_id &lgd_vars;
run;

* Step 5.5: Build final EAD table;

data credit.stage6_ead;
    set credit.reduced_stage5;
    keep customer_id application_id &ead_vars;
run;

* Stage 7: Standardize Variable Naming for LGD and EAD Models;

* One macro to build either LGD or EAD from its Stage-6 table;
%macro stage7_one(ds_in, ds_out);
  %local lib mem has_cid has_aid;
  %let lib=%upcase(%scan(&ds_in,1,.));
  %let mem=%upcase(%scan(&ds_in,2,.));

  * Do the input tables already have customer_id / app_id? (any type);
  proc sql noprint;
    select sum(upcase(name)='CUSTOMER_ID') into :has_cid
    from dictionary.columns where libname="&lib" and memname="&mem";
    select sum(upcase(name)='APP_ID') into :has_aid
    from dictionary.columns where libname="&lib" and memname="&mem";
  quit;

  data &ds_out;
    * Bring ALL columns forward, if IDs exist, rename them out of the way to avoid type clashes;
    %if &has_cid and &has_aid %then %do;
      set &ds_in(rename=(customer_id=_cid_in app_id=_aid_in));
    %end;
    %else %if &has_cid %then %do;
      set &ds_in(rename=(customer_id=_cid_in));
    %end;
    %else %if &has_aid %then %do;
      set &ds_in(rename=(app_id=_aid_in));
    %end;
    %else %do;
      set &ds_in;
    %end;

    * --- Surrogate IDs: cust001 / app001, cust002 / app002, ... ---;
    length customer_id app_id $12 _seq $8;
    _seq = put(_n_, z3.);                 /* 001, 002, ... 999, 1000, ... */
    customer_id = cats('cust', _seq);
    app_id      = cats('app',  _seq);

    * --- Shared LGD/EAD variables (guarded) ---;
    length
      ead_amount loan_amt amt_drawn recovery_amt net_loss recovery_rate
      ead_utilized_ratio unutilized_limit_ratio loss_to_limit_ratio
      collateral_val collateral_to_ead_ratio
      partial_recovery_flag full_recovery_flag zero_recovery_flag
      model_ready_flag 8
    ;

    * If an alias doesn’t exist in Stage-6, SAS will NOTE it as uninitialized (fine) and COALESCE will skip it;
    ead_amount     = max(0, coalesce(exposure_at_default, ead, 0));
    amt_drawn      = max(0, coalesce(amount_drawn, drawdown_amt, 0));
    loan_amt       = max(0, coalesce(loan_amount, total_limit, credit_limit, 0));
    recovery_amt   = max(0, coalesce(recovery_amount, 0));
    collateral_val = max(0, coalesce(collateral_value, 0));

    if loan_amt>0 then unutilized_limit_ratio = min(max((loan_amt - amt_drawn)/loan_amt, 0), 1);
    else unutilized_limit_ratio = .;

    if ead_amount>0 then ead_utilized_ratio = min(max(amt_drawn/ead_amount, 0), 10);
    else if loan_amt>0 then ead_utilized_ratio = min(max(amt_drawn/loan_amt, 0), 10);
    else ead_utilized_ratio = .;

    net_loss = max(ead_amount - recovery_amt, 0);

    if ead_amount>0 then recovery_rate = min(max(recovery_amt/ead_amount, 0), 1);
    else recovery_rate = .;

    if loan_amt>0 then loss_to_limit_ratio = min(max(net_loss/loan_amt, 0), 1);
    else loss_to_limit_ratio = .;

    if ead_amount>0 then collateral_to_ead_ratio = min(max(collateral_val/ead_amount, 0), 10);
    else collateral_to_ead_ratio = .;

    partial_recovery_flag = (0 < recovery_rate and recovery_rate < 1);
    full_recovery_flag    = (recovery_rate = 1);
    zero_recovery_flag    = (recovery_rate = 0);

    model_ready_flag = (nmiss(ead_amount, loan_amt)=0 and not missing(customer_id) and not missing(app_id));

    format recovery_rate unutilized_limit_ratio loss_to_limit_ratio collateral_to_ead_ratio 8.4;

    label
      customer_id              = "Customer ID (Surrogate, cust001..)"
      app_id                   = "Application ID (Surrogate, app001..)"
      ead_amount               = "Exposure at Default (Unified)"
      amt_drawn                = "Amount Drawn (Unified)"
      loan_amt                 = "Sanctioned/Limit Amount (Unified)"
      recovery_amt             = "Total Recovery Amount (Unified)"
      net_loss                 = "Net Loss = EAD - Recoveries (Unified)"
      recovery_rate            = "Recovery Rate (Unified, 0..1)"
      ead_utilized_ratio       = "Utilization vs EAD/Limit (Unified)"
      unutilized_limit_ratio   = "Unutilized Limit Ratio (0..1, Unified)"
      loss_to_limit_ratio      = "Loss to Limit Ratio (0..1, Unified)"
      collateral_val           = "Collateral Value (Unified)"
      collateral_to_ead_ratio  = "Collateral-to-EAD Ratio (Unified)"
      partial_recovery_flag    = "Partial Recovery Flag"
      full_recovery_flag       = "Full Recovery Flag"
      zero_recovery_flag       = "Zero Recovery Flag"
      model_ready_flag         = "Record Ready for Modeling"
    ;
  run;
%mend;

* Build both Stage-7 tables — ALL Stage-6 vars are retained;
%stage7_one(credit.stage6_lgd, credit.stage7_lgd);
%stage7_one(credit.stage6_ead, credit.stage7_ead);

* Sanity summary;
proc sql;
  select 'LGD' as ds length=3
       , count(*) as n_obs
       , sum(missing(customer_id)) as miss_cust
       , sum(missing(app_id))      as miss_app
  from credit.stage7_lgd
  union all
  select 'EAD' as ds length=3
       , count(*) as n_obs
       , sum(missing(customer_id)) as miss_cust
       , sum(missing(app_id))      as miss_app
  from credit.stage7_ead;
quit;

* Stage 8: Variable curation only (no modeling);
   * Inputs:  CREDIT.STAGE7_LGD, CREDIT.STAGE7_EAD;
   * Outputs:;
     * CREDIT.STAGE8_LGD_BASE        (Stage 7 + LGD target);
     * CREDIT.STAGE8_EAD_BASE        (Stage 7 + CCF target);
     * CREDIT.STAGE8_LGD_VARS        (curated predictors + target);
     * CREDIT.STAGE8_EAD_VARS        (curated predictors + target);
     * CREDIT.STAGE8_LGD_VARS_EXCLUDED / _INCLUDED (metadata);
     * CREDIT.STAGE8_EAD_VARS_EXCLUDED / _INCLUDED (metadata);

* ---------- A) Targets only (no modeling) ---------- ;

* LGD target: loss severity bounded [0,1];

data credit.stage8_lgd_base;
  set credit.stage7_lgd;
  if ead_amount>0 then lgd_target = min(max(net_loss/ead_amount, 0), 1);
  else lgd_target = .;
run;

* EAD (CCF) target: clamp to [0,1.5] for sanity (no modeling yet);

data credit.stage8_ead_base;
  set credit.stage7_ead;
  length ccf_target 8;
  if loan_amt>amt_drawn and (loan_amt-amt_drawn)>0 then
    ccf_target = (ead_amount - amt_drawn) / (loan_amt - amt_drawn);
  else if loan_amt>0 then
    ccf_target = ead_amount / loan_amt;
  else ccf_target = .;
  if not missing(ccf_target) then ccf_target = min(max(ccf_target, 0), 1.5);
run;

* ---------- B) Exclusion rules (IDs + leakage) ----------;
* Keep targets in the dataset - we just exclude leakers from the predictor set;

%let _lgd_exclude =
  customer_id app_id
  /* post-default info (leakage) */
  net_loss recovery_amt recovery_rate
  partial_recovery_flag full_recovery_flag zero_recovery_flag
  loss_to_limit_ratio
  /* housekeeping */
  model_ready_flag
;

%let _ead_exclude =
  customer_id app_id
  /* post-default info (leakage) */
  net_loss recovery_amt recovery_rate
  partial_recovery_flag full_recovery_flag zero_recovery_flag
  loss_to_limit_ratio
  /* avoid tautology against CCF/EAD target */
  ead_amount
  /* housekeeping */
  model_ready_flag
;

* ---------- C) Curate helper (drops only exclusions that actually exist) ----------;

%macro _curate(ds_in, ds_out, exclude_list, target_keep);
  %local lib mem outlib outmem excl_quoted drop_list;
  %let lib   = %upcase(%scan(&ds_in ,1,.));
  %let mem   = %upcase(%scan(&ds_in ,2,.));
  %let outlib= %upcase(%scan(&ds_out,1,.));
  %let outmem= %upcase(%scan(&ds_out,2,.));

  * quote a space-separated list -> "A","B","C";

  %macro _quote_list(list);
    %local i word out;
    %let i=1;
    %do %while(%length(%scan(&list,&i,%str( ))));
      %let word=%upcase(%scan(&list,&i,%str( )));
      %if &i=1 %then %let out="&word";
      %else %let out=&out,"&word";
      %let i=%eval(&i+1);
    %end;
    &out
  %mend;
  %let excl_quoted=%_quote_list(&exclude_list);

  * Find intersection between exclusions and actual columns;

  proc sql noprint;
    select name into :drop_list separated by ' '
    from dictionary.columns
    where libname="&lib" and memname="&mem"
      and upcase(name) in (&excl_quoted);
  quit;

  * Build curated table: keep everything except found exclusions;

  %if %superq(drop_list) ne %then %do;
    data &ds_out; set &ds_in(drop=&drop_list); run;
  %end;
  %else %do;
    data &ds_out; set &ds_in; run;
  %end;

  * Metadata tables in SAME library as ds_out;
  
  proc sql;
    create table &outlib..%sysfunc(lowcase(&outmem))_excluded as
      select upcase(name) as name
      from dictionary.columns
      where libname="&lib" and memname="&mem"
        and upcase(name) in (&excl_quoted)
      order by name;

    create table &outlib..%sysfunc(lowcase(&outmem))_included as
      select upcase(name) as name
      from dictionary.columns
      where libname="&outlib" and memname="&outmem"
      order by name;
  quit;
%mend;

* ---------- D) Apply curation (targets are kept in the data) ----------;

%_curate(credit.stage8_lgd_base, credit.stage8_lgd_vars, &_lgd_exclude, lgd_target);
%_curate(credit.stage8_ead_base, credit.stage8_ead_vars, &_ead_exclude, ccf_target);

* ---------- E) Quick sanity summaries ----------;

proc sql;
  select 'LGD' as ds length=3
       , count(*) as n_obs
       , (select count(*) from dictionary.columns
          where libname='CREDIT' and memname='STAGE8_LGD_VARS') as n_vars
  from credit.stage8_lgd_vars
  union all
  select 'EAD' as ds length=3
       , count(*) as n_obs
       , (select count(*) from dictionary.columns
          where libname='CREDIT' and memname='STAGE8_EAD_VARS') as n_vars
  from credit.stage8_ead_vars;
quit;

* Lists of excluded/included variables for governance appendices;

proc print data=credit.stage8_lgd_vars_excluded noobs; run;
proc print data=credit.stage8_ead_vars_excluded noobs; run;

proc print data=credit.stage8_lgd_vars_included; run;
proc print data=credit.stage8_ead_vars_included; run;

* Stage 8: EAD Modeling Depth - CCF Approached & OOT Validation;

* Revolving - Beta regression on CCF (preferred);

* Target construction;
data ccf_target;
  set panel(where=(default_flag=1));
  undrawn = max(limit_obs - balance_obs, 1e-6);
  ccf = (ead_ad - balance_obs) / undrawn;
  if ccf<0 then ccf=0; if ccf>1 then ccf=1;
run;

* Beta regression with logit link;
proc glimmix data=ccf_target;
  where 0<ccf<1;
  class product seg;
  model ccf = utilization mob limit_change_rate bureau_score seg product
              income_ln delinquency_12m season_qtr
              / dist=beta link=logit solution;
  output out=ccf_pred pred(ilink)=p_ccf;
run;

* Convert to EAD prediction;
data ead_pred_rev;
  set ccf_pred;
  ead_hat = balance_obs + p_ccf * undrawn; 
run;

* Revolving — Two-part model (drawdown flag + size). Useful when zeros are common at default;
* Part 1: will the customer draw further?;

proc logistic data=ccf_target outmodel=mdl_draw;
  class product seg;
  model draw_flag(event='1') = utilization mob limit_change_rate bureau_score seg product;
  score data=ccf_target out=draw_scored p=ps_draw;
run;

* Part 2: size given draw (Beta on (0,1]);

proc glimmix data=draw_scored;
  where draw_flag=1 and 0<ccf<=1;
  class product seg;
  model ccf = utilization mob limit_change_rate bureau_score seg product / dist=beta link=logit;
  output out=size_scored pred(ilink)=ps_size;
run;

data ead_pred_two_part;
  merge draw_scored size_scored;
  by _all_;
  p_ccf = ps_draw * coalesce(ps_size,0);
  ead_hat = balance_obs + p_ccf * undrawn;
run;

* Amortizing — Tweedie/Log-linear on EAD_AD;

proc genmod data=amort_target;
  class product seg;
  model ead_ad = mob sched_balance ltv rate product seg prepay_speed
                 income_ln collateral_flag delinquency_12m
                 / dist=tweedie link=log;
  output out=ead_pred_amort pred=ead_hat;
run;

* Out-of-time (OOT) validation. Split by calendar time (e.g., last 12 months as OOT);
* Error metrics;

proc sql;
  create table metrics as
  select 'DEV' as sample, mean(abs(ead_hat-ead_ad)) as mae,
         sqrt(mean((ead_hat-ead_ad)**2)) as rmse
  from ead_pred_dev
  union all
  select 'OOT', mean(abs(ead_hat-ead_ad)), sqrt(mean((ead_hat-ead_ad)**2))
  from ead_pred_oot;
quit;

* Calibration by decile;

proc rank data=ead_pred_oot groups=10 out=oot_dec;
  var ead_hat; ranks decile;
run;
proc means data=oot_dec nway;
  class decile;
  var ead_hat ead_ad;
  output out=calib mean=pred actual;
run;
* ——— Patch: standardize DPD feature names so PROC REG never breaks ———;