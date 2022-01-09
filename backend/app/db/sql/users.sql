-- TABLE SCHEMAS FOR USERS

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false
);

-- TODO: CREATE INDEX ON EMAIL
