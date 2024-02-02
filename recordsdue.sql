select *, (last_update_code + at_update_interval(update_frequency)
) as next_update_due, (last_update_code + at_update_interval(update_frequency)- at_update_reminder(update_frequency)) as reminder_due
from records_update_cycle
where update_frequency not in ('', 'asNeeded') and (last_update_code + at_update_interval(update_frequency)- at_update_reminder(update_frequency)) <= 'now'::text::date
and (last_update_code + at_update_interval(update_frequency)) >= 'now'::text::date
