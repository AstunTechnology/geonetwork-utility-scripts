import requests
import click
import csv
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning


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
		'password': password
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
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			updateURL = session.post('https://34.240.132.21/geonetwork/srv/api/0.1/processes/url-host-relocator', 
				headers=headers, 
				params=params, 
				verify=False
				)
			click.echo(updateURL.text)

if __name__ == '__main__':
    cli()

