import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import xml.etree.ElementTree
from click.testing import CliRunner


def test_osrevisionupdate():
	@click.command()
	@click.argument('url')
	@click.argument('username')
	@click.argument('password')
	def login(url,username,password):
		"""Test we can authenticate"""

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
		click.echo(r_post.status_code)
		# token = geonetwork_session.cookies.get('XSRF-TOKEN')
		# geonetwork_session.headers.update({"X-XSRF-TOKEN" : geonetwork_session.cookies.get('XSRF-TOKEN')})

		# # add session and credentials as context objects so they can be used elsewhere
		# ctx.obj = {
		# 	'session': geonetwork_session,
		# 	'username': username,
		# 	'password': password,
		# 	'url': url
		# }
	runner = CliRunner()
	# TODO run this with non admin username and password!
	result = runner.invoke(login, ['http://geonetwork.astuntechnology.com/geonetwork/astun', 'pythontest', 'ReflectionTribeBurstImagine5'])
	assert result.exit_code == 0
	assert '200' in result.output


if __name__ == '__main__':
	test_osrevisionupdate()
