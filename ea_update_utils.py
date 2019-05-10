import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pandas as pd
from collections import Counter
import os
import glob
from modules import MailLogger
import logging
from logging.handlers import RotatingFileHandler

# set up standard logging to file- rolling file appender

logger = logging.getLogger(__name__)

loggingHandler = RotatingFileHandler("ea-update-utilities.log",
                                      maxBytes=102400, backupCount=5)
loggingHandler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

loggingHandler.setFormatter(
    logging.Formatter("%(asctime)s - "
                      "%(levelname)s - %(message)s"))
logger.addHandler(loggingHandler)

# set up email logging- one file per run

# if not required, comment out the smtpDict block

smtpDict = {
	"smtpServer":"smtp.mailtrap.io",
	"smtpPort":2525,
	"username":"7e8c433f062189",
	"password":"a8903125ef6d03",
	"sender":"jocook@astuntechnology.com",
	"recipients":[
			"jocook@astuntechnology.com"
			],
	"subject":"Automated Updates Error"
}
if smtpDict:
	eaMailLogger = MailLogger.MailLogger(os.getcwd(),smtpDict).fileLogger



@click.group()
@click.option('--url', prompt=True, help='Geonetwork URL')
@click.option('--username', prompt=True, default='admin', help='Geonetwork username')
@click.password_option('--password', prompt=True, confirmation_prompt=True, hide_input=False, help='Geonetwork password')

