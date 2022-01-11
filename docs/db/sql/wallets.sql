-- wallets
CREATE TABLE "wallets" (
    id SERIAL PRIMARY KEY,
    "address" TEXT NOT NULL,
	"email" TEXT NULL,
    "blockChainId" SMALLINT DEFAULT -1,
    "network" TEXT NULL DEFAULT 'MAINNET',
    "walletPass" TEXT NULL,
    "mneumonic" TEXT NULL,
    "socialHandle" TEXT NULL,
    "socialPlatform" TEXT NULL,
    "chatHandle" TEXT NULL,
    "chatPlatform" TEXT NULL,
    "created_dtz" timestamptz NOT NULL DEFAULT now(),
    "lastSeen_dtz" timestamptz NOT NULL DEFAULT now()
)
INSERT INTO "wallets" (id, "address", "blockChainId", "network", "walletPass", "mneumonic", "created_dtz", "lastSeen_dtz", "socialHandle", "socialPlatform", "chatHandle", "chatPlatform") 
VALUES (-1, '__unknown', -1, '__unknown', '__unknown', '__unknown', '1/1/1900', '1/1/1900', '__unknown', '__unknown', '__unknown', '__unknown')

-- blockchains
CREATE TABLE "blockChains" (
    id SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "coin" TEXT NOT NULL,
    "notes" TEXT NULL
)
INSERT INTO "blockChains" (id, "name", "coin", "notes") 
VALUES (-1, '__unknown', '__unknown', '__unknown')
