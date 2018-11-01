import requests
from requests.auth import HTTPBasicAuth

# Credentials (to be passed from config IRL)

username = 'redacted'
password = 'alsoredacted'
url = 'https://geonetwork.astuntechnology.com'

# Establish Session

geonetwork_session = requests.Session()
geonetwork_session.auth = HTTPBasicAuth(username, password)
geonetwork_session.headers.update({"Accept" : "application/xml"})

# Make a call to an endpoint to get cookies and an xsrf token

geonetwork_url = url + '/geonetwork/srv/eng/info?type=me'
r_post = geonetwork_session.post(geonetwork_url)

token = geonetwork_session.cookies.get('XSRF-TOKEN')
geonetwork_session.headers.update({"X-XSRF-TOKEN" : geonetwork_session.cookies.get('XSRF-TOKEN')})

# Try the URL again and see if we get a happy response

r_post = geonetwork_session.post(geonetwork_url)
print r_post.text