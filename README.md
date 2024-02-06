# geonetwork-utility-scripts

A set of scripts for bulk updates of geonetwork based on supplied csv files. Currently includes the following options:

* Check URLs

## Dependencies

* GeoNetwork 4.2 or later with PostgreSQL 14.9 database, Python 3 (including `python-dev`).

### Python

The Python package `psycopg2` requires the following system packages to be installed:

* `libpq-dev`
* `build-dep`
* `python-psycopg2`

**Installed with apt or the package manager of your system**

```
    sudo apt-get install libpq-dev build-dep python-psycopg2
```

# INSTALLATION

```
  git clone https://github.com/AstunTechnology/geonetwork-update-scripts
  cd geonetwork-update-scripts
  python3 -m venv .
  source bin/activate
  pip install -r requirements.txt
```

# GENERAL USAGE

## url_check.py

Module for checking URLs (eg from online resource locators in a metadata record) and listing those that fail.

`python url_check.py --csvfile /path/to/csv/file`

Provide path to the CSV file at prompt, which should comprise of 2 columns, with the headers: **uuid** and **url** (not specifically GeoNetwork URLs).

Output results to `report.csv`- a list of the UUIDs, URLs and their error (or success) code. This is placed in the `output` directory.

A sample file is provided in the `samples` directory which can be used to test the script.

## email_update.py

Module for updating a user's email address either in the user's GeoNetwork profile or in metadata records.

### updating user's email address in the user's profile

`python email_update.py updateuser`

### updating user's email address in metadata records

`python email_update.py updatemetadata`

#### Requirements (common to both scripts)

The scripts require a CSV file with 2 columns (called `old_email` and `new_email`)- see `./samples/email_update.csv.sample` for an example

When ran, the scripts will prompt for the following:

* GeoNetwork URL as far as the node name: e.g. `http://localhost:8080/geonetwork/srv`
* GeoNetwork username: this needs to be a user with the relevant permissions (e.g. an Administrator)
* GeoNetwork password: the login password of the user- this will be required twice for confirmation (the input is hidden for security)
* CSV file path: this is the FULL path to the CSV file containing the updates (see `./samples/email_update.csv.sample` for structure)

The logs will be appended to `email-update.log`.

**######## TO BE REVISED (Don't read below here)########**

# Metadata Update Reminder

See https://astuntech.atlassian.net/wiki/spaces/SYSADMIN/pages/140763762/Metadata+Update+Frequency+Queries for more details

## Requirements

> Send emails when metadata is due for an update or overdue an update, based on the supplied update frequency, date updated, and point of contact

## Setup

### Database

Once the dependencies are installed run `setup.sql` against the GeoNetwork database.

### Logging

All log messages are written to `stdout`, should output be written to a file a sample logrotate configuration is provided (`updatereminder.logrotate`) which should be copied to `/etc/logrotate.d/`.

## Usage

For usage run `updatereminder.py` using the `python` interpreter from the virtual environment:

`python updatereminder.py --help`