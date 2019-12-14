import logging
import argparse as ap
import configparser as cp
from re import match
from sys import exit, platform
from os import path

from sophos_central_api_connector import sophos_central_api_auth as api_auth, sophos_central_api_output as api_output, \
    sophos_central_api_get_data as get_api, sophos_central_api_polling as api_poll, \
    sophos_central_hec_splunk as splunk_hec, sophos_central_api_awssecrets as awssec, \
    sophos_central_api_connector_utils as api_utils, sophos_central_api_tenants as api_tenant
from sophos_central_api_connector.config import sophos_central_api_config as api_conf


# This will retrieve inventory information from the tenants
def get_inventory(tenant_info, output, page_size, splunk_creds=None, tenant=None):
    # Generate urls for tenants
    api = "endpoint"
    # this value is added to the splunk config setting of the sourcetype to ensure they are labelled correct
    sourcetype_value = "inventory"

    # Validate page size set
    page_size = api_utils.validate_page_size(page_size, api)

    # set poll as none as polling is not available for inventory
    poll = None

    # Generate tenant url data
    tenant_url_data = api_utils.generate_tenant_urls(tenant_info, page_size, api, from_str=None, to_str=None)

    for key, value in tenant_url_data.items():
        # If a tenant has been passed in the CLI arguements it checks whether it exists in the tenants obtained
        if tenant == key:
            # The tenant passed has been found
            tenant_url_data = {key: value}
        else:
            # tenant doesnt match
            pass

    # Generate events and send them to output
    for ten_id, ten_item in tenant_url_data.items():
        # Pass the ten_url_data and gather the alerts
        logging.info("Attempting to get inventory information")
        tenant_id = ten_id
        # get data information for the tenant in the loop
        json_data = get_api.get_data(tenant_url_data, page_size, tenant_id, api)
        # process data by the output parameter
        events = api_output.process_output(output, json_data, tenant_url_data, tenant_id, api, sourcetype_value)

        if output == "splunk" or output == "splunk_trans":
            logging.info("Passing inventory to Splunk")
            # splunk argument passed, send the data to splunk
            splunk_hec.send_to_splunk(api, events, splunk_creds, sourcetype_value, tenant_id, from_str=None, to_str=None,
                                      alerts_exists=None, temp_exists=None, alertids_exists=None, poll=None)
            # Completed gathering data for this tenant
            logging.info("Completed processing for Tenant ID: {0}".format(tenant_id))
        else:
            pass
    else:
        # Completed gathering data for this tenant
        logging.info("Completed processing for Tenant ID: {0}".format(tenant_id))

    logging.info("Gathering inventory data complete")
    exit(0)


