CREATE TABLE schedule (
  id serial PRIMARY KEY,
  schedule jsonb NOT NULL,
  overlay bool NOT NULL
);
