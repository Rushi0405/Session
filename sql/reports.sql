-- =====================================================================
-- Part 1 - Task 3: Reports
-- =====================================================================
-- How to run (after schema.sql and seed_data.sql):
--     sqlite3 -header -column mamaearth.db < sql/reports.sql
--
-- All queries run on the RAW data (no cleaning).
-- The "Output:" comment above each query is its real output from SQLite.
--
-- Notes:
-- 1) Revenue of one order = quantity * price * (1 - discount_pct / 100.0)
--    COALESCE(discount_pct, 0) treats a missing (NULL) discount as 0%.
--    We divide by 100.0 (not 100) because in SQLite 10 / 100 = 0 (whole-number
--    division), which would wrongly remove every discount.
-- 2) printf('%.2f', ...) only shows money with 2 decimals (99860.20 instead of
--    99860.2). Sorting is always done on the number, not on this text.
-- 3) Report (i) adds a new column with ALTER TABLE, so run this file only once
--    after loading. To run it again, first re-run schema.sql and seed_data.sql.


-- ---------------------------------------------------------------------
-- (a) Order totals: number of orders, total revenue, average order value
-- ---------------------------------------------------------------------
-- Output:
--   total_orders  total_revenue  avg_order_value
--   ------------  -------------  ---------------
--   180           99860.20       554.78
SELECT
    COUNT(*) AS total_orders,
    printf('%.2f', SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0))) AS total_revenue,
    printf('%.2f', AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0))) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;


-- ---------------------------------------------------------------------
-- (b) COUNT(*) vs COUNT(column)
-- ---------------------------------------------------------------------
-- COUNT(*) counts all rows. COUNT(rating) skips NULL ratings.
-- The difference = orders that have no rating yet.
-- Output:
--   total_orders  rated_orders  unrated_orders
--   ------------  ------------  --------------
--   180           165           15
SELECT
    COUNT(*)                 AS total_orders,
    COUNT(rating)            AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;


-- ---------------------------------------------------------------------
-- (c) Customers with zero orders
-- ---------------------------------------------------------------------
-- Query 1: LEFT JOIN keeps every customer, even with no matching order.
-- COUNT(o.order_id) counts only real orders, so such a customer gets 0.
-- Output:
--   customer_id  name    order_count
--   -----------  ------  -----------
--   C045         Vihaan  0
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- Query 2: a second, independent check using NOT IN.
-- It must return the same customer as Query 1.
-- Output:
--   customer_id  name
--   -----------  ------
--   C045         Vihaan
SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);


-- ---------------------------------------------------------------------
-- (d) Return rate by city (only cities above 20%)
-- ---------------------------------------------------------------------
-- returned is 1 or 0, so SUM(returned) = number of returned orders.
-- HAVING filters the groups after GROUP BY.
-- (Mumbai 17.9% and Delhi 17.4% are below 20%, so they are not shown.)
-- Output:
--   city       total_orders  returned_orders  return_rate_pct
--   ---------  ------------  ---------------  ---------------
--   Jaipur     19            8                42.1
--   Lucknow    49            15               30.6
--   Bangalore  33            8                24.2
SELECT
    c.city,
    COUNT(*)                                     AS total_orders,
    SUM(o.returned)                              AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(*), 1) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;


-- ---------------------------------------------------------------------
-- (e) Top customers by total spend (ORDER BY + LIMIT / OFFSET)
-- ---------------------------------------------------------------------
-- Tie-break: customer_id ASC is a second sort key, so if two customers ever
-- have the same spend they always appear in the same order, and the
-- LIMIT/OFFSET pages never skip or repeat a customer.
--
-- Query 1: top 5 customers
-- Output:
--   customer_id  name     total_spend
--   -----------  -------  -----------
--   C043         Reyansh  12920.00
--   C026         Isha     8371.60
--   C008         Meera    4564.60
--   C011         Arjun    4111.00
--   C042         Sanya    3785.00
SELECT
    c.customer_id,
    c.name,
    printf('%.2f', SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0))) AS total_spend
FROM orders o
JOIN products p  ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)) DESC,
         c.customer_id ASC
LIMIT 5;

-- Query 2: ranks 3 to 5 (skip the first 2 rows, then take 3)
-- Same query and same ORDER BY, only LIMIT 3 OFFSET 2 is different.
-- Output:
--   customer_id  name   total_spend
--   -----------  -----  -----------
--   C008         Meera  4564.60
--   C011         Arjun  4111.00
--   C042         Sanya  3785.00
SELECT
    c.customer_id,
    c.name,
    printf('%.2f', SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0))) AS total_spend
FROM orders o
JOIN products p  ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)) DESC,
         c.customer_id ASC
LIMIT 3 OFFSET 2;


-- ---------------------------------------------------------------------
-- (f) Revenue by category (three-table JOIN + GROUP BY)
-- ---------------------------------------------------------------------
-- Only orders and products are needed here. customers is also joined to
-- show the three-table join works (Part 3 needs it). Every order has a
-- customer, so this join does not change the numbers.
-- Output:
--   category      order_count  category_revenue
--   ------------  -----------  ----------------
--   Haircare      54           44956.10
--   Skincare      60           27346.00
--   Babycare      30           16805.00
--   PersonalCare  36           10753.10
SELECT
    p.category,
    COUNT(*) AS order_count,
    printf('%.2f', SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0))) AS category_revenue
FROM orders o
JOIN products p  ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)) DESC;


-- ---------------------------------------------------------------------
-- (g) Customers whose name starts with 'A' (LIKE)
-- ---------------------------------------------------------------------
-- 'A%' means: starts with A, followed by anything.
-- Output:
--   customer_id  name
--   -----------  ------
--   C001         Aarav
--   C003         Aditi
--   C004         Ananya
--   C011         Arjun
--   C021         Aryan
--   C030         Anika
--   C031         Aditya
--   C036         Aisha
--   C041         Ayaan
--   C044         Aria
SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;


-- ---------------------------------------------------------------------
-- (h) Different acquisition sources (DISTINCT)
-- ---------------------------------------------------------------------
-- DISTINCT removes repeated values, so each source appears once.
-- Output:
--   acquisition_source
--   ------------------
--   Ad
--   Organic
--   Referral
--   Social
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;


-- ---------------------------------------------------------------------
-- (i) Add a loyalty_tier column (ALTER TABLE + UPDATE with CASE)
-- ---------------------------------------------------------------------
-- Step 1: add the new empty column.
-- Step 2: fill it for every customer (no WHERE): Tier-1 city = Gold, else Silver.
-- Step 3: check how many customers are in each tier.
-- Output (of the SELECT in step 3):
--   loyalty_tier  COUNT(*)
--   ------------  --------
--   Gold          28
--   Silver        17
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier = CASE
                       WHEN city_tier = 1 THEN 'Gold'
                       ELSE 'Silver'
                   END;

SELECT
    loyalty_tier,
    COUNT(*)
FROM customers
GROUP BY loyalty_tier;
