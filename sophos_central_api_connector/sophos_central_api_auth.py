import requests
import logging
import getpass
import configparser as cp
import sophos_central_api_connector.config.sophos_central_api_config as api_conf
import sophos_central_api_connector.sophos_central_api_tenants as api_tenant
import sophos_central_api_connector.sophos_central_api_connector_utils as api_utils
import sophos_central_api_connector.sophos_central_api_awssecrets as awssecret


def ten_auth():
    sophos_conf_path = api_conf.sophos_conf_path
    sophos_final_path = api_utils.get_file_location(sophos_conf_path)

    sophos_conf = cp.ConfigParser(allow_no_value=True)
    sophos_conf.read(sophos_final_path)
    secret_name = sophos_conf.get('aws', 'secret_name')
    region_name = sophos_conf.get('aws', 'region_name')

    if secret_name and region_name:
        try:
            # Pull the credentials from AWS Secret Manager and pass to initialise Sophos Central API
            aws_secret = awssecret.get_secret(secret_name, region_name)
            client_id = aws_secret['client_id']
            client_secret = aws_secret['client_secret']
            logging.info(
                "Values have been applied to the credential variables, attempt to initialize Sophos Central API")
        except Exception as aws_exception:
            # Return the exception raised from the aws secrets script
            raise aws_exception
    else:
        logging.info("No AWS creds set in config. Requesting client_id and client_secret")
        client_id = getpass.getpass(prompt="Provide Sophos Central API Client ID: ", stream=None)
        if client_id:
            client_secret = getpass.getpass(prompt="Provide Sophos Central API Client Secret: ", stream=None)
        else:
            logging.error("No Client ID provided. Exiting")
            exit(1)

    # Set authorisation and whoami URLs
    auth_url = api_conf.auth_uri
    whoami_url = api_conf.whoami_uri
    partner_url = api_conf.tenants_ptr_uri
    organization_url = api_conf.tenants_org_uri

    # Get Sophos Central API Bearer Token for authorisation
    sophos_access_token = get_bearer_tok(client_id, client_secret, auth_url)

    # Construct id_headers
    headers = validate_id_headers(sophos_access_token)

    # Lookup up the unique ID assigned to the business entity for Sophos Central API
    whoami_id, whoami_type, whoami_data = get_whoami_data(headers, whoami_url)

    # Obtain correct whoami uri/header based on the whoami type
    header_type, tenant_url = validate_whoami_type(whoami_type, whoami_data, partner_url, organization_url)

    # Construct tenant headers
    tenant_headers = api_tenant.gen_tenant_headers(headers, whoami_id, whoami_type, header_type)

    # Check and gather tenant information
    if whoami_type == "tenant":
        tenant_info = api_tenant.type_tenant(tenant_headers, whoami_id, tenant_url, sophos_access_token)
    else:
        tenant_info = api_tenant.get_tenant_info(headers, tenant_url, sophos_access_token)

    return tenant_info


def get_bearer_tok(client_id, client_secret, auth_url):
    # Call the auth section by passing the client_id and client_secret information
    logging.info("Beginning authorisation process")
    # construct url for obtaining access_token
    logging.info("Obtaining Sophos Central API Authorisation URI")
    # set the initial header information
    logging.info("Setting basic header information for Sophos Central API")
    # set the headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data_tok = "grant_type=client_credentials&client_id={0}&client_secret={1}&scope=token".format(client_id,
                                                                                                  client_secret)

    # post the url and api key information to obtain access_token
    logging.info("Getting the bearer token for Sophos Central API")
    res = requests.post(auth_url, headers=headers, data=data_tok)
    res_code = res.status_code
    res_data = res.json()
    # Check the response and act accordingly
    if res_code == 200:
        # Send back the access token and headers
        sophos_access_token = res_data['access_token']
        logging.info("Successfully obtained the bearer token")
        return sophos_access_token
    else:
        # Failed to obtain a bearer token
        logging.error("Failed to obtain the bearer token")
        res_error_code = res_data['errorCode']
        res_message = "Response Code: {0} Message: {1}".format(res_code, res_data['message'])
        return None, res_message, res_error_code


def validate_id_headers(sophos_access_token):
    # Check whether we have a valid bearer token
    if sophos_access_token[0] is not None:
        # apply the bearer token to the headers and start getting org_id
        logging.info("Applying the bearer token to the 'Authorization' headers")
        headers = {"Authorization": "Bearer {0}".format(sophos_access_token), "Accept": "application/json"}
        return headers
    else:
        # print the response code and message along with the error code
        logging.error("There is no valid bearer token present")
        logging.error(sophos_access_token[1])
        logging.error(sophos_access_token[2])
        exit(1)


def get_whoami_data(headers, whoami_url):
    # construct the url for obtaining the organisation uuid

    # send the request to get the whoami id details
    logging.info("Attempting to get whoami ID")
    try:
        res_whoami = requests.get(whoami_url, headers=headers)
        res_whoami_code = res_whoami.status_code
        whoami_data = res_whoami.json()
    except requests.exceptions.RequestException as res_exception:
        logging.error("Failed to obtain the whoami ID")
        res_whoami_error_code = whoami_data['error']
        logging.error(res_exception)
        logging.error("Err Code: {0}, Err Detail: {1}".format(res_whoami_code, res_whoami_error_code))
        exit(1)

    # check the response code and act accordingly
    if res_whoami_code == 200:
        whoami_id = whoami_data['id']
        whoami_type = whoami_data['idType']
        logging.info("Successfully obtained whoami ID")
        return whoami_id, whoami_type, whoami_data


def validate_whoami_type(whoami_type, whoami_data, partner_url, organization_url):
    # apply the uuid to the variable and add it to the correct header type
    if whoami_type == "partner":
        logging.info("whoami type is 'partner'")
        header_type = "X-Partner-ID"
        tenant_url = partner_url
        return header_type, tenant_url
    elif whoami_type == "organization":
        logging.info("whoami type is 'organization'")
        header_type = "X-Organization-ID"
        tenant_url = organization_url
        return header_type, tenant_url
    elif whoami_type == "tenant":
        logging.info("whoami type is 'tenant'")
        header_type = "X-Tenant-ID"
        tenant_url = whoami_data['apiHosts']['dataRegion']
        return header_type, tenant_url
