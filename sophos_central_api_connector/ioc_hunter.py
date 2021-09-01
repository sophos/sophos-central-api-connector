import datetime
import logging
import getpass
import json
import argparse as ap
import re
import configparser as cp
from sys import getsizeof
from sophos_central_api_connector import sophos_central_api_auth as api_auth
from sophos_central_api_connector import sophos_central_api_awssecrets as awssecret
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils
from sophos_central_api_connector.config import sophos_central_api_config as api_conf
from sophos_central_api_connector import sophos_central_api_output as api_output
from sophos_central_api_connector import sophos_central_api_live_discover as sld


# Global variables
page_size = "250"


def main(params):
    # set params to variables
    log_level = params.log_level
    tenant = params.tenant
    search_filter = params.filter
    search_variables = params.variables
    search_type = params.search_type
    search_val = params.search_input
    misp_attr = params.misp
    api = params.api
    output = params.output

    if log_level is None:
        logging.disable(True)
    else:
        logging.disable(False)
        log_name = log_level
        level = getattr(logging, log_name)
        log_fmt = '%(asctime)s: [%(levelname)s]: %(message)s'
        logging.basicConfig(level=level, format=log_fmt, datefmt='%d/%m/%Y %I:%M:%S %p')

    logging.info("Start of Logging")

    if api == "ld":
        api = "live-discover"
    elif api == "xdr":
        api = "xdr-datalake"
    else:
        logging.error("No api passed, exiting")
        exit(1)

    if misp_attr:
        misp_conf_path = api_conf.misp_conf_path
        misp_final_path = api_utils.get_file_location(misp_conf_path)

        misp_conf = cp.ConfigParser(allow_no_value=True)
        misp_conf.read(misp_final_path)
        secret_name = misp_conf.get('aws', 'secret_name')
        region_name = misp_conf.get('aws', 'region_name')
        misp_tok = misp_conf.get('aws', 'api_key')
        misp_url = misp_conf.get('url', 'misp_instance')

        # Get attributes for iocs to search
        misp_type = params.misp_type
        misp_val = params.misp_val

        if not misp_type or not misp_val:
            logging.error("You must specify a MISP type and value")
            exit(1)
        else:
            pass

        if misp_tok:
            try:
                # Pull the credentials from AWS Secret Manager and pass to initialise misp
                misp_secret = awssecret.get_secret(secret_name, region_name)
                misp_tok = misp_secret['{0}'.format(misp_tok)]
                logging.info("MISP auth token applied")
            except Exception as aws_exception:
                # Return the exception raised from the aws secrets script
                raise aws_exception
            finally:
                attributes = sld.get_misp_attributes(misp_url, misp_type, misp_val, misp_tok, wildcard=True)
        else:
            logging.info("No AWS creds set in config. Requesting MISP API token")
            misp_tok = getpass.getpass(prompt="Provide MISP token: ", stream=None)
            if misp_tok:
                attributes = sld.get_misp_attributes(misp_url, misp_type, misp_val, misp_tok, wildcard=True)
            else:
                logging.error("No MISP token provided. Exiting")
                exit(1)

        if not attributes:
            logging.critical("No attributes found, exiting")
            exit(1)
        else:
            logging.info("MISP attributes obtained")

            pass
    else:
        pass

    # format the filter variable to remove escape characters and pass as json
    if search_filter:
        try:
            search_filter = json.loads(re.sub('[\\?]', '', search_filter))
        except ValueError as err:
            logging.error("JSON malformed: {0}".format(search_filter))
            raise err
        else:
            pass
    elif search_type == "list":
        pass
    elif api == "xdr-datalake":
        pass
    else:
        logging.critical("No filter passed, A filter must be provided")
        exit(1)

    if (search_variables and misp_attr) or (misp_attr and api == "xdr-datalake"):
        if api == "live-discover":
            # Format the search date
            date_frmt = "{0}.000Z".format(search_variables[2])
        else:
            pass

        # estimated size of variables
        ioc_size = getsizeof(attributes)
        if ioc_size < 1 or ioc_size > 5000:
            logging.critical(
                "Size of IOC JSON must be in the range of 1 - 5000. Current estimated size is: {0}".format(ioc_size))
            exit(1)
        else:
            pass

        # Build JSON
        if api == "live-discover":
            variables_json = [
                {
                    "name": "Number of Hours of activity to search",
                    "dataType": "text",
                    "value": "{0}".format(search_variables[0])
                },
                {
                    "name": "IOC JSON",
                    "dataType": "text",
                    "value": attributes
                },
                {
                    "name": "Start Search From",
                    "dataType": "dateTime",
                    "value": "{0}".format(date_frmt)
                }
            ]
        elif api == "xdr-datalake":
            variables_json = [
                {
                    "name": "IOC_JSON",
                    "dataType": "text",
                    "value": attributes
                }
            ]
    elif search_variables:
        if api == "live-discover":
            # Format the search date
            date_frmt = "{0}.000Z".format(search_variables[2])
        else:
            pass

        # esitmated size of variables
        ioc_size = getsizeof(search_variables)
        if ioc_size < 1 or ioc_size > 5000:
            logging.critical(
                "Size of IOC JSON must be in the range of 1 - 5000. Current estimated size is: {0}".format(ioc_size))
            exit(1)
        else:
            pass

        # Build JSON
        if api == "live-discover":
            variables_json = [
                {
                    "name": "Number of Hours of activity to search",
                    "dataType": "text",
                    "value": "{0}".format(search_variables[0])
                },
                {
                    "name": "IOC JSON",
                    "dataType": "text",
                    "value": search_variables[1]
                },
                {
                    "name": "Start Search From",
                    "dataType": "dateTime",
                    "value": "{0}".format(date_frmt)
                }
            ]
        elif api == "xdr-datalake":
            variables_json = [
                {
                    "name": "IOC_JSON",
                    "dataType": "text",
                    "value": search_variables[0]
                }
            ]
    else:
        logging.info("No variables passed")
        variables_json = None

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

    # kick off live discover search
    if search_type == "list":
        query_data = sld.live_discover(tenant_url_data, search_type, search_val, search_filter, variables_json, api)
        if output == 'json':
            api_output.process_output_json(query_data, "{0}_query_list.json".format(api), api)
        else:
            for key, value in query_data.items():
                print(json.dumps(value, indent=2))
    else:
        ld_data, ep_data, res_data = sld.live_discover(tenant_url_data, search_type, search_val, search_filter,
                                                       variables_json, api)
        # output results to temp

        # get datetime for files
        filetime = datetime.datetime.utcnow()
        filetimestamp = filetime.timestamp()

        if ep_data:
            api_output.process_output_json(ep_data, "{0}_endpoint_data_{1}.json".format(api, filetimestamp), api)
        else:
            logging.info("No EP data to output")

        api_output.process_output_json(ld_data, "{0}_search_data_{1}.json".format(api, filetimestamp), api)
        api_output.process_output_json(res_data, "{0}_result_data_{1}.json".format(api, filetimestamp), api)

    logging.info("Script complete")
    exit(0)


