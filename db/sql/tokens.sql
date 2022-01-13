DROP TABLE "tokens";
CREATE TABLE "tokens" (
    id SERIAL PRIMARY KEY,
    "address" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "location" TEXT NULL,
    "emissionAmount" INTEGER,
    "description" TEXT NULL,
    "type" TEXT NOT NULL,
    "decimals" SMALLINT DEFAULT 0
);
INSERT INTO "tokens" ("id", "address", "name", "location", "emissionAmount", "description", "type", "decimals")
VALUES (-1, '', '__unknown', '', 0, '__unknown', '', 0);
