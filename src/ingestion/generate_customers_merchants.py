"""
Generates synthetic customer and merchant data for the
African Commerce & Payments Intelligence Platform.

Names, phone numbers, and business names are country-appropriate
(hand-curated reference pools + real country dialing codes).

Intentionally includes realistic data quality problems:
- missing emails/phone numbers
- duplicate customer records
- invalid phone number formats ("N/A")
- outlier signup dates (plausible: early adopters or future data-entry errors)
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

# Hand-curated, country-appropriate name pools (reference data)
NAME_POOLS = {
    "Nigeria": {
        "first": ["Chidi", "Ngozi", "Emeka", "Adaeze", "Tunde", "Funke", "Ibrahim", "Amina", "Chinedu", "Yemi"],
        "last": ["Okafor", "Adeyemi", "Ogunleye", "Adebayo", "Chukwu", "Bello", "Okonkwo", "Eze", "Balogun"],
    },
    "Kenya": {
        "first": ["Amina", "Wanjiku", "Njeri", "Kevin", "Faith", "Brian", "Mercy", "Joseph", "Sharon", "Dennis"],
        "last": ["Otieno", "Mwangi", "Wanjiru", "Kamau", "Achieng", "Korir", "Njoroge", "Chebet", "Mutiso"],
    },
    "Ghana": {
        "first": ["Kwame", "Akosua", "Kwesi", "Ama", "Yaw", "Efua", "Kofi", "Abena", "Kwabena", "Adjoa"],
        "last": ["Mensah", "Owusu", "Boateng", "Asante", "Appiah", "Darko", "Ampofo", "Tetteh"],
    },
    "Tanzania": {
        "first": ["Juma", "Amina", "Baraka", "Neema", "Zawadi", "Tumaini", "Asha", "Emmanuel", "Fatuma", "Peter"],
        "last": ["Mushi", "Massawe", "Kimaro", "Ndosi", "Shayo", "Mahenge", "Mwakalinga", "Kessy"],
    },
    "South Africa": {
        "first": ["Thabo", "Lerato", "Sipho", "Zanele", "Nomvula", "Kagiso", "Ayanda", "Thandiwe", "Sibusiso", "Naledi"],
        "last": ["Ndlovu", "Mokoena", "Dlamini", "Khumalo", "Nkosi", "Mahlangu", "Zulu", "Mthembu"],
    },
    "Egypt": {
        "first": ["Ahmed", "Fatima", "Mohamed", "Aisha", "Youssef", "Mariam", "Omar", "Layla", "Hassan", "Nour"],
        "last": ["Hassan", "Ibrahim", "Mansour", "Farouk", "Khalil", "Abdelrahman", "El-Sayed", "Shafik"],
    },
    "Uganda": {
        "first": ["Nakato", "Kato", "Joseph", "Grace", "Betty", "Musa", "Sarah", "Patrick", "Rebecca", "Isaac"],
        "last": ["Okello", "Mukasa", "Kabuye", "Wasswa", "Nabukenya", "Tumusiime", "Ssentongo", "Kirabo"],
    },
    "Rwanda": {
        "first": ["Jean", "Claudine", "Eric", "Aline", "Emmanuel", "Divine", "Patrick", "Sandrine", "Innocent", "Josiane"],
        "last": ["Mugisha", "Uwimana", "Nkurunziza", "Habimana", "Mukamana", "Ingabire", "Niyonkuru", "Bizimana"],
    },
}

# Real mobile-number prefixes per country: country code + valid operator prefixes
PHONE_RULES = {
    "Nigeria": {"code": "+234", "prefixes": ["803", "806", "810", "813", "816", "901"], "digits_after": 7},
    "Kenya": {"code": "+254", "prefixes": ["712", "720", "733", "745", "799"], "digits_after": 6},
    "Ghana": {"code": "+233", "prefixes": ["24", "54", "20", "26"], "digits_after": 7},
    "Tanzania": {"code": "+255", "prefixes": ["712", "754", "765", "782"], "digits_after": 6},
    "South Africa": {"code": "+27", "prefixes": ["71", "72", "82", "83"], "digits_after": 7},
    "Egypt": {"code": "+20", "prefixes": ["100", "101", "106", "110", "111"], "digits_after": 7},
    "Uganda": {"code": "+256", "prefixes": ["77", "78", "70", "75"], "digits_after": 7},
    "Rwanda": {"code": "+250", "prefixes": ["78", "72", "73"], "digits_after": 6},
}

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

PHONE_FORMATTERS = [
    lambda c, r: f"{c} {r[:3]} {r[3:6]} {r[6:]}",
    lambda c, r: f"{c}{r}",
    lambda c, r: f"{c}-{r[:3]}-{r[3:6]}-{r[6:]}",
    lambda c, r: f"{c}.{r[:3]}.{r[3:6]}.{r[6:]}",
]


def random_name(country: str) -> tuple[str, str]:
    pool = NAME_POOLS[country]
    return random.choice(pool["first"]), random.choice(pool["last"])


def random_phone(country: str) -> str:
    """Country-correct mobile number, with realistic formatting variety."""
    rules = PHONE_RULES[country]
    prefix = random.choice(rules["prefixes"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(rules["digits_after"]))
    digits = prefix + rest
    formatter = random.choice(PHONE_FORMATTERS)
    return formatter(rules["code"], digits)


def random_email(first_name: str, last_name: str) -> str:
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@{random.choice(EMAIL_DOMAINS)}"


def random_signup_date(outlier: bool = False) -> datetime:
    now = datetime.now()
    if outlier:
        if random.random() < 0.5:
            # Plausible early adopters: mobile-money era, 2015-2022
            start = datetime(2015, 1, 1)
            return start + timedelta(days=random.randint(0, (datetime(2022, 1, 1) - start).days))
        # Data-entry errors: slightly future dates
        return now + timedelta(days=random.randint(30, 365))
    # Normal signups: within the last ~3 years
    return now - timedelta(days=random.randint(0, 3 * 365))


def generate_customers(n: int) -> pd.DataFrame:
    records = []
    for i in range(n):
        country = random.choice(AFRICAN_COUNTRIES)
        region = random.choice(REGIONS_BY_COUNTRY[country])
        first_name, last_name = random_name(country)
        email = None if random.random() < 0.04 else random_email(first_name, last_name)
        if random.random() < 0.03:
            phone = "N/A"
        else:
            phone = random_phone(country)
        signup_date = random_signup_date(outlier=random.random() < 0.02)

        records.append({
            "customer_id": str(uuid.uuid4()),
            "first_name": first_name,
            "last_name": last_name,
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
        first_name, last_name = random_name(country)
        business_type = random.choice(business_types)
        records.append({
            "merchant_id": str(uuid.uuid4()),
            "business_name": f"{last_name} {business_type}",
            "business_type": business_type,
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
    print(f"Invalid phone numbers (N/A): {(customers_df['phone_number'] == 'N/A').sum()}")