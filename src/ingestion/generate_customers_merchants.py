"""
Generates synthetic customer and merchant data for the
African Commerce & Payments Intelligence Platform.

Intentionally includes realistic data quality problems:
- missing emails/phone numbers
- duplicate customer records
- invalid phone number formats
- outlier signup dates
"""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker(["en_US"])
Faker.seed(42)
random.seed(42)

AFRICAN_COUNTRIES = ["Nigeria", "Kenya", "Ghana", "Tanzania", "South Africa", "Egypt", "Uganda", "Rwanda"]
REGIONS_BY_COUNTRY = {
    "Nigeria": ["Lagos", "Abuja", "Kano", "Ibadan"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu"],
    "Ghana": ["Accra", "Kumasi", "Tamale"],
    "Tanzania": ["Dar es Salaam", "Dodoma", "Arusha"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban"],
    "Egypt": ["Cairo", "Alexandria", "Giza"],
    "Uganda": ["Kampala", "Entebbe"],
    "Rwanda": ["Kigali", "Butare"],
}


def random_signup_date(outlier: bool = False) -> datetime:
    if outlier:
        if random.random() < 0.5:
            return datetime(1999, 1, 1) + timedelta(days=random.randint(0, 3000))
        return datetime.now() + timedelta(days=random.randint(30, 400))
    return datetime.now() - timedelta(days=random.randint(0, 3 * 365))


def generate_customers(n: int) -> pd.DataFrame:
    records = []
    for i in range(n):
        country = random.choice(AFRICAN_COUNTRIES)
        region = random.choice(REGIONS_BY_COUNTRY[country])
        email = None if random.random() < 0.04 else fake.email()
        if random.random() < 0.03:
            phone = "N/A"
        else:
            phone = fake.phone_number()
        signup_date = random_signup_date(outlier=random.random() < 0.02)

        records.append({
            "customer_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "phone_number": phone,
            "country": country,
            "region": region,
            "signup_date": signup_date,
        })

    df = pd.DataFrame(records)
    n_dupes = int(len(df) * 0.015)
    dupes = df.sample(n=n_dupes, random_state=42)
    df = pd.concat([df, dupes], ignore_index=True)
    return df


def generate_merchants(n: int) -> pd.DataFrame:
    business_types = ["Retail", "Restaurant", "Electronics", "Fashion", "Groceries", "Pharmacy", "Services"]
    records = []
    for i in range(n):
        country = random.choice(AFRICAN_COUNTRIES)
        region = random.choice(REGIONS_BY_COUNTRY[country])
        records.append({
            "merchant_id": str(uuid.uuid4()),
            "business_name": fake.company(),
            "business_type": random.choice(business_types),
            "country": country,
            "region": region,
            "joined_date": random_signup_date(outlier=random.random() < 0.01),
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    customers_df = generate_customers(10_000)
    merchants_df = generate_merchants(300)

    customers_df.to_csv("data/raw/customers.csv", index=False)
    merchants_df.to_csv("data/raw/merchants.csv", index=False)

    print(f"Generated {len(customers_df)} customer records (incl. duplicates)")
    print(f"Generated {len(merchants_df)} merchant records")
    print(f"Missing emails: {customers_df['email'].isna().sum()}")
    print(f"Invalid phone numbers: {(customers_df['phone_number'] == 'N/A').sum()}")