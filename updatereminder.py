#!/usr/bin/env python

from jinja2 import Template
import json
import argparse
import logging
import os
import psycopg2
import psycopg2.extras
import smtplib
import sys
from collections import defaultdict


# Convert jdbc.properties to a dictionary
def parse_config(conf_file):
    d = defaultdict(list)
    with open(conf_file) as props:
        for line in props:
            k, v = line.split("=")
            d[k] = v.rstrip('\n')
    return d


def build_conn_args(config):
    return {
        'database': config.get("jdbc.database"),
        'host': config.get("jdbc.host"),
        'port': config.get("jdbc.port"),
        'user': config.get("jdbc.username"),
        'password': config.get("jdbc.password")
    }


def slurp(path):
    with open(path, 'r') as f:
        return f.read()


def get_sys_settings(conn, setting_sql_path):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        sql = slurp(setting_sql_path)
        cur.execute(sql)
        settings = {}
        for row in cur.fetchall():
            settings[row["name"]] = row["value"]
        return settings


def send_email(email_body, email_to, sys_settings):
    email_from = sys_settings.get('system/feedback/email')
    # temp address for testing emails
    # comment this out when not testing
    email_to = ""



    email_body = "\r\n".join(["From: %s" % email_from, "To: %s" % email_to, email_body])

    server = smtplib.SMTP('%s:%s' % (sys_settings.get('system/feedback/mailServer/host'),sys_settings.get('system/feedback/mailServer/port')))
    server.starttls()
    server.login(sys_settings.get('system/feedback/mailServer/username'), sys_settings.get('system/feedback/mailServer/password'))
    server.sendmail(email_from, email_to, email_body)
    server.quit()


def get_users_with_overdue_metadata(conn, base_dir):

    log = logging.getLogger('updatereminder')

    users = []

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            due_sql = slurp(os.path.join(base_dir, 'recordsoverdue.sql'))
            log.info('Checking for users with overdue metadata.')
            cur.execute(due_sql)
            log.debug('Executed records_overdue.sql:\n%s\n%s' % (cur.query, cur.statusmessage))
            log.info('Found %s users with overdue metadata.' % cur.rowcount)
            users = cur.fetchall()
    return users


def get_users_with_due_metadata(conn, base_dir):

    log = logging.getLogger('updatereminder')

    users = []

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            due_sql = slurp(os.path.join(base_dir, 'recordsdue.sql'))
            log.info('Checking for users with due metadata.')
            cur.execute(due_sql)
            log.debug('Executed records_due.sql:\n%s\n%s' % (cur.query, cur.statusmessage))
            log.info('Found %s users with due metadata.' % cur.rowcount)
            users = cur.fetchall()

    return users


def overdue_user(conn, base_dir, tmpl, sys_settings, user):
    log = logging.getLogger('updatereminder')
    overdue_tmpl = Template(slurp(tmpl))

    try:
        log.debug('Attempting to send overdue email to user: %s (%s)' % (user.get('contact'), user.get('email_contact')))
        email_body = overdue_tmpl.render(user=user, settings=sys_settings)
        send_email(email_body, user.get('email_contact'), sys_settings)
    except:
        log.exception('Failed to send overdue email.')


def due_user(conn, base_dir, tmpl, sys_settings, user):

    log = logging.getLogger('updatereminder')

    due_tmpl = Template(slurp(tmpl))

    try:
        log.debug('Attempting to send due email to user: %s (%s)' % (user.get('username'), user.get('email_contact')))
        email_body = due_tmpl.render(user=user, settings=sys_settings)
        send_email(email_body, user.get('email_contact'), sys_settings)
    except:
        log.exception('Failed to send due email.')


def main(config, base_dir, args):

    conn = psycopg2.connect(**db_conn_args)

    with conn:
        sys_settings = get_sys_settings(conn, os.path.join(base_dir, 'settings.sql'))
        if args.get('settings'):
            print (json.dumps(sys_settings, indent=4))
            return 0

    # Remind users with overdue metadata
    users = get_users_with_overdue_metadata(conn, base_dir)
    for user in users:
        overdue_user(conn, base_dir, args.get('reminder_template'), sys_settings, user)

    # Remind users with due metadata
    users = get_users_with_due_metadata(conn, base_dir)
    for user in users:
        due_user(conn, base_dir, args.get('template'), sys_settings, user)

    return 0


if __name__ == '__main__':

    # Logging
    log_level = logging.INFO
    log = logging.getLogger('updatereminder')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.setLevel(log_level)
    log.addHandler(handler)

    base_dir = os.path.dirname(os.path.realpath(__file__))

    due_template_path = os.path.join(base_dir, 'records_due.tmpl')
    overdue_template_path = os.path.join(base_dir, 'records_overdue.tmpl')

    parser = argparse.ArgumentParser(__file__, description="Send email reminders to people about metadata records due or overdue an update")
    parser.add_argument("config", help="""path to GeoNetwork config from which database connection details can be read;
                                          other settings are read from the GeoNetwork settings table within the database
                                          including SMTP details used to send email. All GeoNetwork setting are made
                                          available to the email template under the key 'settings'.
                                          To view available settings run with the --settings flag""")
    parser.add_argument("-t", "--template", default=due_template_path, help="path to Jinja2 email due template, default: %s" % due_template_path)
    parser.add_argument("-u", "--reminder_template", default=overdue_template_path, help="path to Jinja2 overdue email template, default: %s" % overdue_template_path)
    parser.add_argument("-s", "--settings", action='store_true', help="print GeoNetwork settings as JSON to stdout and exit")
    parser.add_argument("-l", "--log", default=logging.getLevelName(log_level), help="standard Python logging level, default: %s" % logging.getLevelName(log_level))

    args = vars(parser.parse_args())

    log_level = getattr(logging, args.get('log').upper(), logging.INFO)
    log.setLevel(log_level)

    # tweaked for geonetwork 3 jdbc.properties file (was config-overrides.xml)

    config = parse_config(args.get('config'))
    db_conn_args = build_conn_args(config)
    result = main(db_conn_args, base_dir, args)
    exit(result)
