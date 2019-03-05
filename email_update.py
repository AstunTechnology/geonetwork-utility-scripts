import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import xml.etree.ElementTree
import logging
import psycopg2
import psycopg2.extras
import os
from logging.handlers import RotatingFileHandler
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

loggingHandler = RotatingFileHandler("email-update.log",
									  maxBytes=102400, backupCount=5)
loggingHandler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

loggingHandler.setFormatter(
	logging.Formatter("%(asctime)s - "
					  "%(levelname)s - %(message)s"))
logger.addHandler(loggingHandler)


#logging.basicConfig(filename='example.log',level=logging.ERROR)
logger.info('Starting update')

# Convert jdbc.properties to a dictionary
def parse_config(conf_file):
	d = defaultdict(list)
	with open(conf_file) as props:
		for line in props:
			if line.startswith('jdbc'):
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

@click.group()
@click.option('--url', required=True, help='Geonetwork URL as far as the node name')
@click.option('--username', required=True, help='Geonetwork username')
@click.option('--password', required=True, help='Geonetwork password')
@click.pass_context
def cli(ctx,url,username,password):
	"""Module for updating email addresses in geonetwork user details and metadata records see readme for further details"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	geonetwork_session = requests.Session()
	geonetwork_session.auth = HTTPBasicAuth(username, password)
	geonetwork_session.headers.update({"Accept" : "application/json"})

	# Make a call to an endpoint to get cookies and an xsrf token

	geonetwork_url = url + '/eng/info?type=me'
	r_post = geonetwork_session.post(geonetwork_url,
		verify=False
		)

	token = geonetwork_session.cookies.get('XSRF-TOKEN')
	geonetwork_session.headers.update({"X-XSRF-TOKEN" : geonetwork_session.cookies.get('XSRF-TOKEN')})

	config = parse_config('jdbc.properties')
	db_conn_args = build_conn_args(config)

	# add session, user and database credentials as context objects so they can be used elsewhere
	ctx.obj = {
		'session': geonetwork_session,
		'username': username,
		'password': password,
		'url': url,
		'db_conn_args': db_conn_args
	}

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def updateuser(ctx,csvfile):
	"""Update email address in user details, passed from a CSV file"""

	logger.info("update user details started")

	conn = psycopg2.connect(**ctx.obj['db_conn_args'])
	base_dir = os.path.dirname(os.path.realpath(__file__))

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	# get user id for given email
	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		with conn:
			with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
				user_sql = slurp(os.path.join(base_dir, os.path.join('sql','get_userid_for_email.sql')))
				logger.info('Getting user_ids for email: ' + row['OLDEMAIL'])
				cur.execute(user_sql, {'email': row['OLDEMAIL']})
				logger.debug('Executed get_userid_for_email.sql:\n%s\n%s' % (cur.query, cur.statusmessage))
				user_id = cur.fetchall()
				if user_id:
					logger.info('email: %s has id %s' % (row['OLDEMAIL'], user_id))
				else:
					logger.info('email: %s is not a login email' % row['OLDEMAIL'])

				# update email address for given user_id
				for u in user_id:
					updateuser_sql = slurp(os.path.join(base_dir, os.path.join('sql', 'update_email_for_userid.sql')))
					logger.info('Updating email for user_id: %s' % (u))
					cur.execute(updateuser_sql, {'user_id': u, 'email': row['NEWEMAIL']})
	logger.info('Finished updating user emails')

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def updatemetadata(ctx,csvfile):
	"""Update email addresses in metadata, passed from a CSV file"""

	logger.info("started updating emails in metadata")

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	session = ctx.obj['session']
	url = ctx.obj['url']
	session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
	headers = session.headers
	cookies = session.cookies

	uuidlist = []

	# read oldemails from csv and pop selected records into a bucket
	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		geonetworkSearchURL = url + '/eng/q?_isTemplate=y+or+n&any=' + row['OLDEMAIL']
		click.echo(geonetworkSearchURL)
		searchURL = session.put(geonetworkSearchURL,
			headers=headers,
			verify=False
			)

		# add search results to a bucket called metadata
		geonetworkSelectURL = url + '/api/0.1/selections/metadata'
		selectURL = session.put(geonetworkSelectURL,
			headers=headers,
			verify=False
			)

		# construct params for sending to email-replacer process
		params = (
				('oldEmail', row['OLDEMAIL']),
				('newEmail', row['NEWEMAIL']),
				('bucket', 'metadata')
			)

		geonetworkEmailUpdate = url + '/api/0.1/processes/email-replacer'
		updateURL = session.post(geonetworkEmailUpdate,
				headers=headers,
				params=params,
				verify=False
			)
		logger.info('Updating metadata for email: %s' % (row['OLDEMAIL']))

	logger.info('Finished updating user emails')





if __name__ == '__main__':
	cli()
