CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    "shortDescription" TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    archived BOOLEAN DEFAULT false
);
