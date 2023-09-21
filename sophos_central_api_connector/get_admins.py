import logging
from sophos_central_api_connector import sophos_central_api_auth as api_auth
from sophos_central_api_connector import sophos_central_api_awssecrets as awssecret
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils
from sophos_central_api_connector import sophos_central_api_get_data as get_api
from sophos_central_api_connector import sophos_central_api_output as api_output


# Global variables
page_size = "50" #change in line with documentation
api = "admins" #do not change
tenant = None
output = "stdout"
sourcetype_value = None



def get_admins(tenant_url_data, output, page_size, tenant):
    # Validate page size set
    page_size = api_utils.validate_page_size(page_size, api)

    # Generate events and send them to output
    for ten_id, ten_item in tenant_url_data.items():
        # Pass the ten_url_data and gather the alerts
        logging.info("Attempting to get admin information")
        tenant_id = ten_id
        # get data information for the tenant in the loop
        json_data = get_api.get_data(tenant_url_data, page_size, tenant_id, api)
        # process data by the output parameter
        events = api_output.process_output(output, json_data, tenant_url_data, tenant_id, api, sourcetype_value)
    else:
        # Completed gathering data for this tenant
        logging.info("Completed processing for Tenant ID: {0}".format(tenant_id))


def main():
    log_level="INFO"
    if log_level is None:
        logging.disable(True)
    else:
        logging.disable(False)
        log_name = log_level
        level = getattr(logging, log_name)
        log_fmt = '%(asctime)s: [%(levelname)s]: %(message)s'
        logging.basicConfig(level=level, format=log_fmt, datefmt='%d/%m/%Y %I:%M:%S %p')

    logging.info("Start of Logging")

    # Auth and get tenant information
    tenant_info = api_auth.ten_auth()

    # Generate tenant url data
    tenant_url_data = api_utils.generate_tenant_urls(tenant_info, page_size, api, from_str=None, to_str=None)

    for key, value in tenant_url_data.items():
        # If a tenant has been passed in the CLI arguments it checks whether it exists in the tenants obtained
        if tenant == key:
            # The tenant passed has been found
            logging.info("Tenant ID passed: '{0}'".format(key))
            tenant_url_data = {key: value}
        else:
            pass

    get_admins(tenant_url_data, output, page_size, tenant)

    logging.info("Script complete")
    exit(0)


if __name__ == "__main__":
    main()