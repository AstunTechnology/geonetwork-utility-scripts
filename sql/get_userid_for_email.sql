-- Query the email table, returning the user_id for a given email

SELECT user_id FROM email WHERE email ILIKE %(email)s;