## MISP Configuration

This configuration file is to provide details for accessing your API Key for MISP.

Details on obtaining the correct URL and API Key please follow the documentation:
* [MISP URL](https://www.circl.lu/doc/misp/automation/#automation-url)
* [MISP API Key](https://www.circl.lu/doc/misp/automation/#automation-key)

We are moving away from you having the ability to place your credentials in the configuration in plain text.

You can access your AWS secrets by configuring your details as below:
- **secret_name:** \<secret_name\>
- **region_name:** \<aws_region\>
- **api_key:** \<specified_key_name\>

If no details are entered here, when running the tool you will be prompted for your details using `getpass`

Additionally set your MISP instance URL for where you will obtain your attributes with `/attributes/restSearch`
