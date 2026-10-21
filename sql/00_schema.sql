CREATE TABLE stg_orders (
  case_code TEXT PRIMARY KEY, purchase_timestamp TEXT NOT NULL,
  approved_timestamp TEXT, handover_timestamp TEXT, delivered_timestamp TEXT,
  estimated_timestamp TEXT, order_status TEXT NOT NULL, customer_state TEXT NOT NULL
);
CREATE TABLE stg_items (
  case_code TEXT NOT NULL REFERENCES stg_orders(case_code), item_number INTEGER NOT NULL,
  seller_key INTEGER NOT NULL, origin_state TEXT NOT NULL, category TEXT NOT NULL,
  price_cents INTEGER NOT NULL, freight_cents INTEGER NOT NULL,
  PRIMARY KEY(case_code, item_number)
);
CREATE TABLE stg_reviews (
  review_key TEXT NOT NULL, case_code TEXT NOT NULL REFERENCES stg_orders(case_code),
  review_score INTEGER, created_timestamp TEXT, answered_timestamp TEXT
);
CREATE INDEX review_order ON stg_reviews(case_code);
