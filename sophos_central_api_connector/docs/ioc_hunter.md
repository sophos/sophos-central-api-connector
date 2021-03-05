## IOC Hunter

The IOC Hunter script is to provide the ability to search your estate for IOCs by providing variable details and search filter.

Currently this is only for saved searches in Live Discover. Follow the instructions [here](https://docs.sophos.com/central/Customer/help/en-us/central/Customer/learningContents/LiveDiscover.html#id_e5z_5v1_2lb) to create a custom query from the ioc_hunter.sql file

### Authentication
We are moving away from you having the ability to place your credentials in the configuration in plain text. If nothing is set you will be prompted during the running of the script

### Usage
To obtain help information on how to call the various commands run the following:
```python
ioc_hunter.py --help
```

Using the IOC Hunter you can search for IOCs by either:
* Passing RAW JSON in arguments
* MISP attributes (eventIds or tags)
    * Follow the MISP Configuration documents to utilise this feature [here](https://github.com/sophos-cybersecurity/sophos-central-api-connector/blob/master/sophos_central_api_connector/docs/misp_configuration.md)

By passing MISP attributes the JSON is automatically generated to work with the saved query in Live Discover.

If you are passing RAW JSON it must have the correct schema in order to be parsed by the Live Discover query. 
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
filter: This determines which systems the saved query will run on
variables: These are the variables that the saved query is expecting

### Filter
For the filter argument the skeleton of the schema is already in place. You just need to provide the filter details. Below are some examples.
When passing the argument you need to escape the quotes

#### Specific endpoints
To run the query on specific systems you can pass the following in the `--filter` argument:
```python
--filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

#### Windows platform
```python
--filter "{\"os\": [{\"platform\": \"windows\"}]}"
```

You can build these filters using the schema [here](https://developer.sophos.com/docs/live-discover-v1/1/routes/queries/runs/post)

### Variables
These are the variables which are used in the SQLite query in Live Discover to query the endpoints. The variables are:
* Number of Hours of activity to search
  * Be conscious how wide this is set. If the span is too wide the query may be terminated
* IOC JSON
  * If you are using MISP attributes you can simply enter `%`
  * Follow the schema above when passing RAW JSON in this variable
* Start Search From
  * This follows the format: `%Y-%m-%dT%H:%M:%S`

If no variables are passed the values in the saved search will be used.

### Examples
Below are some example commands to begin searching your estate

List queries from tenants
```python
ioc_hunter.py --search_type list
```

Hunt using a MISP eventId
```python
ioc_hunter.py --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 % 2021-03-01T00:00:00 --misp true --misp_type eventid --misp_val int
```

Hunt using a MISP tag
```python
ioc_hunter.py --search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 % 2021-03-01T00:00:00 --misp true --misp_type tag --misp_val str
```

Hunt using a search with no variables
```python
--search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

Hunt using a RAW JSON
```python
--search_type saved --search_input IOC_Hunter --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}" --variables 24 "{   \"ioc_data\": [     {       \"indicator_type\": \"url\",       \"data\": \"%sophos.com%\"     },     {       \"indicator_type\": \"ip\",       \"data\": \"%192.%\"     },     {       \"indicator_type\": \"filepath\",       \"data\": \"C:\\Windows\\System32\\%\"     }   ] }" 2021-03-01T00:00:00
```

Running standard saved search
```python
--search_type saved --search_input "CPU information" --filter "{\"ids\": [\"74125749-6a48-48e1-bf41-243b227e444c\"]}"
```

### Output
Once the searches have completed three JSON files will be put into a tmp folder:
* endpoint_data.json
  * This contains details on the endpoints that the query was run on 
* result_data.json
  * This contains any hits on the IOCs or provides details on the outcome of the saved search run 
* search_data.json
  * This contains details on the search run and on which tenants. It contains information on the overall outcome of the search
