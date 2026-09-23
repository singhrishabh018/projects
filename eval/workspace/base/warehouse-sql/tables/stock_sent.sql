CREATE TABLE stock_sent (
    sku        VARCHAR(40) NOT NULL,
    qty        INTEGER     NOT NULL,
    sent_at    TIMESTAMP   NOT NULL,
    raw        JSONB       NOT NULL
);
