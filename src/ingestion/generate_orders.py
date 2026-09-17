"""
Generates synthetic order data for the African Commerce & Payments
Intelligence Platform.

Orders reference real customer_id / merchant_id values from the
customers.csv and merchants.csv files (foreign keys).

Intentionally includes realistic data quality problems:
- orphaned orders (customer_id that exists nowhere)
- orders dated before the customer signed up / in the future
- zero or negative amounts (outliers)
- duplicate order records
"""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd



random.seed(42)

CURRENCY_BY_COUNTRY = {
    "Nigeria": "NGN",
    "Kenya": "KES",
    "Ghana": "GHS",
    "Tanzania": "TZS",
    "South Africa": "ZAR",
    "Egypt": "EGP",
    "Uganda": "UGX",
    "Rwanda": "RWF",
}

# Plausible per-order totals in local currency
AMOUNT_RANGE_BY_COUNTRY = {
    "Nigeria": (3000, 180000),
    "Kenya": (250, 15000),
    "Ghana": (50, 2500),
    "Tanzania": (5000, 250000),
    "South Africa": (100, 4000),
    "Egypt": (150, 9000),
    "Uganda": (8000, 400000),
    "Rwanda": (2000, 120000),
}

ORDER_STATUSES = ["completed", "completed", "completed", "completed",  # weight toward completed
                  "cancelled", "returned"]


def load_entities():
    """Load customers and merchants generated in the previous step."""
    customers = pd.read_csv("data/raw/customers.csv")
    merchants = pd.read_csv("data/raw/merchants.csv")

    # Deduplicate so we only sample unique, real IDs
    unique_customers = customers.drop_duplicates(subset="customer_id")
    return unique_customers, merchants


def generate_orders(n: int, customers: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now()
    records = []

    # Build fast lookup: customer_id -> (signup_date, country)
    customer_rows = customers[["customer_id", "country", "signup_date"]].to_dict("records")
    merchant_ids = merchants["merchant_id"].tolist()

    for i in range(n):
        cust = random.choice(customer_rows)
        country = cust["country"]
        signup_date = datetime.fromisoformat(cust["signup_date"])

        # An order must happen after signup, but before "now"
        days_open = (now - signup_date).days
        if days_open < 1:
            days_open = 1
        order_date = signup_date + timedelta(days=random.randint(0, days_open))

        amount = round(random.uniform(*AMOUNT_RANGE_BY_COUNTRY[country]), 2)

        records.append({
            "order_id": str(uuid.uuid4()),
            "customer_id": cust["customer_id"],
            "merchant_id": random.choice(merchant_ids),
            "order_date": order_date,
            "status": random.choice(ORDER_STATUSES),
            "currency": CURRENCY_BY_COUNTRY[country],
            "amount": amount,
            "item_count": random.randint(1, 8),
        })

    df = pd.DataFrame(records)

    # --- Intentional messiness ---

    # 1. ~2% orphaned orders: customer_id that matches no real customer
    orphan_mask = random.sample(range(len(df)), int(len(df) * 0.02))
    for idx in orphan_mask:
        df.loc[idx, "customer_id"] = str(uuid.uuid4())

    # 2. ~1% zero/negative amounts (outliers)
    outlier_idx = random.sample(range(len(df)), int(len(df) * 0.01))
    for idx in outlier_idx:
        df.loc[idx, "amount"] = random.choice([0.0, round(random.uniform(-500, -10), 2)])

    # 3. ~1.5% exact duplicate rows
    n_dupes = int(len(df) * 0.015)
    dupes = df.sample(n=n_dupes, random_state=42)
    df = pd.concat([df, dupes], ignore_index=True)

    return df


if __name__ == "__main__":
    customers, merchants = load_entities()
    orders_df = generate_orders(25_000, customers, merchants)

    orders_df.to_csv("data/raw/orders.csv", index=False)

    print(f"Generated {len(orders_df)} order records (incl. duplicates)")
    print(f"Unique customers referenced: {orders_df['customer_id'].nunique()}")
    print(f"Orphaned customer_ids: "
          f"{(~orders_df['customer_id'].isin(customers['customer_id'])).sum()}")
    print(f"Zero/negative amounts: {(orders_df['amount'] <= 0).sum()}")
    print(f"Duplicate rows: {orders_df.duplicated().sum()}")