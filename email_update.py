import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import logging
import psycopg2
import psycopg2.extras
import os
from logging.handlers import RotatingFileHandler
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

loggingHandler = RotatingFileHandler('email-update.log',
									  maxBytes=102400, backupCount=5)
loggingHandler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

loggingHandler.setFormatter(
	logging.Formatter('%(asctime)s - '
					  '%(levelname)s - %(message)s'))
logger.addHandler(loggingHandler)


#logging.basicConfig(filename='example.log',level=logging.ERROR)
logger.info('Starting update')

# Convert jdbc.properties to a dictionary
def parse_config(conf_file):
	d = defaultdict(list)
	with open(conf_file) as props:
		for line in props:
			if line.startswith('jdbc'):
				k, v = line.split('=')
				d[k] = v.rstrip('\n')
	return d


def build_conn_args(config):
	return {
		'database': config.get('jdbc.database'),
		'host': config.get('jdbc.host'),
		'port': config.get('jdbc.port'),
		'user': config.get('jdbc.username'),
		'password': config.get('jdbc.password')
	}

def slurp(path):
	with open(path, 'r') as f:
		return f.read()

@click.group()
@click.option('--url', required=True, prompt='GeoNetwork URL as far as the node name', help='GeoNetwork URL as far as the node name')
@click.option('--username', required=True, prompt='GeoNetwork username', help='GeoNetwork username')
@click.option('--password', required=True, prompt='GeoNetwork password', help='GeoNetwork password', hide_input=True, confirmation_prompt=True)
@click.pass_context
def cli(ctx,url,username,password):
	"""Module for updating email addresses in geonetwork user details and metadata records see readme for further details"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	geonetwork_session = requests.Session()
	geonetwork_session.auth = HTTPBasicAuth(username, password)
	geonetwork_session.headers.update({"Accept" : "application/json"})

	# Make a call to an endpoint to get cookies and an xsrf token

	geonetwork_user_info_endpoint = url + '/api/me'
	get_user_info_response = geonetwork_session.get(geonetwork_user_info_endpoint, verify=False)

	if get_user_info_response != 200:
		logger.error('Authentication to the portal failed.')
		raise Exception ('Failed to authenticate. Try again!')

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
@click.option('--csvfile', required=True, prompt='CSV file to use for update', help='CSV file to use for update')
@click.pass_context
def updateuser(ctx,csvfile):
	"""Update email address in user details, passed from a CSV file"""

	logger.info('Started updating user details')

	conn = psycopg2.connect(**ctx.obj['db_conn_args'])
	base_dir = os.path.dirname(os.path.realpath(__file__))

	# disabling https warnings for testing purposes
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	# get user id for given email
	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		with conn:
			with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:

				user_sql = slurp(os.path.join(base_dir, os.path.join('sql','get_userid_for_email.sql')))
				logger.info(f'Getting user ID for email: {row["old_email"]}')

				cur.execute(user_sql, {'email': row['old_email']})
				logger.debug(f'Executed get_userid_for_email.sql:{cur.query}{cur.statusmessage}')

				user_id = cur.fetchall()
				if user_id:
					logger.info(f'Email {row["old_email"]} has ID {user_id}')

				else:
					logger.error(f'Email {row["old_email"]} is not a login email')

				# update email address for given user_id
				for u in user_id:
					updateuser_sql = slurp(os.path.join(base_dir, os.path.join('sql', 'update_email_for_userid.sql')))
					logger.info(f'Updating email for user ID: {u}')

					cur.execute(updateuser_sql, {'user_id': u, 'email': row['new_email']})
	logger.info('Finished updating user emails')

@cli.command()
@click.option('--csvfile', required=True, prompt='CSV file to use for update', help='CSV file to use for update')
@click.pass_context
def updatemetadata(ctx,csvfile):
	"""Update email addresses in metadata, passed from a CSV file"""

	logger.info('Started updating emails in metadata')

	# disabling https warnings for testing purposes
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	session = ctx.obj['session']
	url = ctx.obj['url']
	session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
	headers = session.headers
	cookies = session.cookies

	geonetwork_search_endpoint = url + '/api/search/records/_search'

	uuid_list = []

	# read oldemails from csv and pop selected records into a bucket
	df = pd.read_csv(csvfile)

	for index, row in df.iterrows():

		try:
			headers.update({'Content-Type': 'application/json'})

			find_records_response = session.post(
				geonetwork_search_endpoint,
				headers=headers,
				json=getAPIQuery(row['old_email']),
				verify=False
			)

			if find_records_response.status_code not in (200, 201):
				logger.error(f'Unexpected status code {find_records_response.status_code} - Email ({row["old_email"]}) couldn\'t be found')
				return None

			find_records_json_response = find_records_response.json()

			for record in find_records_json_response['hits']['hits']:
				for point_of_contact in record['_source'].get('contact', []):
					if row['old_email'] == point_of_contact['email']:
						if record['_source']['uuid'] not in uuid_list:
							uuid_list.append(record['_source']['uuid'])

				for contact_for_resource in record['_source'].get('contactForResource', []):
					if row['old_email'] == contact_for_resource['email']:
						if record['_source']['uuid'] not in uuid_list:
							uuid_list.append(record['_source']['uuid'])

		except Exception as e:
			logger.error(f'Exception raised for email {row["old_email"]}: {e}')

		if len(uuid_list) == 0:
			print(f'\n No records found containing email "{row["old_email"]}" - Nothing to update.')
			print(30 * '-')
			logger.warning(f'No records found containing email {row["old_email"]}')
			continue

		else:
			print(f'\n Records updated for email "{row["old_email"]}": {uuid_list}')

		create_selection_params={
			'uuid': uuid_list
		}

		# add search results to a bucket called metadata
		geonetwork_selections_endpoint = url + '/api/selections/metadata'
		build_selection_response = session.put(geonetwork_selections_endpoint,
			headers=headers,
			verify=False,
			params=create_selection_params
		)

		if build_selection_response.status_code not in (200, 201):
				logger.error(f'Unexpected status code {build_selection_response.status_code}: Could not build the selection - Aborting.')
				raise Exception(f'Unexpected API response:\n{json.dumps(build_selection_response.json(), indent=2)}')

		# check records selection
		geonetwork_selections_endpoint = url + '/api/selections/metadata'
		get_current_selection_response = session.get(geonetwork_selections_endpoint,
			headers=headers,
			verify=False
		)

		logger.info(f'Selected UUIDs: {get_current_selection_response.json()}')

		# construct params for sending to email-replacer process
		params = {
			'oldEmail': row['old_email'],
			'newEmail': row['new_email'],
			'bucket': 'metadata'
		}

		geonetwork_processing_endpoint = url + '/api/processes/email-replacer'

		geonetwork_processing_response = session.post(geonetwork_processing_endpoint,
			headers=headers,
			params=params,
			verify=False
		)

		geonetwork_processing_json_response = geonetwork_processing_response.json()

		logger.info(f'Updating metadata for email: {row["old_email"]}')

		if geonetwork_processing_response.status_code not in (200, 201):
			logger.error(f'Unexpected status code {geonetwork_processing_response.status_code}: Could not update metadata.')
			raise Exception(f'Unexpected API response:\n{json.dumps(geonetwork_processing_json_response, indent=2)}')

		print('\n' + json.dumps(geonetwork_processing_json_response, indent=2))
		print(30 * '-')
		logger.info('Finished updating metadata records')


def getAPIQuery(email):
	return {
    "query": {
        "query_string": {
            "query": email
        }
    },
    "_source": [
        "resourceTitle*",
        "metadataIdentifier",
        "uuid",
        "contact*",
        "contactForResource*"
    ]
}


if __name__ == '__main__':
	cli()
