"""
Weekly incremental ETL: flat GlobalOrder-format CSV → normalized tables

Usage:
    python etl_increment.py --file weekly_2026_W17.csv

Input CSV columns (same as GlobalOrder table):
    order_id, order_date, order_status, order_priority, is_weekend,
    customer_id, gender, age, customer_segment, country, city,
    customer_loyalty_score, total_orders_by_customer, account_creation_date,
    product_id, product_name, category, sub_category, brand,
    product_rating_avg, product_reviews_count, stock_quantity,
    unit_price_usd, quantity, discount_percent, discount_amount_usd,
    total_price_usd, cost_usd, profit_usd, profit_margin_percent, tax_usd,
    shipping_method, shipping_cost_usd, delivery_days, shipping_country,
    warehouse_location, delivery_status, payment_method, payment_status,
    installment_plan, coupon_used, coupon_code, campaign_source, device_type,
    traffic_source, session_duration_minutes, pages_visited,
    abandoned_cart_before, rating, review_sentiment, customer_feedback,
    fraud_risk_score, support_ticket_created, return_reason
"""
import argparse
import csv
import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "data" / "Ecommerce.db")


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_id(cur, table: str, id_col: str) -> int:
    cur.execute(f"SELECT MAX({id_col}) FROM {table}")
    val = cur.fetchone()[0]
    return (val or 0) + 1


def run(rows: list[dict], conn: sqlite3.Connection):
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys = OFF")

    stats = {"category": 0, "customer": 0, "product": 0,
             "order": 0, "order_item": 0, "order_extra": 0, "review": 0,
             "skipped_orders": 0}

    # ── 1. Category: INSERT OR IGNORE (structure rarely changes) ──────────
    existing_cats = {r[0] for r in cur.execute("SELECT Name FROM Category")}

    for r in rows:
        for cat_name in [r["category"], r.get("sub_category")]:
            if cat_name and cat_name not in existing_cats:
                next_cat_id = next_id(cur, "Category", "CategoryId")
                # determine parent
                parent_id = None
                if cat_name == r.get("sub_category") and r["category"] in existing_cats:
                    cur.execute("SELECT CategoryId FROM Category WHERE Name=?", (r["category"],))
                    row = cur.fetchone()
                    parent_id = row[0] if row else None
                conn.execute(
                    "INSERT OR IGNORE INTO Category (CategoryId, Name, ParentCategoryId) VALUES (?,?,?)",
                    (next_cat_id, cat_name, parent_id)
                )
                existing_cats.add(cat_name)
                stats["category"] += 1

    # ── 2. Customer: UPSERT (segment and loyalty score can change) ─────────
    for r in rows:
        cur.execute("SELECT CustomerId FROM Customer WHERE SourceId=?", (r["customer_id"],))
        existing = cur.fetchone()
        if existing:
            conn.execute(
                """UPDATE Customer SET
                   City=?, Province=?, RegisterDate=?,
                   Gender=?, Age=?, Segment=?, LoyaltyScore=?
                   WHERE SourceId=?""",
                (r["city"], r["country"], r["account_creation_date"],
                 r["gender"], r["age"], r["customer_segment"],
                 r["customer_loyalty_score"], r["customer_id"])
            )
        else:
            new_id = next_id(cur, "Customer", "CustomerId")
            conn.execute(
                """INSERT INTO Customer
                   (CustomerId, Name, City, Province, RegisterDate,
                    Gender, Age, Segment, LoyaltyScore, SourceId)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (new_id, r["customer_id"], r["city"], r["country"],
                 r["account_creation_date"], r["gender"], r["age"],
                 r["customer_segment"], r["customer_loyalty_score"], r["customer_id"])
            )
            stats["customer"] += 1

    # ── 3. Product: UPSERT (stock and price can change) ───────────────────
    for r in rows:
        cur.execute("SELECT ProductId FROM Product WHERE SourceId=?", (r["product_id"],))
        existing = cur.fetchone()
        cat_key = r.get("sub_category") or r["category"]
        cur.execute("SELECT CategoryId FROM Category WHERE Name=?", (cat_key,))
        cat_row = cur.fetchone()
        cat_id = cat_row[0] if cat_row else None

        if existing:
            conn.execute(
                "UPDATE Product SET Price=?, Stock=?, CategoryId=? WHERE SourceId=?",
                (r["unit_price_usd"], r["stock_quantity"], cat_id, r["product_id"])
            )
        else:
            new_id = next_id(cur, "Product", "ProductId")
            conn.execute(
                """INSERT INTO Product
                   (ProductId, Name, CategoryId, Brand, Price, Stock, Status, SourceId)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (new_id, r["product_name"], cat_id, r["brand"],
                 r["unit_price_usd"], r["stock_quantity"], "Active", r["product_id"])
            )
            stats["product"] += 1

    # ── 4. Order_ / OrderItem / OrderExtra / Review: INSERT only ──────────
    for r in rows:
        # skip if order already exists
        cur.execute("SELECT OrderId FROM Order_ WHERE SourceId=?", (r["order_id"],))
        if cur.fetchone():
            stats["skipped_orders"] += 1
            continue

        cur.execute("SELECT CustomerId FROM Customer WHERE SourceId=?", (r["customer_id"],))
        cust_id = cur.fetchone()[0]
        cur.execute("SELECT ProductId FROM Product WHERE SourceId=?", (r["product_id"],))
        prod_id = cur.fetchone()[0]

        ord_int = next_id(cur, "Order_", "OrderId")

        conn.execute(
            """INSERT INTO Order_
               (OrderId, CustomerId, OrderDate, Status, TotalAmount,
                ShippingCity, ShippingProvince, Priority, IsWeekend, SourceId)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (ord_int, cust_id, r["order_date"], r["order_status"],
             r["total_price_usd"], r["city"], r["country"],
             r["order_priority"], r["is_weekend"], r["order_id"])
        )
        stats["order"] += 1

        discount_coeff = round(1.0 - float(r["discount_percent"] or 0) / 100.0, 4)
        item_id = next_id(cur, "OrderItem", "OrderItemId")
        conn.execute(
            """INSERT INTO OrderItem
               (OrderItemId, OrderId, ProductId, SkuId, Quantity, UnitPrice, Discount)
               VALUES (?,?,?,?,?,?,?)""",
            (item_id, ord_int, prod_id, None,
             r["quantity"], r["unit_price_usd"], discount_coeff)
        )
        stats["order_item"] += 1

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
        stats["order_extra"] += 1

        if r.get("rating"):
            rev_id = next_id(cur, "Review", "ReviewId")
            conn.execute(
                """INSERT INTO Review
                   (ReviewId, CustomerId, ProductId, Rating, Content, CreateDate)
                   VALUES (?,?,?,?,?,?)""",
                (rev_id, cust_id, prod_id, r["rating"],
                 r.get("customer_feedback"), r["order_date"])
            )
            stats["review"] += 1

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to weekly CSV file")
    args = parser.parse_args()

    rows = load_csv(args.file)
    print(f"Loaded {len(rows)} rows from {args.file}")

    conn = sqlite3.connect(DB_PATH)
    stats = run(rows, conn)
    conn.close()

    print("\n── Result ──")
    print(f"  New categories : {stats['category']}")
    print(f"  New customers  : {stats['customer']}")
    print(f"  New products   : {stats['product']}")
    print(f"  New orders     : {stats['order']}")
    print(f"  Skipped orders : {stats['skipped_orders']} (already in DB)")
    print(f"  Reviews        : {stats['review']}")
    print("Done.")


if __name__ == "__main__":
    main()
