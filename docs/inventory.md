### Endpoint Information

Gathering the inventory information can be done for all of your tenants or one specific tenant. There are various methods on how this data can be presented. The output methods are stdout, json or sending the data to Splunk. More detailed example are covered under the Advanced Usage section.

There are various products which can utilise data from stdout such as running a script in Splunk and indexing the data dynamically. Also this can be used as a response in automation to provide further details on a systems health etc.

The syntax to use when requesting to get inventory is the following:
```python
python sophos_central_main.py --auth <auth_option> --get inventory --output <output_option>
```

### Alert/Event Information

To gather alerts for your tenants you can pass the alerts option when running the --get parameter. Some additional options are available
when gathering alerts above calling the inventory of machines:

- --days
- --poll_alerts (covered in the Advanced Usage section)
- --reset (covered in the Advanced Usage section)

As with calling the inventory option, you can pull alerts for a specific tenant or all of the tenants. In addition you can specify the number of days of events you would like to pull back by using the days parameter.

Sophos Central holds event data for 90 days, so when calling the days parameter you can specifiy days as an integer from 1-90. If no days parameter is passed a default of 1 day is set. below is an example of passing the days parameter:
```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --output <output_option>
```

### Local Site Information

You can review the sites which have been added to Global Settings > Website Management using the API.

As with previous abilities you can pull the sites for a specific tenant or for all tenants for review. It will automatically reference
the category integer to a human readable category. This can be output to all the available options.
```python
python sophos_central_main.py --auth <auth_option> --get local-sites --output <output_option>
```

### Intelix

We have incorporated the SophosLabs Intelix API to assist with cleaning up local site information which can be obtained from the global settings mentioned above.

If you have not used or signed up for the Intelix API further information can be found here: https://api.labs.sophos.com/doc/index.html#registration-howto

We use the Intelix API package as a base: https://github.com/sophos-cybersecurity/intelix

There are a number of options available.

#### Test
You can run a test to ensure that your configuration is working without the need to run the full commands.
```python
python sophos_central_main.py --auth <auth_option> --intelix test
```

#### Report

Running the intelix command in report mode will gather the local site information (all or one tenant) and check Intelix API to see if SophosLabs detect the site.

As part of the process we automatically dedupe the URLs queried with Intelix to reduce the api calls made.

It will automatically generate JSON files for the reports. One which is combined Intelix and local site data: `<date>_<time>_results_combined.json` and another for just the
Intelix results: `<date>_<time>_intelix_results.json`

```python
python sophos_central_main.py --auth <auth_option> --intelix report
```

#### Clean_ls

Running the intelix command with clean_ls will go through the process of checking the sites against the Intelix API and proceed to delete the local-site entry in
the global settings in Sophos Central.

In addition to the clean_ls command you must specify a clean-level to specify which sites that Intelix has a risk level for will be deleted from local-sites. Below are the
accepted risks for the command

- ALL
- HIGH
- HIGH_MEDIUM
- MEDIUM
- LOW

We do not delete sites which have not been categorised by SophosLabs.

Before running the clean_ls command and actively deleting the local sites from Central we highly recommend using the '--dry_run' switch. This will generate a report of what would have
been deleted based on the parameters passed:
```python
python sophos_central_main.py --auth <auth_option> --intelix clean_ls --clean_level <level> --dry_run
```

Please review the dry run report carefully before running the active clean command. The report is: `<tenantId>_<date>_<time>_<clean_level>_dry_run_report.json`

Once you are happy with the dry-run results you can go forward and commit the changes by running the command without the dry-run switch:
```python
python sophos_central_main.py --auth <auth_option> --intelix clean_ls --clean_level <level>
```

Once complete two files will be created. One is a report on the count of deletions etc. for each tenant: `<date>_<time>_deletion_report.json` and another
which is more details on the sites which were sent for deletion, their deletion status and the time of the transaction. This is covered under the file:
`<date>_<time>_deletion_details.json`

## Configuration
### intelix_config.ini
> #### **Important!**
> Whilst you are able to set static API credentials in this configuration we strongly advise that this is only done for testing purposes.
> Where possible use AWS Secrets Manager to store your credential id and token
> Please reference the authentication section under advanced usage to use the correct parameter

The AWS secret credentials follows the same format as the sophos_config.ini.

