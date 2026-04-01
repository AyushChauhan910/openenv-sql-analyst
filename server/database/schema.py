import sqlite3
import random
from datetime import datetime, timedelta
from typing import Tuple

SCHEMA_SQL = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_amount REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    review_date DATE NOT NULL,
    comment TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

SCHEMA_INFO = """
Database Schema:

Table: customers
- id (INTEGER, PRIMARY KEY)
- name (TEXT, NOT NULL)
- email (TEXT, NOT NULL, UNIQUE)
- city (TEXT, NOT NULL)
- signup_date (DATE, NOT NULL)

Table: products
- id (INTEGER, PRIMARY KEY)
- name (TEXT, NOT NULL)
- category (TEXT, NOT NULL) -- Values: Electronics, Clothing, Books, Home
- price (REAL, NOT NULL)
- stock (INTEGER, NOT NULL, DEFAULT 0)

Table: orders
- id (INTEGER, PRIMARY KEY)
- customer_id (INTEGER, NOT NULL, FOREIGN KEY -> customers.id)
- order_date (DATE, NOT NULL)
- status (TEXT, NOT NULL) -- Values: pending, processing, shipped, delivered, cancelled
- total_amount (REAL, NOT NULL, DEFAULT 0.0)

Table: order_items
- id (INTEGER, PRIMARY KEY)
- order_id (INTEGER, NOT NULL, FOREIGN KEY -> orders.id)
- product_id (INTEGER, NOT NULL, FOREIGN KEY -> products.id)
- quantity (INTEGER, NOT NULL)
- unit_price (REAL, NOT NULL)

Table: reviews
- id (INTEGER, PRIMARY KEY)
- product_id (INTEGER, NOT NULL, FOREIGN KEY -> products.id)
- customer_id (INTEGER, NOT NULL, FOREIGN KEY -> customers.id)
- rating (INTEGER, NOT NULL, CHECK 1-5)
- review_date (DATE, NOT NULL)
- comment (TEXT)
"""


def get_schema_info() -> str:
    return SCHEMA_INFO.strip()


def get_db_connection(seed: int = 42) -> Tuple[sqlite3.Connection, str]:
    random.seed(seed)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    conn.executescript(SCHEMA_SQL)
    _seed_customers(conn)
    _seed_products(conn)
    _seed_orders(conn)
    _seed_order_items(conn)
    _seed_reviews(conn)
    conn.commit()

    return conn, get_schema_info()


def _seed_customers(conn: sqlite3.Connection) -> None:
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
        "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
        "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
    ]

    customers = []
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 6, 30)
    date_range = (end_date - start_date).days

    for i in range(50):
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        city = cities[i % len(cities)]
        signup = start_date + timedelta(days=random.randint(0, date_range))
        customers.append((name, email, city, signup.strftime("%Y-%m-%d")))

    conn.executemany(
        "INSERT INTO customers (name, email, city, signup_date) VALUES (?, ?, ?, ?)",
        customers
    )


def _seed_products(conn: sqlite3.Connection) -> None:
    products = [
        ("Wireless Headphones", "Electronics", 79.99, 150),
        ("Bluetooth Speaker", "Electronics", 49.99, 200),
        ("USB-C Hub", "Electronics", 34.99, 300),
        ("Mechanical Keyboard", "Electronics", 129.99, 75),
        ("Webcam HD", "Electronics", 59.99, 120),
        ("Cotton T-Shirt", "Clothing", 19.99, 500),
        ("Denim Jeans", "Clothing", 49.99, 350),
        ("Running Shoes", "Clothing", 89.99, 180),
        ("Winter Jacket", "Clothing", 149.99, 90),
        ("Wool Sweater", "Clothing", 69.99, 220),
        ("Python Programming", "Books", 39.99, 400),
        ("Data Science Guide", "Books", 44.99, 280),
        ("Machine Learning Basics", "Books", 54.99, 160),
        ("Web Development 101", "Books", 34.99, 320),
        ("SQL Cookbook", "Books", 29.99, 450),
        ("Desk Lamp", "Home", 24.99, 250),
        ("Coffee Maker", "Home", 69.99, 140),
        ("Throw Blanket", "Home", 39.99, 300),
        ("Wall Clock", "Home", 29.99, 200),
        ("Plant Pot Set", "Home", 34.99, 180),
    ]

    conn.executemany(
        "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
        products
    )


