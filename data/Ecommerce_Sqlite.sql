/*******************************************************************************
   Ecommerce Database - BritShop UK E-Commerce Scenario
   Description: Creates and populates the Ecommerce database.
   DB Server: SQLite
   Tables: Category, Product, SKU, Customer, Order_, OrderItem, Review
   Client: BritShop (via Unlikely AI)
********************************************************************************/

DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS OrderItem;
DROP TABLE IF EXISTS "Order_";
DROP TABLE IF EXISTS SKU;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Category;

/*******************************************************************************
   Create Tables
********************************************************************************/

CREATE TABLE Category (
    CategoryId INTEGER NOT NULL PRIMARY KEY,
    Name       NVARCHAR(100) NOT NULL,
    ParentCategoryId INTEGER,
    FOREIGN KEY (ParentCategoryId) REFERENCES Category(CategoryId)
);

CREATE TABLE Product (
    ProductId  INTEGER NOT NULL PRIMARY KEY,
    Name       NVARCHAR(200) NOT NULL,
    CategoryId INTEGER NOT NULL,
    Brand      NVARCHAR(100),
    Price      NUMERIC(10,2) NOT NULL,
    Stock      INTEGER NOT NULL DEFAULT 0,
    Status     NVARCHAR(20) NOT NULL DEFAULT 'Active',
    FOREIGN KEY (CategoryId) REFERENCES Category(CategoryId)
);

CREATE TABLE SKU (
    SkuId     INTEGER NOT NULL PRIMARY KEY,
    ProductId INTEGER NOT NULL,
    Color     NVARCHAR(50),
    Storage   NVARCHAR(50),
    Size      NVARCHAR(20),
    Price     NUMERIC(10,2) NOT NULL,
    Stock     INTEGER NOT NULL DEFAULT 0,
    Status    NVARCHAR(20) NOT NULL DEFAULT 'Active',
    FOREIGN KEY (ProductId) REFERENCES Product(ProductId)
);

CREATE TABLE Customer (
    CustomerId   INTEGER NOT NULL PRIMARY KEY,
    Name         NVARCHAR(100) NOT NULL,
    Email        NVARCHAR(200),
    City         NVARCHAR(100),
    Province     NVARCHAR(100),
    Phone        NVARCHAR(50),
    RegisterDate DATETIME
);

CREATE TABLE "Order_" (
    OrderId          INTEGER NOT NULL PRIMARY KEY,
    CustomerId       INTEGER NOT NULL,
    OrderDate        DATETIME NOT NULL,
    Status           NVARCHAR(20) NOT NULL,
    TotalAmount      NUMERIC(10,2) NOT NULL,
    ShippingCity     NVARCHAR(100),
    ShippingProvince NVARCHAR(100),
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
);

CREATE TABLE OrderItem (
    OrderItemId INTEGER NOT NULL PRIMARY KEY,
    OrderId     INTEGER NOT NULL,
    ProductId   INTEGER NOT NULL,
    SkuId       INTEGER,
    Quantity    INTEGER NOT NULL DEFAULT 1,
    UnitPrice   NUMERIC(10,2) NOT NULL,
    Discount    NUMERIC(4,2) NOT NULL DEFAULT 1,
    FOREIGN KEY (OrderId) REFERENCES "Order_"(OrderId),
    FOREIGN KEY (ProductId) REFERENCES Product(ProductId),
    FOREIGN KEY (SkuId) REFERENCES SKU(SkuId)
);

CREATE TABLE Review (
    ReviewId   INTEGER NOT NULL PRIMARY KEY,
    CustomerId INTEGER NOT NULL,
    ProductId  INTEGER NOT NULL,
    Rating     INTEGER NOT NULL,
    Content    NVARCHAR(500),
    CreateDate DATETIME,
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId),
    FOREIGN KEY (ProductId) REFERENCES Product(ProductId)
);

/*******************************************************************************
   Insert Categories
   1-8: Parent categories, 11-22: Subcategories
********************************************************************************/

INSERT INTO Category VALUES(1,  'Electronics',          NULL);
INSERT INTO Category VALUES(2,  'Computers & Office',   NULL);
INSERT INTO Category VALUES(3,  'Clothing & Footwear',  NULL);
INSERT INTO Category VALUES(4,  'Food & Groceries',     NULL);
INSERT INTO Category VALUES(5,  'Home Appliances',      NULL);
INSERT INTO Category VALUES(6,  'Beauty & Skincare',    NULL);
INSERT INTO Category VALUES(7,  'Sports & Outdoors',    NULL);
INSERT INTO Category VALUES(8,  'Books & Media',        NULL);
INSERT INTO Category VALUES(11, 'Smartphones',          1);
INSERT INTO Category VALUES(12, 'Tablets',              1);
INSERT INTO Category VALUES(13, 'Headphones & Speakers',1);
INSERT INTO Category VALUES(14, 'Laptops',              2);
INSERT INTO Category VALUES(15, 'Keyboards & Mice',     2);
INSERT INTO Category VALUES(16, 'Men''s Clothing',      3);
INSERT INTO Category VALUES(17, 'Women''s Clothing',    3);
INSERT INTO Category VALUES(18, 'Sports Shoes',         7);
INSERT INTO Category VALUES(19, 'Snacks & Drinks',      4);
INSERT INTO Category VALUES(20, 'Fresh Produce',        4);
INSERT INTO Category VALUES(21, 'Air Conditioners',     5);
INSERT INTO Category VALUES(22, 'Washing Machines',     5);

/*******************************************************************************
   Insert Products (40 products, prices in GBP)
********************************************************************************/

-- Smartphones (CategoryId=11)
INSERT INTO Product VALUES(1,  'Apple iPhone 15 Pro 256GB',              11, 'Apple',       999.00,  150, 'Active');
INSERT INTO Product VALUES(2,  'Samsung Galaxy S24 Ultra 512GB',         11, 'Samsung',    1249.00,  120, 'Active');
INSERT INTO Product VALUES(3,  'Google Pixel 8 Pro 128GB',               11, 'Google',      799.00,  200, 'Active');
INSERT INTO Product VALUES(4,  'OnePlus 12 256GB',                       11, 'OnePlus',     699.00,  180, 'Active');
INSERT INTO Product VALUES(5,  'Sony Xperia 1 V 256GB',                  11, 'Sony',        849.00,   90, 'Active');

-- Tablets (CategoryId=12)
INSERT INTO Product VALUES(6,  'Apple iPad Pro 12.9" M2 256GB',          12, 'Apple',      1099.00,   80, 'Active');
INSERT INTO Product VALUES(7,  'Samsung Galaxy Tab S9 Ultra 256GB',      12, 'Samsung',    1099.00,   70, 'Active');
INSERT INTO Product VALUES(8,  'Microsoft Surface Pro 9 256GB',          12, 'Microsoft',  1299.00,   60, 'Active');

-- Headphones & Speakers (CategoryId=13)
INSERT INTO Product VALUES(9,  'Sony WH-1000XM5 Wireless Headphones',   13, 'Sony',        349.00,  250, 'Active');
INSERT INTO Product VALUES(10, 'Apple AirPods Pro 2nd Generation',       13, 'Apple',       249.00,  300, 'Active');
INSERT INTO Product VALUES(11, 'Bose QuietComfort 45 Headphones',        13, 'Bose',        279.00,  150, 'Active');
INSERT INTO Product VALUES(12, 'JBL Charge 5 Portable Speaker',          13, 'JBL',         139.00,  200, 'Active');

-- Laptops (CategoryId=14)
INSERT INTO Product VALUES(13, 'Dell XPS 15 Core i7 512GB',              14, 'Dell',       1599.00,   60, 'Active');
INSERT INTO Product VALUES(14, 'Apple MacBook Air M2 256GB',             14, 'Apple',      1099.00,  100, 'Active');
INSERT INTO Product VALUES(15, 'Lenovo ThinkPad X1 Carbon Gen 11',       14, 'Lenovo',     1449.00,   50, 'Active');
INSERT INTO Product VALUES(16, 'HP Spectre x360 14" Core i7',            14, 'HP',         1299.00,   70, 'Active');

-- Keyboards & Mice (CategoryId=15)
INSERT INTO Product VALUES(17, 'Logitech MX Keys Advanced Keyboard',     15, 'Logitech',     99.00,  400, 'Active');
INSERT INTO Product VALUES(18, 'Apple Magic Keyboard with Touch ID',     15, 'Apple',         99.00,  300, 'Active');
INSERT INTO Product VALUES(19, 'Razer DeathAdder V3 Gaming Mouse',       15, 'Razer',          69.00,  350, 'Active');

-- Men's Clothing (CategoryId=16)
INSERT INTO Product VALUES(20, 'Barbour Men''s Beaufort Wax Jacket',     16, 'Barbour',     229.00,  150, 'Active');
INSERT INTO Product VALUES(21, 'Levi''s 501 Original Fit Jeans',         16, 'Levi''s',      85.00,  300, 'Active');
INSERT INTO Product VALUES(22, 'Ted Baker Men''s Slim Fit Oxford Shirt', 16, 'Ted Baker',    75.00,  200, 'Active');

-- Women's Clothing (CategoryId=17)
INSERT INTO Product VALUES(23, 'Zara Women''s Wool Blend Midi Coat',     17, 'Zara',        119.00,  180, 'Active');
INSERT INTO Product VALUES(24, '& Other Stories Floral Midi Dress',      17, '& Other Stories', 89.00, 160, 'Active');
INSERT INTO Product VALUES(25, 'Reiss Women''s Blazer',                  17, 'Reiss',       195.00,  120, 'Active');

-- Sports Shoes (CategoryId=18)
INSERT INTO Product VALUES(26, 'Nike Air Max 270 Trainers',              18, 'Nike',        130.00,  250, 'Active');
INSERT INTO Product VALUES(27, 'Adidas Ultraboost 23 Running Shoes',     18, 'Adidas',      160.00,  220, 'Active');
INSERT INTO Product VALUES(28, 'New Balance 574 Classic Trainers',       18, 'New Balance',  85.00,  300, 'Active');
INSERT INTO Product VALUES(29, 'Puma RS-X Running Shoes',                18, 'Puma',         90.00,  180, 'Active');

