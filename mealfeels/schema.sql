CREATE TABLE IF NOT EXISTS phones (
  id SERIAL PRIMARY KEY,
  phone VARCHAR UNIQUE,
  token VARCHAR NOT NULL,
  verification_code VARCHAR,
  verified BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS bms (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  bm_description VARCHAR NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS meals (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  meal VARCHAR NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS feels (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  full_description VARCHAR NOT NULL,
  symptoms JSONB,
  created_at TIMESTAMP WITH TIME ZONE default now()
);

CREATE TABLE IF NOT EXISTS sleeps (
  id SERIAL PRIMARY KEY,
  phone_id INT REFERENCES phones(id),
  description VARCHAR NOT NULL,
  hours INT,
  created_at TIMESTAMP WITH TIME ZONE default now()
);
