## Local Site Information

You can review the sites which have been added to Global Settings > Website Management using the API.

As with previous abilities you can pull the sites for a specific tenant or for all tenants for review. It will automatically reference
the category integer to a human readable category. This can be output to all the available options.
```python
python sophos_central_main.py --auth <auth_option> --get local-sites --output <output_option>
```