-- Snacks & Drinks (CategoryId=19)
INSERT INTO Product VALUES(30, 'Cadbury Dairy Milk Chocolate 360g',      19, 'Cadbury',       4.50, 1000, 'Active');
INSERT INTO Product VALUES(31, 'Walkers Crisps Variety Pack 20 Bags',   19, 'Walkers',        6.00,  800, 'Active');
INSERT INTO Product VALUES(32, 'Twinings English Breakfast Tea 80 Bags', 19, 'Twinings',      4.00, 1200, 'Active');
INSERT INTO Product VALUES(33, 'Innocent Smoothie Mixed Berries 750ml',  19, 'Innocent',       3.50,  600, 'Active');

-- Fresh Produce (CategoryId=20)
INSERT INTO Product VALUES(34, 'British Organic Strawberries 400g',      20, 'Fresh Farm',    3.50,  500, 'Active');
INSERT INTO Product VALUES(35, 'Scottish Smoked Salmon 200g',            20, 'Loch Fyne',     8.00,  300, 'Active');
INSERT INTO Product VALUES(36, 'Free Range British Eggs 12 Pack',        20, 'Happy Hens',    4.00,  600, 'Active');

-- Air Conditioners (CategoryId=21)
INSERT INTO Product VALUES(37, 'Dyson Hot+Cool Fan Purifier HP09',       21, 'Dyson',       549.00,   80, 'Active');
INSERT INTO Product VALUES(38, 'LG DualCool Inverter AC 12000 BTU',      21, 'LG',          699.00,   60, 'Active');

-- Washing Machines (CategoryId=22)
INSERT INTO Product VALUES(39, 'Bosch Series 6 9kg Washing Machine',     22, 'Bosch',       699.00,   70, 'Active');
INSERT INTO Product VALUES(40, 'Samsung EcoBubble 10kg Washing Machine', 22, 'Samsung',     599.00,   80, 'Active');

/*******************************************************************************
   Insert SKUs (~104 SKUs, variants per product)
   Format: SkuId, ProductId, Color, Storage, Size, Price, Stock, Status
********************************************************************************/

-- Smartphones (Products 1-5)
INSERT INTO SKU VALUES(1,  1, 'Black Titanium',    '256GB', NULL,  999.00, 50, 'Active');
INSERT INTO SKU VALUES(2,  1, 'White Titanium',    '256GB', NULL,  999.00, 50, 'Active');
INSERT INTO SKU VALUES(3,  1, 'Black Titanium',    '512GB', NULL, 1099.00, 30, 'Active');
INSERT INTO SKU VALUES(4,  1, 'Natural Titanium',  '512GB', NULL, 1099.00, 20, 'Active');
INSERT INTO SKU VALUES(5,  2, 'Titanium Black',    '512GB', NULL, 1249.00, 40, 'Active');
INSERT INTO SKU VALUES(6,  2, 'Titanium Grey',     '512GB', NULL, 1249.00, 40, 'Active');
INSERT INTO SKU VALUES(7,  2, 'Titanium Black',    '1TB',   NULL, 1399.00, 20, 'Active');
INSERT INTO SKU VALUES(8,  3, 'Obsidian',          '128GB', NULL,  799.00, 70, 'Active');
INSERT INTO SKU VALUES(9,  3, 'Porcelain',         '128GB', NULL,  799.00, 70, 'Active');
INSERT INTO SKU VALUES(10, 3, 'Obsidian',          '256GB', NULL,  899.00, 30, 'Active');
INSERT INTO SKU VALUES(11, 4, 'Silky Black',       '256GB', NULL,  699.00, 60, 'Active');
INSERT INTO SKU VALUES(12, 4, 'Flowy Emerald',     '256GB', NULL,  699.00, 60, 'Active');
INSERT INTO SKU VALUES(13, 4, 'Silky Black',       '512GB', NULL,  799.00, 30, 'Active');
INSERT INTO SKU VALUES(14, 5, 'Black',             '256GB', NULL,  849.00, 30, 'Active');
INSERT INTO SKU VALUES(15, 5, 'Platinum Silver',   '256GB', NULL,  849.00, 30, 'Active');
INSERT INTO SKU VALUES(16, 5, 'Khaki Green',       '256GB', NULL,  849.00, 20, 'Active');

-- Tablets (Products 6-8)
INSERT INTO SKU VALUES(17, 6, 'Space Grey', '256GB', NULL, 1099.00, 25, 'Active');
INSERT INTO SKU VALUES(18, 6, 'Silver',     '256GB', NULL, 1099.00, 25, 'Active');
INSERT INTO SKU VALUES(19, 6, 'Space Grey', '512GB', NULL, 1299.00, 15, 'Active');
INSERT INTO SKU VALUES(20, 7, 'Graphite',   '256GB', NULL, 1099.00, 25, 'Active');
INSERT INTO SKU VALUES(21, 7, 'Graphite',   '512GB', NULL, 1199.00, 20, 'Active');
INSERT INTO SKU VALUES(22, 8, 'Platinum',   '256GB/i5', NULL, 1299.00, 20, 'Active');
INSERT INTO SKU VALUES(23, 8, 'Platinum',   '256GB/i7', NULL, 1499.00, 15, 'Active');
INSERT INTO SKU VALUES(24, 8, 'Graphite',   '512GB/i7', NULL, 1699.00, 10, 'Active');

-- Headphones & Speakers (Products 9-12)
INSERT INTO SKU VALUES(25, 9,  'Black',       NULL, NULL,  349.00, 80, 'Active');
INSERT INTO SKU VALUES(26, 9,  'Silver',      NULL, NULL,  349.00, 70, 'Active');
INSERT INTO SKU VALUES(27, 10, 'White',       NULL, NULL,  249.00, 150,'Active');
INSERT INTO SKU VALUES(28, 11, 'Black',       NULL, NULL,  279.00, 50, 'Active');
INSERT INTO SKU VALUES(29, 11, 'White Smoke', NULL, NULL,  279.00, 50, 'Active');
INSERT INTO SKU VALUES(30, 12, 'Black',       NULL, NULL,  139.00, 60, 'Active');
INSERT INTO SKU VALUES(31, 12, 'Blue',        NULL, NULL,  139.00, 50, 'Active');
INSERT INTO SKU VALUES(32, 12, 'Red',         NULL, NULL,  139.00, 40, 'Active');

-- Laptops (Products 13-16)
INSERT INTO SKU VALUES(33, 13, NULL, '512GB/16GB RAM', NULL, 1599.00, 20, 'Active');
INSERT INTO SKU VALUES(34, 13, NULL, '1TB/32GB RAM',   NULL, 1899.00, 15, 'Active');
INSERT INTO SKU VALUES(35, 14, 'Midnight',    '256GB/8GB',  NULL, 1099.00, 35, 'Active');
INSERT INTO SKU VALUES(36, 14, 'Starlight',   '512GB/8GB',  NULL, 1299.00, 25, 'Active');
INSERT INTO SKU VALUES(37, 14, 'Space Grey',  '512GB/16GB', NULL, 1499.00, 15, 'Active');
INSERT INTO SKU VALUES(38, 15, 'Black', '512GB/16GB RAM', NULL, 1449.00, 20, 'Active');
INSERT INTO SKU VALUES(39, 15, 'Black', '1TB/32GB RAM',   NULL, 1699.00, 10, 'Active');
INSERT INTO SKU VALUES(40, 16, 'Nightfall Black', '512GB/16GB', NULL, 1299.00, 25, 'Active');
INSERT INTO SKU VALUES(41, 16, 'Poseidon Blue',   '1TB/16GB',   NULL, 1499.00, 20, 'Active');

-- Keyboards & Mice (Products 17-19)
INSERT INTO SKU VALUES(42, 17, 'Graphite',   NULL, NULL,  99.00, 150, 'Active');
INSERT INTO SKU VALUES(43, 17, 'Pale Grey',  NULL, NULL,  99.00, 100, 'Active');
INSERT INTO SKU VALUES(44, 18, 'Silver',     NULL, NULL,  99.00, 120, 'Active');
INSERT INTO SKU VALUES(45, 18, 'Space Grey', NULL, NULL,  99.00,  80, 'Active');
INSERT INTO SKU VALUES(46, 19, 'Black',      NULL, NULL,  69.00, 150, 'Active');

-- Men's Clothing (Products 20-22)
INSERT INTO SKU VALUES(47, 20, NULL, NULL, 'S',  229.00, 30, 'Active');
INSERT INTO SKU VALUES(48, 20, NULL, NULL, 'M',  229.00, 40, 'Active');
INSERT INTO SKU VALUES(49, 20, NULL, NULL, 'L',  229.00, 40, 'Active');
INSERT INTO SKU VALUES(50, 20, NULL, NULL, 'XL', 229.00, 30, 'Active');
INSERT INTO SKU VALUES(51, 21, NULL, NULL, 'W30/L32', 85.00, 50, 'Active');
INSERT INTO SKU VALUES(52, 21, NULL, NULL, 'W32/L32', 85.00, 60, 'Active');
INSERT INTO SKU VALUES(53, 21, NULL, NULL, 'W34/L32', 85.00, 50, 'Active');
INSERT INTO SKU VALUES(54, 21, NULL, NULL, 'W36/L32', 85.00, 40, 'Active');
INSERT INTO SKU VALUES(55, 22, NULL, NULL, 'S',  75.00, 40, 'Active');
INSERT INTO SKU VALUES(56, 22, NULL, NULL, 'M',  75.00, 50, 'Active');
INSERT INTO SKU VALUES(57, 22, NULL, NULL, 'L',  75.00, 40, 'Active');
INSERT INTO SKU VALUES(58, 22, NULL, NULL, 'XL', 75.00, 30, 'Active');

