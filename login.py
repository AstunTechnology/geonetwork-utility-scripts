import requests
import click
from requests.auth import HTTPBasicAuth

# Establish Session

@click.command()
@click.option('--url', prompt=True, help='Geonetwork URL')
@click.option('--username', prompt=True, default='admin', help='Geonetwork username')
@click.password_option('--password', prompt=True, confirmation_prompt=False, hide_input=True, help='Geonetwork password')
def login(url,username,password):
	
	geonetwork_session = requests.Session()
	geonetwork_session.auth = HTTPBasicAuth(username, password)
	geonetwork_session.headers.update({"Accept" : "application/xml"})

	# Make a call to an endpoint to get cookies and an xsrf token

	geonetwork_url = url + '/geonetwork/srv/eng/info?type=me'
	r_post = geonetwork_session.post(geonetwork_url)

	token = geonetwork_session.cookies.get('XSRF-TOKEN')
	geonetwork_session.headers.update({"X-XSRF-TOKEN" : geonetwork_session.cookies.get('XSRF-TOKEN')})

	# Try the URL again and see if we get a happy response- should print the results of the info request
	# for the user with the given credentials

	r_post = geonetwork_session.post(geonetwork_url)
	click.echo(r_post.text)

if __name__ == '__main__':
	login()