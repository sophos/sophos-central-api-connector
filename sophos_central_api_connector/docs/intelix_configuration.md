## SophosLabs Intelix Configuration
> ### **Important!**
> Whilst you are able to set static API credentials in this configuration we strongly advise that this is only done for testing purposes.
> Where possible use AWS Secrets Manager to store your credential id and token
> Please reference the authentication section under advanced usage to use the correct parameter

The AWS secret credentials follows the same format as the sophos_config.ini.

There is an additional section in regards to the IP lookup categorisation. To align with the URL riskLevel we have provided the ability to set the IP categories against the risk level. The values already set
and should be reviewed and amended to prevent deleting sites incorrectly from the local sites settings in Central.