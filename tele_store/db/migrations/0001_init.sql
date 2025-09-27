
CREATE TABLE categories (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	description TEXT, 
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_categories_name ON categories (name);


CREATE TABLE users (
	id INTEGER NOT NULL, 
	tg_id BIGINT NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_users_tg_id ON users (tg_id);


CREATE TABLE carts (
	id INTEGER NOT NULL, 
	tg_id BIGINT NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tg_id) REFERENCES users (tg_id) ON DELETE CASCADE
)

;

CREATE UNIQUE INDEX ix_carts_tg_id ON carts (tg_id);


CREATE TABLE orders (
	id INTEGER NOT NULL, 
	order_number VARCHAR(32) NOT NULL, 
	tg_id BIGINT, 
	name VARCHAR NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	address VARCHAR NOT NULL, 
	total_price NUMERIC(12, 2) NOT NULL, 
	delivery_method VARCHAR(64), 
	status VARCHAR(10) NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT total_price_non_negative CHECK (total_price >= 0), 
	FOREIGN KEY(tg_id) REFERENCES users (tg_id) ON DELETE SET NULL
)

;

CREATE INDEX ix_orders_tg_id ON orders (tg_id);

CREATE UNIQUE INDEX ix_orders_order_number ON orders (order_number);


CREATE TABLE products (
	id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	price NUMERIC(10, 2) NOT NULL, 
	photo_file_id VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT price_non_negative CHECK (price >= 0), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_products_name ON products (name);

CREATE INDEX ix_products_category_id ON products (category_id);


CREATE TABLE cart_items (
	id INTEGER NOT NULL, 
	cart_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT quantity_positive CHECK (quantity > 0), 
	CONSTRAINT uq_cartitem_cart_product UNIQUE (cart_id, product_id), 
	FOREIGN KEY(cart_id) REFERENCES carts (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_cart_items_cart_id ON cart_items (cart_id);

CREATE INDEX ix_cart_items_cart_product ON cart_items (cart_id, product_id);

CREATE INDEX ix_cart_items_product_id ON cart_items (product_id);


CREATE TABLE order_items (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	price NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT orderitem_qty_positive CHECK (quantity > 0), 
	CONSTRAINT orderitem_price_non_negative CHECK (price >= 0), 
	CONSTRAINT uq_orderitem_order_product UNIQUE (order_id, product_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_order_items_product_id ON order_items (product_id);

CREATE INDEX ix_order_items_order_product ON order_items (order_id, product_id);

CREATE INDEX ix_order_items_order_id ON order_items (order_id);
