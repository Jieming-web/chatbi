ROLE_DICT = {
    "metric":      "Business metric to aggregate or measure, e.g. revenue, GMV, order count, return rate, rating, inventory, profit, average price, sales, orders",
    "time":        "Time range or point, e.g. last month, this quarter, last year, past 30 days, Q1, last month, this year",
    "comparison":  "Comparison, ranking, or extreme value, e.g. year-over-year, month-over-month, highest, lowest, exceeds, ranked, top, bottom, vs",
    "status":      "Order or product status, e.g. shipped, pending, refunded, cancelled, delivered, returned",
    "aggregation": "Grouping dimension or aggregation basis, e.g. by brand, each city, per category, per, by, group by",
    "limit":       "Quantity limit, e.g. top 5, top 10, most, least, first, last",
    "entity":      "Brand name, product name, or category name (must be selected from candidates below, do not invent)",
    "location":    "City or state (must be selected from candidates below, do not invent)",
}

FEW_SHOT_EXAMPLES = """
Example 1 — revenue by category:
Question: Which category has the highest revenue?
SQL:
SELECT c.Name AS category, SUM(oi.UnitPrice * oi.Quantity * oi.Discount) AS revenue
FROM OrderItem oi
JOIN Product p ON oi.ProductId = p.ProductId
JOIN Category c ON p.CategoryId = c.CategoryId
GROUP BY c.Name
ORDER BY revenue DESC
LIMIT 1;

Example 2 — frequent buyers:
Question: Which customers have placed more than 3 orders?
SQL:
SELECT cu.Name, cu.City, COUNT(o.OrderId) AS order_count
FROM Customer cu
JOIN Order_ o ON cu.CustomerId = o.CustomerId
GROUP BY cu.CustomerId
HAVING COUNT(o.OrderId) > 3
ORDER BY order_count DESC;

Example 3 — return rate by brand:
Question: What is the return rate for each brand?
SQL:
SELECT p.Brand,
       ROUND(SUM(CASE WHEN o.Status = 'Returned' THEN 1.0 ELSE 0 END) / COUNT(*), 4) AS return_rate
FROM Order_ o
JOIN OrderItem oi ON o.OrderId = oi.OrderId
JOIN Product p ON oi.ProductId = p.ProductId
GROUP BY p.Brand
ORDER BY return_rate DESC;

Example 4 — monthly sales trend:
Question: Show me the monthly revenue trend for last year.
SQL:
SELECT strftime('%Y-%m', o.OrderDate) AS month,
       SUM(oi.UnitPrice * oi.Quantity * oi.Discount) AS revenue
FROM Order_ o
JOIN OrderItem oi ON o.OrderId = oi.OrderId
WHERE o.OrderDate >= '2024-01-01' AND o.OrderDate < '2025-01-01'
GROUP BY month
ORDER BY month;

Example 5 — top products by city:
Question: What are the top 5 best-selling products in Los Angeles?
SQL:
SELECT p.Name, SUM(oi.Quantity) AS units_sold
FROM OrderItem oi
JOIN Order_ o ON oi.OrderId = o.OrderId
JOIN Product p ON oi.ProductId = p.ProductId
WHERE o.ShippingCity = 'Los Angeles'
GROUP BY p.ProductId
ORDER BY units_sold DESC
LIMIT 5;

Example 6 — average rating by brand:
Question: Which brand has the highest average customer rating?
SQL:
SELECT p.Brand, ROUND(AVG(r.Rating), 2) AS avg_rating
FROM Review r
JOIN Product p ON r.ProductId = p.ProductId
GROUP BY p.Brand
ORDER BY avg_rating DESC
LIMIT 1;
"""

SQL_SYSTEM_PROMPT = """You are an e-commerce data analyst assistant that converts natural language questions into SQLite SQL queries.

Rules:
1. Output only the SQL statement — no explanations, no markdown code blocks
2. Table and column names are case-sensitive; use them exactly as shown in the schema below
3. The orders table is named Order_ (with underscore, because ORDER is a SQL reserved word)
4. Revenue formula: UnitPrice * Quantity * Discount
5. Date format: 'YYYY-MM-DD'
6. Dimension hierarchy: Brand → Product → SKU; when a parent level is specified, use LIKE 'xxx%' to cover sub-levels
7. Status values are capitalized: 'Delivered', 'Returned', 'Cancelled', 'Shipped', 'Pending'

{schema_context}

{few_shot}
"""
