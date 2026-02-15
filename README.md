# cmbs-cashflow

Python CMBS new-issue loan-level cashflow projection engine.

## Outputs (Notebook 01)
- outputs/loan_level_projection.csv
- outputs/collateral_cashflows.csv

### 01_loan_level_cashflow_projection 

## Notebook 01 — Loan-level cashflow projection

**Purpose:** Build a new-issue CMBS loan-level monthly projection and aggregate to deal-level collateral cashflows (by scenario).

### Inputs (`data/`)
- `cmbs_loan_tape_new_issue.csv` — one row per loan at cutoff (balance, rate, IO flag, amort term, servicing fee bps, IDs).
- `cmbs_deal_terms.csv` — deal-wide settings (CutoffDate, ProjectionHorizonMonths, RecoveryLagMonths).
- `scenario_shocks.csv` — scenario assumptions (annual CPR/CDR and severity).
- `OUTPUT_loan_level_projection_TEMPLATE.csv` and `OUTPUT_collateral_cashflows_TEMPLATE.csv` — schema templates used to enforce output column names/order.

### Outputs (`outputs/`)
- `loan_level_projection.csv` — loan-level monthly cashflows (Scenario × LoanID × PeriodEndDate).
- `collateral_cashflows.csv` — deal-level collateral cashflows aggregated across loans (Scenario × PeriodEndDate).

### Run
Run `notebooks/01_loan_level_cashflow_projection.ipynb` to generate the outputs.


That’s it: **loan tape + assumptions → projected loan cashflows → aggregated collateral cashflows.**