# this will retrieve alert information from the tenants
def get_alerts(tenant_info, output, poll, days, reset_flag, page_size, splunk_creds, tenant=None):
    # Set the type of api this is using
    api = "common"
    sourcetype_value = "alerts"

    # Validate page size set
    page_size = api_utils.validate_page_size(page_size, api)

    # Check if the polling log is available
    alerts_exists = path.isfile('sophos_central_api_connector/polling/poll_config.json')
    alertids_exists = path.isfile('sophos_central_api_connector/polling/alert_ids.json')
    temp_exists = path.isfile('sophos_central_api_connector/polling/temp_alert_ids.json')

    # If the number of days to check is set to None it will set the value to the default number of days: 1
    # It will also set the days_flag to False in order to validate args when checking polling in alerts
    if days is not None and alerts_exists is True and reset_flag is True:
        # Criteria has been met to use the day_flag for resetting polling
        day_flag = True
        logging.info("Reset flag passed with days and poll")
    elif days > 1 or alerts_exists is True:
        # defaults the days to 1
        days = 1
        day_flag = False
    else:
        # sets the day flag
        day_flag = True

    # Checks whether the polling arguement has been passed in order to calculate the to and from strings
    if poll:
        # Polling arguement has been passed
        if output == "json" or output == "stdout":
            # Will error is output is json or stdout. Only accepts splunk or splunk_trans
            logging.error("Polling not available for the output: {0}".format(output))
            exit(1)
        else:
            logging.info("Polling has been set")
            # splunk or splunk_trans has been passed. Pass the information to the polling alerts function
            to_str, from_str, reset_flag = api_poll.polling_alerts(alerts_exists, temp_exists, reset_flag, day_flag,
                                                                   days)
    else:
        logging.info("No polling passed")
        # No polling has been set so calulate from and to strings normally
        to_str, from_str = api_utils.calculate_from_to(days, poll_date=None)

    # Generate urls for tenants
    tenant_url_data = api_utils.generate_tenant_urls(tenant_info, page_size, api, from_str, to_str)

    for key, value in tenant_url_data.items():
        # If a tenant has been passed in the CLI arguements it checks whether it exists in the tenants obtained
        if tenant == key:
            # The tenant passed has been found
            tenant_url_data = {key: value}
        else:
            # Does not match tenant data
            pass

    for ten_id, ten_item in tenant_url_data.items():
        # Pass the ten_url_data and gather the alerts
        logging.info("Attempting to get alert information for tenant: {0}".format(ten_id))
        tenant_id = ten_id
        # Send the data to get data to gather the events
        json_data = get_api.get_data(tenant_url_data, page_size, tenant_id, api)
        if len(json_data) > 0:
            # There are events to process. Send to check the output
            events = api_output.process_output(output, json_data, tenant_url_data, tenant_id, api,
                                               sourcetype_value)
            if output == "splunk" or output == "splunk_trans":
                # output parameter has been passed with splunk or splunk_trans
                logging.info("Splunk output selected. Send events")
                # pass the event data to the HEC script to be processed and sent to Splunk
                splunk_hec.send_to_splunk(api, events, splunk_creds, sourcetype_value, tenant_id,
                                                                  from_str, to_str, alerts_exists, temp_exists,
                                                                  alertids_exists, poll)
                logging.info("Completed processing for Tenant ID: {0}".format(tenant_id))
            else:
                pass
    else:
        # No further data to process for the tenant
        logging.info("Completed processing for Tenant ID: {0}".format(tenant_id))

    if poll:
        #If the polling parameter has been passed need to finalise the config and events
        api_poll.finalise_polling(poll, to_str)

    logging.info("Gathering alert data complete")
    exit(0)


def print_tenant_info(tenant_info):
    logging.info("Printing out tenant information")
    print("\nYour tenant information is as follows:\n")
    # loop through each of the tenants and print its information to stdout
    for ten_id, ten_item in tenant_info.items():
        ten_name = ten_item['name']
        print("Tenant Name: {0}\nTenantID: {1}\n".format(ten_name, ten_id))
    exit(0)


def get_splunk_creds(splunk_final_path):
    # Initially set the Splunk flag and Splunk creds to None.
    splunk_aws_flag = None
    splunk_creds = None

    # load and read the splunk config
    logging.info("Reading Splunk configuration information")
    splunk_conf = cp.ConfigParser(allow_no_value=True)
    splunk_conf.read(splunk_final_path)
    splunk_use_aws = splunk_conf.get('splunk_aws', 'splunk_aws')
    splunk_ack_enabled = splunk_conf.get('splunk_hec', 'splunk_ack_enabled')
    splunk_verify_ack = splunk_conf.get('splunk_hec', 'verify_ack_result')

    # check authentication method
    logging.info("Splunk output has been set")
    if splunk_use_aws == "1":
        logging.info("Config setting set to use Splunk creds from AWS Secrets Manager")
        # Confirm that the check indexer acknowledgement has not been set without the config for ack_enabled being 0
        if splunk_verify_ack == "1" and splunk_ack_enabled == "0":
            logging.error(
                "To verify Splunk Index Acknowledgements, you must set the config 'splunk_ack_enabled' to '1'")
            exit(1)
        else:
            # Apply the splunk aws settings to variables in order to get aws secret information
            logging.info("Flag set to pull HEC token from AWS Secrets Manager. Getting config settings")
            token_key = splunk_conf.get('splunk_aws', 'token_key')
            secret_name = splunk_conf.get('splunk_aws', 'secret_name')
            region_name = splunk_conf.get('splunk_aws', 'region_name')
            # verify that the config is valid
            try:
                # Pull the credentials from AWS Secret Manager and add to splunk_creds variable
                logging.info("Attempting to get Splunk HEC token from AWS")
                aws_secret = awssec.get_secret(secret_name, region_name)
                splunk_token = aws_secret[token_key]
                # Verify that the token matches expected format
                aws_token_match = match(r"{0}".format(api_conf.uuid_regex), splunk_token)
                if aws_token_match is None:
                    # An exception will be raised if the token does not match the correct format
                    logging.error("Please ensure you have a valid HEC token in your AWS Secrets Manager")
                    exit(1)
                else:
                    logging.info("HEC token is in a valid format")
                    #splunk_creds = {'tok': '{0}'.format(splunk_token)}
                    splunk_creds = splunk_token
                    return splunk_creds
            except Exception("AWSException") as aws_exception:
                raise aws_exception
    elif splunk_use_aws == "0":
        logging.info("Config setting set to use static Splunk HEC token from config")
        logging.info("Getting static credentials for Splunk HEC from config")
        splunk_static_tok = splunk_conf.get('splunk_static', 'token')
        logging.info("Verying token passed is in the correct format")
        token_match = match(r"{0}".format(api_conf.uuid_regex), splunk_static_tok)
        # verify that the value in the static Splunk HEC token is valid
        if token_match is None:
            logging.error("Please ensure you have a valid HEC token in the splunk_config.ini")
            exit(1)
        else:
            logging.info("Token is in the correct format")
            splunk_creds = {'tok': '{0}'.format(splunk_static_tok)}
            return splunk_creds


