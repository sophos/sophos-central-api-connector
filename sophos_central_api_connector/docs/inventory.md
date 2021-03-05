## Endpoint Information

Gathering the inventory information can be done for all of your tenants or one specific tenant. There are various methods on how this data can be presented. The output methods are stdout, json or sending the data to Splunk. More detailed example are covered under the Advanced Usage section.

There are various products which can utilise data from stdout such as running a script in Splunk and indexing the data dynamically. Also this can be used as a response in automation to provide further details on a systems health etc.

The syntax to use when requesting to get inventory is the following:
```python
python sophos_central_main.py --auth <auth_option> --get inventory --output <output_option>
```