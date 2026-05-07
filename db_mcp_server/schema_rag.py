"""
Schema RAG orchestrator
-----------------------
Two-stage retrieval: Retriever (top-k fields -> candidate tables) + Reranker
(reduce to the minimum necessary tables) + JOIN path inference.
Retriever/Reranker implementations are selected through core/registry.py based
on the pluggable settings.yaml configuration.
"""

import sqlite3
from collections import defaultdict, deque
from typing import Dict, List, Tuple

from config import settings
from core.registry import create_retriever, create_reranker
import impl  # noqa: F401  Triggers retriever/reranker decorator registration
from db_mcp_server.utils import DB_PATH


FIELD_DESCRIPTIONS = [
    # ── Category ──────────────────────────────────────────────────────────
    ("Category", "CategoryId",       "primary key of the category — use to JOIN with Product.CategoryId"),
    ("Category", "Name",             "category or sub-category name e.g. Electronics, Clothing, Smartphones, Women's Apparel, Sneakers, Footwear, Shoes, Sportswear — use when filtering or grouping by product type, electronics orders, parent category, or sub-category"),
    ("Category", "ParentCategoryId", "parent category FK — NULL for top-level categories; use to distinguish parent category from sub-category and to roll sub-categories up to parent categories"),

    # ── Product ───────────────────────────────────────────────────────────
    ("Product", "ProductId",  "primary key of the product — use to JOIN with OrderItem.ProductId or Review.ProductId"),
    ("Product", "Name",       "full product name e.g. 'Samsung Galaxy S23', 'Nike Air Max', 'IKEA Chair' — use when query asks about a specific product, item, or product type like sneakers, phones, laptops"),
    ("Product", "CategoryId", "FK to Category — use to filter or group products by category or sub-category"),
    ("Product", "Brand",      "brand name of the product e.g. Nike, Samsung, Apple, IKEA, Adidas — use when query mentions a brand name or asks to filter/group by brand"),
    ("Product", "Price",      "listed retail price in USD — use for price comparison or average selling price queries"),
    ("Product", "Stock",      "current total stock level — use for inventory analysis or low-stock alerts"),
    ("Product", "Status",     "product availability: Active or Inactive — use when filtering for available products"),

    # ── Customer ──────────────────────────────────────────────────────────
    ("Customer", "CustomerId",    "primary key of the customer — use to JOIN with Order_.CustomerId or Review.CustomerId"),
    ("Customer", "City",          "US city where the customer is located e.g. Los Angeles, Houston — use when filtering by city"),
    ("Customer", "Province",      "US state where the customer is located e.g. California, Texas — use when grouping or filtering by state"),
    ("Customer", "RegisterDate",  "date the customer account was created — use for cohort analysis or customer tenure queries"),
    ("Customer", "Gender",        "gender of the customer: Male, Female — use for demographic breakdown"),
    ("Customer", "Age",           "age of the customer — use when filtering or grouping by age group"),
    ("Customer", "Segment",       "customer tier: Regular, Premium, VIP, New — use for customer segment analysis or filtering orders placed by VIP or premium customers"),
    ("Customer", "LoyaltyScore",  "numeric loyalty score — use for average loyalty, high loyalty customers, or top-loyalty customer queries"),

    # ── Order_ ────────────────────────────────────────────────────────────
    ("Order_", "OrderId",          "primary key of the order — use to JOIN with OrderItem.OrderId or OrderExtra.OrderId"),
    ("Order_", "CustomerId",       "FK to Customer — use to JOIN orders with customer profile, customer segment, loyalty score, or customer location"),
    ("Order_", "OrderDate",        "date the order was placed — use for time-range filtering, monthly trends, quarter filters like Q1 2025, or year-over-year analysis"),
    ("Order_", "Status",           "fulfilment status: Delivered, Shipped, Pending, Cancelled, Returned — use for return rate, cancellation rate, or filtering by order outcome"),
    ("Order_", "TotalAmount",      "total revenue paid by the customer in USD after discount — use for revenue, sales amount, GMV, or order value queries"),
    ("Order_", "ShippingCity",     "city the order was shipped to — use when filtering orders by destination city"),
    ("Order_", "ShippingProvince", "US state the order was shipped to — use when filtering orders by destination state"),
    ("Order_", "Priority",         "priority level of the order: High, Medium, Low — use when query asks about high-priority or urgent orders"),
    ("Order_", "IsWeekend",        "1 if the order was placed on a weekend, 0 otherwise — use for weekend vs weekday comparison"),

    # ── GlobalOrder ───────────────────────────────────────────────────────
    ("GlobalOrder", "OrderId",     "primary key of the global order record"),
    ("GlobalOrder", "Country",     "country name for the order destination in global geography rollups — use when query explicitly compares countries or asks for geo-wide sales"),
    ("GlobalOrder", "State",       "state or province for global geography reporting — use when grouping or ranking US states in location-focused sales analysis"),
    ("GlobalOrder", "City",        "city in the global geography rollup table — use for city-level geographic summaries"),
    ("GlobalOrder", "OrderDate",   "date of the global order record — use for time-range trends on global geography reports"),
    ("GlobalOrder", "Status",      "status for global order reporting such as delivered or cancelled"),
    ("GlobalOrder", "TotalAmount", "order amount for country/state/city rollups in the global geography table — prefer Order_ for normal order analytics"),

    # ── OrderItem ─────────────────────────────────────────────────────────
    ("OrderItem", "OrderItemId", "primary key of the order line item"),
    ("OrderItem", "OrderId",     "FK to Order_ — use to JOIN order items with order header when combining products with order date, customer, status, or payment/shipping attributes"),
    ("OrderItem", "ProductId",   "FK to Product — use to JOIN order items with product details, brand, or category"),
    ("OrderItem", "SkuId",       "FK to SKU — use when query asks about specific product variants (color, size, storage)"),
    ("OrderItem", "Quantity",    "number of units purchased in this line item — use for total units sold, quantity sold, bestseller ranking, or product sales by customer/location"),
    ("OrderItem", "UnitPrice",   "price per unit at the time of purchase in USD — use for line-item revenue calculation by brand, category, or sub-category: UnitPrice * Quantity * Discount"),
    ("OrderItem", "Discount",    "discount coefficient applied (e.g. 0.9 means 10% off) — revenue = UnitPrice * Quantity * Discount"),

    # ── OrderExtra ────────────────────────────────────────────────────────
    ("OrderExtra", "OrderId",           "FK to Order_ — use to JOIN extra order attributes with order header"),
    ("OrderExtra", "PaymentMethod",     "how the customer paid: Credit Card, PayPal, Apple Pay, Google Pay, Bank Transfer, Crypto — use for payment method breakdown"),
    ("OrderExtra", "PaymentStatus",     "whether the payment was completed — use when filtering by paid or unpaid orders"),
    ("OrderExtra", "ShippingMethod",    "delivery speed chosen: Standard, Express, Same-Day, Overnight, Economy — use for shipping performance or preference analysis"),
    ("OrderExtra", "ShippingCostUSD",   "shipping fee in USD — use for shipping cost analysis or average shipping fee queries"),
    ("OrderExtra", "DeliveryDays",      "number of days taken to deliver the order — use for delivery speed or SLA analysis"),
    ("OrderExtra", "DeliveryStatus",    "whether delivery succeeded: On Time, Delayed, Lost — use for logistics quality or SLA analysis"),
    ("OrderExtra", "WarehouseLocation", "US warehouse that fulfilled the order e.g. East-NJ, West-CA, Central-TX — use for warehouse or fulfilment performance analysis"),
    ("OrderExtra", "CampaignSource",    "marketing channel that brought the customer: Google Ads, Facebook, Instagram, TikTok, YouTube, Email Newsletter, Organic Search, Influencer — use for marketing ROI analysis"),
    ("OrderExtra", "DeviceType",        "device used to place the order: Mobile, Desktop, Tablet — use for device mix or conversion analysis"),
    ("OrderExtra", "TrafficSource",     "how the customer arrived: Email, Direct, Referral, Social Media, Paid Ad, Search Engine — use for traffic attribution"),
    ("OrderExtra", "FraudRiskScore",    "numeric fraud risk score 0-1 per order — use for fraud analysis or risk segmentation"),
    ("OrderExtra", "CouponUsed",        "1 if a coupon was applied, 0 otherwise — use for coupon adoption rate or promotional effectiveness"),
    ("OrderExtra", "CouponCode",        "coupon code string applied to the order — use when filtering by specific promotion"),
    ("OrderExtra", "ReturnReason",      "reason the order was returned — use when query asks about return causes or most common return reasons"),

    # ── Review ────────────────────────────────────────────────────────────
    ("Review", "ReviewId",    "primary key of the review"),
    ("Review", "CustomerId",  "FK to Customer — use to JOIN reviews with customer profile"),
    ("Review", "ProductId",   "FK to Product — use to JOIN reviews with product details"),
    ("Review", "Rating",      "customer satisfaction rating 1-5 — use only when query explicitly asks about ratings, reviews, or satisfaction scores"),
    ("Review", "Content",     "free-text customer feedback — use only when query asks about review text or customer comments"),
    ("Review", "CreateDate",  "date the review was submitted — use only when query filters reviews by date"),

    # ── SKU ───────────────────────────────────────────────────────────────
    ("SKU", "SkuId",     "primary key of the SKU variant — use to JOIN with OrderItem.SkuId"),
    ("SKU", "ProductId", "FK to Product — use to JOIN SKU variants with product"),
    ("SKU", "Color",     "color variant of the product e.g. Black, White, Rose — use when query filters by color"),
    ("SKU", "Storage",   "storage capacity variant e.g. 128GB, 256GB, 512GB — use for electronics storage queries"),
    ("SKU", "Size",      "size variant e.g. S, M, L, XL — use only when query asks about clothing or shoe size variants specifically"),
    ("SKU", "Price",     "variant-level price in USD — may differ from Product.Price; use for SKU-level pricing queries"),
    ("SKU", "Stock",     "stock level for this specific variant — use for variant-level inventory analysis"),
    ("SKU", "Status",    "variant availability: Active or Inactive — use when filtering for available variants"),
]

