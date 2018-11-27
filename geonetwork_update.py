import requests
import click
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pandas as pd
from collections import Counter

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
	"""Update oldURL and replace with newURL, passed from a CSV file"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.notnull(row['OLDURL']) and pd.notnull(row['NEWURL']):
			#click.echo(row)
			params = (
				('uuids', row['UUID']),
				('index', 'true'),
				('urlPrefix', row['OLDURL']),
				('newProtocol', row['PROTOCOL']),
				('newName', row['NAME']),
				('newDescription', row['DESCRIPTION']),
				('newUrlPrefix', row['NEWURL'])
			)

			session = ctx.obj['session']
			url = ctx.obj['url']
			session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
			headers = session.headers
			cookies = session.cookies
			geonetworkUpdateURL = url + '/geonetwork/srv/api/0.1/processes/extended-url-host-relocator'
			updateURL = session.post(geonetworkUpdateURL, 
				headers=headers, 
				params=params, 
				verify=False
				)
			
			# get at response for some error handling
			response = json.loads(updateURL.text)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				click.echo(click.style(row['UUID'] + ': done', fg='green'))
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				click.echo(click.style(row['UUID'] + ': not found', fg='red'))
				results.append('not found')
			else:
				click.echo(click.style(row['UUID'] + ': error \n' + updateURL.text, fg='red'))
				results.append('error')
		else:
			click.echo(click.style(row['UUID'] + ': skipped', fg='blue'))
			results.append('skipped')
	counter = Counter(results)
	click.echo('=============')
	click.echo('RESULTS: see updateurlresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('urlupdateresults.csv', index=False)

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def urladd(ctx,csvfile):
	"""add newURL as a new transfer option, passed from CSV file"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.isnull(row['OLDURL']) and pd.notnull(row['NEWURL']):
			# build json payload
			jsonpayload = json.dumps([{"value":"<gmd:onLine xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"> \
							<gmd:CI_OnlineResource> \
							<gmd:linkage><gmd:URL>" + row['NEWURL'] + "</gmd:URL></gmd:linkage> \
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
			geonetworkAddURL = url + '/geonetwork/srv/api/0.1/records/batchediting?uuids=' + row['UUID']
			updateURL = session.put(geonetworkAddURL, 
				headers=headers, 
				data=jsonpayload, 
				verify=False
				)

			# get at response for some error handling
			response = json.loads(updateURL.text)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				click.echo(click.style(row['UUID'] + ': done', fg='green'))
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				click.echo(click.style(row['UUID'] + ': not found', fg='red'))
				results.append('not found')
			else:
				click.echo(click.style(row['UUID'] + ': error \n' + updateURL.text, fg='red'))
				results.append('error')
		else:
			click.echo(click.style(row['UUID'] + ': skipped', fg='blue'))
			results.append('skipped')
	counter = Counter(results)
	click.echo('=============')
	click.echo('RESULTS: see updateaddresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('urladdresults.csv', index=False)


@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def urlremove(ctx,csvfile):
	"""remove oldURL as a transfer option, passed from CSV file"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	uuidlist = []
	results = []

	df = pd.read_csv(csvfile)
	for index, row in df.iterrows():
		uuidlist.append(row["UUID"])
		rf = pd.DataFrame(uuidlist, columns=['UUID'])
		if pd.notnull(row['OLDURL']) and pd.isnull(row['NEWURL']):
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
			geonetworkUpdateURL = url + '/geonetwork/srv/api/0.1/processes/extended-onlinesrc-remove'
			updateURL = session.post(geonetworkUpdateURL, 
				headers=headers, 
				params=params, 
				verify=False
				)
			
			# get at response for some error handling
			response = json.loads(updateURL.text)

			if updateURL.status_code == 201 and response["numberOfNullRecords"] == 0 and not response["errors"]:
				click.echo(click.style(row['UUID'] + ': done', fg='green'))
				results.append('done')
			elif updateURL.status_code == 201 and response["numberOfNullRecords"] == 1:
				click.echo(click.style(row['UUID'] + ': not found', fg='red'))
				results.append('not found')
			else:
				click.echo(click.style(row['UUID'] + ': error \n' + updateURL.text, fg='red'))
				results.append('error')
		else:
			click.echo(click.style(row['UUID'] + ': skipped', fg='blue'))
			results.append('skipped')
	counter = Counter(results)
	click.echo('=============')
	click.echo('RESULTS: see updateremoveresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('urlremoveresults.csv', index=False)

@cli.command()
@click.option('--csvfile',prompt=True, help='CSV file')
@click.pass_context
def sharing(ctx,csvfile):

	"""update permissions on a record for each group in a CSV"""

	# disabling https warnings while testing
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
	url = ctx.obj['url']

	session = ctx.obj['session']
	url = ctx.obj['url']
	session.auth = HTTPBasicAuth(ctx.obj['username'],ctx.obj['password'])
	headers = session.headers
	cookies = session.cookies
	
	# get group ID from name and create dictionary of names and ids
	groupurl = url + '/geonetwork/srv/api/0.1/groups?withReservedGroup=true'
	groupresponse = session.get(groupurl,
		verify=False
		)
	groupdict = {g["name"]: g["id"] for g in json.loads(groupresponse.text)}

	df = pd.read_csv(csvfile)
	
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
		geonetworkSharingURL = url + '/geonetwork/srv/api/0.1/records/' + u + '/sharing'
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

		# rudimentary error handling
		if sharingURL.status_code == 204:
			click.echo(click.style(row['UUID'] + ': done', fg='green'))
			results.append('done')
		else:
			click.echo(click.style(row['UUID'] + ': error \n' + sharingURL.text, fg='red'))
			results.append('error')
	
	counter = Counter(results)
	click.echo('=============')
	click.echo('RESULTS: see sharingresults.csv for details')
	for k,v in sorted(counter.iteritems()):
		print k, v
	rf.insert(1,'RESULT',results)
	rf.to_csv('sharingresults.csv', index=False)


if __name__ == '__main__':
	cli()

