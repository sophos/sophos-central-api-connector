import requests
import logging


def gen_tenant_headers(headers, whoami_id, whoami_type, header_type):
    # Check whether we have received a valid uuid
    if whoami_id is not None:
        logging.info("Applying the uuid to the header")
        # Apply the uuid to the variable and add it to the correct header
        headers[header_type] = whoami_id
        if whoami_type == "tenant":
            # the type is tenant so just return the data to gather the events
            logging.info("uuid is tenant only. Applying to the tenant headers")
            logging.info("Skipping collecting further information on the tenant ids")
            tenant_headers = {"{0}".format(header_type): "{0}".format(whoami_id)}
            return tenant_headers
        else:
            # return that the type is not tenant so the tenant information can be gathered
            tenant_headers = None
            return tenant_headers
    else:
        # Return the response code and error information and exit the script
        logging.error("Response Code: {0} Error Code: {1}".format(whoami_type, header_type))
        exit(1)


# This function will get the page total and pass the data to get_page function to gather the tenant information
def get_tenant_info(headers, tenant_url, sophos_access_token):
    # Get the total number of pages
    page_total_url = "{0}{1}".format(tenant_url, "?pageTotal=true")
    res_tenant = requests.get(page_total_url, headers=headers)
    res_tenant_code = res_tenant.status_code
    tenant_data = res_tenant.json()

    # Check the response and if good pass to get_page
    if res_tenant_code == 200:
        logging.info("Total tenant page information gathered")
        tenant_page_total = tenant_data['pages']['total']
        tenant_info = dict()
        # Call get_page function
        get_next_page(tenant_url, headers, tenant_page_total, sophos_access_token, tenant_info)
        return tenant_info
    else:
        # If the connection is not successful then pass back errors
        logging.error("Failed to get tenant information")
        res_tenant_error_code = tenant_data['error']
        return None, res_tenant_code, res_tenant_error_code


def get_next_page(tenant_url, headers, tenant_page_total, sophos_access_token, tenant_info):
    # This function constructs the url to gather pages of tenant information
    next_page = 1
    paged_url = "{0}{1}{2}".format(tenant_url, "?page=", next_page)
    # while page_url is not null it will calculate the next page and append tenant info to tenant_list
    while paged_url:
        res_tenant = requests.get(paged_url, headers=headers)
        tenant_data = res_tenant.json()
        # from the tenant data construct the headers to connect to the correct api url
        for item in tenant_data['items']:
            tenant_id = "{0}".format(item['id'])
            tenant_headers = {"X-Tenant-ID": tenant_id, "Authorization": "Bearer {0}".format(sophos_access_token),
                              "Accept": "application/json"}
            tenant_item = {item['id']: {"name": item['name'], "headers": tenant_headers, "page_url": item['apiHost']}}
            tenant_info.update(tenant_item)

        next_page += 1
        # checks if the next_page value is less than or equal to total pages. If so create next url for pass
        if next_page <= tenant_page_total:
            paged_url = "{0}{1}{2}".format(tenant_url, "?page=", next_page)
        else:
            paged_url = False


def type_tenant(tenant_headers, whoami_id, tenant_url, sophos_access_token):
    # Creates a tenant object if the whoami is solely a tenant object. This will not construct headers for Partner or
    # Organisation
    tenant_headers["Authorization"] = "Bearer {0}".format(sophos_access_token)
    tenant_headers["Accept"] = "application/json"
    tenant_info = {whoami_id: {"name": "tenant", "headers": tenant_headers, "page_url": tenant_url}}
    return tenant_info