There is an additional section in regards to the IP lookup categorisation. To align with the URL riskLevel we have provided the ability to set the IP categories against the risk level. The values already set
and should be reviewed and amended to prevent deleting sites incorrectly from the local sites settings in Central.


### splunk_config.ini
This config is solely for users who are sending the events and inventory directly to Splunk. There are options for both static token information or there is also an option to use the AWS Secrets Manager.

> #### **Important!**
> We would recommend that the static entry is only used for testing purposes and the token is stored and accessed securely.
> Please reference the authentication section under advanced usage to use the correct parameter

#### splunk_aws
To enable the use of the token from the AWS Secrets Manager set : `1`

Setting this option to `0` will allow the use of the static token entry. The 'splunk_hec' section determines the correct settings to where to send the events to Splunk

#### splunk_url
This is the URL to your Splunk instance: `http(s)://<your_splunk_url>:8088/services/collector`

Information on how to configure HEC (HTTP Event Collector) can be found at the following Splunk URL: https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector

#### splunk_ack_enabled
If you have set Splunk Index Acknowledgements when creating your HEC token, you will need to set this value to '1'. If you have not set the indexer acknowledgements to `0`. This will ensure that the correct URL is used when sending events to Splunk.

#### verify_ack_result
This is not currently in use

#### channel
If you have the index acknowledgements checked in your HEC token you will need to provide a channel GUID. These can be anything you like as long as they are unique to your HEC token environment. Further information on setting the channel and enabling Index Acknowledgements
can be found on the Splunk website: https://docs.splunk.com/Documentation/Splunk/7.3.1/Data/AboutHECIDXAck

#### ack_batch_size
This is not currently in use

#### splunk_transform
This section of the config allows you to override the details for source, host and sourcetype when the events are sent to Splunk. If this setting is not set then it will use the data that is contained in the transforms file on the indexer. This is not able to override the index that the data is sent to.

## Advanced Usage

### Authentication
There are two options for authentication, the setting used here will be used for all areas of authentication, i.e both Sophos Central API and Splunk HEC token. As mentioned under the configuration section we recommend using the AWS Secrets Manager for storing these credentials. Only use the static credentials for testing purposes.

#### Static Credentials
To specify using the static credentials which are in the \*config.ini files you can use the following:
`python3 sophos_central_main.py --auth static`

#### AWS Secrets Manager
To specify using the AWS settings which are in the \*config.ini files to retrieve the secrets and token you can use the following:
`python3 sophos_central_main.py --auth aws`

### Logging
All logging is done via the naitive python `logging` library. Valid logging levels are:

- INFO
- DEBUG
- CRITICAL
- WARNING
- ERROR

For basic feedback set the logging level to `INFO`

### Output Options
There are four output options available for the inventory, simply add one of the following after `--output`:
- **stdout:** Print the information to the console.
- **json:** Save the output of the request to a json file
- **splunk:** This will send the data to Splunk with no changes made. This will apply the settings made in the transform files.
- **splunk_trans:** Using this output will apply the information set in the splunk_config.ini for the host, source and sourcetype. This will overrun the settings in the transform files in Splunk but not the Index that the data should be sent to.

### Polling Alert Information
The polling option is available for alert events. This is so you can gather alerts over a period of time and maintain a list of events in Splunk.

The correct syntax to poll for alert events is as follows:
```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --poll_alerts --output <splunk or splunk_trans>
```
On the initial run of this syntax the following files will be created:
- poll_config.json
- alert_ids.json

The poll_config.json maintains the results of the last poll attempt and also from when the next poll should get events from and to. Along with maintaining the state of the current run and logging whether any failures have occurred.

When running the poll_alerts for a second time a new file will be generated called:
- temp_alert_ids.json

This file maintains a list of events which have already been successfully sent to Splunk and will be removed from the alerts obtained from the Sophos Central API.

### Resetting Polling
If you need to reset the polling and start re-pulling in events you can pass the reset parameter to initiate this. Along with the reset parameter you can also pass the days parameter in order to specify how many days should be pulled using the API. Syntax on how to pass this is as follows:

```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --reset --poll_alerts --output <splunk or splunk_trans>
```

Running this syntax will delete the files:
- poll_config.json
- alert_ids.json
- temp_alert_ids.json