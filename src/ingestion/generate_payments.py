"""
Generates synthetic payment data for the African Commerce & Payments
Intelligence Platform.

Payments reference real order_ids from orders.csv (foreign keys).
Payment methods are country-realistic (mobile money dominant in East/West Africa).

Intentionally includes realistic data quality problems:
- orphaned payments (order_id that exists nowhere)
- amount mismatches (payment amount != order amount)
- successful payments on cancelled/returned orders
- duplicate payment records
"""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)

# Mobile money and card mix per country — weights reflect real market dominance
PAYMENT_METHODS_BY_COUNTRY = {
    "Kenya": [("mpesa", 0.55), ("card", 0.15), ("bank_transfer", 0.10), ("airtel_money", 0.10), ("paypal", 0.10)],
    "Tanzania": [("mpesa", 0.45), ("airtel_money", 0.20), ("tigopesa", 0.15), ("card", 0.15), ("bank_transfer", 0.05)],
    "Nigeria": [("bank_transfer", 0.30), ("card", 0.25), ("mtn_momo", 0.25), ("ussd", 0.20)],
    "Ghana": [("mtn_momo", 0.50), ("card", 0.15), ("bank_transfer", 0.15), ("vodafone_cash", 0.20)],
    "Uganda": [("mtn_momo", 0.45), ("airtel_money", 0.35), ("card", 0.10), ("bank_transfer", 0.10)],
    "South Africa": [("card", 0.50), ("bank_transfer", 0.20), ("eft", 0.15), ("paypal", 0.15)],
    "Egypt": [("card", 0.40), ("fawry", 0.30), ("bank_transfer", 0.15), ("vodafone_cash", 0.15)],
    "Rwanda": [("mtn_momo", 0.40), ("airtel_money", 0.30), ("card", 0.20), ("bank_transfer", 0.10)],
}

# Failure reason codes with realistic weights (funds and network issues dominate)
FAILURE_REASONS = [
    ("insufficient_funds", 0.30),
    ("network_timeout", 0.25),
    ("customer_cancelled", 0.15),
    ("limit_exceeded", 0.12),
    ("invalid_pin", 0.10),
    ("provider_error", 0.08),
]

STATUS_WEIGHTS = [("successful", 0.72), ("failed", 0.20), ("pending", 0.05), ("refunded", 0.03)]


def weighted_choice(options_with_weights):
    population = [opt for opt, _ in options_with_weights]
    weights = [w for _, w in options_with_weights]
    return random.choices(population, weights=weights, k=1)[0]


def generate_payments(orders: pd.DataFrame) -> pd.DataFrame:
    # Only completed orders should normally receive successful payments,
    # but failed/pending attempts can exist against any order.
    # Fast lookup: order_id -> (amount, currency, status, order_date, country)
    order_rows = orders[["order_id", "amount", "currency", "status", "order_date"]]
    order_list = order_rows.to_dict("records")

    now = datetime.now()
    records = []

    for order in order_list:
        # Number of payment attempts for this order (most get exactly one)
        n_attempts = random.choices([1, 2, 3], weights=[0.80, 0.15, 0.05], k=1)[0]

        order_date = datetime.fromisoformat(order["order_date"])
        country_methods = None  # resolved lazily via currency

        for attempt in range(n_attempts):
            # Resolve country from currency (orders carry currency)
            currency = order["currency"]
            method = weighted_choice(PAYMENT_METHODS_BY_COUNTRY.get(
                CURRENCY_TO_COUNTRY.get(currency, "Kenya"), PAYMENT_METHODS_BY_COUNTRY["Kenya"]))

            # Attempt timing: minutes to days after the order
            payment_ts = order_date + timedelta(minutes=random.randint(1, 60 * 24 * 3))
            if payment_ts > now:
                payment_ts = now - timedelta(minutes=random.randint(1, 60))

            status = weighted_choice(STATUS_WEIGHTS)
            # Retries after a failed first attempt are more likely to succeed
            if attempt > 0 and status == "failed":
                status = "successful" if random.random() < 0.6 else status

            payment_amount = order["amount"]
            failure_reason = weighted_choice(FAILURE_REASONS) if status == "failed" else None

            records.append({
                "payment_id": str(uuid.uuid4()),
                "order_id": order["order_id"],
                "payment_method": method,
                "status": status,
                "amount": payment_amount,
                "currency": currency,
                "failure_reason": failure_reason,
                "payment_timestamp": payment_ts,
                "attempt_number": attempt + 1,
            })

    df = pd.DataFrame(records)

    # --- Intentional messiness ---

    # 1. ~2% amount mismatches (wrong amount recorded)
    mismatch_idx = random.sample(range(len(df)), int(len(df) * 0.02))
    for idx in mismatch_idx:
        original = df.loc[idx, "amount"]
        df.loc[idx, "amount"] = round(original * random.uniform(0.5, 1.5), 2)

    # 2. ~1% orphaned payments (order_id that matches nothing)
    orphan_idx = random.sample(range(len(df)), int(len(df) * 0.01))
    for idx in orphan_idx:
        df.loc[idx, "order_id"] = str(uuid.uuid4())

    # 3. ~1.5% exact duplicates
    n_dupes = int(len(df) * 0.015)
    dupes = df.sample(n=n_dupes, random_state=42)
    df = pd.concat([df, dupes], ignore_index=True)

    return df


CURRENCY_TO_COUNTRY = {
    "NGN": "Nigeria", "KES": "Kenya", "GHS": "Ghana", "TZS": "Tanzania",
    "ZAR": "South Africa", "EGP": "Egypt", "UGX": "Uganda", "RWF": "Rwanda",
}


if __name__ == "__main__":
    orders = pd.read_csv("data/raw/orders.csv")
    payments_df = generate_payments(orders)

    payments_df.to_csv("data/raw/payments.csv", index=False)

    print(f"Generated {len(payments_df)} payment records (incl. duplicates)")
    print(f"Payment methods: {payments_df['payment_method'].value_counts().to_dict()}")
    print(f"Statuses: {payments_df['status'].value_counts().to_dict()}")
    print(f"Failed payments by reason: {payments_df[payments_df['status'] == 'failed']['failure_reason'].value_counts().to_dict()}")
    print(f"Orphaned payments: {(~payments_df['order_id'].isin(orders['order_id'])).sum()}")
    print(f"Duplicate rows: {payments_df.duplicated().sum()}")