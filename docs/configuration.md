## Configuration
The following configuration files can be changed to reflect your environment and also your needs.

### sophos_central_api_config.py
Majority of the variables contained in this config file are to remain static in order to maintain the correct functionality of the Sophos Central API Connector. However, there are two variables which can be changed if you would like default behaviour to be different.

#### DEFAULT_OUTPUT
This variable is set to `stdout` so in the event that no output parameter is passed to the CLI then results will be returned to the console. You can change this to be another valid parameter value if desired.

#### DEFAULT_DAYS
This variable is set to `1` in the event that no days parameter is passed in certain scenarios. This default is also used for the default number of days passed for polling alert events.

### sophos_config.ini
> #### **Important!**
> Whilst you are able to set static API credentials in this configuration we strongly advise that this is only done for testing purposes.
> Where possible use AWS Secrets Manager to store your credential id and token
> Please reference the authentication section under advanced usage to use the correct parameter

You can access your AWS secrets by configuring your details as below:
- **secret_name:** \<secret_name\>
- **region_name:** \<aws_region\>
- **client_id_key:** \<specified_key_name\>
- **client_secret_key:** \<specified_key_name\>

The page size configuration is the number of events you would like to appear per page when querying the Sophos Central API. There are maximum sizes which are checked during the execution of the connector. If these are left blank they will use the default page sizes as determined by the API