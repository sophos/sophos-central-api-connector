## Get Roles (get_roles.py)

This is based on following Sophos Central documentation page: 
https://developer.sophos.com/docs/common-v1/1/routes/roles/get

To simplify the workflow of gathering various aspects of Central this is a separate script to gather the roles from
your Sophos Central tenants. You do not need to pass parameters to run the script. However, there are some global 
variables which can be changed to adjust tenant, output.

Global variables that can be changed:
- tenant
- output

You still have control of how the data is saved:
- JSON
- STDOUT
- Splunk

The default setting is `STDOUT`, if you change the setting to `JSON` the files will be saved under the `output` folder:
```
sophos_central_api_connector
|___output
|   |___roles_data
|   |       <tenant_name>_<tenant_id>.json
|   |       ...
```

The log level can be adjusted under the main function for the variable: `log_level` to gather more granular feedback when
running the script.