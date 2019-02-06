import click
import requests
import pandas as pd
import csv

@click.command()
@click.option('--csvfile', default='urls.csv', help='CSV file')
def get404s(csvfile):
	"""Get list of urls returning a 404 error from a provided csv"""

	df = pd.read_csv(csvfile)
	resultFile = open("404s.csv", "wb")
	wr = csv.writer(resultFile, dialect='excel')
	for index, row in df.iterrows():
		try:
			r = requests.get(row['url'])
			if r.status_code == 200:
				wr.writerow([row['uuid'], row['url'], 'OK'])
			else:
				wr.writerow([row['uuid'], row['url'],str(r.status_code)])
		except requests.exceptions.InvalidURL:
			wr.writerow([row['uuid'], row['url'],'invalid URL'])
			pass
		except requests.exceptions.InvalidSchema:
			wr.writerow([row['uuid'],  row['url'], 'invalid URL'])
			pass
		except requests.exceptions.ConnectionError:
			wr.writerow([row['uuid'],  row['url'], 'connection error'])
			pass

if __name__ == '__main__':
	get404s()