def get_sophos_creds(sophos_auth, sophos_final_path):
    # load and read the sophos config file
    sophos_conf = cp.ConfigParser(allow_no_value=True)
    sophos_conf.read(sophos_final_path)

    if sophos_auth == "static":
        # Auth is static so the creds are pulled from the config
        logging.info("Static API credentials parameter, has been passed. Getting value from config")
        client_id = sophos_conf.get('static', 'client_id')
        client_secret = sophos_conf.get('static', 'client_secret')
        if client_secret is None or client_id is None:
            # verifies that there is something in the variable
            logging.info("Please verify the static credentials are valid in config.ini")
        else:
            logging.info("Values have been applied to the credential variables")
            return client_id, client_secret
    elif sophos_auth == "aws":
        # Creds are held in AWS, gather the config information
        logging.info("Attempting to get Sophos Central API credentials from AWS Secrets Manager")
        client_id_key = sophos_conf.get('aws', 'client_id_key')
        client_secret_key = sophos_conf.get('aws', 'client_secret_key')
        secret_name = sophos_conf.get('aws', 'secret_name')
        region_name = sophos_conf.get('aws', 'region_name')
        try:
            # Pull the credentials from AWS Secret Manager and pass to initialise Sophos Central API
            aws_secret = awssec.get_secret(secret_name, region_name)
            client_id = aws_secret[client_id_key]
            client_secret = aws_secret[client_secret_key]
            logging.info(
                "Values have been applied to the credential variables, attempt to initialize Sophos Central API")
            return client_id, client_secret
        except Exception as aws_exception:
            # Return the exception raised from the aws secrets script
            raise aws_exception
    else:
        # Invalid auth parameter has been passed
        logging.error(
            "No authentication or an incorrect authentication method has been specified.\nPlease run --help for "
            "further information")


def get_file_location(process_path):
    dir_name = path.dirname(__file__)
    final_path = "{0}{1}".format(dir_name,process_path)
    return final_path


