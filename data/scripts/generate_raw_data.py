"""Generate synthetic supermarket data for the retail data platform.

Produces CSVs in data/raw/ that mimic the source systems of an online
supermarket: customers, suppliers, products, orders, order items,
payments, deliveries, inventory snapshots, and supplier orders.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------- config
SEED = 42
N_CUSTOMERS = 500
N_SUPPLIERS = 30
N_PRODUCTS = 200
N_ORDERS = 5000
DAYS_OF_HISTORY = 180
N_WAREHOUSES = 2
N_ZONES = 6
N_DRIVERS = 25

TODAY = datetime(2026, 10, 1)
START_DATE = TODAY - timedelta(days=DAYS_OF_HISTORY)

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

CHANNELS = ["express", "scheduled"]
ORDER_STATUSES = ["delivered", "delivered", "delivered", "cancelled", "returned"]
PAYMENT_METHODS = ["mpesa", "card", "cash"]
PAYMENT_STATUSES = ["paid", "paid", "paid", "pending", "refunded"]
CATEGORIES = ["produce", "dairy", "bakery", "meat", "pantry", "beverages", "household"]
ZONES = ["westlands", "karen", "kilimani", "eastlands", "southb", "riverside"]
WAREHOUSES = ["nairobi_main", "nairobi_north"]


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(
        seconds=random.randint(0, int(delta.total_seconds()))
    )


# ---------------------------------------------------------------- suppliers
def gen_suppliers() -> pd.DataFrame:
    rows = []
    for i in range(1, N_SUPPLIERS + 1):
        rows.append({
            "supplier_id": f"SUP{i:04d}",
            "supplier_name": fake.company(),
            "lead_time_days": random.randint(1, 14),
            "payment_terms": random.choice(["net_15", "net_30", "net_45"]),
            "country": "Kenya",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- products
def gen_products(suppliers: pd.DataFrame) -> pd.DataFrame:
    supplier_ids = suppliers["supplier_id"].tolist()
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        unit_cost = round(random.uniform(20, 800), 2)
        markup = random.uniform(1.15, 1.6)
        rows.append({
            "product_id": f"PRD{i:05d}",
            "product_name": fake.catch_phrase(),
            "category": random.choice(CATEGORIES),
            "brand": fake.company(),
            "unit_cost": unit_cost,
            "unit_price": round(unit_cost * markup, 2),
            "supplier_id": random.choice(supplier_ids),
            "perishable_flag": random.choice([True, False]),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- customers
def gen_customers() -> pd.DataFrame:
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        signup = random_date(START_DATE - timedelta(days=365), TODAY)
        rows.append({
            "customer_id": f"CUS{i:05d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.msisdn()[:12],
            "city": "Nairobi",
            "signup_date": signup.date().isoformat(),
            "acquisition_channel": random.choice(
                ["organic", "referral", "paid_social", "paid_search"]
            ),
            "segment": random.choice(["new", "returning", "vip"]),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- orders
def gen_orders(customers: pd.DataFrame) -> pd.DataFrame:
    customer_ids = customers["customer_id"].tolist()
    rows = []
    for i in range(1, N_ORDERS + 1):
        order_dt = random_date(START_DATE, TODAY)
        gross = round(random.uniform(300, 12000), 2)
        discount = round(gross * random.uniform(0, 0.15), 2)
        delivery_fee = random.choice([0, 100, 150, 200])
        net = round(gross - discount + delivery_fee, 2)
        rows.append({
            "order_id": f"ORD{i:06d}",
            "customer_id": random.choice(customer_ids),
            "order_date": order_dt.date().isoformat(),
            "order_timestamp": order_dt.isoformat(),
            "order_status": random.choice(ORDER_STATUSES),
            "channel": random.choice(CHANNELS),
            "delivery_zone_id": f"ZN{random.randint(1, N_ZONES):03d}",
            "warehouse_id": f"WH{random.randint(1, N_WAREHOUSES):03d}",
            "gross_amount": gross,
            "discount_amount": discount,
            "delivery_fee": delivery_fee,
            "net_revenue": net,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- order items
def gen_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    product_lookup = products.set_index("product_id")[
        ["unit_price", "unit_cost"]
    ].to_dict("index")
    product_ids = list(product_lookup.keys())
    rows = []
    item_id = 1
    for order_id in orders["order_id"]:
        n_items = random.randint(1, 8)
        for _ in range(n_items):
            pid = random.choice(product_ids)
            qty = random.randint(1, 5)
            price = product_lookup[pid]["unit_price"]
            cost = product_lookup[pid]["unit_cost"]
            rows.append({
                "order_item_id": f"OI{item_id:08d}",
                "order_id": order_id,
                "product_id": pid,
                "quantity": qty,
                "unit_price": price,
                "unit_cost": cost,
                "line_total": round(price * qty, 2),
            })
            item_id += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- payments
def gen_payments(orders: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, row in orders.iterrows():
        order_dt = datetime.fromisoformat(row["order_timestamp"])
        paid_dt = order_dt + timedelta(minutes=random.randint(1, 60))
        rows.append({
            "payment_id": f"PAY{i + 1:07d}",
            "order_id": row["order_id"],
            "method": random.choice(PAYMENT_METHODS),
            "amount": row["net_revenue"],
            "status": random.choice(PAYMENT_STATUSES),
            "paid_at": paid_dt.isoformat(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- deliveries
def gen_deliveries(orders: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, row in orders.iterrows():
        order_dt = datetime.fromisoformat(row["order_timestamp"])
        promised = order_dt + timedelta(hours=random.choice([2, 4, 24, 48]))
        dispatch = order_dt + timedelta(minutes=random.randint(20, 180))
        delivered = dispatch + timedelta(minutes=random.randint(20, 240))
        status = "delivered"
        if delivered > promised:
            status = random.choice(["delivered_late", "delivered_late", "failed"])
        rows.append({
            "delivery_id": f"DLV{i + 1:07d}",
            "order_id": row["order_id"],
            "dispatch_at": dispatch.isoformat(),
            "delivered_at": delivered.isoformat(),
            "promised_at": promised.isoformat(),
            "delivery_status": status,
            "driver_id": f"DRV{random.randint(1, N_DRIVERS):03d}",
            "zone_id": row["delivery_zone_id"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- inventory
def gen_inventory(products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day_offset in range(DAYS_OF_HISTORY):
        snapshot_date = (START_DATE + timedelta(days=day_offset)).date().isoformat()
        for pid in products["product_id"]:
            for wh in range(1, N_WAREHOUSES + 1):
                on_hand = random.randint(0, 500)
                reserved = random.randint(0, min(on_hand, 50))
                rows.append({
                    "snapshot_date": snapshot_date,
                    "product_id": pid,
                    "warehouse_id": f"WH{wh:03d}",
                    "qty_on_hand": on_hand,
                    "qty_reserved": reserved,
                    "qty_available": on_hand - reserved,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- supplier orders
def gen_supplier_orders(suppliers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sup_lookup = suppliers.set_index("supplier_id")["lead_time_days"].to_dict()
    for i in range(1, 1501):
        sup_id = random.choice(list(sup_lookup.keys()))
        pid = random.choice(products["product_id"].tolist())
        ordered_at = random_date(START_DATE, TODAY)
        lead = sup_lookup[sup_id]
        received_at = ordered_at + timedelta(days=lead + random.randint(-2, 5))
        ordered_qty = random.randint(20, 500)
        received_qty = max(0, ordered_qty - random.randint(0, 20))
        rows.append({
            "supplier_order_id": f"SO{i:06d}",
            "supplier_id": sup_id,
            "product_id": pid,
            "ordered_qty": ordered_qty,
            "received_qty": received_qty,
            "ordered_at": ordered_at.isoformat(),
            "received_at": received_at.isoformat(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main
def main() -> None:
    print("Generating suppliers...")
    suppliers = gen_suppliers()
    suppliers.to_csv(RAW_DIR / "suppliers.csv", index=False)

    print("Generating products...")
    products = gen_products(suppliers)
    products.to_csv(RAW_DIR / "products.csv", index=False)

    print("Generating customers...")
    customers = gen_customers()
    customers.to_csv(RAW_DIR / "customers.csv", index=False)

    print("Generating orders...")
    orders = gen_orders(customers)
    orders.to_csv(RAW_DIR / "orders.csv", index=False)

    print("Generating order items...")
    order_items = gen_order_items(orders, products)
    order_items.to_csv(RAW_DIR / "order_items.csv", index=False)

    print("Generating payments...")
    payments = gen_payments(orders)
    payments.to_csv(RAW_DIR / "payments.csv", index=False)

    print("Generating deliveries...")
    deliveries = gen_deliveries(orders)
    deliveries.to_csv(RAW_DIR / "deliveries.csv", index=False)

    print("Generating inventory snapshots (this takes a moment)...")
    inventory = gen_inventory(products)
    inventory.to_csv(RAW_DIR / "inventory_snapshots.csv", index=False)

    print("Generating supplier orders...")
    supplier_orders = gen_supplier_orders(suppliers, products)
    supplier_orders.to_csv(RAW_DIR / "supplier_orders.csv", index=False)

    print("\nRow counts:")
    for name, df in [
        ("customers", customers),
        ("suppliers", suppliers),
        ("products", products),
        ("orders", orders),
        ("order_items", order_items),
        ("payments", payments),
        ("deliveries", deliveries),
        ("inventory_snapshots", inventory),
        ("supplier_orders", supplier_orders),
    ]:
        print(f"  {name:22s} {len(df):>10,}")


if __name__ == "__main__":
    main()