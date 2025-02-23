INSERT INTO phones (phone, token, verification_code, verified)
VALUES ('8001002000', 'token', '123456', true)
ON CONFLICT (phone) DO NOTHING;

TRUNCATE TABLE meals CASCADE;
INSERT INTO meals (phone_id, meal, created_at)
VALUES
(1, CAST('burrito' AS bytea), '2025-02-19T01:00:00'),
(1, CAST('apple' AS bytea), '2025-02-19T03:00:00'),
(1, CAST('chicken and waffles' AS bytea), '2025-02-19T05:00:00');

TRUNCATE TABLE feels CASCADE;
INSERT INTO feels (phone_id, full_description, symptoms, created_at)
VALUES
(1, CAST('' AS bytea), CAST('{"bloated": "1"}' AS bytea) ,'2025-02-19T00:00:00'),
(1, CAST('' AS bytea), CAST('{"bloated": "4"}' AS bytea) ,'2025-02-19T02:00:00'),
(1, CAST('' AS bytea), CAST('{"bloated": "2"}' AS bytea) ,'2025-02-19T04:00:00'),
(1, CAST('' AS bytea), CAST('{"bloated": "8"}' AS bytea) ,'2025-02-19T06:00:00');
