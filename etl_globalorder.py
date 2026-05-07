"""
ETL: GlobalOrder (flat) → normalized tables
Clears existing ecommerce data and inserts US-oriented data derived from GlobalOrder.
"""
import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "data" / "Ecommerce.db")
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()

# ─────────────────────────────────────────────
# 1. Add new columns (ignore error if already exists)
# ─────────────────────────────────────────────
new_cols = [
    ("Customer", "Gender",       "TEXT"),
    ("Customer", "Age",          "INTEGER"),
    ("Customer", "Segment",      "TEXT"),
    ("Customer", "LoyaltyScore", "REAL"),
    ("Order_",   "Priority",     "TEXT"),
    ("Order_",   "IsWeekend",    "INTEGER"),
]
for table, col, dtype in new_cols:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
        print(f"  + {table}.{col}")
    except Exception:
        print(f"  ~ {table}.{col} already exists, skipped")

# ─────────────────────────────────────────────
# 2. Clear existing data (order matters for FK)
# ─────────────────────────────────────────────
for table in ["Review", "OrderExtra", "OrderItem", "SKU", "Order_", "Customer", "Product", "Category"]:
    conn.execute(f"DELETE FROM {table}")
    print(f"  cleared {table}")

# ─────────────────────────────────────────────
# 3. Load GlobalOrder
# ─────────────────────────────────────────────
cur.execute("SELECT * FROM GlobalOrder")
cols = [d[0] for d in cur.description]
rows = [dict(zip(cols, r)) for r in cur.fetchall()]
print(f"  loaded {len(rows)} rows from GlobalOrder")

# ─────────────────────────────────────────────
# 4. Category (parent → sub_category hierarchy)
# ─────────────────────────────────────────────
parent_cats = sorted({r["category"] for r in rows})
cat_id_map = {}  # name → CategoryId

for i, name in enumerate(parent_cats, start=1):
    cat_id_map[name] = i
    conn.execute(
        "INSERT INTO Category (CategoryId, Name, ParentCategoryId) VALUES (?,?,NULL)",
        (i, name)
    )

sub_cats = sorted({(r["sub_category"], r["category"]) for r in rows if r["sub_category"]})
next_id = len(parent_cats) + 1
for sub_name, parent_name in sub_cats:
    cat_id_map[sub_name] = next_id
    conn.execute(
        "INSERT INTO Category (CategoryId, Name, ParentCategoryId) VALUES (?,?,?)",
        (next_id, sub_name, cat_id_map[parent_name])
    )
    next_id += 1

print(f"  inserted {len(cat_id_map)} categories")

# ─────────────────────────────────────────────
# 5. Product (deduplicate by product_id)
# ─────────────────────────────────────────────
seen_products = {}
prod_id_map = {}  # str_id → int_id

for r in rows:
    pid = r["product_id"]
    if pid in seen_products:
        continue
    int_id = len(prod_id_map) + 1
    prod_id_map[pid] = int_id
    # prefer sub_category for CategoryId, fall back to parent
    cat_key = r["sub_category"] if r["sub_category"] in cat_id_map else r["category"]
    conn.execute(
        "INSERT INTO Product (ProductId, Name, CategoryId, Brand, Price, Stock, Status) VALUES (?,?,?,?,?,?,?)",
        (int_id, r["product_name"], cat_id_map.get(cat_key), r["brand"],
         r["unit_price_usd"], r["stock_quantity"], "Active")
    )
    seen_products[pid] = True

print(f"  inserted {len(prod_id_map)} products")

# ─────────────────────────────────────────────
# 6. Customer (deduplicate by customer_id)
# ─────────────────────────────────────────────
seen_customers = {}
cust_id_map = {}  # str_id → int_id

for r in rows:
    cid = r["customer_id"]
    if cid in seen_customers:
        continue
    int_id = len(cust_id_map) + 1
    cust_id_map[cid] = int_id
    conn.execute(
        """INSERT INTO Customer
           (CustomerId, Name, Email, City, Province, Phone, RegisterDate,
            Gender, Age, Segment, LoyaltyScore)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (int_id, cid, None,
         r["city"], r["country"], None, r["account_creation_date"],
         r["gender"], r["age"], r["customer_segment"], r["customer_loyalty_score"])
    )
    seen_customers[cid] = True

print(f"  inserted {len(cust_id_map)} customers")

# ─────────────────────────────────────────────
# 7. Order_ + OrderItem + OrderExtra + Review
# ─────────────────────────────────────────────
ord_id_map = {}  # str_id → int_id
review_id = 1

for r in rows:
    oid = r["order_id"]
    ord_int = len(ord_id_map) + 1
    ord_id_map[oid] = ord_int
    cust_int = cust_id_map[r["customer_id"]]
    prod_int = prod_id_map[r["product_id"]]

    # Order_
    conn.execute(
        """INSERT INTO Order_
           (OrderId, CustomerId, OrderDate, Status, TotalAmount,
            ShippingCity, ShippingProvince, Priority, IsWeekend)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (ord_int, cust_int, r["order_date"], r["order_status"], r["total_price_usd"],
         r["city"], r["country"], r["order_priority"], r["is_weekend"])
    )

    # OrderItem (one item per order in GlobalOrder)
    discount_coeff = round(1.0 - (r["discount_percent"] or 0) / 100.0, 4)
    conn.execute(
        """INSERT INTO OrderItem
           (OrderId, ProductId, SkuId, Quantity, UnitPrice, Discount)
           VALUES (?,?,?,?,?,?)""",
        (ord_int, prod_int, None, r["quantity"], r["unit_price_usd"], discount_coeff)
    )

    # OrderExtra
    conn.execute(
        """INSERT INTO OrderExtra
           (OrderId, PaymentMethod, PaymentStatus, ShippingMethod, ShippingCostUSD,
            DeliveryDays, DeliveryStatus, WarehouseLocation, CampaignSource,
            DeviceType, TrafficSource, FraudRiskScore, CouponUsed, CouponCode, ReturnReason)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (ord_int, r["payment_method"], r["payment_status"], r["shipping_method"],
         r["shipping_cost_usd"], r["delivery_days"], r["delivery_status"],
         r["warehouse_location"], r["campaign_source"], r["device_type"],
         r["traffic_source"], r["fraud_risk_score"], r["coupon_used"],
         r["coupon_code"], r["return_reason"])
    )

    # Review (only when rating exists)
    if r["rating"] is not None:
        conn.execute(
            """INSERT INTO Review
               (ReviewId, CustomerId, ProductId, Rating, Content, CreateDate)
               VALUES (?,?,?,?,?,?)""",
            (review_id, cust_int, prod_int, r["rating"],
             r["customer_feedback"], r["order_date"])
        )
        review_id += 1

print(f"  inserted {len(ord_id_map)} orders, {len(ord_id_map)} order items, "
      f"{len(ord_id_map)} order extras, {review_id-1} reviews")

# ─────────────────────────────────────────────
# 8. Commit & verify
# ─────────────────────────────────────────────
conn.commit()
conn.execute("PRAGMA foreign_keys = ON")

print("\n── Row counts ──")
for table in ["Category", "Product", "Customer", "Order_", "OrderItem", "OrderExtra", "Review", "SKU"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table:12s}: {cur.fetchone()[0]}")

conn.close()
print("\nDone.")
