# geonetwork-utility-scripts

A set of scripts for bulk updates of geonetwork based on supplied csv files. Currently includes the following options:

* Update URL (replace old URL with new one)
* Remove URL
* Add URL
* Update Sharing Permissions
* Check URLs

Outputs results to terminal and csv.

**Note that the URL updating modules can work from the same CSV, and will skip records depending on whether both OLDURL and NEWURL are supplied, or just one.**

# INSTALLATION

**Requires Python 2.7**

```
  git clone https://github.com/AstunTechnology/geonetwork-update-scripts
  cd geonetwork-update-scripts
  python virtualenv .
  source bin/activate
  pip install -r requirements.txt
  ```

# GENERAL USAGE

## ea_update_utils.py

Modules for updating/editing/removing URLs from metadata records, and updating sharing permissions

`python ea_update_utils.py --help`

### urlupdate

`python ea_update_utils.py --url={root geonetwork URL eg http://localhost:8080/geonetwork/srv/} --username={admin username} urlupdate`

Add password for `{admin username}`and path to `filename.csv` at prompts

Runs `url-host-relocator.xsl` via `/api/0.1/processes/`. This file must be present in the `process` folder for the schema of the records you are trying to update.
Requires CSV file in same format as `updateurl.csv.sample`, eg:

  * UUID: uuid of the record
  * OLDURL: the URL you wish to update
  * NEWURL: the URL you wish to update to
  * PROTOCOL: (optional) protocol for the transfer option
  * NAME: (optional) name for the transfer option
  * DESCRIPTION: (optional) description for the transfer option

Outputs results to `urlupdateresults.csv`


### urladd
`python ea_update_utils.py --url={root geonetwork URL eg http://localhost:8080/geonetwork/srv/} --username={admin username} urlupdate`

Add password for `{admin username}`and path to `filename.csv` at prompts

Runs `url-host-relocator.xsl` via `/api/0.1/processes/`. This file must be present in the `process` folder for the schema of the records you are trying to update.
Requires CSV file in same format as `updateurl.csv.sample`, eg:

  * UUID: uuid of the record
  * OLDURL: LEAVE BLANK
  * NEWURL: the URL you wish add
  * PROTOCOL: (mandatory) protocol for the new URL
  * NAME: (mandatory) name for the new URL
  * DESCRIPTION: (mandatory) description for the new URL

Outputs results to `urladdresults.csv`

### urlremove

`python ea_update_utils.py --url={root geonetwork URL eg http://localhost:8080/geonetwork/srv/} --username={admin username} urlupdate`

Add password for `{admin username}`and path to `filename.csv` at prompts

Runs `/api/0.1/records/batchediting`.

Requires CSV file in same format as `updateurl.csv.sample`, eg:

  * UUID: uuid of the record
  * OLDURL: the URL you wish to remove
  * NEWURL: LEAVE BLANK
  * PROTOCOL: (optional) protocol for the URL
  * NAME: (mandatory) name for the URL
  * DESCRIPTION: (optional) description for the URL

Outputs results to `urlremoveresults.csv`

### sharing

`python ea_update_utils.py --url={root geonetwork URL eg http://localhost:8080/geonetwork/srv/} --username={admin username} sharing`
 
Add password for `{admin username}`and path to `filename.csv` at prompts

Runs `/api/0.1/records/[uuid]/sharing` for each UUID and GROUP in provided CSV

Requires CSV file in same format as `sharing.csv.sample`, eg a row for each UUID and GROUP combination:

  * UUID: uuid of the record
  * GROUP: group name (must be full name and is case-sensitive),
  * VIEW: true/false for this operation for this group,
  * DOWNLOAD: true/false for this operation for this group,
  * DYNAMIC: true/false for this operation for this group,
  * FEATURED: true/false for this operation for this group,
  * NOTIFY: true/false for this operation for this group,
  * EDITING: true/false for this operation for this group

Outputs results to `sharingresults.csv`

## url_check.py

Module for checking URLs (eg from online resource locators in a metadata record) and listing those that fail

`python url_check.py --csvfile={csvfile}`

Provide path to `{csvfile}` at prompt, which should comprise a single column with no header listing URLs (not specifically geonetwork

Outputs results to 404s.csv- a list of failing URLs and their error code

## os_update_revisiondate.py

For records harvested from [https://www.ordnancesurvey.co.uk/xml/products/](https://www.ordnancesurvey.co.uk/xml/products/) updates the revision dates with the latest values from [https://www.ordnancesurvey.co.uk/xml/atom/LiveProductFeed.xml](https://www.ordnancesurvey.co.uk/xml/atom/LiveProductFeed.xml)

`python os_update_revisiondate.py --url={root geonetwork URL eg http://localhost:8080/geonetwork/srv/} --username={admin username} osrevisionupdate`

Add password for `{admin username}` at prompt

Runs `os-update-revisiondate.xsl` via `/api/0.1/processes/`. This file must be present in the `process` folder for the schema of the records you are trying to update. In the case of the OS data this means ISO19139 and ISO19139.Gemini22

Outputs logs to `logs/os-update-revisiondate.log`

# Tests

IN PROGRESS

**Requires python-nose**

Run `nosetests` in the root folder to execute all tests in the `tests` folder.
