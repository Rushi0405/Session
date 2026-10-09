-- =====================================================================
-- Part 1 - Task 1: Create the tables (schema)
-- =====================================================================
-- How to run:  sqlite3 mamaearth.db < sql/schema.sql
--
-- We create 3 tables: customers, products and orders.
-- "orders" is linked to the other two tables using FOREIGN KEYs.

-- Turn on foreign key checking (SQLite has it OFF by default)
PRAGMA foreign_keys = ON;

-- Delete old tables first so this file can be run again safely.
-- orders is dropped first because it depends on the other two tables.
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;


-- Table 1: customers (one row per customer)
CREATE TABLE customers (
    customer_id        VARCHAR(10) PRIMARY KEY,   -- unique id, e.g. C001
    name               VARCHAR(50) NOT NULL,
    city               VARCHAR(50) NOT NULL,
    city_tier          INT         NOT NULL,      -- 1 = big city, 2 = smaller city
    signup_date        DATE        NOT NULL,
    acquisition_source VARCHAR(20) NOT NULL       -- Ad, Organic, Referral or Social
);


-- Table 2: products (one row per product)
CREATE TABLE products (
    product_id   VARCHAR(10)   PRIMARY KEY,       -- unique id, e.g. P01
    product_name VARCHAR(100)  NOT NULL,
    category     VARCHAR(30)   NOT NULL,          -- Haircare, Skincare, Babycare, PersonalCare
    price        DECIMAL(10,2) NOT NULL           -- price in Rupees (INR)
);


-- Table 3: orders (one row per order)
-- discount_pct and rating have NO "NOT NULL" on purpose:
-- an order can have no promo code or no rating yet, so NULL is allowed.
CREATE TABLE orders (
    order_id       VARCHAR(10) PRIMARY KEY,       -- unique id, e.g. O0001
    customer_id    VARCHAR(10) NOT NULL,
    product_id     VARCHAR(10) NOT NULL,
    order_date     DATE        NOT NULL,
    quantity       INT         NOT NULL,
    discount_pct   INT,                           -- can be NULL (no promo code)
    payment_method VARCHAR(10) NOT NULL,          -- COD, Card or UPI
    rating         INT,                           -- can be NULL (not rated yet)
    returned       INT         NOT NULL DEFAULT 0, -- 1 = returned, 0 = kept
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);