-- Women's Clothing (Products 23-25)
INSERT INTO SKU VALUES(59, 23, NULL, NULL, 'XS', 119.00, 30, 'Active');
INSERT INTO SKU VALUES(60, 23, NULL, NULL, 'S',  119.00, 40, 'Active');
INSERT INTO SKU VALUES(61, 23, NULL, NULL, 'M',  119.00, 40, 'Active');
INSERT INTO SKU VALUES(62, 23, NULL, NULL, 'L',  119.00, 30, 'Active');
INSERT INTO SKU VALUES(63, 24, NULL, NULL, 'XS',  89.00, 30, 'Active');
INSERT INTO SKU VALUES(64, 24, NULL, NULL, 'S',   89.00, 40, 'Active');
INSERT INTO SKU VALUES(65, 24, NULL, NULL, 'M',   89.00, 40, 'Active');
INSERT INTO SKU VALUES(66, 24, NULL, NULL, 'L',   89.00, 30, 'Active');
INSERT INTO SKU VALUES(67, 25, NULL, NULL, 'XS', 195.00, 20, 'Active');
INSERT INTO SKU VALUES(68, 25, NULL, NULL, 'S',  195.00, 30, 'Active');
INSERT INTO SKU VALUES(69, 25, NULL, NULL, 'M',  195.00, 30, 'Active');
INSERT INTO SKU VALUES(70, 25, NULL, NULL, 'L',  195.00, 20, 'Active');

-- Sports Shoes (Products 26-29)
INSERT INTO SKU VALUES(71, 26, NULL, NULL, 'UK 6',  130.00, 30, 'Active');
INSERT INTO SKU VALUES(72, 26, NULL, NULL, 'UK 7',  130.00, 40, 'Active');
INSERT INTO SKU VALUES(73, 26, NULL, NULL, 'UK 8',  130.00, 50, 'Active');
INSERT INTO SKU VALUES(74, 26, NULL, NULL, 'UK 9',  130.00, 40, 'Active');
INSERT INTO SKU VALUES(75, 26, NULL, NULL, 'UK 10', 130.00, 30, 'Active');
INSERT INTO SKU VALUES(76, 27, NULL, NULL, 'UK 6',  160.00, 25, 'Active');
INSERT INTO SKU VALUES(77, 27, NULL, NULL, 'UK 7',  160.00, 35, 'Active');
INSERT INTO SKU VALUES(78, 27, NULL, NULL, 'UK 8',  160.00, 40, 'Active');
INSERT INTO SKU VALUES(79, 27, NULL, NULL, 'UK 9',  160.00, 35, 'Active');
INSERT INTO SKU VALUES(80, 27, NULL, NULL, 'UK 10', 160.00, 25, 'Active');
INSERT INTO SKU VALUES(81, 28, NULL, NULL, 'UK 6',   85.00, 40, 'Active');
INSERT INTO SKU VALUES(82, 28, NULL, NULL, 'UK 7',   85.00, 50, 'Active');
INSERT INTO SKU VALUES(83, 28, NULL, NULL, 'UK 8',   85.00, 60, 'Active');
INSERT INTO SKU VALUES(84, 28, NULL, NULL, 'UK 9',   85.00, 50, 'Active');
INSERT INTO SKU VALUES(85, 28, NULL, NULL, 'UK 10',  85.00, 40, 'Active');
INSERT INTO SKU VALUES(86, 29, NULL, NULL, 'UK 6',   90.00, 30, 'Active');
INSERT INTO SKU VALUES(87, 29, NULL, NULL, 'UK 7',   90.00, 40, 'Active');
INSERT INTO SKU VALUES(88, 29, NULL, NULL, 'UK 8',   90.00, 40, 'Active');
INSERT INTO SKU VALUES(89, 29, NULL, NULL, 'UK 9',   90.00, 30, 'Active');

-- Food & Fresh Produce (Products 30-36, single SKU each)
INSERT INTO SKU VALUES(90, 30, NULL, NULL, NULL,  4.50, 500, 'Active');
INSERT INTO SKU VALUES(91, 31, NULL, NULL, NULL,  6.00, 400, 'Active');
INSERT INTO SKU VALUES(92, 32, NULL, NULL, NULL,  4.00, 600, 'Active');
INSERT INTO SKU VALUES(93, 33, NULL, NULL, NULL,  3.50, 300, 'Active');
INSERT INTO SKU VALUES(94, 34, NULL, NULL, NULL,  3.50, 250, 'Active');
INSERT INTO SKU VALUES(95, 35, NULL, NULL, NULL,  8.00, 150, 'Active');
INSERT INTO SKU VALUES(96, 36, NULL, NULL, NULL,  4.00, 300, 'Active');

-- Appliances (Products 37-40)
INSERT INTO SKU VALUES(97,  37, 'White/Silver',  NULL, NULL, 549.00, 30, 'Active');
INSERT INTO SKU VALUES(98,  37, 'Black/Nickel',  NULL, NULL, 549.00, 25, 'Active');
INSERT INTO SKU VALUES(99,  38, 'White',         NULL, NULL, 699.00, 25, 'Active');
INSERT INTO SKU VALUES(100, 38, 'Graphite',      NULL, NULL, 699.00, 20, 'Active');
INSERT INTO SKU VALUES(101, 39, 'White',         NULL, NULL, 699.00, 30, 'Active');
INSERT INTO SKU VALUES(102, 39, 'Silver',        NULL, NULL, 749.00, 20, 'Active');
INSERT INTO SKU VALUES(103, 40, 'White',         NULL, NULL, 599.00, 35, 'Active');
INSERT INTO SKU VALUES(104, 40, 'Graphite',      NULL, NULL, 599.00, 25, 'Active');

/*******************************************************************************
   Insert Customers (50 customers, UK cities)
********************************************************************************/

