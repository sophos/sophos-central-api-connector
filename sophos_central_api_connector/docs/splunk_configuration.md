## Splunk Configuration
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