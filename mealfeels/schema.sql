CREATE TABLE IF NOT EXISTS bms (
  id SERIAL PRIMARY KEY,
  phone VARCHAR,
  bm_description VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS meals (
  id SERIAL PRIMARY KEY,
  meal VARCHAR,
  description VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS feels (
  id SERIAL PRIMARY KEY,
  symptom VARCHAR,
  magnitude INT,
  description VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS phones (
  id SERIAL PRIMARY KEY,
  phone VARCHAR UNIQUE,
  token VARCHAR NOT NULL,
  verification_code VARCHAR,
  verified BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE default now()
);