INSERT INTO Customer VALUES(1,  'James Smith',       'james.smith@gmail.com',        'London',     'England',          '07700900001', '2022-01-15 10:00:00');
INSERT INTO Customer VALUES(2,  'Emma Johnson',      'emma.johnson@hotmail.com',     'Manchester',  'England',          '07700900002', '2022-02-20 11:00:00');
INSERT INTO Customer VALUES(3,  'Oliver Williams',   'oliver.williams@gmail.com',    'Birmingham',  'England',          '07700900003', '2022-03-10 09:00:00');
INSERT INTO Customer VALUES(4,  'Sophia Brown',      'sophia.brown@yahoo.com',       'Leeds',       'England',          '07700900004', '2022-04-05 14:00:00');
INSERT INTO Customer VALUES(5,  'Harry Jones',       'harry.jones@gmail.com',        'Bristol',     'England',          '07700900005', '2022-05-12 10:30:00');
INSERT INTO Customer VALUES(6,  'Isabella Taylor',   'isabella.taylor@hotmail.com',  'Liverpool',   'England',          '07700900006', '2022-06-18 15:00:00');
INSERT INTO Customer VALUES(7,  'Jack Wilson',       'jack.wilson@gmail.com',        'Sheffield',   'England',          '07700900007', '2022-07-22 11:00:00');
INSERT INTO Customer VALUES(8,  'Mia Davies',        'mia.davies@outlook.com',       'London',      'England',          '07700900008', '2022-08-30 13:00:00');
INSERT INTO Customer VALUES(9,  'George Evans',      'george.evans@gmail.com',       'Newcastle',   'England',          '07700900009', '2022-09-14 09:30:00');
INSERT INTO Customer VALUES(10, 'Amelia Thomas',     'amelia.thomas@hotmail.com',    'Edinburgh',   'Scotland',         '07700900010', '2022-10-05 10:00:00');
INSERT INTO Customer VALUES(11, 'Noah Roberts',      'noah.roberts@gmail.com',       'Glasgow',     'Scotland',         '07700900011', '2022-11-20 14:00:00');
INSERT INTO Customer VALUES(12, 'Charlotte Jackson', 'charlotte.jackson@yahoo.com',  'Cardiff',     'Wales',            '07700900012', '2022-12-08 11:00:00');
INSERT INTO Customer VALUES(13, 'Liam White',        'liam.white@gmail.com',         'Belfast',     'Northern Ireland', '07700900013', '2023-01-15 09:00:00');
INSERT INTO Customer VALUES(14, 'Emily Harris',      'emily.harris@hotmail.com',     'London',      'England',          '07700900014', '2023-02-10 10:30:00');
INSERT INTO Customer VALUES(15, 'William Martin',    'william.martin@gmail.com',     'Manchester',  'England',          '07700900015', '2023-03-25 13:00:00');
INSERT INTO Customer VALUES(16, 'Isla Thompson',     'isla.thompson@outlook.com',    'Birmingham',  'England',          '07700900016', '2023-04-12 11:00:00');
INSERT INTO Customer VALUES(17, 'Benjamin Garcia',   'benjamin.garcia@gmail.com',    'Leeds',       'England',          '07700900017', '2023-05-08 14:30:00');
INSERT INTO Customer VALUES(18, 'Sophie Martinez',   'sophie.martinez@hotmail.com',  'Bristol',     'England',          '07700900018', '2023-06-20 10:00:00');
INSERT INTO Customer VALUES(19, 'Elijah Robinson',   'elijah.robinson@gmail.com',    'Liverpool',   'England',          '07700900019', '2023-07-14 09:30:00');
INSERT INTO Customer VALUES(20, 'Grace Clark',       'grace.clark@yahoo.com',        'Sheffield',   'England',          '07700900020', '2023-08-30 15:00:00');
INSERT INTO Customer VALUES(21, 'Lucas Rodriguez',   'lucas.rodriguez@gmail.com',    'London',      'England',          '07700900021', '2023-09-05 11:00:00');
INSERT INTO Customer VALUES(22, 'Lily Lewis',        'lily.lewis@hotmail.com',       'Newcastle',   'England',          '07700900022', '2023-10-18 10:00:00');
INSERT INTO Customer VALUES(23, 'Mason Lee',         'mason.lee@gmail.com',          'Edinburgh',   'Scotland',         '07700900023', '2023-11-02 14:00:00');
INSERT INTO Customer VALUES(24, 'Chloe Walker',      'chloe.walker@yahoo.com',       'Glasgow',     'Scotland',         '07700900024', '2023-12-14 09:00:00');
INSERT INTO Customer VALUES(25, 'Logan Hall',        'logan.hall@gmail.com',         'Cardiff',     'Wales',            '07700900025', '2024-01-08 10:30:00');
INSERT INTO Customer VALUES(26, 'Hannah Allen',      'hannah.allen@hotmail.com',     'London',      'England',          '07700900026', '2024-01-20 13:00:00');
INSERT INTO Customer VALUES(27, 'Ethan Young',       'ethan.young@gmail.com',        'Manchester',  'England',          '07700900027', '2024-02-05 11:00:00');
INSERT INTO Customer VALUES(28, 'Zoe Hernandez',     'zoe.hernandez@outlook.com',    'Birmingham',  'England',          '07700900028', '2024-02-18 14:30:00');
INSERT INTO Customer VALUES(29, 'Alexander King',    'alexander.king@gmail.com',     'Leeds',       'England',          '07700900029', '2024-03-01 10:00:00');
INSERT INTO Customer VALUES(30, 'Lucy Wright',       'lucy.wright@hotmail.com',      'Bristol',     'England',          '07700900030', '2024-03-15 09:30:00');
INSERT INTO Customer VALUES(31, 'Daniel Lopez',      'daniel.lopez@gmail.com',       'Liverpool',   'England',          '07700900031', '2024-03-20 11:00:00');
INSERT INTO Customer VALUES(32, 'Ella Hill',         'ella.hill@yahoo.com',          'Sheffield',   'England',          '07700900032', '2024-04-02 14:00:00');
INSERT INTO Customer VALUES(33, 'Michael Scott',     'michael.scott@gmail.com',      'London',      'England',          '07700900033', '2024-04-10 10:30:00');
INSERT INTO Customer VALUES(34, 'Ava Green',         'ava.green@hotmail.com',        'Newcastle',   'England',          '07700900034', '2024-04-22 13:00:00');
INSERT INTO Customer VALUES(35, 'Matthew Adams',     'matthew.adams@gmail.com',      'Edinburgh',   'Scotland',         '07700900035', '2024-05-05 09:00:00');
INSERT INTO Customer VALUES(36, 'Scarlett Baker',    'scarlett.baker@yahoo.com',     'Glasgow',     'Scotland',         '07700900036', '2024-05-18 11:30:00');
INSERT INTO Customer VALUES(37, 'Owen Nelson',       'owen.nelson@gmail.com',        'Cardiff',     'Wales',            '07700900037', '2024-06-01 14:00:00');
INSERT INTO Customer VALUES(38, 'Poppy Carter',      'poppy.carter@hotmail.com',     'London',      'England',          '07700900038', '2024-06-14 10:00:00');
INSERT INTO Customer VALUES(39, 'Sebastian Mitchell','sebastian.mitchell@gmail.com', 'Manchester',  'England',          '07700900039', '2024-06-25 09:30:00');
INSERT INTO Customer VALUES(40, 'Freya Perez',       'freya.perez@outlook.com',      'Birmingham',  'England',          '07700900040', '2024-07-08 13:00:00');
INSERT INTO Customer VALUES(41, 'Joseph Roberts',    'joseph.roberts@gmail.com',     'Leeds',       'England',          '07700900041', '2024-07-20 11:00:00');
INSERT INTO Customer VALUES(42, 'Phoebe Turner',     'phoebe.turner@hotmail.com',    'Bristol',     'England',          '07700900042', '2024-08-02 14:30:00');
INSERT INTO Customer VALUES(43, 'Samuel Phillips',   'samuel.phillips@gmail.com',    'Liverpool',   'England',          '07700900043', '2024-08-15 10:00:00');
INSERT INTO Customer VALUES(44, 'Daisy Campbell',    'daisy.campbell@yahoo.com',     'Sheffield',   'England',          '07700900044', '2024-08-28 09:00:00');
INSERT INTO Customer VALUES(45, 'Ryan Parker',       'ryan.parker@gmail.com',        'London',      'England',          '07700900045', '2024-09-10 13:30:00');
INSERT INTO Customer VALUES(46, 'Ruby Evans',        'ruby.evans@hotmail.com',       'Newcastle',   'England',          '07700900046', '2024-09-22 11:00:00');
INSERT INTO Customer VALUES(47, 'Nathan Collins',    'nathan.collins@gmail.com',     'Edinburgh',   'Scotland',         '07700900047', '2024-10-05 14:00:00');
INSERT INTO Customer VALUES(48, 'Evelyn Stewart',    'evelyn.stewart@yahoo.com',     'Glasgow',     'Scotland',         '07700900048', '2024-10-18 10:30:00');
INSERT INTO Customer VALUES(49, 'Adam Morris',       'adam.morris@gmail.com',        'Cardiff',     'Wales',            '07700900049', '2024-11-01 09:00:00');
INSERT INTO Customer VALUES(50, 'Rosie Rogers',      'rosie.rogers@hotmail.com',     'London',      'England',          '07700900050', '2024-11-15 13:00:00');

/*******************************************************************************
   Insert Orders (180 orders)
   Round 1 (1-50):  Jan-Apr 2024, customer = order_id
   Round 2 (51-100): May-Aug 2024, customer = order_id - 50
   Round 3 (101-150): Sep-Dec 2024, customer = order_id - 100
   Round 4 (151-180): Jan-Mar 2025, customer = order_id - 150 (customers 1-30 only)
********************************************************************************/