def main(args):
    # Assign parameters to variables
    log_level = args.log_level
    output = args.output
    days = args.days
    sophos_auth = args.auth
    poll = args.poll_alerts
    reset_flag = args.reset
    get = args.get
    tenant = args.tenant
    splunk_conf_path = api_conf.splunk_conf_path
    splunk_final_path = get_file_location(splunk_conf_path)
    sophos_conf_path = api_conf.sophos_conf_path
    sophos_final_path = get_file_location(sophos_conf_path)

    # Set authorisation and whoami URLs
    auth_url = api_conf.auth_uri
    whoami_url = api_conf.whoami_uri
    partner_url = api_conf.tenants_ptr_uri
    organization_url = api_conf.tenants_org_uri

    # Get sophos config
    sophos_conf = cp.ConfigParser(allow_no_value=True)
    sophos_conf.read(sophos_final_path)

    # Set the level of the handler based on the value passed by the parameter
    if log_level is None:
        logging.disable(True)
    else:
        logging.disable(False)
        log_name = log_level
        level = getattr(logging, log_name)
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%d/%m/%Y %I:%M:%S %p')

    logging.info("Start of logging")

    # Get Sophos Central API Creds and check for Splunk Creds if required
    client_id, client_secret = get_sophos_creds(sophos_auth, sophos_final_path)

    # Get Splunk credentials if required
    splunk_creds = None
    if output == "splunk" or output == "splunk_trans":
        splunk_creds = get_splunk_creds(splunk_final_path)

    # Get Sophos Central API Bearer Token for authorisation
    sophos_access_token = api_auth.get_bearer_tok(client_id, client_secret, auth_url)

    # Construct id_headers
    headers = api_auth.validate_id_headers(sophos_access_token)

    # Lookup up the unique ID assigned to the business entity for Sophos Central API
    whoami_id, whoami_type, whoami_data = api_auth.get_whoami_data(headers, whoami_url)

    # Obtain correct whoami uri/header based on the whoami type
    header_type, tenant_url = api_auth.validate_whoami_type(whoami_type, whoami_data, partner_url, organization_url)

    # Construct tenant headers
    tenant_headers = api_tenant.gen_tenant_headers(headers, whoami_id, whoami_type, header_type)

    # Check and gather tenant information
    if whoami_type == "tenant":
        tenant_info = api_tenant.type_tenant(tenant_headers, whoami_id, tenant_url, sophos_access_token)
    else:
        logging.info("Gather tenant information")
        tenant_info = api_tenant.get_tenant_info(headers, tenant_url, sophos_access_token)

    # Check which get parameter was passed and get that data
    logging.info("Check which parameters have been passed to main.")
    if get == "tenants":
        print_tenant_info(tenant_info)
    elif get == "inventory":
        logging.info("Inventory parameter passed.")
        logging.info("Checking page sizes passed through config")
        page_size = sophos_conf.get('page_size', 'inventory_ps')
        # begin the process to gather inventory information
        get_inventory(tenant_info, output, page_size, splunk_creds, tenant)
    elif get == "alerts":
        logging.info("Alerts parameter passed.")
        page_size = sophos_conf.get('page_size', 'alerts_ps')
        # begin the process to gather alert information
        get_alerts(tenant_info, output, poll, days, reset_flag, page_size, splunk_creds, tenant)
    else:
        # invalid get parameter has been passed
        logging.error("Invalid --get parameter passed")
        exit(1)

    exit(0)


# this is executed if the script is called from the command line.
if __name__ == "__main__":

    # Parse the various parameters to be used when calling the main script.
    parser = ap.ArgumentParser(formatter_class=ap.RawTextHelpFormatter,
                               description="sophos_central_main.py:\n\nThis script utilises the Sophos Central API. "
                                           "In order to use the script you\nwill require a valid API key. To obtain a "
                                           "valid API key please reference\nthe documentation here: "
                                           "https://developer.sophos.com/intro")
    parser.add_argument('-a', '--auth', choices=['static', 'aws'], required=True,
                        help="This is a required option to specify which auth method to use.")
    parser.add_argument('-g', '--get', choices=['inventory', 'alerts', 'tenants'],
                        help="This will set what information to get from tenants")
    parser.add_argument('-t', '--tenant',
                        help="Allows to specify one tenant\nIf this argument is not specified all tenants will apply.")
    parser.add_argument('-o', '--output', choices=['stdout', 'json', 'splunk', 'splunk_trans'], default="stdout",
                        help="Allows you to specify an output method for the data retrieved. If no option is selected"
                        "it will default to stdout.")
    parser.add_argument('-pa', '--poll_alerts', action='store_true',
                        help="N.B. This parameter only works with the '--get alerts' parameter:\nCalling this "
                             "parameter will set the value to true, in doing so it will maintain a config of when the "
                             "last\nquery was run and when it is next run will use this\ninformation to set the "
                             "relevant from flag to continue getting alerts from that point.")
    parser.add_argument('-d', '--days', type=int, choices=range(1, 91), default=1,
                        help="This is the number of days to go back and gather. Min is 1 and max number of days is 90.")
    parser.add_argument('-r', '--reset', action='store_true',
                        help="Setting this flag with the poll_alerts and days flags will reset the poll config")
    parser.add_argument('-ll', '--log_level', choices=['INFO', 'DEBUG', 'CRITICAL', 'WARNING', 'ERROR'],
                        help="Set logging level mode for more detailed error information, default is disabled")

    # parse the argument values to the arg variable
    args = parser.parse_args()

    # Go to main with the arguments
    main(args)
