# sophos-central-api-connector
Python library to gather alerts and endpoint data from your Sophos Central tenants

[![Generic badge](https://img.shields.io/badge/version-0.1.0-green.svg)](https://shields.io/)

Sophos Central API Documentation: https://developer.sophos.com/

## Getting Started
The below instructions will take you through obtaining a copy of the project and details on how to obtain an Sophos Central API key.

### Prerequisites
In order to use the package you will require a valid API key from your Sophos Central tenant. To obtain a valid API key please reference the documentation here: https://developer.sophos.com/intro

### Install
Add in some information here once this has been added to PyPI.

## Advanced Usage

### Logging
All logging is done via the naitive python `logging` library. Valid logging levels are:

- INFO
- DEBUG
- CRITICAL
- WARNING
- ERROR

For basic feedback set the logging level to `INFO`

### Configuration
The following configuration files can be changed to reflect your environment and also your needs.

#### sophos_central_api_config.py
Majority of the variables contained in this config file are to remain static in order to maintain the correct functionality of the Sophos Central API Connector. However, there are two variables which can be changed if you would like default behaviour to be different.

##### DEFAULT_OUTPUT
This variable is set to `stdout` so in the event that no output parameter is passed to the CLI then results will be returned to the console. You can change this to be another valid parameter value if desired.

##### DEFAULT_DAYS
This variable is set to `1` in the event that no days parameter is passed in certain scenarios. This default is also used for the default number of days passed for polling alert events.

#### sophos_config.ini
> #### **Important!**
> Whilst you are able to set static API credentials in this configuration we strongly advise that this is only done for testing purposes.
> Where possible use AWS Secrets Manager to store your credential id and token

You can access your AWS secrets by configuring your details as below:
- **secret_name:** \<secret_name\>
- **region_name:** \<aws_region\>
- **client_id_key:** \<specified_key_name\>
- **client_secret_key:** \<specified_key_name\>

The page size configuration is the number of events you would like to appear per page when querying the Sophos Central API. There are maximum sizes which are checked during the execution of the connector. If these are left blank they will use the default page sizes as determined by the API

#### splunk_config.ini
This config is solely for users who are sending the events and inventory directly to Splunk. There are options for both static token information or there is also an option to use the AWS Secrets Manager. 

> #### **Important!**
> We would recommend that the statiic entry is only used for testing purposes and the token is stored and accessed securely.

##### splunk_aws
To enable the use of the token from the AWS Secrets Manager set : `1`

Setting this option to `0` will allow the use of the static token entry. The 'splunk_hec' section determines the correct settings to where to send the events to Splunk

##### splunk_url
This is the URL to your Splunk instance: `http(s)://<your_splunk_url>:8088/services/collector`

Information on how to configure HEC (HTTP Event Collector) can be found at the following Splunk URL: https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector

##### splunk_ack_enabled
If you have set Splunk Index Acknowledgements when creating your HEC token, you will need to set this value to '1'. If you have not set the indexer acknowledgements to `0`. This will ensure that the correct URL is used when sending events to Splunk.

##### verify_ack_result
This is not currently in use

##### channel
If you have the index acknowledgements checked in your HEC token you will need to provide a channel GUID. These can be anything you like as long as they are unique to your HEC token environment. Further information on setting the channel and enabling Index Acknowledgements
can be found on the Splunk website: https://docs.splunk.com/Documentation/Splunk/7.3.1/Data/AboutHECIDXAck

##### ack_batch_size
This is not currently in use

##### splunk_transform
This section of the config allows you to override the details for source, host and sourcetype when the events are sent to Splunk. If this setting is not set then it will use the data that is contained in the transforms file on the indexer. This is not able to override the index that the data is sent to.

## Workflow
Put some information in here how the different functions hang together. This will give users an idea what to do if they import individual functions to their own project
