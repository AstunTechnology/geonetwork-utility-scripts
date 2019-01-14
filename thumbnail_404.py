import click
import requests
import pandas as pd
import csv

@click.command()
@click.option('--csvfile', default='thumbnails.csv', help='CSV file')
def get404s(csvfile):
	"""Get list of thumbnails returning a 404 error from a provided csv"""

	df = pd.read_csv(csvfile)
	resultFile = open("404s.csv", "wb")
	wr = csv.writer(resultFile, dialect='excel')
	for index, row in df.iterrows():
		try:
			r = requests.get(row['url'])
			if r.status_code == 200:
				pass
			else:
				wr.writerow([row['uuid'],str(r.status_code)])
		except requests.exceptions.InvalidURL:
			wr.writerow([row['uuid'],'invalid URL'])
			pass
		except requests.exceptions.InvalidSchema:
			wr.writerow([row['uuid'], 'invalid URL'])
			pass

if __name__ == '__main__':
	get404s()