def _seed_orders(conn: sqlite3.Connection) -> None:
    statuses = ["delivered", "delivered", "delivered", "shipped", "processing", "pending", "cancelled"]
    orders = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    order_counts = {}
    for year in (2023, 2024):
        for month in range(1, 13):
            if month in (11, 12):
                order_counts[(year, month)] = 12
            elif month in (1, 2):
                order_counts[(year, month)] = 6
            else:
                order_counts[(year, month)] = 8

    for (year, month), num_orders in order_counts.items():
        for _ in range(num_orders):
                customer_id = random.randint(1, 50)
                day = random.randint(1, 28)
                order_date = datetime(year, month, day)
                status = random.choice(statuses)
                orders.append((
                    customer_id,
                    order_date.strftime("%Y-%m-%d"),
                    status,
                    0.0
                ))

    conn.executemany(
        "INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)",
        orders
    )


def _seed_order_items(conn: sqlite3.Connection) -> None:
    order_items = []
    cursor = conn.execute("SELECT id, order_date FROM orders ORDER BY id")
    orders_data = cursor.fetchall()

    product_cursor = conn.execute("SELECT id, price FROM products")
    products = product_cursor.fetchall()

    seasonal_products = {
        11: [4, 9, 10, 17],
        12: [4, 9, 10, 17, 19],
    }

    for order_row in orders_data:
        order_id = order_row["id"]
        order_date = datetime.strptime(order_row["order_date"], "%Y-%m-%d")
        month = order_date.month
        num_items = random.randint(1, 3)

        available_products = list(products)
        if month in seasonal_products:
            for pid in seasonal_products[month]:
                prod = next((p for p in products if p["id"] == pid), None)
                if prod and prod not in available_products:
                    available_products.append(prod)

        selected = random.sample(available_products, min(num_items, len(available_products)))

        for product in selected:
            quantity = random.randint(1, 4)
            unit_price = product["price"]
            order_items.append((order_id, product["id"], quantity, unit_price))

    conn.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        order_items
    )

    conn.execute("""
        UPDATE orders SET total_amount = (
            SELECT COALESCE(SUM(quantity * unit_price), 0)
            FROM order_items WHERE order_items.order_id = orders.id
        )
    """)


def _seed_reviews(conn: sqlite3.Connection) -> None:
    positive_comments = [
        "Great product, exactly what I needed!",
        "Excellent quality, highly recommend.",
        "Fast shipping and well packaged.",
        "Better than expected, very happy with this purchase.",
        "Perfect fit and great value for money.",
        "Love it! Will buy again.",
        "Outstanding quality and performance.",
        "Exactly as described, very satisfied.",
    ]
    neutral_comments = [
        "Decent product for the price.",
        "Works as expected, nothing special.",
        "Average quality but gets the job done.",
        "Okay product, met my basic needs.",
        "Fair product, shipping was a bit slow.",
    ]
    negative_comments = [
        "Disappointed with the quality.",
        "Not worth the price, expected better.",
        "Had issues with this product.",
        "Would not recommend, poor quality.",
        "Returned this item, did not meet expectations.",
    ]

    reviews = []
    used_combinations = set()
    start_date = datetime(2023, 2, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    for _ in range(100):
        attempts = 0
        while attempts < 50:
            product_id = random.randint(1, 20)
            customer_id = random.randint(1, 50)
            combo = (product_id, customer_id)
            if combo not in used_combinations:
                used_combinations.add(combo)
                break
            attempts += 1
        else:
            continue

        rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]

        if rating >= 4:
            comment = random.choice(positive_comments)
        elif rating == 3:
            comment = random.choice(neutral_comments)
        else:
            comment = random.choice(negative_comments)

        review_date = start_date + timedelta(days=random.randint(0, date_range))
        reviews.append((
            product_id,
            customer_id,
            rating,
            review_date.strftime("%Y-%m-%d"),
            comment
        ))

    conn.executemany(
        "INSERT INTO reviews (product_id, customer_id, rating, review_date, comment) VALUES (?, ?, ?, ?, ?)",
        reviews
    )
