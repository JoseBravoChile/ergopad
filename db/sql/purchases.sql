DROP TABLE "purchases";
CREATE TABLE "purchases" (
    id SERIAL PRIMARY KEY,
    "walletId" INTEGER NOT NULL,
    "eventId" INTEGER NOT NULL,
    "toAddress" TEXT NOT NULL,
    "tokenId" INTEGER,
    "tokenAmount" INTEGER,
    "currency" TEXT NOT NULL, -- ergo, sigusd...
    "currencyAmount" NUMERIC(32, 8), -- in currency
    "feeAmount" NUMERIC(16,8), -- in currency
    "ipAddress" TEXT NULL
);
INSERT INTO "purchases" ("walletId", "eventId", "toAddress", "tokenId", "tokenAmount", "currency", "currencyAmount", "feeAmount")
VALUES (-1, -1, '', -1, 0, '__unknown', 0, 0);