TABLE_DESCRIPTIONS = {
    "Category":   "product taxonomy with parent-child hierarchy — CategoryId, Name, ParentCategoryId. Top-level rows (ParentCategoryId IS NULL) are parent categories e.g. Electronics, Clothing; child rows are sub-categories e.g. Smartphones, Women's Apparel. JOIN to Product via Product.CategoryId when a query asks about category, sub-category, or parent-category rollups.",
    "Product":    "product master table — ProductId, Name, CategoryId, Brand, Price, Stock, Status. One row per distinct product (1000 products). JOIN to Category for category name, to OrderItem for sales data, to Review for ratings, to SKU for variants.",
    "Customer":   "customer profile table — CustomerId, Name, City, Province, RegisterDate, Gender, Age, Segment, LoyaltyScore. One row per customer (1000 customers). JOIN to Order_ for purchase history, customer segment, loyalty, and geography filters; JOIN to Review for reviews written.",
    "Order_":     "order header table (note underscore: ORDER is a SQL reserved word) — OrderId, CustomerId, OrderDate, Status, TotalAmount, ShippingCity, ShippingProvince, Priority, IsWeekend. One row per order (1003 orders). Use this table whenever a question mixes products with customer attributes, order dates, order value, or order status. JOIN to Customer, OrderItem, OrderExtra.",
    "GlobalOrder":"global geography fact table — OrderId, Country, State, City, OrderDate, Status, TotalAmount. Prefer this table only for explicitly location-focused country/state/city sales questions; prefer Order_ for normal order analytics.",
    "OrderItem":  "order line items — OrderItemId, OrderId, ProductId, SkuId, Quantity, UnitPrice, Discount. Revenue = UnitPrice * Quantity * Discount. One row per product line per order. Use this table for product-level revenue, quantity sold, brand/category/sub-category rollups, or any query about which customers bought which products. JOIN to Order_, Product, SKU.",
    "OrderExtra": "extended order attributes — OrderId, PaymentMethod, PaymentStatus, ShippingMethod, ShippingCostUSD, DeliveryDays, DeliveryStatus, WarehouseLocation, CampaignSource, DeviceType, TrafficSource, FraudRiskScore, CouponUsed, CouponCode, ReturnReason. One-to-one with Order_.",
    "Review":     "customer product reviews — ReviewId, CustomerId, ProductId, Rating (1-5), Content, CreateDate. One row per review. JOIN to Customer and Product.",
    "SKU":        "product variant table — SkuId, ProductId, Color, Storage, Size, Price, Stock, Status. One row per variant (3190 SKUs, ~3 per product). JOIN to Product and OrderItem.",
}


