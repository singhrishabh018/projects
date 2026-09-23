CREATE TABLE brand (
    brand_id          VARCHAR(16) PRIMARY KEY,
    name              VARCHAR(200) NOT NULL,
    status            VARCHAR(16)  NOT NULL,   -- active | paused | retired
    is_searchable     BOOLEAN      NOT NULL,   -- shown in site-search suggestions
    fulfillment_type  VARCHAR(16)  NOT NULL,   -- ship | store_only | dropship
    web_eligible      BOOLEAN      NOT NULL    -- may be sold on the website
);
