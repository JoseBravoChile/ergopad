DROP TABLE "whitelist";
CREATE TABLE "whitelist" (
    id SERIAL PRIMARY KEY,
    "walletId" INTEGER NOT NULL,
    "eventId" INTEGER DEFAULT -1,
    "created_dtz" timestamptz NOT NULL DEFAULT now(), 
    "allowance_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "remaining_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "isAvailable" SMALLINT DEFAULT 0,
    "lastAssemblerId" TEXT,
    "lastAssemblerStatus" TEXT
);
