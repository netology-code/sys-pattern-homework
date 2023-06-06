-- CREATE TABLE orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
        order_id serial PRIMARY KEY,
        name VARCHAR ( 50 ) NOT NULL,
        price  integer 
);


-- CREATE TABLE clients
DROP TABLE IF EXISTS clients;
CREATE TABLE clients (
        client_id serial PRIMARY KEY,
        family VARCHAR ( 50 ) NOT NULL,
        country  VARCHAR ( 50 )  NOT NULL,
        orderId integer,
        FOREIGN KEY (orderId) REFERENCES orders (order_id)
);

-- CREATE user test-simple-user
CREATE USER "test-simple-user";

-- ADD PRIVILIGE user test-simple-user to test_db
GRANT SELECT,INSERT,UPDATE,DELETE ON orders, clients to "test-simple-user";
