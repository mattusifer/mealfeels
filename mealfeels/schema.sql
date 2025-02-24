CREATE TABLE IF NOT EXISTS phones (
  id SERIAL PRIMARY KEY,
  phone VARCHAR UNIQUE,
  token VARCHAR NOT NULL,
  verification_code VARCHAR,
  verified BOOLEAN NOT NULL DEFAULT false,
  public_key VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS bms (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  bm_description BYTEA,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS meals (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  meal BYTEA NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS feels (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  full_description BYTEA NOT NULL,
  symptoms BYTEA,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS sleeps (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  description BYTEA NOT NULL,
  hours INT,
  created_at TIMESTAMP WITH TIME ZONE default now()
);
