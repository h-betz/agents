CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    zpid BIGINT NOT NULL,
    price INTEGER,
    time BIGINT,
    date TEXT,
    price_per_sq_ft NUMERIC,
    price_change_rate NUMERIC,
    event TEXT,
    UNIQUE (zpid, time, event)
);

CREATE INDEX idx_price_history_zpid ON price_history(zpid);
CREATE INDEX idx_price_history_time ON price_history(time);
CREATE INDEX idx_price_history_event ON price_history(event);