@click.pass_context
def cli(ctx,url,username,password):
	"""Modules for updating metadata UUIDs based on values in a CSV, see samples for structure"""

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
@click.option('--inputdir',prompt=True, help='Directory containing CSV file')
@click.option('--outputsite',prompt=True, type=click.Choice(['DSPUAT','DSPTEST','LIVE']), help='Server updates should apply to')
@click.pass_context
def urlupdate(ctx,inputdir,outputsite):
	"""Update oldURL and replace with newURL, passed from a CSV file.
	newURL can be one of three, dependent on outputsite parameter passed at CLI.
	Will take latest (modified) csv file in named input directory"""

	logger.info('Starting urlupdate')
	eaMailLogger.info('Starting urlupdate')

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	# go to directory
	# get latest csv file by date
	list_of_files = glob.glob(inputdir +'/*.csv')
	latest_file = max(list_of_files, key=os.path.getmtime)
	df = pd.read_csv(latest_file)
	click.echo(latest_file)
	for index, row in df.iterrows():
		# which newURL are we using?
		if outputsite =='DSPUAT':
			urlcol = row['NEWDSPUATURL']
		elif outputsite == 'DSPTEST':
			urlcol = row['NEWDSPTESTURL']
		elif outputsite == 'LIVE':
			urlcol = row['NEWLIVEURL']
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.notnull(row['OLDURL']) and pd.notnull(urlcol):
			click.echo(row)
			params = (
				('uuids', row['UUID']),
				('index', 'true'),
				('urlPrefix', row['OLDURL']),
				('newProtocol', row['PROTOCOL']),
				('newName', row['NAME']),
				('newDescription', row['DESCRIPTION']),
				('newUrlPrefix', urlcol)
			)

			session = ctx.obj['session']
			url = ctx.obj['url']
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			geonetworkUpdateURL = url + '/api/0.1/processes/extended-url-host-relocator'
			updateURL = session.post(geonetworkUpdateURL,
				headers=headers,
				params=params,
				verify=False
				)
			#click.echo(updateURL.text)
			# get at response for some error handling
			response = json.loads(updateURL.text)
			logger.info(response)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				logger.info(row['UUID'] + ': done')
				if smtpDict:
					eaMailLogger.info(row['UUID'] + ': done')
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				logger.info(row['UUID'] + ': not found')
				eaMailLogger.info(row['UUID'] + ': not found')
				results.append('not found')
			else:
				logger.error(row['UUID'] + ': error \n' + updateURL.text)
				if smtpDict:
					eaMailLogger.error(row['UUID'] + ': error \n' + updateURL.text)
				results.append('error')

		else:
			logger.info(row['UUID'] + ': skipped')
			eaMailLogger.info(row['UUID'] + ': skipped')
			results.append('skipped')
	counter = Counter(results)
	logger.info('Finished Processing')
	eaMailLogger.info('Finished Processing')
	logger.info('---------------')
	click.echo('=============')
	click.echo('RESULTS: see updateurlresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
		eaMailLogger.info(k, v)
	rf.insert(1,'RESULT',results)
	rf.to_csv('urlupdateresults.csv', index=False)

@cli.command()
@click.option('--inputdir',prompt=True, help='Directory containing CSV file')
@click.option('--outputsite',prompt=True, type=click.Choice(['DSPUAT','DSPTEST','LIVE']), help='Server updates should apply to')
@click.pass_context
def urladd(ctx,inputdir,outputsite):
	"""add newURL as a new transfer option, passed from CSV file"""

	logger.info('Starting urladd')

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	# go to directory
	# get latest csv file by date
	list_of_files = glob.glob(inputdir +'/*.csv')
	latest_file = max(list_of_files, key=os.path.getmtime)
	df = pd.read_csv(latest_file)
	for index, row in df.iterrows():
		# which newURL are we using?
		if outputsite =='DSPUAT':
			urlcol = row['NEWDSPUATURL']
		elif outputsite == 'DSPTEST':
			urlcol = row['NEWDSPTESTURL']
		elif outputsite == 'LIVE':
			urlcol = row['NEWLIVEURL']
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.isnull(row['OLDURL']) and pd.notnull(urlcol):
			# build json payload
			jsonpayload = json.dumps([{"value":"<gmd:onLine xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"> \
							<gmd:CI_OnlineResource> \
							<gmd:linkage><gmd:URL>" + urlcol + "</gmd:URL></gmd:linkage> \
							<gmd:protocol><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">" + row['PROTOCOL'] + "</gco:CharacterString></gmd:protocol>  \
							<gmd:name><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">" + row['NAME'] + "</gco:CharacterString></gmd:name>  \
							<gmd:description><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">" + row['DESCRIPTION'] + "</gco:CharacterString></gmd:description>  \
							</gmd:CI_OnlineResource> \
							</gmd:onLine>",
							"xpath": "/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/"}])
			session = ctx.obj['session']
			url = ctx.obj['url']
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			headers.update({'Content-Type': 'application/json'})
			geonetworkAddURL = url + '/api/0.1/records/batchediting?uuids=' + row['UUID']
			updateURL = session.put(geonetworkAddURL,
				headers=headers,
				data=jsonpayload,
				verify=False
				)

			# get at response for some error handling
			response = json.loads(updateURL.text)
			logger.info(response)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				logger.info(row['UUID'] + ': done')
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				logger.info(row['UUID'] + ': not found')
				results.append('not found')
			else:
				logger.error(row['UUID'] + ': error \n' + updateURL.text)
				if smtpDict:
					eaMailLogger.error(row['UUID'] + ': error \n' + updateURL.text)
				results.append('error')
		else:
			logger.info(row['UUID'] + ': skipped')
			results.append('skipped')
	counter = Counter(results)
	logger.info('Finished Processing')
	logger.info('---------------')
	click.echo('=============')
	click.echo('RESULTS: see updateaddresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('urladdresults.csv', index=False)


@cli.command()
@click.option('--inputdir',prompt=True, help='Directory containing CSV file')
@click.pass_context
def urlremove(ctx,inputdir):
	"""remove oldURL as a transfer option, passed from CSV file"""

	logger.info('Starting urlremove')

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	# go to directory
	# get latest csv file by date
	list_of_files = glob.glob(inputdir +'/*.csv')
	latest_file = max(list_of_files, key=os.path.getmtime)
	df = pd.read_csv(latest_file)
	for index, row in df.iterrows():
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.notnull(row['OLDURL']) and pd.isnull(row['NEWDSPTESTURL']) and pd.isnull(row['NEWDSPUATURL']) and pd.isnull(row['NEWLIVEURL']):
			#click.echo(row)
			params = (
				('uuids', row['UUID']),
				('index', 'true'),
				('url', row['OLDURL'])
			)

			session = ctx.obj['session']
			url = ctx.obj['url']
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			geonetworkUpdateURL = url + '/api/0.1/processes/extended-onlinesrc-remove'
			updateURL = session.post(geonetworkUpdateURL,
				headers=headers,
				params=params,
				verify=False
				)

			# get at response for some error handling
			response = json.loads(updateURL.text)
			logger.info(response)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				logger.info(row['UUID'] + ': done')
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				logger.info(row['UUID'] + ': not found')
				results.append('not found')
			else:
				logger.error(row['UUID'] + ': error \n' + updateURL.text)
				if smtpDict:
					eaMailLogger.error(row['UUID'] + ': error \n' + updateURL.text)
				results.append('error')
		else:
			logger.info(row['UUID'] + ': skipped')
			results.append('skipped')
	counter = Counter(results)
	logger.info('Finished Processing')
	logger.info('---------------')
	click.echo('=============')
	click.echo('RESULTS: see updateremoveresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('urlremoveresults.csv', index=False)

@cli.command()
@click.option('--inputdir',prompt=True, help='Directory containing CSV file')
@click.pass_context
def sharing(ctx,inputdir):

	"""update permissions on a record for each group in a CSV"""

	logger.info('Starting permissions update')

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
	url = ctx.obj['url']

	session = ctx.obj['session']
	url = ctx.obj['url']
	session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
	headers = session.headers
	cookies = session.cookies

	# get group ID from name and create dictionary of names and ids
	groupurl = url + '/api/0.1/groups?withReservedGroup=true'
	groupresponse = session.get(groupurl,
		verify=False
		)
	groupdict = {g["name"]: g["id"] for g in json.loads(groupresponse.text)}

	# go to directory
	# get latest csv file by date
	list_of_files = glob.glob(inputdir +'/*.csv')
	latest_file = max(list_of_files, key=os.path.getmtime)
	df = pd.read_csv(latest_file)

	uuidlist = []
	results=[]
	for index, row in df.iterrows():
		# iterate through uuids and create list of distinct uuids. Also use
		# this list later for a results csv
		if row["UUID"] not in uuidlist:
			uuidlist.append(row["UUID"])
			rf = pd.DataFrame(uuidlist, columns=['UUID'])

	for u in uuidlist:
		# build sharingurl from uuid
		geonetworkSharingURL = url + '/api/0.1/records/' + u + '/sharing'
		#click.echo(geonetworkSharingURL)

		privlist = []
		sf = df.loc[df['UUID'] == u]
		for index, row in sf.iterrows():
			sharingdict = {}
			groupID = groupdict[row["GROUP"]]
			sharingdict.update({"group":groupID,
				"operations": {k.lower(): v for (k, v) in row.items() if k not in ['UUID', 'GROUP']}
				})

			# create a list collection of all the dictionary entries for that UUID
			privlist.append(sharingdict)

		# add the list to the dictionary of operation options
		privdict = {}
		privdict.update({"clear":True,"privileges":privlist})

		# send privdict to api as json payload
		session = ctx.obj['session']
		session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
		headers = session.headers
		cookies = session.cookies
		sharingURL = session.put(geonetworkSharingURL,
			headers=headers,
			verify=False,
			json =privdict
			)
		logger.info(json.loads(sharingURL.text))

		# rudimentary error handling
		if sharingURL.status_code == 204:
			logger.info(row['UUID'] + ': done')
			results.append('done')
		else:
			logger.error(row['UUID'] + ': error \n' + sharingURL.text)
			if smtpDict:
				eaMailLogger.error(row['UUID'] + ': error \n' + sharingURL.text)
			results.append('error')

	counter = Counter(results)
	logger.info('Finished Processing')
	logger.info('---------------')
	click.echo('=============')
	click.echo('RESULTS: see sharingresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('sharingresults.csv', index=False)


if __name__ == '__main__':
	cli()

