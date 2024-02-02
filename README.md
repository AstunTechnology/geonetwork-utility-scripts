# geonetwork-utility-scripts

A set of scripts for bulk updates of geonetwork based on supplied csv files. Currently includes the following options:

* Check URLs


Outputs results to terminal and csv.

# INSTALLATION

**Requires Python 3.12**

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

# Tests

IN PROGRESS

**Requires python-nose**

Run `nosetests` in the root folder to execute all tests in the `tests` folder.


# Metadata Update Reminder

See https://astuntech.atlassian.net/wiki/spaces/SYSADMIN/pages/140763762/Metadata+Update+Frequency+Queries for more details

Requirements:

> Send emails when metadata is due for an update or overdue an update, based on the supplied update frequency, date updated, and point of contact

## Dependencies

* GeoNetwork 4.2 or later with PostgreSQL 14.9 database

### Python

* The Python package `psycopg2` requires the system packages `python-dev` and `libpq-dev` be installed.

## Setup

### Database

Once the dependencies are installed run `setup.sql` against the GeoNetwork database.

### Python

Create a Python 3.12 virtual environment and install dependencies using:

    pip install -r requirements.txt


### Logging

All log messages are written to `stdout`, should output be written to a file a sample logrotate configuration is provided (`updatereminder.logrotate`) which should be copied to `/etc/logrotate.d/`.

## Usage

For usage run `updatereminder.py` using the `python` interpreter from the virtual environment:

    python updatereminder.py --help

## Tests

Not done yet

## Implementation

### Workflow

* The script `updatereminder.py` is ran daily, it:
    * does some stuff
