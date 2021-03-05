# Sophos Central API Connector
Python library to utilise many of the features in Sophos Central API across multiple or single tenants

* [Documentation: Sophos Central API](https://developer.sophos.com/)
* [Documentation: Sophos Central API Connector](https://github.com/sophos-cybersecurity/sophos_central_api_connector/tree/master/docs)

![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Generic badge](https://img.shields.io/badge/version-0.1.4-green.svg)](https://shields.io/)
   ___

## Table of contents: 

- [Sophos Central API Connector](#sophos-central-api-connector)
  * [Features](#features)
  * [Quick start](#quick-start)
      - [**Important!**](#--important---)
  * [Prerequisites](#prerequisites)
  * [Install](#install)
  * [Basic Examples](#basic-examples)
    + [Help](#help)
    + [Tenants List](#tenants-list)
    + [Inventory](#inventory)
    + [Alerts/Event Information](#alerts-event-information)
    + [Local Site](#local-site)
  * [Structure](#structure)
  
   ___

## Features
All features can be run against single or multiple tenants
* Gather tenant system inventory 
  * Output to stdout, json, Splunk
* Gather alerts
   * Alert polling
   * Output to stdout, json, Splunk
* Local Sites
   * Clean up Global exclusions
      * Compare exclusions to SophosLabs Intelix
   * Generate report
* IOC Hunting - Utilising Live Discover
   * MISP Attribute hunting (eventId, tags)
   * RAW JSON input
   * Saved search
    
___

## Quick start
Want to test as quickly as possible? Follow the below quick start steps to begin looking at your Sophos Central data!
1. Install latest version of Python 3
1. Create a folder e.g "sophos_test"
1. Open a command prompt/terminal
1. Create a Python Virtual Environment:
   ```python
   python -m venv <folder_name>
   ```
1. Activate the Python Virtual Environment:
   ```python
   <path_to_folder>\Scripts\activate
   ```
1. Install the Sophos Central API Connector (this will also install the requirements):
   ```python
   pip install sophos-central-api-connector
   ```
1. Once it has finished installing browse to:
   ```python
   cd <path_to_folder>\Lib\site-packages\sophos_central_api_connector
   ```
1. Run the following command to view help to begin:
   ```python
   python sophos_central_main.py --help
   ```
1. Add your Sophos Central API id and secret to the sophos_config.ini under the folder: \Lib\site-packages\sophos_central_api_connector\config

   > #### **Important!**
   > We would recommend that the static entry is only used for testing purposes and the token is stored and accessed securely.
   > Please reference the authentication section under advanced usage to use the correct parameter
___

## Prerequisites
In order to use the package you will require a valid API key from your Sophos Central tenant. To obtain a valid API key please reference the documentation [here](https://developer.sophos.com/intro)
___

## Install
```python
pip install --user sophos_central_api_connector
```
___

## Authentication
There are two options for authentication, the setting used here will be used for all areas of authentication. As mentioned under the configuration section we recommend using the AWS Secrets Manager for storing these credentials. Only use the static credentials for testing purposes.

### Static Credentials
To specify using the static credentials which are in the \*config.ini files you can use the following:
`python3 sophos_central_main.py --auth static`

### AWS Secrets Manager
To specify using the AWS settings which are in the \*config.ini files to retrieve the secrets and token you can use the following:
`python3 sophos_central_main.py --auth aws`
___

## Basic Examples

### Help
To get information on the CLI commands when using the `sophos_central_main.py` run:

```python
python sophos_central_main.py --help
```

### Tenants List
To get a list of tenants:

```python
python sophos_central_main.py --auth <auth_option> --get tenants
```

### Inventory
To get inventory data:
```python
python sophos_central_main.py --auth <auth_option> --get inventory --output <output_option>
```

### Alerts/Event Information
To get alert data:
```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --output <output_option>
```

### Local Site
To get a list of local site data:
```python
python sophos_central_main.py --auth <auth_option> --get local-sites --output <output_option>
```
   ___

## Output Options
There are four output options available for the inventory, simply add one of the following after `--output`:
- **stdout:** Print the information to the console.
- **json:** Save the output of the request to a json file
- **splunk:** This will send the data to Splunk with no changes made. This will apply the settings made in the transform files.
- **splunk_trans:** Using this output will apply the information set in the splunk_config.ini for the host, source and sourcetype. This will overrun the settings in the transform files in Splunk but not the Index that the data should be sent to.

___

## Troubleshooting
All logging is done via the python `logging` library. Valid logging levels are:

- INFO
- DEBUG
- CRITICAL
- WARNING
- ERROR

For basic feedback set the logging level to `INFO`
___

## Structure
Below is the structure after installing through pip:
```
sophos_central_api_connector
|   .gitignore
|   LICENSE
|   MANIFEST.in
|   README.md
|   requirements.txt
|   setup.py
|___docs
|       alerts.md
|       intelix.md
|       intelix_configuration.md
|       inventory.md
|       ioc_hunter.md
|       local_sites.md
|       misp_configuration.md
|       sophos_configuration.md
|       splunk_configuration.md
|___xdr_queries
|       |___Live Discover
|               ioc_hunter.sqlite
|___sophos_central_api_connector
|       ioc_hunter.py
|       sophos_central_api_live_discover.py
|       sophos_central_api_auth.py
|       sophos_central_api_awssecrets.py
|       sophos_central_api_connector_utils.py
|       sophos_central_api_delete_data.py
|       sophos_central_api_get_data.py
|       sophos_central_api_intelix.py
|       sophos_central_api_output.py
|       sophos_central_api_polling.py
|       sophos_central_api_tenants.py
|       sophos_central_api_hec_splunk.py
|       sophos_central_main.py
|___config
|       intelix_config.ini
|       misp_config.ini
|       sophos_central_api_config.py
|       sophos_config.ini
|       splunk_config.ini
```

Below is the structure with all the files that are created through different mechanisms:
```
sophos_central_api_connector
|   .gitignore
|   LICENSE
|   MANIFEST.in
|   README.md
|   requirements.txt
|   setup.py
|___docs
|       alerts.md
|       intelix.md
|       intelix_configuration.md
|       inventory.md
|       ioc_hunter.md
|       local_sites.md
|       misp_configuration.md
|       sophos_configuration.md
|       splunk_configuration.md
|___xdr_queries
|       |___Live Discover
|               ioc_hunter.sqlite
|___sophos_central_api_connector
|       ioc_hunter.py
|       sophos_central_api_live_discover.py
|       sophos_central_api_auth.py
|       sophos_central_api_awssecrets.py
|       sophos_central_api_connector_utils.py
|       sophos_central_api_delete_data.py
|       sophos_central_api_get_data.py
|       sophos_central_api_intelix.py
|       sophos_central_api_output.py
|       sophos_central_api_polling.py
|       sophos_central_api_tenants.py
|       sophos_central_api_hec_splunk.py
|       sophos_central_main.py
|___config
|       intelix_config.ini
|       misp_config.ini
|       sophos_central_api_config.py
|       sophos_config.ini
|       splunk_config.ini
|___logs
|       failed_events.json
|___output
|   |___get_alerts
|   |       <tenant_name>_<tenant_id>.json
|   |       ...
|   |___get_inventory
|           <tenant_name>_<tenant_id>.json
|   |___get_local_sites
|           <tenant_name>_<tenant_id>.json
|           ...
|   |___intelix
|       |___delete_local_sites
|           <date>_<time>_deletion_details.json
|           <date>_<time>_deletion_report.json
|           ...
|       <date>_<time>_intelix_results.json
|       <date>_<time>_results_combined.json
|       <tenant_id>_<date>_<time>_<risk_level>_dry_run_report.json
|       ...
|___polling
|       poll_config.json
|       alert_ids.json
|       temp_alert_ids.json
|___tmp
      endpoint_data.json
      result_data.json
      search_data.json
```
