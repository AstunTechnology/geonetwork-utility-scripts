#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import xml.etree.ElementTree
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

loggingHandler = RotatingFileHandler("os-update-revisiondate.log",
                                      maxBytes=102400, backupCount=5)
loggingHandler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

loggingHandler.setFormatter(
    logging.Formatter("%(asctime)s - "
                      "%(levelname)s - %(message)s"))
logger.addHandler(loggingHandler)


#logging.basicConfig(filename='example.log',level=logging.ERROR)
logger.info('Starting update')

@click.group()
@click.option('--url', required=True, help='Geonetwork URL as far as the node name')
@click.option('--username', required=True, help='Geonetwork username')
@click.option('--password', required=True, help='Geonetwork password')
@click.pass_context
def cli(ctx,url,username,password):
	"""Modules for updating metadata see readme for further details"""

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

	# add session and credentials as context objects so they can be used elsewhere
	ctx.obj = {
		'session': geonetwork_session,
		'username': username,
		'password': password,
		'url': url
	}


@cli.command()
@click.pass_context
def osrevisionupdate(ctx):
	"""Update OS metadata with revisiondate from their atom feed. Requires Ordnance Survey metadata to be in category 'Ordnance Survey'"""
	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	session = ctx.obj['session']
	url = ctx.obj['url']
	session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
	headers = session.headers
	cookies = session.cookies

	uuidlist = []

	# create a selection bucket containing the records owned by the OS group
	geonetworkSearchURL = url + '/eng/q?_cat=Ordnance+Survey'
	searchURL = session.put(geonetworkSearchURL,
		headers=headers,
		verify=False
		)
	#click.echo(geonetworkSearchURL)


	# add search results to a bucket called metadata
	geonetworkSelectURL = url + '/api/0.1/selections/metadata'
	selectURL = session.put(geonetworkSelectURL,
		headers=headers,
		verify=False
		)
	#click.echo(json.loads(selectURL.text))

	geonetworkProcessURL = url + '/api/0.1/processes/os-update-revisiondate'
	processURL = session.post(geonetworkProcessURL,
			headers=headers,
			#params=params,
			verify=False
			)

	logger.info(json.loads(processURL.text))


if __name__ == '__main__':
	cli()
