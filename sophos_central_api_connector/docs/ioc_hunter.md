## IOC Hunter

The IOC Hunter script provides the ability to search your estate for IOCs using variables. This is available for both Live Discover and XDR DataLake!

Follow the instructions [here](https://docs.sophos.com/central/Customer/help/en-us/central/Customer/learningContents/LiveDiscover.html) to create a custom query from the ioc_hunter.sql file for the perspective method.

### Logging
All logging is done via the python `logging` library. Pass the switch `--log_level` or `-ll`

Valid logging levels are:

- INFO
- DEBUG
- CRITICAL
- WARNING
- ERROR

For basic feedback set the logging level to `INFO`. No logging returned if the `--log_level` parameter is not passed

### Authentication
Providing no authentication parameter will result in being prompted during the running of the script.

### Usage
To obtain help information on how to call the various commands run the following:
```commandline
ioc_hunter.py --help
```

Using the IOC Hunter you can search for IOCs by either:
* Passing RAW JSON in arguments
* MISP attributes (eventIds or tags)
    * Follow the MISP Configuration documents to utilise this feature [here](https://github.com/sophos-cybersecurity/sophos-central-api-connector/blob/master/sophos_central_api_connector/docs/misp_configuration.md)

By passing MISP attributes the JSON is automatically generated to work with the saved query.

Passing RAW JSON requires the correct schema in order to be parsed by the Live Discover query. 
The correct schema is as follows:
```json
{   "ioc_data": [
      {
        "indicator_type": "<type>",
        "data": "<ioc_data>"
      }
    ]
}
```

The two arguments that need prior setup are:
* filter: This determines which systems the saved query will run on (LiveDiscover ONLY)
* variables: These are the variables that the saved query is expecting

### Filter (LiveDiscover)
For the filter argument the skeleton of the schema is already in place. You just need to provide the filter details. Below are some examples.

When passing the argument you need to escape the quotes

#### Specific endpoints
To run the query on specific systems you can pass the following in the `--filter` argument:
```commandline
--filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

#### Windows platform
```commandline
--filter "{\"os\": [{\"platform\": \"windows\"}]}"
```

You can build these filters using the schema [here](https://developer.sophos.com/docs/live-discover-v1/1/routes/queries/runs/post)

### Variables
LiveDiscover and XDR DataLake take slightly different variables. LiveDiscover expects 3, whereas XDR only expects 1.

#### LiveDiscover
* Number of Hours of activity to search
  * Be conscious how wide this is set. If the span is too wide the query may be terminated
* IOC JSON
  * If you are using MISP attributes you can simply enter `%`
  * Follow the schema above when passing RAW JSON in this variable
* Start Search From
  * This follows the format: `%Y-%m-%dT%H:%M:%S`
  
#### XDR DataLake
* IOC JSON
  * Follow the schema above when passing RAW JSON in this variable

The values in the saved search will be used if no variables are passed

### Examples
Below are some example commands to begin searching your estate

#### LiveDiscover

List queries from tenants to stdout
```commandline
ioc_hunter.py --api ld --search_type list
```

Outputting query list to JSON
```commandline
ioc_hunter.py --api ld --search_type list --output json
```

Hunt using a MISP eventId
```commandline
ioc_hunter.py --api ld --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 % 2021-03-01T00:00:00 --misp true --misp_type eventid --misp_val int
```

Hunt using a MISP tag
```commandline
ioc_hunter.py --api ld --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 % 2021-03-01T00:00:00 --misp true --misp_type tag --misp_val str
```

Hunt using a search with no variables
```commandline
ioc_hunter.py --api ld --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

Hunt using a RAW JSON
```commandline
ioc_hunter.py --api ld --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 "{   \"ioc_data\": [     {       \"indicator_type\": \"url\",       \"data\": \"%sophos.com%\"     },     {       \"indicator_type\": \"ip\",       \"data\": \"%192.%\"     },     {       \"indicator_type\": \"filepath\",       \"data\": \"C:\\Windows\\System32\\%\"     }   ] }" 2021-03-01T00:00:00
```

Running standard saved search
```commandline
ioc_hunter.py --api ld --search_type saved --search_input "CPU information" --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

#### XDR DataLake

List queries from tenants to stdout
```commandline
ioc_hunter.py --api xdr --search_type list
```

Outputting query list to JSON
```commandline
ioc_hunter.py --api xdr --search_type list --output json
```

Hunt using a MISP eventId
```commandline
ioc_hunter.py --api xdr --search_type saved --search_input IOC_Hunter --misp true --misp_type eventid --misp_val <int>
```

Hunt using a MISP tag
```commandline
ioc_hunter.py --api xdr --search_type saved --search_input IOC_Hunter --misp true --misp_type tag --misp_val <str>
```

Hunt using a search with no variables
```commandline
ioc_hunter.py --api xdr --search_type saved --search_input IOC_Hunter
```

Hunt using a RAW JSON
```commandline
ioc_hunter.py --api xdr --search_type saved --search_input IOC_Hunter --variables "{   \"ioc_data\": [     {       \"indicator_type\": \"url\",       \"data\": \"%sophos.com%\"     },     {       \"indicator_type\": \"ip\",       \"data\": \"%192.%\"     },     {       \"indicator_type\": \"filepath\",       \"data\": \"C:\\Windows\\System32\\%\"     }   ] }"
```

Running standard saved search
```commandline
ioc_hunter.py --api xdr --search_type saved --search_input "BitLocker info"
```

### Output
When running the LiveDiscover API three JSON files will be put into the query folder, whereas two for XDR API:

#### LiveDiscover & XDR
* <api>_result_data_<timestamp>.json
  * This contains any hits on the IOCs or provides details on the outcome of the saved search run 
* <api>_search_data_<timestamp>.json
  * This contains details on the search run and on which tenants. It contains information on the overall outcome of the search
  
#### LiveDiscover
* <api>_endpoint_data_<timestamp>.json
  * This contains details on the endpoints that the query was run on 
