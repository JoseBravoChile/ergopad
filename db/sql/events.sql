drop table "events";
create table "events" (
    id SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "blockChain" TEXT DEFAULT 'ERGO',
    "total_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "buffer_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "owner" TEXT NOT NULL DEFAULT 'sigma@ergopad.io',
    "walletId" INTEGER,
    "isWhitelist" SMALLINT DEFAULT 0,
    "start_dtz" timestamptz NOT NULL DEFAULT now(),
    "end_dtz" timestamptz NOT NULL DEFAULT now()
);
INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz", "isWhitelist")
VALUES (-1, '__unknown', '__unknown', NULL, 0.0, 0.0, '__unknown', '1/1/1900', '1/1/1900', -1);

INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz", "isWhitelist")
VALUES (1, 'seedsale-ergopad-202112', 'ErgoPad SeedSale', 'ERGO', 100000.0, 20000.0, 'sigma@ergopad.io', '12/26/2021 17:00', '12/28/2021 17:00', 1);

INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz", "isWhitelist")
VALUES (2, 'strategic-ergopad-202201', 'ErgoPad Strategic', 'ERGO', 100000.0, 20000.0, 'sigma@ergopad.io', '12/28/2021 17:00', '12/30/2021 17:00', 1);

INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz", "isWhitelist")
VALUES (3, 'presale-ergopad-202201wl', 'ErgoPad Presale', 'ERGO', 600000.0, 600000.0, 'sigma@ergopad.io', '1/15/2022 17:00', '1/15/2022 17:00', 1);
