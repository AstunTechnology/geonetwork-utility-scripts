import requests
import click
import csv
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pandas as pd

@click.group()
@click.option('--url', prompt=True, help='Geonetwork URL')
@click.option('--username', prompt=True, default='admin', help='Geonetwork username')
@click.password_option('--password', prompt=True, confirmation_prompt=False, hide_input=True, help='Geonetwork password')


@click.pass_context
def cli(ctx,url,username,password):

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		
	geonetwork_session = requests.Session()
	geonetwork_session.auth = HTTPBasicAuth(username, password)
	geonetwork_session.headers.update({"Accept" : "application/json"})

	# Make a call to an endpoint to get cookies and an xsrf token

	geonetwork_url = url + '/geonetwork/srv/eng/info?type=me'
	r_post = geonetwork_session.post(geonetwork_url,
		verify=False
		)

	token = geonetwork_session.cookies.get('XSRF-TOKEN')
	geonetwork_session.headers.update({"X-XSRF-TOKEN" : geonetwork_session.cookies.get('XSRF-TOKEN')})

	# add session and credentials as context objects so they can be used elsewhere
	ctx.obj = {
		'session': geonetwork_session,
		'username': username,
		'password': password,
		'url': url
	}

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def urlupdate(ctx,csvfile):

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


	with open(csvfile, 'rb') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			#click.echo(row)
			params = (
				('uuids', row['UUID']),
				('index', 'true'),
				('urlPrefix', row['OLDURL']),
				('newUrlPrefix', row['NEWURL'])
			)

			session = ctx.obj['session']
			url = ctx.obj['url']
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			geonetworkUpdateURL = url + '/geonetwork/srv/api/0.1/processes/url-host-relocator'
			updateURL = session.post(geonetworkUpdateURL, 
				headers=headers, 
				params=params, 
				verify=False
				)
			click.echo(updateURL.text)

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def sharing(ctx,csvfile):

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
	url = ctx.obj['url']

	

	df = pd.read_csv(csvfile)
	uuidlist = []
	for index, row in df.iterrows():
		# iterate through uuids and create list of distinct entries
		if row["UUID"] not in uuidlist: 
			uuidlist.append(row["UUID"])
	
	for u in uuidlist:
		# build sharingurl from uuid
		geonetworkSharingURL = url + '/geonetwork/srv/api/0.1/records/' + u + '/sharing'
		#click.echo(geonetworkSharingURL)

		# build dictionary of group operations for groups with this uuid, 
		# where key is operation column header and value is cell value
		privlist = []
		sf = df.loc[df['UUID'] == u]
		for index, row in sf.iterrows():
			sharingdict = {}
			sharingdict.update({"group":row["GROUP"],
				"operations":
					{"view":row["VIEW"],
					"download":row["DOWNLOAD"],
					"dynamic":row["DYNAMIC"],
					"featured": row["FEATURED"],
					"notify":row["NOTIFY"],
					"editing":row["EDITING"]
					}
				})

			# create a list collection of all the dictionary entries for that UUID
			privlist.append(sharingdict)

		# add the list to the dictionary of operation options
		privdict = {}
		privdict.update({"clear":"true","privileges":privlist})
	
		#click.echo(json.dumps(privdict))

		session = ctx.obj['session']
		session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
		headers = session.headers
		cookies = session.cookies
		sharingURL = session.put(geonetworkSharingURL, 
			headers=headers, 
			verify=False,
			json = json.dumps(privdict)
			)
		click.echo(sharingURL.text)


if __name__ == '__main__':
	cli()

