import csv
import os
import sqlite3
from pathlib import Path

from config import settings


_BOOTSTRAP_SQL = [
    """
    CREATE TABLE IF NOT EXISTS "Category" (
        "CategoryId" INTEGER PRIMARY KEY,
        "Name" TEXT,
        "ParentCategoryId" INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "Product" (
        "ProductId" INTEGER PRIMARY KEY,
        "Name" TEXT,
        "CategoryId" INTEGER,
        "Brand" TEXT,
        "Price" REAL,
        "Stock" INTEGER,
        "Status" TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "Customer" (
        "CustomerId" INTEGER PRIMARY KEY,
        "Name" TEXT,
        "City" TEXT,
        "Province" TEXT,
        "RegisterDate" TEXT,
        "Gender" TEXT,
        "Age" INTEGER,
        "Segment" TEXT,
        "LoyaltyScore" REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "Order_" (
        "OrderId" INTEGER PRIMARY KEY,
        "CustomerId" INTEGER,
        "OrderDate" TEXT,
        "Status" TEXT,
        "TotalAmount" REAL,
        "ShippingCity" TEXT,
        "ShippingProvince" TEXT,
        "Priority" TEXT,
        "IsWeekend" INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "OrderItem" (
        "OrderItemId" INTEGER PRIMARY KEY,
        "OrderId" INTEGER,
        "ProductId" INTEGER,
        "SkuId" INTEGER,
        "Quantity" INTEGER,
        "UnitPrice" REAL,
        "Discount" REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "OrderExtra" (
        "OrderId" INTEGER PRIMARY KEY,
        "PaymentMethod" TEXT,
        "PaymentStatus" TEXT,
        "ShippingMethod" TEXT,
        "ShippingCostUSD" REAL,
        "DeliveryDays" INTEGER,
        "DeliveryStatus" TEXT,
        "WarehouseLocation" TEXT,
        "CampaignSource" TEXT,
        "DeviceType" TEXT,
        "TrafficSource" TEXT,
        "FraudRiskScore" REAL,
        "CouponUsed" INTEGER,
        "CouponCode" TEXT,
        "ReturnReason" TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "Review" (
        "ReviewId" INTEGER PRIMARY KEY,
        "CustomerId" INTEGER,
        "ProductId" INTEGER,
        "Rating" REAL,
        "Content" TEXT,
        "CreateDate" TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "SKU" (
        "SkuId" INTEGER PRIMARY KEY,
        "ProductId" INTEGER,
        "Color" TEXT,
        "Storage" TEXT,
        "Size" TEXT,
        "Price" REAL,
        "Stock" INTEGER,
        "Status" TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS "GlobalOrder" (
        "OrderId" INTEGER PRIMARY KEY,
        "Country" TEXT,
        "State" TEXT,
        "City" TEXT,
        "OrderDate" TEXT,
        "Status" TEXT,
        "TotalAmount" REAL
    )
    """,
]

_SEED_ROWS = {
    "Category": [
        (1, "Electronics", None),
        (2, "Smartphones", 1),
        (3, "Clothing", None),
        (4, "Sneakers", 3),
    ],
    "Product": [
        (1, "Nike Air Max", 4, "Nike", 120.0, 100, "Active"),
        (2, "Samsung Galaxy S23", 2, "Samsung", 899.0, 50, "Active"),
        (3, "Apple iPhone 15", 2, "Apple", 999.0, 40, "Active"),
        (4, "Adidas Ultraboost", 4, "Adidas", 150.0, 80, "Active"),
        (5, "Sony WH-1000XM5", 1, "Sony", 349.0, 60, "Active"),
    ],
    "Customer": [
        (1, "Alice", "Los Angeles", "California", "2025-01-01", "Female", 30, "VIP", 95.0),
        (2, "Bob", "New York", "New York", "2025-01-02", "Male", 35, "Premium", 88.0),
        (3, "Carol", "San Francisco", "California", "2025-01-03", "Female", 29, "Regular", 70.0),
        (4, "Dave", "Chicago", "Illinois", "2025-01-04", "Male", 41, "VIP", 91.0),
        (5, "Eve", "Houston", "Texas", "2025-01-05", "Female", 33, "New", 64.0),
        (6, "Frank", "Miami", "Florida", "2025-01-06", "Male", 37, "Regular", 72.0),
        (7, "Grace", "Philadelphia", "Pennsylvania", "2025-01-07", "Female", 32, "Premium", 83.0),
    ],
}

