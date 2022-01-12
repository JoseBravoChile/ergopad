CREATE TABLE "purchases" (
    id SERIAL PRIMARY KEY,
    "walletId" INTEGER NOT NULL,
    "toAddress" TEXT NOT NULL,
    "tokenId" INTEGER,
    "tokenAmount" INTEGER,
    "currency" TEXT NOT NULL,
    "currencyAmount" NUMERIC(32, 8),
    "feeAmount" NUMERIC(16,8),
    "ipAddress" TEXT NULL
)
INSERT INTO "purchases" ("walletId", "toAddress", "tokenId", "tokenAmount", "currency", "currencyAmount", "feeAmount")
VALUES (-1, '', -1, 0, '__unknown', 0, 0)
