CREATE TABLE homes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamp default now(),
    url TEXT NOT NULL,
    sold_price TEXT,
    raw_sold_price INTEGER NOT NULL,
    address_city TEXT NOT NULL,
    address_street TEXT NOT NULL,
    address_state TEXT NOT NULL,
    address_zipcode TEXT NOT NULL,
    date_sold BIGINT NOT NULL,
    bedrooms INTEGER,
    bathrooms FLOAT,
    sqft FLOAT,
    days_on_market INTEGER,
    type TEXT,
    zestimate INTEGER,
    lot_size FLOAT,
    lot_size_unit TEXT,
    tax_assessment NUMERIC,
    UNIQUE (address_city, address_street, address_state, date_sold)
);

CREATE INDEX idx_homes_address ON homes(address_city, address_street, address_zipcode);
CREATE INDEX idx_homes_date_sold ON homes(date_sold);
