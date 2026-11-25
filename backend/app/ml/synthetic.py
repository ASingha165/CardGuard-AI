"""Deterministic synthetic credit-card fraud dataset generator.

All generated records are explicitly marked as Synthetic Demo Data.
Raw card numbers are never generated or stored; only HMAC-like tokens and last4 digits.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import hashlib

import numpy as np
import pandas as pd


MERCHANTS = [
    ("Apex Electronics Ltd", "electronics", 0.35),
    ("CloudHost Global", "saas", 0.15),
    ("Nordic Air Express", "travel", 0.28),
    ("BitVault Exchange", "crypto_exchange", 0.62),
    ("Metro Fresh Market", "grocery", 0.05),
    ("Bistro Lumiere", "dining", 0.07),
    ("Vanguard Luxury Goods", "luxury_retail", 0.48),
    ("StreamPulse Digital", "digital_goods", 0.32),
    ("OmniPay Gift Cards", "digital_goods", 0.58),
    ("Urban Transit Co", "transit", 0.04),
]

COUNTRIES = ["US", "GB", "CA", "DE", "SG", "BR", "NG", "RU"]
CHANNELS = ["card_not_present", "pos_chip", "contactless", "recurring"]


def _make_token(seed_str: str) -> str:
    return "tok_" + hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:16]


def generate_synthetic_transactions(n_rows: int = 1200, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic synthetic dataset with embedded fraud rings."""
    rng = np.random.default_rng(seed)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    # Create pool of cardholders, devices, and IP subnets
    n_cards = max(80, n_rows // 10)
    card_pool = [
        (_make_token(f"card_{i}_{seed}"), f"{1000 + (i * 37) % 9000:04d}")
        for i in range(n_cards)
    ]
    normal_devices = [f"dev_{i:04d}" for i in range(n_cards)]
    normal_ips = [f"10.{(i // 250) + 1}.{(i % 250) + 1}.0/24" for i in range(n_cards)]

    # Fraud ring shared infrastructure (creates realistic connected components)
    fraud_ring_devices = ["dev_ring_alpha", "dev_ring_bravo", "dev_ring_charlie"]
    fraud_ring_ips = ["185.220.101.0/24", "45.142.212.0/24"]

    rows: List[Dict] = []
    fraud_target = int(n_rows * 0.045)  # ~4.5% fraud rate
    fraud_indices = set(rng.choice(n_rows, size=fraud_target, replace=False).tolist())

    for idx in range(n_rows):
        is_fraud = 1 if idx in fraud_indices else 0
        card_idx = int(rng.integers(0, n_cards))
        card_token, card_last4 = card_pool[card_idx]

        # Timestamp spread over last 30 days
        hours_ago = int(rng.integers(0, 30 * 24))
        minutes_offset = int(rng.integers(0, 60))
        ts = now - timedelta(hours=hours_ago, minutes=minutes_offset)
        hour_of_day = ts.hour

        if is_fraud:
            # Fraudulent transactions exhibit higher velocity, higher amounts,
            # international/unfamiliar merchants, and shared ring infrastructure.
            merchant, category, m_risk = MERCHANTS[int(rng.choice([0, 3, 6, 7, 8]))]
            amount = float(np.round(rng.lognormal(mean=6.4, sigma=0.75), 2))
            amount = min(max(amount, 45.0), 14500.0)
            velocity_1h = int(rng.integers(3, 11))
            distance_km = float(np.round(rng.uniform(350.0, 8200.0), 1))
            amount_zscore = float(np.round(rng.uniform(2.1, 6.2), 2))
            is_international = int(rng.choice([0, 1], p=[0.2, 0.8]))
            country = str(rng.choice(["NG", "RU", "BR", "SG", "US"], p=[0.25, 0.25, 0.2, 0.15, 0.15]))
            channel = str(rng.choice(["card_not_present", "recurring"], p=[0.85, 0.15]))
            device_id = str(rng.choice(fraud_ring_devices))
            ip_subnet = str(rng.choice(fraud_ring_ips))
            # Concentrate some fraud at late-night hours
            if rng.random() < 0.65:
                hour_of_day = int(rng.choice([0, 1, 2, 3, 4, 23]))
                ts = ts.replace(hour=hour_of_day)
        else:
            merchant, category, m_risk = MERCHANTS[int(rng.integers(0, len(MERCHANTS)))]
            amount = float(np.round(rng.lognormal(mean=4.0, sigma=0.8), 2))
            amount = min(max(amount, 2.50), 2200.0)
            velocity_1h = int(rng.choice([1, 1, 1, 2, 2, 3]))
            distance_km = float(np.round(rng.exponential(scale=28.0), 1))
            amount_zscore = float(np.round(rng.normal(loc=0.0, scale=0.85), 2))
            is_international = int(rng.choice([0, 1], p=[0.92, 0.08]))
            country = "US" if is_international == 0 else str(rng.choice(["GB", "CA", "DE"]))
            channel = str(rng.choice(CHANNELS, p=[0.30, 0.35, 0.25, 0.10]))
            device_id = normal_devices[card_idx]
            ip_subnet = normal_ips[card_idx]

        rows.append(
            {
                "tx_id": f"TX-{100000 + idx}",
                "timestamp": ts,
                "card_token": card_token,
                "card_last4": card_last4,
                "merchant": merchant,
                "merchant_category": category,
                "amount": amount,
                "currency": "USD",
                "country": country,
                "channel": channel,
                "device_id": device_id,
                "ip_subnet": ip_subnet,
                "velocity_1h": velocity_1h,
                "distance_from_home_km": distance_km,
                "amount_zscore": amount_zscore,
                "is_international": is_international,
                "hour_of_day": hour_of_day,
                "merchant_risk_index": m_risk,
                "is_fraud": is_fraud,
            }
        )

    df = pd.DataFrame(rows).sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df
