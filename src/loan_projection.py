import numpy as np
import pandas as pd
import numpy_financial as npf

def month_ends(cutoff_date: str, horizon_months: int) -> pd.DatetimeIndex:
    asof = pd.Timestamp(cutoff_date)
    first = asof + pd.offsets.MonthEnd(1)
    return pd.date_range(first, periods=horizon_months, freq="ME")

def cpr_to_smm(cpr: float) -> float:
    return 1 - (1 - cpr) ** (1/12)

def cdr_to_mdr(cdr: float) -> float:
    return 1 - (1 - cdr) ** (1/12)

def amort_payment(balance: float, annual_rate: float, amort_months: int) -> float:
    r = annual_rate / 12.0
    if amort_months <= 0:
        return 0.0
    if abs(r) < 1e-12:
        return balance / amort_months
    return -float(npf.pmt(r, amort_months, balance))

def run_projection(loan_tape: pd.DataFrame, deal_terms: pd.DataFrame, scenarios: pd.DataFrame):
    cutoff = str(deal_terms.loc[0, "CutoffDate"])
    horizon = int(deal_terms.loc[0, "ProjectionHorizonMonths"])
    recovery_lag = int(deal_terms.loc[0, "RecoveryLagMonths"])

    dates = month_ends(cutoff, horizon)

    req = ["DealID","LoanID","OriginalBalance_AtCutoff","NoteRate_AtCutoff","IOFlag_AtCutoff","AmortTermMonths","ServicingFeeBps"]
    missing = [c for c in req if c not in loan_tape.columns]
    if missing:
        raise ValueError(f"Missing required columns in loan tape: {missing}")

    out_loan_rows = []
    out_pool_rows = []

    for scen_name, s in scenarios.groupby("Scenario"):
        cpr = float(s["CPR_Annual"].iloc[0])
        cdr = float(s["CDR_Annual"].iloc[0])
        sev = float(s["Severity"].iloc[0])

        smm = cpr_to_smm(cpr)
        mdr = cdr_to_mdr(cdr)

        rec_q = {lid: np.zeros(len(dates)) for lid in loan_tape["LoanID"].tolist()}
        balances = {r.LoanID: float(r.OriginalBalance_AtCutoff) for r in loan_tape.itertuples(index=False)}

        for t, dt in enumerate(dates):
            period_end = dt.date().isoformat()

            pool_int = pool_prin = pool_rec = pool_loss = pool_fee = 0.0
            pool_end = 0.0

            for r in loan_tape.itertuples(index=False):
                lid = r.LoanID
                beg = balances[lid]
                if beg <= 0:
                    continue

                rate = float(r.NoteRate_AtCutoff)
                io = str(r.IOFlag_AtCutoff).upper() == "Y"
                amort_m = int(r.AmortTermMonths)
                svc_bps = float(r.ServicingFeeBps)

                gross_int = beg * rate / 12.0
                svc_fee = beg * (svc_bps/10000.0) / 12.0
                net_int = max(gross_int - svc_fee, 0.0)

                if io:
                    sched_prin = 0.0
                else:
                    pmt = amort_payment(beg, rate, amort_m)
                    sched_prin = max(pmt - gross_int, 0.0)

                default_prin = mdr * beg
                loss = sev * default_prin
                recovery_amt = (1 - sev) * default_prin

                lag_idx = t + recovery_lag
                if lag_idx < len(dates):
                    rec_q[lid][lag_idx] += recovery_amt

                prepay_base = max(beg - default_prin, 0.0)
                prepay_prin = smm * prepay_base

                rec_paid = float(rec_q[lid][t])

                principal_reduction = min(beg, sched_prin + prepay_prin + default_prin)
                end = max(beg - principal_reduction, 0.0)

                status = "Current" if default_prin < 1e-6 else "Defaulted"

                out_loan_rows.append({
                    "DealID": r.DealID,
                    "Scenario": scen_name,
                    "LoanID": lid,
                    "PeriodEndDate": period_end,
                    "BeginningBalance": round(beg, 2),
                    "GrossInterest": round(gross_int, 2),
                    "ServicingFee": round(svc_fee, 2),
                    "NetInterest": round(net_int, 2),
                    "ScheduledPrincipal": round(sched_prin, 2),
                    "PrepaymentPrincipal": round(prepay_prin, 2),
                    "DefaultPrincipal": round(default_prin, 2),
                    "RecoveryAmount": round(rec_paid, 2),
                    "RealizedLoss": round(loss, 2),
                    "EndingBalance": round(end, 2),
                    "Status": status
                })

                pool_int += net_int
                pool_prin += (sched_prin + prepay_prin + default_prin)
                pool_rec += rec_paid
                pool_loss += loss
                pool_fee += svc_fee
                pool_end += end

                balances[lid] = end

            out_pool_rows.append({
                "DealID": loan_tape["DealID"].iloc[0],
                "Scenario": scen_name,
                "PeriodEndDate": period_end,
                "InterestCollected": round(pool_int, 2),
                "PrincipalCollected": round(pool_prin, 2),
                "Recoveries": round(pool_rec, 2),
                "RealizedLosses": round(pool_loss, 2),
                "FeesPaid": round(pool_fee, 2),
                "NetCollections": round(pool_int + pool_prin + pool_rec - pool_fee, 2),
                "EndingCollateralBalance": round(pool_end, 2)
            })

    return pd.DataFrame(out_loan_rows), pd.DataFrame(out_pool_rows)