def rank_tables_from_hits(hits, limit: int) -> List[str]:
    """Select unique tables in hit order."""
    seen, tables = set(), []
    for hit in hits:
        if hit.table in seen:
            continue
        seen.add(hit.table)
        tables.append(hit.table)
        if len(tables) == limit:
            break
    return tables


def _contains_any(text: str, phrases: List[str]) -> bool:
    text = text.lower()
    return any(phrase in text for phrase in phrases)


def refine_candidate_tables(query: str, candidate_tables: List[str], limit: int) -> List[str]:
    query_l = query.lower()
    boosts: List[str] = []

    has_geo = _contains_any(query_l, [" state", " states", " city", " cities", " country", " countries", "province", "geo", "geography", "us "])
    has_category = _contains_any(query_l, ["category", "sub-category", "subcategory", "electronics", "clothing", "sneakers", "shoes", "sportswear", "smartphones"])
    has_product_metric = _contains_any(query_l, ["brand", "brands", "product", "products", "quantity", "sold", "sales", "revenue", "rating", "review"])
    has_customer_filter = _contains_any(query_l, ["customer", "customers", "vip", "segment", "loyalty", "loyal"])
    has_order_time = _contains_any(query_l, ["q1", "q2", "q3", "q4", "quarter", "month", "year", "2024", "2025"])
    has_order_extra = _contains_any(query_l, ["delivery", "shipping", "payment", "warehouse", "fraud", "device", "mobile"])

    if has_category:
        boosts.extend(["Category", "Product"])
    if has_product_metric:
        boosts.extend(["OrderItem", "Product"])
    if has_customer_filter and (has_product_metric or has_order_extra):
        boosts.extend(["Order_", "Customer"])
    if has_order_time and _contains_any(query_l, ["revenue", "sales", "return", "status", "cancel", "deliv"]):
        boosts.append("Order_")
    if has_order_extra:
        boosts.extend(["OrderExtra", "Order_"])
        if has_category or has_product_metric:
            boosts.extend(["OrderItem", "Product"])

    ordered: List[str] = []
    for table in boosts + candidate_tables:
        if table == "GlobalOrder" and not has_geo:
            continue
        if table not in ordered:
            ordered.append(table)

    if "GlobalOrder" in candidate_tables and has_geo and "GlobalOrder" not in ordered:
        ordered.append("GlobalOrder")

    return ordered[:limit]

