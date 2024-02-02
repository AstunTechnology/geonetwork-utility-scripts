from mock import patch
from nose.tools import eq_
from resetpasswd import slurp, main
import psycopg2
import psycopg2.extras
import testing.postgresql

db = None
conn = None
conn_args = None


def setUp(self):
    global db, conn, conn_args
    db = testing.postgresql.Postgresql()
    conn_args = db.dsn()
    conn = psycopg2.connect(**conn_args)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/setup.sql'))
        cur.execute(slurp('./test/fixtures/audit.sql'))
        cur.execute(slurp('./setup.sql'))


def tearDown(self):
    conn.close()
    db.stop()


def test_all_users_reset_on_first_run():

    # If ran on a fresh database with existing users and no audit entries all
    # users should be forced to reset

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_initial.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {"days": 42, "reminder": 7, "template": 'email_reset.tmpl', "reminder_template": 'email_reminder.tmpl', "settings": False})
        eq_(smtp_instance.sendmail.call_count, 3)


def test_no_reset_required_if_ran_on_same_day():

    # If ran again immediately after all users have been reset no users should
    # need resetting

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_all_reset.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 0)


def test_user_changed_password_within_x_days_no_reset_required():

    # The user changed their password within x days so no reset is required

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_changed_password_40_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 0)


def test_user_not_changed_password_within_x_days_reset_required():

    # If a user was reset by the script and have not updated their password
    # within by the number of days a user is required to reset they will be
    # forced to reset again and sent another email

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_reset_43_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 1)

    # Check that there are now two rows in the audit.logged_actions table
    # following the subsequent reset, previously there was a bug which resulted
    # in users being sent an email every day once 2 x the reset interval had
    # elapsed without them changing their password. Each time a user is reset a
    # row should now be inserted into logged_actions
    with conn.cursor() as cur:
        cur.execute("""SELECT * FROM audit.logged_actions;""")
        rows = cur.fetchall()
        eq_(len(rows), 2)


def test_send_reminder_to_active_user():

    # A reminder email should be sent to all users who are due to be reset. The
    # reminder is sent a given number of days before they are due to be reset.
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_changed_password_35_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 1)
        assert 'reminder' in smtp_instance.sendmail.call_args[0][2]


def test_only_consider_latest_password_change_event_when_determining_if_reminder_due():

    # An issue was identified by @archaeogeek where a reminder was sent for a
    # previous password change event even though her password had been changed
    # via the admin pages more recently and hence no reminder was required
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_changed_password_35_and_5_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 0)


def test_dont_send_reminder_to_reset_user():

    # Only users who are not already reset should be sent a reminder
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_reset_35_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 0)


def test_dont_send_reminder_when_not_due():

    # Don't send a reminder if it's not the appropriate time
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_changed_password_40_days_ago.sql'))

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 0)


def test_user_not_reset_if_sending_email_fails():

    # If a reset email can not be sent to a user they are not reset (otherwise
    # they will be reset without having accessing the change password function)

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_with_invalid_email.sql'))
        cur.execute("""SELECT * from users;""")
        rows = cur.fetchall()
        original_user = rows[0]

    with patch("smtplib.SMTP") as mock_smtp:
        smtp_instance = mock_smtp.return_value
        smtp_instance.sendmail.side_effect = sendmail_raise_on_invalid_email
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 1)

    with conn.cursor() as cur:
        # No rows in the audit.logged_actions table
        cur.execute("""SELECT count(*) from audit.logged_actions;""")
        rows = cur.fetchall()
        eq_(rows[0][0], 0)
        cur.execute("""SELECT * from users;""")
        rows = cur.fetchall()
        current_user = rows[0]

    eq_(cmp(current_user, original_user), 0)


def test_continue_to_reset_other_users_if_a_users_email_is_invalid():

    # If a reset email can not be sent to a user but there are other users
    # still to reset the process continues to attempt to reset the remaining
    # users

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_one_user_with_invalid_email.sql'))

    with patch("smtplib.SMTP") as mock_smtp:

        smtp_instance = mock_smtp.return_value
        smtp_instance.sendmail.side_effect = sendmail_raise_on_invalid_email
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})
        eq_(smtp_instance.sendmail.call_count, 3)

    with conn.cursor() as cur:
        # No rows in the audit.logged_actions table
        cur.execute("""SELECT count(*) from audit.logged_actions;""")
        rows = cur.fetchall()
        eq_(rows[0][0], 2)


def test_change_password_restores_profile_after_successive_resets():

    # Following a users password being reset more than once (due to them being
    # reset then not updating their password before the next reset interval
    # elapses) their profile is still correctly restored

    # original_profiles = set(['Administrator'])
    original_profiles = set([0])
    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_user_reset_4_and_46_days_ago.sql'))

    with conn.cursor() as cur:
        reset_profiles = distinct_profiles(conn)

    # assert reset_profiles == set(['RegisteredUser'])
    assert reset_profiles == set([4])

    # Simulate a user changing their password to cause the profile reset
    # database trigger to fire (the password used here is simply 80 random
    # characters)
    with conn.cursor() as cur:
        cur.execute("""UPDATE users SET password = 'f5a1609a6f7dbff1604d299a36cdd41c5ca7cc9ddcf983c4c052f9ac6afef4e5500884afc24edf3b'""")
        updated_profiles = distinct_profiles(conn)

    assert updated_profiles != reset_profiles
    assert updated_profiles == original_profiles


def test_change_password_restores_profile():

    # When reset users are give RegisteredUser profile, when their password is
    # later updated their profile is restored

    with conn.cursor() as cur:
        cur.execute(slurp('./test/fixtures/state_initial.sql'))
        original_profiles = distinct_profiles(conn)

    # Do an initial run from fresh which triggers a reset for all users
    with patch("smtplib.SMTP"):
        main(conn_args, './', {'days': 42, 'reminder': 7, 'template': 'email_reset.tmpl', 'reminder_template': 'email_reminder.tmpl', 'settings': False})

    with conn.cursor() as cur:
        reset_profiles = distinct_profiles(conn)

    assert reset_profiles != original_profiles
    # assert reset_profiles == set(['RegisteredUser'])
    assert reset_profiles == set([4])

    with conn.cursor() as cur:
        cur.execute("""UPDATE users SET password = rpad('', 80, 'z')""")
        updated_profiles = distinct_profiles(conn)

    assert updated_profiles != reset_profiles
    assert updated_profiles == original_profiles


# Helper functions

def distinct_profiles(conn):
    with conn.cursor() as cur:
        cur.execute("""SELECT DISTINCT profile FROM users;""")
        rows = cur.fetchall()
        profiles = set([row[0] for row in rows])
        return profiles


def sendmail_raise_on_invalid_email(email_from, email_to, email_body):
    if email_to[0] == 'invalid-email':
        raise Exception
    else:
        return True