_TABLES = [
    "Category",
    "Product",
    "Customer",
    "Order_",
    "OrderItem",
    "OrderExtra",
    "Review",
    "SKU",
    "GlobalOrder",
]


def _resolve_db_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    configured = Path(settings.db.path)
    if not configured.is_absolute():
        configured = repo_root / configured
    return configured


def _csv_source_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "ecommerce_sample_1000.csv"


def _to_float(value, default=0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _to_int(value, default=0) -> int:
    if value in (None, ""):
        return default
    return int(float(value))


def _to_bool_int(value) -> int:
    return 1 if str(value).strip().lower() in {"1", "true", "yes", "y"} else 0


def _import_sample_csv(conn: sqlite3.Connection, csv_path: Path) -> None:
    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        return

    for table in reversed(_TABLES):
        conn.execute(f'DELETE FROM "{table}"')

    parent_categories: dict[str, int] = {}
    categories: list[tuple] = []
    category_seq = 1
    sub_categories: dict[tuple[str, str], int] = {}

    customer_ids: dict[str, int] = {}
    customers: list[tuple] = []
    customer_seq = 1

    product_ids: dict[str, int] = {}
    products: list[tuple] = []
    sku_ids: dict[str, int] = {}
    skus: list[tuple] = []
    product_seq = 1
    sku_seq = 1

    order_ids: dict[str, int] = {}
    orders: list[tuple] = []
    order_extras: list[tuple] = []
    global_orders: list[tuple] = []
    order_extra_seen: set[int] = set()
    order_seq = 1

    order_items: list[tuple] = []
    reviews: list[tuple] = []
    order_item_seq = 1
    review_seq = 1

    for row in rows:
        category_name = (row.get("category") or "Unknown").strip()
        sub_category_name = (row.get("sub_category") or "").strip()
        if category_name not in parent_categories:
            parent_categories[category_name] = category_seq
            categories.append((category_seq, category_name, None))
            category_seq += 1
        parent_id = parent_categories[category_name]

        category_id = parent_id
        if sub_category_name:
            key = (category_name, sub_category_name)
            if key not in sub_categories:
                sub_categories[key] = category_seq
                categories.append((category_seq, sub_category_name, parent_id))
                category_seq += 1
            category_id = sub_categories[key]

        customer_key = row["customer_id"]
        if customer_key not in customer_ids:
            customer_ids[customer_key] = customer_seq
            customers.append((
                customer_seq,
                row.get("customer_name", ""),
                row.get("city", ""),
                row.get("country", ""),  # source file has country, no state/province
                row.get("account_creation_date", ""),
                row.get("gender", ""),
                _to_int(row.get("age")),
                row.get("customer_segment", ""),
                _to_float(row.get("customer_loyalty_score")),
            ))
            customer_seq += 1
        customer_id = customer_ids[customer_key]

        product_key = row["product_id"]
        if product_key not in product_ids:
            product_ids[product_key] = product_seq
            products.append((
                product_seq,
                row.get("product_name", ""),
                category_id,
                row.get("brand", ""),
                _to_float(row.get("unit_price_usd")),
                _to_int(row.get("stock_quantity")),
                "Active",
            ))
            sku_ids[product_key] = sku_seq
            skus.append((
                sku_seq,
                product_seq,
                None,
                None,
                None,
                _to_float(row.get("unit_price_usd")),
                _to_int(row.get("stock_quantity")),
                "Active",
            ))
            product_seq += 1
            sku_seq += 1
        product_id = product_ids[product_key]
        sku_id = sku_ids[product_key]

        order_key = row["order_id"]
        if order_key not in order_ids:
            order_ids[order_key] = order_seq
            orders.append((
                order_seq,
                customer_id,
                row.get("order_date", ""),
                row.get("order_status", ""),
                _to_float(row.get("total_price_usd")),
                row.get("city", ""),
                row.get("country", ""),  # source file has country, no state/province
                row.get("order_priority", ""),
                _to_bool_int(row.get("is_weekend")),
            ))
            global_orders.append((
                order_seq,
                row.get("shipping_country") or row.get("country", ""),
                row.get("country", ""),
                row.get("city", ""),
                row.get("order_date", ""),
                row.get("order_status", ""),
                _to_float(row.get("total_price_usd")),
            ))
            order_seq += 1
        order_id = order_ids[order_key]

        if order_id not in order_extra_seen:
            order_extras.append((
                order_id,
                row.get("payment_method", ""),
                row.get("payment_status", ""),
                row.get("shipping_method", ""),
                _to_float(row.get("shipping_cost_usd")),
                _to_int(row.get("delivery_days")),
                row.get("delivery_status", ""),
                row.get("warehouse_location", ""),
                row.get("campaign_source", ""),
                row.get("device_type", ""),
                row.get("traffic_source", ""),
                _to_float(row.get("fraud_risk_score")),
                _to_bool_int(row.get("coupon_used")),
                row.get("coupon_code", ""),
                row.get("return_reason", ""),
            ))
            order_extra_seen.add(order_id)

        unit_price = _to_float(row.get("unit_price_usd"))
        discount_percent = _to_float(row.get("discount_percent"))
        discount_multiplier = max(0.0, 1.0 - (discount_percent / 100.0))
        order_items.append((
            order_item_seq,
            order_id,
            product_id,
            sku_id,
            _to_int(row.get("quantity"), 1),
            unit_price,
            discount_multiplier,
        ))
        order_item_seq += 1

        if row.get("rating") not in (None, ""):
            reviews.append((
                review_seq,
                customer_id,
                product_id,
                _to_float(row.get("rating")),
                row.get("customer_feedback", ""),
                row.get("order_date", ""),
            ))
            review_seq += 1

    conn.executemany('INSERT INTO "Category" VALUES (?, ?, ?)', categories)
    conn.executemany('INSERT INTO "Product" VALUES (?, ?, ?, ?, ?, ?, ?)', products)
    conn.executemany('INSERT INTO "Customer" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', customers)
    conn.executemany('INSERT INTO "Order_" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', orders)
    conn.executemany('INSERT INTO "OrderItem" VALUES (?, ?, ?, ?, ?, ?, ?)', order_items)
    conn.executemany('INSERT INTO "OrderExtra" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', order_extras)
    conn.executemany('INSERT INTO "Review" VALUES (?, ?, ?, ?, ?, ?)', reviews)
    conn.executemany('INSERT INTO "SKU" VALUES (?, ?, ?, ?, ?, ?, ?, ?)', skus)
    conn.executemany('INSERT INTO "GlobalOrder" VALUES (?, ?, ?, ?, ?, ?, ?)', global_orders)


def ensure_db_exists() -> str:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        for stmt in _BOOTSTRAP_SQL:
            conn.execute(stmt)
        csv_path = _csv_source_path()
        order_count = conn.execute('SELECT COUNT(*) FROM "Order_"').fetchone()[0]
        order_item_count = conn.execute('SELECT COUNT(*) FROM "OrderItem"').fetchone()[0]
        if csv_path.exists() and order_count == 0 and order_item_count == 0:
            _import_sample_csv(conn, csv_path)
        else:
            for table, rows in _SEED_ROWS.items():
                count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if count == 0 and rows:
                    placeholders = ", ".join("?" for _ in rows[0])
                    conn.executemany(
                        f'INSERT INTO "{table}" VALUES ({placeholders})',
                        rows,
                    )
        conn.commit()
    finally:
        conn.close()
    return str(db_path)


DB_PATH = ensure_db_exists()

"""
The LLM generates an SQL string.
utils.query(sql) executes that string against the database.
The query result is then returned.
"""
def query(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    res = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return res


if __name__ == "__main__":
    sql = "SELECT * FROM Product LIMIT 5;"
    res = query(sql)
    for row in res:
        print(row)
