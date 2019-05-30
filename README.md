# geonetwork-utility-scripts

A set of scripts for bulk updates of geonetwork based on supplied csv files. Currently includes the following options:

* Check URLs
* Update revision dates for OS data from their atom feed

Outputs results to terminal and csv.

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
