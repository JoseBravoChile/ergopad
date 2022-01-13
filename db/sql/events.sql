create table "events" (
    id SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "blockChain" TEXT DEFAULT 'ERGO',
    "total_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "buffer_sigusd" NUMERIC(16,6) DEFAULT 0.0,
    "owner" TEXT NOT NULL DEFAULT 'sigma@ergopad.io',
    "start_dtz" timestamptz NOT NULL DEFAULT now(),
    "end_dtz" timestamptz NOT NULL DEFAULT now()
);
INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz")
VALUES (-1, '__unknown', '__unknown', NULL, 0.0, 0.0, '__unknown', '1/1/1900', '1/1/1900');

INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz")
VALUES (1, 'seedsale_202112_whitelist', 'ErgoPad SeedSale, Dec 2021', 'ERGO', 100000.0, 20000.0, 'sigma@ergopad.io', '12/26/2021 17:00', '12/28/2021 17:00');

INSERT INTO "events" ("id", "name", "description", "blockChain", "total_sigusd", "buffer_sigusd", "owner", "start_dtz", "end_dtz")
VALUES (2, 'seedsale_202112_waitlist', 'ErgoPad SeedSale, Dec 2021', 'ERGO', 100000.0, 20000.0, 'sigma@ergopad.io', '12/28/2021 17:00', '12/30/2021 17:00');

