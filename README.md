# geonetwork-update-scripts

Scripts for bulk updates of geonetwork based on supplied csv files. Currently includes the following update options:

* Update URL (replace old URL with new one)
* Remove URL
* Add URL
* Update Sharing Permissions

CAUTION: Work in progress, with very minimal error handling!

## INSTALLATION

**Requires Python 2.7**

```
  git clone https://github.com/AstunTechnology/geonetwork-update-scripts
  cd geonetwork-update-scripts
  python virtualenv .
  source bin/activate
  pip install -r requirements.txt
  ```

## GENERAL USAGE

`python geonetwork_update.py --help`

### urlupdate

`python geonetwork_update.py --url={root geonetwork URL eg http://localhost:8080} --username={admin username} urlupdate`
* Add password for `{admin username}` at prompt
* Add `filename.csv` at prompt

* Runs `url-host-relocator.xsl` via `/geonetwork/srv/api/0.1/processes/`. This file must be present in the `process` folder for the schema of the records you are trying to update.
* Requires CSV file in same format as `updateurl.csv.sample`, eg:
  * UUID: uuid of the record
  * OLDURL: the URL you wish to update
  * NEWURL: the URL you wish to update to
  * PROTOCOL: (optional) protocol for the transfer option
  * NAME: (optional) name for the transfer option
  * DESCRIPTION: (optional) description for the transfer option

### urladd
`python geonetwork_update.py --url={root geonetwork URL eg http://localhost:8080} --username={admin username} urlupdate`
* Add password for `{admin username}` at prompt
* Add `filename.csv` at prompt

* Runs `url-host-relocator.xsl` via `/geonetwork/srv/api/0.1/processes/`. This file must be present in the `process` folder for the schema of the records you are trying to update.
* Requires CSV file in same format as `updateurl.csv.sample`, eg:
  * UUID: uuid of the record
  * OLDURL: LEAVE BLANK
  * NEWURL: the URL you wish add
  * PROTOCOL: (mandatory) protocol for the new URL
  * NAME: (mandatory) name for the new URL
  * DESCRIPTION: (mandatory) description for the new URL

### urlremove

`python geonetwork_update.py --url={root geonetwork URL eg http://localhost:8080} --username={admin username} urlupdate`
* Add password for `{admin username}` at prompt
* Add `filename.csv` at prompt

* Runs `/geonetwork/srv/api/0.1/records/batchediting`.
* Requires CSV file in same format as `updateurl.csv.sample`, eg:
  * UUID: uuid of the record
  * OLDURL: the URL you wish to remove
  * NEWURL: LEAVE BLANK
  * PROTOCOL: (optional) protocol for the URL
  * NAME: (mandatory) name for the URL
  * DESCRIPTION: (optional) description for the URL

### sharing

`python geonetwork_update.py --url={root geonetwork URL eg http://localhost:8080} --username={admin username} sharing`
* Add password for `{admin username}` at prompt
* Add `filename.csv` at prompt

* Runs `geonetwork/srv/api/0.1/records/[uuid]\sharing` for each UUID and GROUP in provided CSV
* Requires CSV file in same format as `sharing.csv.sample`, eg a row for each UUID and GROUP combination:
  * UUID: uuid of the record
  * GROUP: group name (must be full name and is case-sensitive),
  * VIEW: true/false for this operation for this group,
  * DOWNLOAD: true/false for this operation for this group,
  * DYNAMIC: true/false for this operation for this group,
  * FEATURED: true/false for this operation for this group,
  * NOTIFY: true/false for this operation for this group,
  * EDITING: true/false for this operation for this group