-- Round 1
INSERT INTO "Order_" VALUES(1,  1,  '2024-01-03 10:15:00', 'Completed',  999.00, 'London',     'England');
INSERT INTO "Order_" VALUES(2,  2,  '2024-01-05 14:30:00', 'Completed', 1249.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(3,  3,  '2024-01-08 09:45:00', 'Completed',  799.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(4,  4,  '2024-01-10 16:20:00', 'Completed', 1099.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(5,  5,  '2024-01-12 11:30:00', 'Completed',  349.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(6,  6,  '2024-01-15 13:45:00', 'Completed', 1599.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(7,  7,  '2024-01-18 10:00:00', 'Completed', 1099.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(8,  8,  '2024-01-20 15:30:00', 'Completed',  249.00, 'London',     'England');
INSERT INTO "Order_" VALUES(9,  9,  '2024-01-22 09:15:00', 'Completed',  699.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(10, 10, '2024-01-25 14:00:00', 'Completed',  279.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(11, 11, '2024-01-28 11:30:00', 'Completed',  849.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(12, 12, '2024-01-30 16:45:00', 'Completed', 1449.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(13, 13, '2024-02-01 10:30:00', 'Completed', 1299.00, 'Belfast',    'Northern Ireland');
INSERT INTO "Order_" VALUES(14, 14, '2024-02-03 13:15:00', 'Completed',   99.00, 'London',     'England');
INSERT INTO "Order_" VALUES(15, 15, '2024-02-05 09:00:00', 'Completed',  229.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(16, 16, '2024-02-07 15:30:00', 'Completed',   85.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(17, 17, '2024-02-10 11:00:00', 'Completed',  130.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(18, 18, '2024-02-12 14:30:00', 'Completed',  160.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(19, 19, '2024-02-15 10:15:00', 'Completed',  119.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(20, 20, '2024-02-17 16:00:00', 'Completed',  549.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(21, 21, '2024-02-20 11:30:00', 'Completed',  699.00, 'London',     'England');
INSERT INTO "Order_" VALUES(22, 22, '2024-02-22 13:00:00', 'Completed',  699.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(23, 23, '2024-02-24 09:45:00', 'Completed',  599.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(24, 24, '2024-02-26 15:15:00', 'Completed',  139.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(25, 25, '2024-02-28 10:30:00', 'Completed',  195.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(26, 26, '2024-03-01 14:00:00', 'Completed',   89.00, 'London',     'England');
INSERT INTO "Order_" VALUES(27, 27, '2024-03-03 11:15:00', 'Completed',   85.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(28, 28, '2024-03-05 16:30:00', 'Completed',   90.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(29, 29, '2024-03-07 10:00:00', 'Completed',    4.50, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(30, 30, '2024-03-10 13:30:00', 'Completed',    6.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(31, 31, '2024-03-12 11:00:00', 'Completed',    4.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(32, 32, '2024-03-15 15:45:00', 'Completed',    3.50, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(33, 33, '2024-03-17 10:30:00', 'Completed',    3.50, 'London',     'England');
INSERT INTO "Order_" VALUES(34, 34, '2024-03-20 14:15:00', 'Completed',    8.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(35, 35, '2024-03-22 11:45:00', 'Completed',    4.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(36, 36, '2024-03-25 16:00:00', 'Completed',   75.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(37, 37, '2024-03-27 10:15:00', 'Completed',   99.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(38, 38, '2024-03-29 13:45:00', 'Completed',   69.00, 'London',     'England');
INSERT INTO "Order_" VALUES(39, 39, '2024-04-01 11:30:00', 'Completed', 1299.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(40, 40, '2024-04-03 15:00:00', 'Completed', 1099.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(41, 41, '2024-04-05 10:45:00', 'Completed',  999.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(42, 42, '2024-04-08 14:30:00', 'Completed',  349.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(43, 43, '2024-04-10 11:15:00', 'Completed',  249.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(44, 44, '2024-04-12 16:00:00', 'Completed',  130.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(45, 45, '2024-04-15 10:30:00', 'Completed',  160.00, 'London',     'England');
INSERT INTO "Order_" VALUES(46, 46, '2024-04-17 14:00:00', 'Completed', 1249.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(47, 47, '2024-04-20 11:45:00', 'Completed',  799.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(48, 48, '2024-04-22 15:30:00', 'Completed',  699.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(49, 49, '2024-04-25 10:15:00', 'Completed',  849.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(50, 50, '2024-04-28 13:45:00', 'Completed', 1099.00, 'London',     'England');

-- Round 2 (order 51 has 2 items: total = 279+99 = 378)
INSERT INTO "Order_" VALUES(51,  1,  '2024-05-01 10:30:00', 'Completed',  378.00, 'London',     'England');
INSERT INTO "Order_" VALUES(52,  2,  '2024-05-03 14:15:00', 'Completed', 1599.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(53,  3,  '2024-05-06 11:00:00', 'Completed',  229.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(54,  4,  '2024-05-08 15:45:00', 'Completed',   85.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(55,  5,  '2024-05-10 10:30:00', 'Completed',  119.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(56,  6,  '2024-05-13 14:00:00', 'Completed',  195.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(57,  7,  '2024-05-15 11:15:00', 'Completed',   89.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(58,  8,  '2024-05-17 16:30:00', 'Completed',   85.00, 'London',     'England');
INSERT INTO "Order_" VALUES(59,  9,  '2024-05-20 10:00:00', 'Completed',  549.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(60, 10,  '2024-05-22 13:30:00', 'Completed',  699.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(61, 11,  '2024-05-24 11:45:00', 'Completed',  599.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(62, 12,  '2024-05-27 15:15:00', 'Completed',  139.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(63, 13,  '2024-05-29 10:30:00', 'Completed', 1099.00, 'Belfast',    'Northern Ireland');
INSERT INTO "Order_" VALUES(64, 14,  '2024-06-01 14:15:00', 'Completed', 1449.00, 'London',     'England');
INSERT INTO "Order_" VALUES(65, 15,  '2024-06-03 11:00:00', 'Completed',   75.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(66, 16,  '2024-06-05 15:45:00', 'Completed',  699.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(67, 17,  '2024-06-08 10:30:00', 'Completed',   99.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(68, 18,  '2024-06-10 14:00:00', 'Completed',   69.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(69, 19,  '2024-06-12 11:15:00', 'Completed',    4.50, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(70, 20,  '2024-06-15 16:30:00', 'Completed',    6.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(71, 21,  '2024-06-17 10:00:00', 'Completed', 1299.00, 'London',     'England');
INSERT INTO "Order_" VALUES(72, 22,  '2024-06-20 13:30:00', 'Completed',   90.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(73, 23,  '2024-06-22 11:45:00', 'Completed',    3.50, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(74, 24,  '2024-06-24 15:00:00', 'Completed',    8.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(75, 25,  '2024-06-27 10:15:00', 'Completed',    4.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(76, 26,  '2024-06-29 14:30:00', 'Completed',  999.00, 'London',     'England');
INSERT INTO "Order_" VALUES(77, 27,  '2024-07-01 11:15:00', 'Shipped',   1318.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(78, 28,  '2024-07-03 15:45:00', 'Shipped',    799.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(79, 29,  '2024-07-05 10:30:00', 'Shipped',    349.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(80, 30,  '2024-07-08 14:00:00', 'Shipped',    249.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(81, 31,  '2024-07-10 11:15:00', 'Shipped',    699.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(82, 32,  '2024-07-12 16:30:00', 'Shipped',   1099.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(83, 33,  '2024-07-15 10:00:00', 'Shipped',   1099.00, 'London',     'England');
INSERT INTO "Order_" VALUES(84, 34,  '2024-07-17 13:30:00', 'Shipped',    130.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(85, 35,  '2024-07-20 11:45:00', 'Shipped',    160.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(86, 36,  '2024-07-22 15:15:00', 'Shipped',     85.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(87, 37,  '2024-07-24 10:30:00', 'Shipped',   1599.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(88, 38,  '2024-07-27 14:15:00', 'Shipped',    229.00, 'London',     'England');
INSERT INTO "Order_" VALUES(89, 39,  '2024-07-29 11:00:00', 'Shipped',     85.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(90, 40,  '2024-08-01 15:45:00', 'Shipped',    119.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(91, 41,  '2024-08-03 10:30:00', 'Shipped',    549.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(92, 42,  '2024-08-05 14:00:00', 'Shipped',    699.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(93, 43,  '2024-08-08 11:15:00', 'Shipped',    699.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(94, 44,  '2024-08-10 16:30:00', 'Shipped',    599.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(95, 45,  '2024-08-12 10:00:00', 'Shipped',    195.00, 'London',     'England');
INSERT INTO "Order_" VALUES(96, 46,  '2024-08-15 13:30:00', 'Shipped',     89.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(97, 47,  '2024-08-17 11:45:00', 'Shipped',     90.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(98, 48,  '2024-08-20 15:15:00', 'Shipped',    139.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(99, 49,  '2024-08-22 10:30:00', 'Shipped',     75.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(100,50,  '2024-08-24 14:15:00', 'Shipped',     99.00, 'London',     'England');

-- Round 3
INSERT INTO "Order_" VALUES(101, 1,  '2024-09-01 10:15:00', 'Paid',    849.00, 'London',     'England');
INSERT INTO "Order_" VALUES(102, 2,  '2024-09-03 14:00:00', 'Paid',   1099.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(103, 3,  '2024-09-05 11:30:00', 'Paid',   1299.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(104, 4,  '2024-09-08 15:45:00', 'Paid',    279.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(105, 5,  '2024-09-10 10:00:00', 'Paid',   1449.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(106, 6,  '2024-09-12 13:30:00', 'Paid',   1299.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(107, 7,  '2024-09-15 11:00:00', 'Paid',     99.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(108, 8,  '2024-09-17 16:15:00', 'Paid',     99.00, 'London',     'England');
INSERT INTO "Order_" VALUES(109, 9,  '2024-09-20 10:30:00', 'Paid',     69.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(110, 10, '2024-09-22 14:00:00', 'Paid',      4.50, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(111, 11, '2024-09-24 11:45:00', 'Paid',      6.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(112, 12, '2024-09-27 15:30:00', 'Paid',      4.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(113, 13, '2024-09-29 10:15:00', 'Paid',      3.50, 'Belfast',    'Northern Ireland');
INSERT INTO "Order_" VALUES(114, 14, '2024-10-01 14:30:00', 'Paid',      8.00, 'London',     'England');
INSERT INTO "Order_" VALUES(115, 15, '2024-10-03 11:00:00', 'Paid',      4.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(116, 16, '2024-10-05 16:45:00', 'Paid',    999.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(117, 17, '2024-10-08 10:30:00', 'Paid',   1249.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(118, 18, '2024-10-10 14:15:00', 'Paid',    799.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(119, 19, '2024-10-12 11:00:00', 'Paid',    699.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(120, 20, '2024-10-15 15:30:00', 'Paid',    349.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(121, 21, '2024-10-17 10:15:00', 'Pending', 1099.00, 'London',    'England');
INSERT INTO "Order_" VALUES(122, 22, '2024-10-20 14:00:00', 'Pending', 1599.00, 'Newcastle', 'England');
INSERT INTO "Order_" VALUES(123, 23, '2024-10-22 11:30:00', 'Pending',  229.00, 'Edinburgh', 'Scotland');
INSERT INTO "Order_" VALUES(124, 24, '2024-10-24 15:45:00', 'Pending',  130.00, 'Glasgow',   'Scotland');
INSERT INTO "Order_" VALUES(125, 25, '2024-10-27 10:00:00', 'Pending',  160.00, 'Cardiff',   'Wales');
INSERT INTO "Order_" VALUES(126, 26, '2024-10-29 13:30:00', 'Pending',   85.00, 'London',    'England');
INSERT INTO "Order_" VALUES(127, 27, '2024-11-01 11:00:00', 'Pending',   90.00, 'Manchester','England');
INSERT INTO "Order_" VALUES(128, 28, '2024-11-03 16:15:00', 'Pending',  195.00, 'Birmingham','England');
INSERT INTO "Order_" VALUES(129, 29, '2024-11-05 10:30:00', 'Pending',   89.00, 'Leeds',     'England');
INSERT INTO "Order_" VALUES(130, 30, '2024-11-07 14:00:00', 'Pending',   75.00, 'Bristol',   'England');
INSERT INTO "Order_" VALUES(131, 31, '2024-11-10 11:15:00', 'Pending',  549.00, 'Liverpool', 'England');
INSERT INTO "Order_" VALUES(132, 32, '2024-11-12 15:30:00', 'Pending',  699.00, 'Sheffield', 'England');
INSERT INTO "Order_" VALUES(133, 33, '2024-11-14 10:15:00', 'Pending',  599.00, 'London',    'England');
INSERT INTO "Order_" VALUES(134, 34, '2024-11-17 14:30:00', 'Pending',  139.00, 'Newcastle', 'England');
INSERT INTO "Order_" VALUES(135, 35, '2024-11-19 11:00:00', 'Pending',  249.00, 'Edinburgh', 'Scotland');
INSERT INTO "Order_" VALUES(136, 36, '2024-11-21 16:45:00', 'Completed', 699.00, 'Glasgow',  'Scotland');
INSERT INTO "Order_" VALUES(137, 37, '2024-11-24 10:30:00', 'Completed',1099.00, 'Cardiff',  'Wales');
INSERT INTO "Order_" VALUES(138, 38, '2024-11-26 14:15:00', 'Completed',1449.00, 'London',   'England');
INSERT INTO "Order_" VALUES(139, 39, '2024-11-28 11:00:00', 'Completed',1299.00, 'Manchester','England');
INSERT INTO "Order_" VALUES(140, 40, '2024-12-01 15:30:00', 'Completed',  99.00, 'Birmingham','England');
INSERT INTO "Order_" VALUES(141, 41, '2024-12-03 10:15:00', 'Completed',  69.00, 'Leeds',    'England');
INSERT INTO "Order_" VALUES(142, 42, '2024-12-05 14:00:00', 'Completed', 849.00, 'Bristol',  'England');
INSERT INTO "Order_" VALUES(143, 43, '2024-12-08 11:30:00', 'Completed',1099.00, 'Liverpool','England');
INSERT INTO "Order_" VALUES(144, 44, '2024-12-10 15:45:00', 'Completed', 279.00, 'Sheffield','England');
INSERT INTO "Order_" VALUES(145, 45, '2024-12-12 10:00:00', 'Completed',   4.50, 'London',   'England');
INSERT INTO "Order_" VALUES(146, 46, '2024-12-15 13:30:00', 'Completed',   6.00, 'Newcastle','England');
INSERT INTO "Order_" VALUES(147, 47, '2024-12-17 11:00:00', 'Completed',   4.00, 'Edinburgh','Scotland');
INSERT INTO "Order_" VALUES(148, 48, '2024-12-20 16:15:00', 'Completed',   3.50, 'Glasgow',  'Scotland');
INSERT INTO "Order_" VALUES(149, 49, '2024-12-22 10:30:00', 'Completed',   3.50, 'Cardiff',  'Wales');
INSERT INTO "Order_" VALUES(150, 50, '2024-12-24 14:00:00', 'Completed',   8.00, 'London',   'England');

-- Round 4 (customers 1-30 only)
INSERT INTO "Order_" VALUES(151, 1,  '2025-01-05 10:15:00', 'Completed',  999.00, 'London',     'England');
INSERT INTO "Order_" VALUES(152, 2,  '2025-01-07 14:30:00', 'Completed', 1249.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(153, 3,  '2025-01-10 11:00:00', 'Completed',  799.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(154, 4,  '2025-01-12 15:45:00', 'Completed', 1099.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(155, 5,  '2025-01-15 10:30:00', 'Completed',  349.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(156, 6,  '2025-01-17 14:15:00', 'Completed', 1599.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(157, 7,  '2025-01-20 11:00:00', 'Completed', 1099.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(158, 8,  '2025-01-22 16:30:00', 'Completed',  249.00, 'London',     'England');
INSERT INTO "Order_" VALUES(159, 9,  '2025-01-25 10:15:00', 'Completed',  699.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(160, 10, '2025-01-27 14:00:00', 'Completed',  699.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(161, 11, '2025-02-01 11:30:00', 'Completed',  229.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(162, 12, '2025-02-03 15:45:00', 'Completed',  130.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(163, 13, '2025-02-05 10:00:00', 'Completed',  160.00, 'Belfast',    'Northern Ireland');
INSERT INTO "Order_" VALUES(164, 14, '2025-02-08 13:30:00', 'Completed',   85.00, 'London',     'England');
INSERT INTO "Order_" VALUES(165, 15, '2025-02-10 11:00:00', 'Completed',  119.00, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(166, 16, '2025-02-12 16:15:00', 'Completed',  195.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(167, 17, '2025-02-15 10:30:00', 'Completed',   89.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(168, 18, '2025-02-17 14:00:00', 'Completed',   85.00, 'Bristol',    'England');
INSERT INTO "Order_" VALUES(169, 19, '2025-02-20 11:15:00', 'Completed',   75.00, 'Liverpool',  'England');
INSERT INTO "Order_" VALUES(170, 20, '2025-02-22 15:30:00', 'Completed',  549.00, 'Sheffield',  'England');
INSERT INTO "Order_" VALUES(171, 21, '2025-02-24 10:15:00', 'Shipped',    599.00, 'London',     'England');
INSERT INTO "Order_" VALUES(172, 22, '2025-02-27 14:30:00', 'Shipped',    139.00, 'Newcastle',  'England');
INSERT INTO "Order_" VALUES(173, 23, '2025-03-01 11:00:00', 'Shipped',     99.00, 'Edinburgh',  'Scotland');
INSERT INTO "Order_" VALUES(174, 24, '2025-03-03 15:45:00', 'Shipped',     90.00, 'Glasgow',    'Scotland');
INSERT INTO "Order_" VALUES(175, 25, '2025-03-05 10:30:00', 'Shipped',      4.00, 'Cardiff',    'Wales');
INSERT INTO "Order_" VALUES(176, 26, '2025-03-07 14:15:00', 'Shipped',      6.00, 'London',     'England');
INSERT INTO "Order_" VALUES(177, 27, '2025-03-10 11:00:00', 'Shipped',      4.50, 'Manchester', 'England');
INSERT INTO "Order_" VALUES(178, 28, '2025-03-12 16:30:00', 'Pending',   1299.00, 'Birmingham', 'England');
INSERT INTO "Order_" VALUES(179, 29, '2025-03-15 10:15:00', 'Pending',     69.00, 'Leeds',      'England');
INSERT INTO "Order_" VALUES(180, 30, '2025-03-17 14:00:00', 'Pending',     99.00, 'Bristol',    'England');

/*******************************************************************************
   Insert OrderItems (182 items)
   Orders 51 and 77 have 2 items each
********************************************************************************/

-- Format: OrderItemId, OrderId, ProductId, SkuId, Quantity, UnitPrice, Discount
INSERT INTO OrderItem VALUES(1,  1,  1,  1,  1,  999.00, 1);
INSERT INTO OrderItem VALUES(2,  2,  2,  5,  1, 1249.00, 1);
INSERT INTO OrderItem VALUES(3,  3,  3,  8,  1,  799.00, 1);
INSERT INTO OrderItem VALUES(4,  4,  6,  17, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(5,  5,  9,  25, 1,  349.00, 1);
INSERT INTO OrderItem VALUES(6,  6,  13, 33, 1, 1599.00, 1);
INSERT INTO OrderItem VALUES(7,  7,  14, 35, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(8,  8,  10, 27, 1,  249.00, 1);
INSERT INTO OrderItem VALUES(9,  9,  4,  11, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(10, 10, 11, 28, 1,  279.00, 1);
INSERT INTO OrderItem VALUES(11, 11, 5,  14, 1,  849.00, 1);
INSERT INTO OrderItem VALUES(12, 12, 15, 38, 1, 1449.00, 1);
INSERT INTO OrderItem VALUES(13, 13, 16, 40, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(14, 14, 17, 42, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(15, 15, 20, 48, 1,  229.00, 1);
INSERT INTO OrderItem VALUES(16, 16, 21, 52, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(17, 17, 26, 73, 1,  130.00, 1);
INSERT INTO OrderItem VALUES(18, 18, 27, 78, 1,  160.00, 1);
INSERT INTO OrderItem VALUES(19, 19, 23, 60, 1,  119.00, 1);
INSERT INTO OrderItem VALUES(20, 20, 37, 97, 1,  549.00, 1);
INSERT INTO OrderItem VALUES(21, 21, 38, 99, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(22, 22, 39, 101,1,  699.00, 1);
INSERT INTO OrderItem VALUES(23, 23, 40, 103,1,  599.00, 1);
INSERT INTO OrderItem VALUES(24, 24, 12, 30, 1,  139.00, 1);
INSERT INTO OrderItem VALUES(25, 25, 25, 68, 1,  195.00, 1);
INSERT INTO OrderItem VALUES(26, 26, 24, 64, 1,   89.00, 1);
INSERT INTO OrderItem VALUES(27, 27, 28, 83, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(28, 28, 29, 88, 1,   90.00, 1);
INSERT INTO OrderItem VALUES(29, 29, 30, 90, 1,    4.50, 1);
INSERT INTO OrderItem VALUES(30, 30, 31, 91, 1,    6.00, 1);
INSERT INTO OrderItem VALUES(31, 31, 32, 92, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(32, 32, 33, 93, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(33, 33, 34, 94, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(34, 34, 35, 95, 1,    8.00, 1);
INSERT INTO OrderItem VALUES(35, 35, 36, 96, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(36, 36, 22, 56, 1,   75.00, 1);
INSERT INTO OrderItem VALUES(37, 37, 18, 44, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(38, 38, 19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(39, 39, 8,  22, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(40, 40, 7,  20, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(41, 41, 1,  2,  1,  999.00, 1);
INSERT INTO OrderItem VALUES(42, 42, 9,  26, 1,  349.00, 1);
INSERT INTO OrderItem VALUES(43, 43, 10, 27, 1,  249.00, 1);
INSERT INTO OrderItem VALUES(44, 44, 26, 74, 1,  130.00, 1);
INSERT INTO OrderItem VALUES(45, 45, 27, 79, 1,  160.00, 1);
INSERT INTO OrderItem VALUES(46, 46, 2,  6,  1, 1249.00, 1);
INSERT INTO OrderItem VALUES(47, 47, 3,  9,  1,  799.00, 1);
INSERT INTO OrderItem VALUES(48, 48, 4,  12, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(49, 49, 5,  15, 1,  849.00, 1);
INSERT INTO OrderItem VALUES(50, 50, 6,  18, 1, 1099.00, 1);
-- Order 51 has 2 items
INSERT INTO OrderItem VALUES(51, 51, 11, 29, 1,  279.00, 1);
INSERT INTO OrderItem VALUES(181,51, 17, 43, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(52, 52, 13, 34, 1, 1599.00, 1);
INSERT INTO OrderItem VALUES(53, 53, 20, 49, 1,  229.00, 1);
INSERT INTO OrderItem VALUES(54, 54, 21, 53, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(55, 55, 23, 61, 1,  119.00, 1);
INSERT INTO OrderItem VALUES(56, 56, 25, 69, 1,  195.00, 1);
INSERT INTO OrderItem VALUES(57, 57, 24, 65, 1,   89.00, 1);
INSERT INTO OrderItem VALUES(58, 58, 28, 84, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(59, 59, 37, 98, 1,  549.00, 1);
INSERT INTO OrderItem VALUES(60, 60, 39, 102,1,  699.00, 1);
INSERT INTO OrderItem VALUES(61, 61, 40, 104,1,  599.00, 1);
INSERT INTO OrderItem VALUES(62, 62, 12, 31, 1,  139.00, 1);
INSERT INTO OrderItem VALUES(63, 63, 14, 36, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(64, 64, 15, 39, 1, 1449.00, 1);
INSERT INTO OrderItem VALUES(65, 65, 22, 57, 1,   75.00, 1);
INSERT INTO OrderItem VALUES(66, 66, 38, 100,1,  699.00, 1);
INSERT INTO OrderItem VALUES(67, 67, 18, 45, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(68, 68, 19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(69, 69, 30, 90, 1,    4.50, 1);
INSERT INTO OrderItem VALUES(70, 70, 31, 91, 1,    6.00, 1);
INSERT INTO OrderItem VALUES(71, 71, 8,  23, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(72, 72, 29, 87, 1,   90.00, 1);
INSERT INTO OrderItem VALUES(73, 73, 33, 93, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(74, 74, 35, 95, 1,    8.00, 1);
INSERT INTO OrderItem VALUES(75, 75, 36, 96, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(76, 76, 1,  3,  1,  999.00, 1);
-- Order 77 has 2 items
INSERT INTO OrderItem VALUES(77, 77, 2,  7,  1, 1249.00, 1);
INSERT INTO OrderItem VALUES(182,77, 19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(78, 78, 3,  10, 1,  799.00, 1);
INSERT INTO OrderItem VALUES(79, 79, 9,  25, 1,  349.00, 1);
INSERT INTO OrderItem VALUES(80, 80, 10, 27, 1,  249.00, 1);
INSERT INTO OrderItem VALUES(81, 81, 4,  11, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(82, 82, 6,  19, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(83, 83, 14, 37, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(84, 84, 26, 75, 1,  130.00, 1);
INSERT INTO OrderItem VALUES(85, 85, 27, 80, 1,  160.00, 1);
INSERT INTO OrderItem VALUES(86, 86, 28, 85, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(87, 87, 13, 33, 1, 1599.00, 1);
INSERT INTO OrderItem VALUES(88, 88, 20, 50, 1,  229.00, 1);
INSERT INTO OrderItem VALUES(89, 89, 21, 54, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(90, 90, 23, 62, 1,  119.00, 1);
INSERT INTO OrderItem VALUES(91, 91, 37, 97, 1,  549.00, 1);
INSERT INTO OrderItem VALUES(92, 92, 38, 99, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(93, 93, 39, 101,1,  699.00, 1);
INSERT INTO OrderItem VALUES(94, 94, 40, 103,1,  599.00, 1);
INSERT INTO OrderItem VALUES(95, 95, 25, 70, 1,  195.00, 1);
INSERT INTO OrderItem VALUES(96, 96, 24, 66, 1,   89.00, 1);
INSERT INTO OrderItem VALUES(97, 97, 29, 86, 1,   90.00, 1);
INSERT INTO OrderItem VALUES(98, 98, 12, 32, 1,  139.00, 1);
INSERT INTO OrderItem VALUES(99, 99, 22, 58, 1,   75.00, 1);
INSERT INTO OrderItem VALUES(100,100,17, 43, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(101,101,5,  16, 1,  849.00, 1);
INSERT INTO OrderItem VALUES(102,102,7,  21, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(103,103,8,  24, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(104,104,11, 28, 1,  279.00, 1);
INSERT INTO OrderItem VALUES(105,105,15, 38, 1, 1449.00, 1);
INSERT INTO OrderItem VALUES(106,106,16, 41, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(107,107,17, 42, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(108,108,18, 44, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(109,109,19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(110,110,30, 90, 1,    4.50, 1);
INSERT INTO OrderItem VALUES(111,111,31, 91, 1,    6.00, 1);
INSERT INTO OrderItem VALUES(112,112,32, 92, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(113,113,34, 94, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(114,114,35, 95, 1,    8.00, 1);
INSERT INTO OrderItem VALUES(115,115,36, 96, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(116,116,1,  4,  1,  999.00, 1);
INSERT INTO OrderItem VALUES(117,117,2,  5,  1, 1249.00, 1);
INSERT INTO OrderItem VALUES(118,118,3,  8,  1,  799.00, 1);
INSERT INTO OrderItem VALUES(119,119,4,  13, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(120,120,9,  26, 1,  349.00, 1);
INSERT INTO OrderItem VALUES(121,121,6,  17, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(122,122,13, 33, 1, 1599.00, 1);
INSERT INTO OrderItem VALUES(123,123,20, 47, 1,  229.00, 1);
INSERT INTO OrderItem VALUES(124,124,26, 72, 1,  130.00, 1);
INSERT INTO OrderItem VALUES(125,125,27, 77, 1,  160.00, 1);
INSERT INTO OrderItem VALUES(126,126,28, 82, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(127,127,29, 89, 1,   90.00, 1);
INSERT INTO OrderItem VALUES(128,128,25, 67, 1,  195.00, 1);
INSERT INTO OrderItem VALUES(129,129,24, 63, 1,   89.00, 1);
INSERT INTO OrderItem VALUES(130,130,22, 55, 1,   75.00, 1);
INSERT INTO OrderItem VALUES(131,131,37, 97, 1,  549.00, 1);
INSERT INTO OrderItem VALUES(132,132,39, 101,1,  699.00, 1);
INSERT INTO OrderItem VALUES(133,133,40, 103,1,  599.00, 1);
INSERT INTO OrderItem VALUES(134,134,12, 30, 1,  139.00, 1);
INSERT INTO OrderItem VALUES(135,135,10, 27, 1,  249.00, 1);
INSERT INTO OrderItem VALUES(136,136,38, 99, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(137,137,14, 35, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(138,138,15, 38, 1, 1449.00, 1);
INSERT INTO OrderItem VALUES(139,139,8,  22, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(140,140,18, 44, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(141,141,19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(142,142,5,  14, 1,  849.00, 1);
INSERT INTO OrderItem VALUES(143,143,7,  20, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(144,144,11, 29, 1,  279.00, 1);
INSERT INTO OrderItem VALUES(145,145,30, 90, 1,    4.50, 1);
INSERT INTO OrderItem VALUES(146,146,31, 91, 1,    6.00, 1);
INSERT INTO OrderItem VALUES(147,147,32, 92, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(148,148,33, 93, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(149,149,34, 94, 1,    3.50, 1);
INSERT INTO OrderItem VALUES(150,150,35, 95, 1,    8.00, 1);
INSERT INTO OrderItem VALUES(151,151,1,  1,  1,  999.00, 1);
INSERT INTO OrderItem VALUES(152,152,2,  5,  1, 1249.00, 1);
INSERT INTO OrderItem VALUES(153,153,3,  8,  1,  799.00, 1);
INSERT INTO OrderItem VALUES(154,154,6,  17, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(155,155,9,  25, 1,  349.00, 1);
INSERT INTO OrderItem VALUES(156,156,13, 33, 1, 1599.00, 1);
INSERT INTO OrderItem VALUES(157,157,14, 35, 1, 1099.00, 1);
INSERT INTO OrderItem VALUES(158,158,10, 27, 1,  249.00, 1);
INSERT INTO OrderItem VALUES(159,159,38, 99, 1,  699.00, 1);
INSERT INTO OrderItem VALUES(160,160,39, 101,1,  699.00, 1);
INSERT INTO OrderItem VALUES(161,161,20, 48, 1,  229.00, 1);
INSERT INTO OrderItem VALUES(162,162,26, 71, 1,  130.00, 1);
INSERT INTO OrderItem VALUES(163,163,27, 76, 1,  160.00, 1);
INSERT INTO OrderItem VALUES(164,164,28, 81, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(165,165,23, 59, 1,  119.00, 1);
INSERT INTO OrderItem VALUES(166,166,25, 68, 1,  195.00, 1);
INSERT INTO OrderItem VALUES(167,167,24, 64, 1,   89.00, 1);
INSERT INTO OrderItem VALUES(168,168,21, 51, 1,   85.00, 1);
INSERT INTO OrderItem VALUES(169,169,22, 56, 1,   75.00, 1);
INSERT INTO OrderItem VALUES(170,170,37, 97, 1,  549.00, 1);
INSERT INTO OrderItem VALUES(171,171,40, 104,1,  599.00, 1);
INSERT INTO OrderItem VALUES(172,172,12, 30, 1,  139.00, 1);
INSERT INTO OrderItem VALUES(173,173,17, 42, 1,   99.00, 1);
INSERT INTO OrderItem VALUES(174,174,29, 88, 1,   90.00, 1);
INSERT INTO OrderItem VALUES(175,175,36, 96, 1,    4.00, 1);
INSERT INTO OrderItem VALUES(176,176,31, 91, 1,    6.00, 1);
INSERT INTO OrderItem VALUES(177,177,30, 90, 1,    4.50, 1);
INSERT INTO OrderItem VALUES(178,178,16, 40, 1, 1299.00, 1);
INSERT INTO OrderItem VALUES(179,179,19, 46, 1,   69.00, 1);
INSERT INTO OrderItem VALUES(180,180,18, 44, 1,   99.00, 1);

/*******************************************************************************
   Insert Reviews (60 reviews)
********************************************************************************/

INSERT INTO Review VALUES(1,  1,  1,  5, 'Absolutely love my new iPhone 15 Pro! The camera quality is outstanding and it runs incredibly smooth.', '2024-01-20 10:00:00');
INSERT INTO Review VALUES(2,  2,  2,  5, 'The Samsung Galaxy S24 Ultra is a beast! Amazing display and the S Pen is very useful.', '2024-01-22 14:00:00');
INSERT INTO Review VALUES(3,  3,  3,  4, 'Great camera performance from the Pixel 8 Pro. Google AI features are very impressive.', '2024-01-25 09:00:00');
INSERT INTO Review VALUES(4,  4,  6,  5, 'The iPad Pro M2 is simply incredible for creative work. Worth every penny!', '2024-01-28 15:00:00');
INSERT INTO Review VALUES(5,  5,  9,  5, 'Best noise-cancelling headphones I have ever owned. Sony has done it again!', '2024-01-30 11:00:00');
INSERT INTO Review VALUES(6,  6,  13, 5, 'Dell XPS 15 is a powerhouse! Stunning display and excellent build quality.', '2024-02-02 13:00:00');
INSERT INTO Review VALUES(7,  7,  14, 5, 'MacBook Air M2 is the perfect laptop. Incredibly fast and completely silent.', '2024-02-05 10:00:00');
INSERT INTO Review VALUES(8,  8,  10, 4, 'AirPods Pro 2 are brilliant. Seamless integration with my iPhone and great ANC.', '2024-02-08 14:00:00');
INSERT INTO Review VALUES(9,  9,  4,  4, 'Excellent value for money. OnePlus 12 fast charging is incredible!', '2024-02-10 09:30:00');
INSERT INTO Review VALUES(10, 10, 11, 4, 'Bose QC45 delivers excellent sound and noise cancellation. Very comfortable for long wear.', '2024-02-12 11:00:00');
INSERT INTO Review VALUES(11, 11, 5,  3, 'Decent phone but quite expensive for what it offers. Battery life is average.', '2024-02-15 14:00:00');
INSERT INTO Review VALUES(12, 12, 15, 5, 'Lenovo ThinkPad X1 Carbon is built for professionals. Reliable, durable and lightweight.', '2024-02-18 10:00:00');
INSERT INTO Review VALUES(13, 13, 16, 3, 'HP Spectre x360 is beautiful but runs warm under heavy load. Disappointing.', '2024-02-20 13:00:00');
INSERT INTO Review VALUES(14, 14, 17, 5, 'Logitech MX Keys is the best keyboard I have used. Typing experience is superb.', '2024-02-22 11:00:00');
INSERT INTO Review VALUES(15, 15, 20, 5, 'My Barbour jacket is fantastic quality. Keeps me warm and looks great. A true British classic!', '2024-02-25 14:00:00');
INSERT INTO Review VALUES(16, 16, 21, 4, 'Classic Levi''s 501 jeans. Perfect fit and very durable. True to size.', '2024-02-28 10:00:00');
INSERT INTO Review VALUES(17, 17, 26, 5, 'Nike Air Max 270 are so comfortable! I wear them every day. Highly recommend.', '2024-03-02 13:00:00');
INSERT INTO Review VALUES(18, 18, 27, 5, 'Adidas Ultraboost 23 are the best running shoes I have ever worn. Feel like running on clouds!', '2024-03-05 11:00:00');
INSERT INTO Review VALUES(19, 19, 23, 3, 'Zara coat looks great but the quality could be better for the price. Stitching came loose.', '2024-03-08 14:00:00');
INSERT INTO Review VALUES(20, 20, 37, 5, 'Dyson Hot+Cool is worth every penny! Works brilliantly in all seasons. Great investment.', '2024-03-10 10:00:00');
INSERT INTO Review VALUES(21, 21, 38, 4, 'LG air conditioner is very efficient and quiet. Happy with the purchase overall.', '2024-03-12 13:00:00');
INSERT INTO Review VALUES(22, 22, 39, 5, 'Bosch washing machine is incredibly reliable. Clothes come out perfectly clean every time.', '2024-03-15 11:00:00');
INSERT INTO Review VALUES(23, 23, 40, 4, 'Samsung EcoBubble is quiet and energy efficient. Very impressed with the wash quality.', '2024-03-18 14:00:00');
INSERT INTO Review VALUES(24, 24, 12, 4, 'JBL Charge 5 has impressive bass and is great for outdoor use. Battery lasts ages.', '2024-03-20 10:00:00');
INSERT INTO Review VALUES(25, 25, 25, 5, 'Reiss blazer is impeccably tailored. Perfect for the office and smart casual occasions.', '2024-03-22 13:00:00');
INSERT INTO Review VALUES(26, 26, 24, 5, 'Love this dress! Beautiful pattern and great quality fabric. Very flattering fit.', '2024-03-25 11:00:00');
INSERT INTO Review VALUES(27, 27, 28, 4, 'Classic New Balance 574. Timeless design and very comfortable. Great everyday trainers.', '2024-03-28 14:00:00');
INSERT INTO Review VALUES(28, 28, 29, 3, 'Puma RS-X look great but the sizing runs a bit small. Order a size up.', '2024-04-01 10:00:00');
INSERT INTO Review VALUES(29, 29, 30, 5, 'Classic British chocolate! Cadbury Dairy Milk never disappoints. My favourite treat.', '2024-04-03 13:00:00');
INSERT INTO Review VALUES(30, 30, 31, 4, 'Great value variety pack. Everyone''s favourite crisps. Perfect for parties!', '2024-04-05 11:00:00');
INSERT INTO Review VALUES(31, 31, 32, 5, 'Nothing beats a proper cup of Twinings English Breakfast tea. Brilliant quality.', '2024-04-08 14:00:00');
INSERT INTO Review VALUES(32, 32, 33, 4, 'Refreshing and healthy smoothie. Love the mixed berries flavour. Great for breakfast.', '2024-04-10 10:00:00');
INSERT INTO Review VALUES(33, 33, 34, 5, 'Delicious organic strawberries! Fresh and perfectly ripe. Will definitely reorder.', '2024-04-12 13:00:00');
INSERT INTO Review VALUES(34, 34, 35, 5, 'Outstanding Scottish smoked salmon. Restaurant quality at home. Absolutely delicious.', '2024-04-15 11:00:00');
INSERT INTO Review VALUES(35, 35, 36, 4, 'Free range eggs with beautiful golden yolks. Excellent quality and taste.', '2024-04-18 14:00:00');
INSERT INTO Review VALUES(36, 36, 22, 4, 'Ted Baker shirt is beautifully tailored. Excellent for both work and casual wear.', '2024-04-20 10:00:00');
INSERT INTO Review VALUES(37, 37, 18, 4, 'Apple Magic Keyboard is sleek and responsive. Love the Touch ID feature. Great build quality.', '2024-04-22 13:00:00');
INSERT INTO Review VALUES(38, 38, 19, 4, 'Razer DeathAdder V3 is very precise. Perfect for gaming sessions. Comfortable grip.', '2024-04-25 11:00:00');
INSERT INTO Review VALUES(39, 39, 8,  5, 'Microsoft Surface Pro 9 is perfect for productivity. Great build quality and display.', '2024-04-28 14:00:00');
INSERT INTO Review VALUES(40, 40, 7,  4, 'Samsung Galaxy Tab S9 Ultra is a fantastic Android tablet. Very happy with it.', '2024-05-01 10:00:00');
INSERT INTO Review VALUES(41, 41, 1,  5, 'Second iPhone and still the best phone I have used. Excellent camera and performance!', '2024-05-05 13:00:00');
INSERT INTO Review VALUES(42, 42, 9,  5, 'Sony WH-1000XM5 are phenomenal headphones. Great for long commutes and travel.', '2024-05-08 11:00:00');
INSERT INTO Review VALUES(43, 43, 10, 4, 'AirPods Pro 2 have great battery life and fit very securely. Very satisfied.', '2024-05-10 14:00:00');
INSERT INTO Review VALUES(44, 44, 26, 4, 'Nike Air Max are stylish and comfortable. True to size. Great for casual wear.', '2024-05-12 10:00:00');
INSERT INTO Review VALUES(45, 45, 27, 5, 'Adidas Ultraboost are amazing for long distance running. Best investment I made this year!', '2024-05-15 13:00:00');
INSERT INTO Review VALUES(46, 46, 2,  4, 'Samsung Galaxy S24 Ultra camera is mind-blowing. Great phone overall, very premium feel.', '2024-05-18 11:00:00');
INSERT INTO Review VALUES(47, 47, 3,  5, 'Google Pixel 8 Pro has the best computational photography on the market. Stunning photos.', '2024-05-20 14:00:00');
INSERT INTO Review VALUES(48, 48, 4,  4, 'OnePlus 12 is a great flagship killer. Fast and smooth performance at a great price.', '2024-05-22 10:00:00');
INSERT INTO Review VALUES(49, 49, 5,  2, 'Sony Xperia is overpriced for what you get. Disappointed with the battery life.', '2024-05-25 13:00:00');
INSERT INTO Review VALUES(50, 50, 6,  5, 'iPad Pro M2 has transformed how I work. The display is absolutely stunning. Love it!', '2024-05-28 11:00:00');
INSERT INTO Review VALUES(51, 1,  14, 5, 'My MacBook Air M2 is the best laptop I have ever owned. Battery lasts all day easily.', '2024-09-10 10:00:00');
INSERT INTO Review VALUES(52, 2,  13, 4, 'Dell XPS 15 is a great workstation. Build quality is top notch and display is gorgeous.', '2024-09-12 13:00:00');
INSERT INTO Review VALUES(53, 3,  20, 5, 'Barbour jacket is a true British classic. Will last for years. Absolutely love it.', '2024-09-15 11:00:00');
INSERT INTO Review VALUES(54, 4,  11, 5, 'Absolutely outstanding headphones. Worth every penny. Best purchase I have made all year!', '2024-09-18 14:00:00');
INSERT INTO Review VALUES(55, 5,  15, 4, 'ThinkPad X1 Carbon is the ultimate business laptop. Keyboard is outstanding.', '2024-09-20 10:00:00');
INSERT INTO Review VALUES(56, 6,  37, 5, 'Dyson Hot+Cool has changed how I manage room temperature. Works brilliantly all year round.', '2024-09-22 13:00:00');
INSERT INTO Review VALUES(57, 7,  39, 4, 'Bosch washing machine is quiet and efficient. Clothes come out fresh and clean every time.', '2024-09-25 11:00:00');
INSERT INTO Review VALUES(58, 8,  28, 3, 'New Balance 574 look great but took a while to break in. Comfortable once worn in.', '2024-09-28 14:00:00');
INSERT INTO Review VALUES(59, 9,  38, 4, 'LG air conditioner keeps the room perfectly cool. Energy efficient and very quiet operation.', '2024-10-01 10:00:00');
INSERT INTO Review VALUES(60, 10, 40, 5, 'Samsung EcoBubble is fantastic. Excellent wash results and whisper quiet. Highly recommend!', '2024-10-05 13:00:00');
