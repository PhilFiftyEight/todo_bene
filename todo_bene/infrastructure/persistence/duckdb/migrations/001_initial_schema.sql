-- Table Users
CREATE TABLE IF NOT EXISTS users (
    uuid UUID PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE
);

-- Table Todos
CREATE TABLE IF NOT EXISTS todos (
    uuid UUID PRIMARY KEY,
    title VARCHAR,
    description TEXT,
    category VARCHAR,
    state BOOLEAN,
    priority BOOLEAN,
    date_start DOUBLE,
    date_due DOUBLE,
    user_id UUID,
    parent_id UUID
);

-- Table Categories
CREATE TABLE IF NOT EXISTS categories (
    name TEXT,
    user_id UUID,
    PRIMARY KEY (name, user_id)
);