FOREIGN_KEYS = [
    # (src_table, src_col, dst_table, dst_col)
    ("Category",   "ParentCategoryId", "Category",  "CategoryId"),
    ("Product",    "CategoryId",       "Category",  "CategoryId"),
    ("Order_",     "CustomerId",       "Customer",  "CustomerId"),
    ("OrderItem",  "OrderId",          "Order_",    "OrderId"),
    ("OrderItem",  "ProductId",        "Product",   "ProductId"),
    ("OrderItem",  "SkuId",            "SKU",       "SkuId"),
    ("OrderExtra", "OrderId",          "Order_",    "OrderId"),
    ("Review",     "CustomerId",       "Customer",  "CustomerId"),
    ("Review",     "ProductId",        "Product",   "ProductId"),
    ("SKU",        "ProductId",        "Product",   "ProductId"),
]


class SchemaRAG:
    def __init__(self, llm=None):
        self.db_path = DB_PATH
        self.retriever_cfg = settings.retriever
        self.reranker_cfg = settings.reranker
        self.retriever = create_retriever(
            settings.retriever,
            field_descriptions=FIELD_DESCRIPTIONS,
            embedding_model_name=settings.embedding.model_name,
        )
        self.reranker = create_reranker(
            settings.reranker,
            table_descriptions=TABLE_DESCRIPTIONS,
            llm=llm,
        )
        self._build_fk_graph()

    def _build_fk_graph(self):
        self.fk_graph: Dict[str, List[Tuple]] = defaultdict(list)
        for src_table, src_col, dst_table, dst_col in FOREIGN_KEYS:
            self.fk_graph[src_table].append((dst_table, src_col, dst_col, src_table))
            self.fk_graph[dst_table].append((src_table, dst_col, src_col, dst_table))

    def _candidate_tables_from_hits(self, hits) -> List[str]:
        return rank_tables_from_hits(hits, self.retriever_cfg.final_tables)

    def _stage2_join_paths(self, candidate_tables: List[str]) -> List[str]:
        if len(candidate_tables) <= 1:
            return []
        join_conditions = []
        visited_pairs = set()
        for i, src in enumerate(candidate_tables):
            for dst in candidate_tables[i + 1:]:
                pair = tuple(sorted([src, dst]))
                if pair in visited_pairs:
                    continue
                path = self._bfs_path(src, dst)
                if path:
                    visited_pairs.add(pair)
                    join_conditions.extend(path)
        seen = set()
        deduped = []
        for jc in join_conditions:
            left, right = jc.split(" = ")
            key = tuple(sorted([left, right]))
            if key not in seen:
                seen.add(key)
                deduped.append(jc)
        return deduped

    def _bfs_path(self, src: str, dst: str) -> List[str]:
        if src == dst:
            return []
        queue = deque([(src, [])])
        visited = {src}
        while queue:
            current, path = queue.popleft()
            for neighbor, src_col, dst_col, from_table in self.fk_graph[current]:
                join_cond = f"{from_table}.{src_col} = {neighbor}.{dst_col}"
                new_path = path + [join_cond]
                if neighbor == dst:
                    return new_path
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))
        return []

    def _get_table_structured(self, table: str) -> dict:
        """Return structured table info including DDL, business description, and sample rows."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = cursor.fetchall()
        col_defs = ", ".join(f"{col[1]} {col[2]}" for col in columns)
        col_names = [col[1] for col in columns]
        cursor.execute(f'SELECT * FROM "{table}" LIMIT 2')
        rows = cursor.fetchall()
        conn.close()

        return {
            "name": table,
            "description": TABLE_DESCRIPTIONS.get(table, ""),
            "ddl": f'CREATE TABLE "{table}" ({col_defs})',
            "columns": col_names,
            "sample_rows": [dict(zip(col_names, row)) for row in rows],
        }

    def retrieve(self, query: str) -> dict:
        """
        Run two-stage RAG retrieval and return a structured SchemaContext:
        {
            "tables": [{"name", "ddl", "columns", "sample_rows"}, ...],
            "join_paths": ["TableA.col = TableB.col", ...]
        }
        """
        hits = self.retriever.retrieve(query, top_k=self.retriever_cfg.top_k * 4)
        candidate_tables = self._candidate_tables_from_hits(hits)
        candidate_tables = refine_candidate_tables(
            query,
            candidate_tables,
            self.retriever_cfg.final_tables,
        )
        candidate_tables = self.reranker.rerank(
            query, candidate_tables, top_k=self.reranker_cfg.top_k
        )
        join_paths = self._stage2_join_paths(candidate_tables)
        tables = [self._get_table_structured(t) for t in candidate_tables]
        return {"tables": tables, "join_paths": join_paths}


if __name__ == "__main__":
    rag = SchemaRAG()

    test_queries = [
        "show me last month sales for Samsung phones",
        "which brand has the highest revenue",
        "count orders delivered to London",
        "what is the return rate for Nike sneakers",
        "top 5 customers by total spend",
    ]

    for q in test_queries:
        result = rag.retrieve(q)
        tables = [t["name"] for t in result["tables"]]
        joins  = result["join_paths"]
        print(f"Query : {q}")
        print(f"Tables: {tables}")
        print(f"JOINs : {joins if joins else '(none)'}")
        print("-" * 60)