if __name__ == "__main__":
    def set_bool_val(arg_val):
        if isinstance(arg_val, bool):
            return arg_val
        if arg_val.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif arg_val.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise ap.ArgumentTypeError('Boolean value expected')


    # Parse the various parameters to be used when calling the main script.
    parser = ap.ArgumentParser(formatter_class=ap.RawTextHelpFormatter,
                               description="This script allows you to pass IOC lists and perform queries in Live "
                                           "Discover and generate a report")
    parser.add_argument('-t', '--tenant', nargs='?', help="Allows to specify one tenant\nIf this argument is not "
                                                          "specified all tenants will apply.")
    parser.add_argument('-st', '--search_type', choices=["saved", "adhoc", "list"], required=True,
                        help="Must specify if the search to be run is a saved or adhoc search. Alternatively you "
                             "can list the saved queries available in the tenants (name, description, variables "
                             "and tenant)")
    parser.add_argument('-si', '--search_input', nargs='?', help="Enter input based on selected search type")
    parser.add_argument('-f', '--filter', nargs='?', help="Not setting a search filter will default to the pre-compiled"
                                                          " filter. You can set a custom JSON filter following the "
                                                          "documentation. \nEncapsulate your filter in single quotes, "
                                                          "''")
    parser.add_argument('-v', '--variables', nargs='+', help="Add the following values for the variables in order for "
                                                             "live-discover:\n"
                                                             "[0] Number of Hours of activity to search\n"
                                                             "[1] IOC JSON\n"
                                                             "[2] Start Search From\n"
                                                             "For XDR, only IOC JSON is required")
    parser.add_argument('-m', '--misp', type=set_bool_val, nargs='?', const=True, default=False, help="Enable MISP "
                                                                                                      "attributes. "
                                                                                                      "Boolean")
    parser.add_argument('-mt', '--misp_type', choices=["eventid", "tag"], help="Specify whether you want to get "
                                                                               "attributes for an event ID or tag")
    parser.add_argument('-mv', '--misp_val', help="The value to pass according to the misp attribute type to search for")
    parser.add_argument('-a', '--api', choices=["ld", "xdr"], required=True,
                        help="[ld] - This will perform the search directly on endpoints which are put in the filter\n"
                             "[xdr] - This will perform the search on the DataLake")
    parser.add_argument('-ll', '--log_level', choices=['INFO', 'DEBUG', 'CRITICAL', 'WARNING', 'ERROR'],
                        help="Set logging level mode for more detailed error information, default is disabled")
    parser.add_argument('-o', '--output', choices=['stdout', 'json'], default="stdout",
                        help="Allows you to specify an output method for the query list retrieved. If no option is "
                             "selected it will default to stdout.")

    # parse the argument values to the arg variable
    args = parser.parse_args()

    # Go to main with the arguments
    main(args)
