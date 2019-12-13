import requests
import logging


def get_bearer_tok(client_id, client_secret, auth_url):
    # Call the auth section by passing the client_id and client_secret information
    logging.info("Beginning authorization process")
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
