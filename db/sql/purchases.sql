DROP TABLE "purchases";
CREATE TABLE "purchases" (
    id SERIAL PRIMARY KEY,
    "walletAddress" TEXT NOT NULL,
    "eventName" TEXT NOT NULL,
    "toAddress" TEXT NOT NULL,
    "tokenId" TEXT,
    "tokenAmount" INTEGER,
    "currency" TEXT NOT NULL,
    "currencyAmount" NUMERIC(32, 8),
    "feeAmount" NUMERIC(16,8),
    "assemblerId" TEXT,
    "ipAddress" TEXT NULL
);
INSERT INTO "purchases" ("walletAddress", "eventName", "toAddress", "tokenId", "tokenAmount", "currency", "currencyAmount", "feeAmount")
VALUES ('__unknown', '__unknown', '', -1, 0, '__unknown', 0, 0);
