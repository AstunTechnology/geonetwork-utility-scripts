-- Update emails for given user_ids

UPDATE email SET email = %(email)s WHERE user_id = ANY(%(user_id)s)