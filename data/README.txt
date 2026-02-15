CMBS NEW-ISSUE PROJECTION DATASET (SYNTHETIC)
============================================
DealID: CMBS_NEW_AEOYEE
CutoffDate: 2026-01-31

This package is for NEW ISSUE projection modeling.
It intentionally contains NO historical periodic file.

What you build:
1) Loan-level monthly projection table (match OUTPUT_loan_level_projection_TEMPLATE.csv)
2) Deal-level monthly collateral cashflows (match OUTPUT_collateral_cashflows_TEMPLATE.csv)

Key assumptions live in:
- scenario_shocks.csv (CDR/CPR/Severity + NOI growth and shocks)
- cmbs_deal_terms.csv (projection horizon, recovery lag, fee bps)

Minimum engine requirements:
- amortization (IO vs amort)
- CPR->SMM and CDR->MDR conversion
- default timing and severity, recoveries with lag
- aggregation to deal-level cashflows
