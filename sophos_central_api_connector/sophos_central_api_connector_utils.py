import logging
from requests.utils import requote_uri
from datetime import datetime, timedelta
from sophos_central_api_connector.config import sophos_central_api_config as api_conf

# static global entries for the urls of the apis for Sophos Central
endpoint_url = api_conf.endpoints_uri
alerts_url = api_conf.alerts_uri


def generate_tenant_urls(tenant_info, page_size, api, from_str, to_str):
    # dependent on the api type passed this will generate the appropriate headers
    logging.info("Generating tenant URL data")
    # create a dictionary ready to apply the headers for each of the tenants
    tenant_url_data = dict()
    if api == "endpoint":
        # api for endpoint has been passed. For loop to generate the headers for each of the tenant ids
        for ten_id, ten_item in tenant_info.items():
            tenant_url_data[ten_id] = {"filename": "{0}{1}{2}{3}".format(ten_item["name"], "_", ten_id, ".json"),
                                       "orig_url": "{0}{1}".format(ten_item["page_url"], endpoint_url),
                                       "pageurl": "{0}{1}?pageSize={2}".format(ten_item['page_url'], endpoint_url,
                                                                               page_size),
                                       "headers": ten_item["headers"]}
        return tenant_url_data
    elif api == "common":
        # api for common has been passed. For loop to generate the headers for each of the tenant ids
        for ten_id, ten_item in tenant_info.items():
            # a decoded url is constructed from the variables
            decoded_url = str("{0}{1}?from={2}&to={3}&pageSize={4}".format(ten_item["page_url"],
                                                                           alerts_url, from_str, to_str, page_size))
            # the decoded urls are encoded so they are valid urls to be passed
            pageurl = requote_uri(decoded_url)
            tenant_url_data[ten_id] = {"filename": "{0}{1}{2}{3}".format(ten_item["name"], "_", ten_id, ".json"),
                                       "orig_url": pageurl, "pageurl": pageurl,
                                       "headers": ten_item["headers"]}
        return tenant_url_data
    else:
        # this is return if an invalid api variable is supplied
        logging.error("The {0} API does not appear to exist.".format(api))
        exit(1)


def build_json_data(ep_item_data, json_items, event_count):
    # from the item data retrieved build json with event count
    for item in ep_item_data:
        event_count += 1
        json_items[event_count] = item
    return json_items, event_count


def calculate_from_to(days, poll_date):
    # dependent on whether polling has been selected and the number of days passed to calculate the from/to dates
    def calc_from(polling_date, delta_calc, time_now):
        # This calculates the from date based on the information in the poll config date passed
        if polling_date:
            less_delta = (polling_date - delta_calc)
            start = '{0:%Y-%m-%dT%H:%M:%S.%fZ}'.format(less_delta)
            # Need to remove milliseconds from the calculated date so it is accepted by Sophos Central API
            start = start[:-4]
            start = "{0}Z".format(start)
            return start
        else:
            # calculate the from date by the value of delta
            less_delta = (time_now - delta_calc)
            pre_start = datetime.combine(less_delta, datetime.min.time())
            new_start = pre_start.strftime('%Y-%m-%dT%H:%M:%S.%f')
            # Need to remove milliseconds from the calculated date so it is accepted by Sophos Central API
            new_start = new_start[:-3]
            new_start = "{0}Z".format(new_start)
            return new_start

    # calculate the datetime now
    now = datetime.utcnow()
    time = "days"
    # delta is calculated by the number of days passed
    delta = timedelta(**{time: days})
    logging.debug("now={0}, time={1}, delta={2}".format(now, time, delta))
    # send to calc_from function to get formatted datetime
    from_str = calc_from(poll_date, delta, now)

    # calculate the to date from now.
    new_to = now.strftime('%Y-%m-%dT%H:%M:%S.%f')
    # Need to remove milliseconds from the calculated date so it is accepted by Sophos Central API
    new_to = new_to[:-3]
    to_str = "{0}Z".format(new_to)
    logging.debug("to_str={0}, from_str={1}".format(to_str, from_str))
    return to_str, from_str


def validate_page_size(page_size, api):
    # The sophos central api has a number page size which can be retrieved. The max is set in the
    # sophos_central_api_config.py. Below verifies that the sizes set in sophos_config.ini are within limits
    if api == "endpoint":
        # Verify the page sizes for the endpoint api
        logging.info("Verifying page size requested")
        if page_size == "":
            # if no value is set then a default value is passed for this variable
            logging.info("No value set in the config. Apply default.")
            page_size = 50
        elif int(page_size) > api_conf.max_inv_page:
            # Returns an error if the size of the page passed is greater than the max
            logging.error("Inventory page size has a max of: {0}".format(api_conf.max_inv_page))
            logging.error("Please ensure that the value in config.ini is less than or equal to this")
            exit(1)
        elif int(page_size) <= api_conf.max_inv_page:
            # Continues if the page size set is less than or equal to the max
            logging.info("Applying setting from config. Setting is less than or equal to the maximum allowed")
            pass
    elif api == "common":
        # Verify the page sizes for the common api
        if page_size == "":
            # set a limit if no page_size is passed
            logging.info("No value set in the config. Apply default.")
            page_size = 50
        elif int(page_size) <= api_conf.max_alerts_page:
            # Continues if the page size set is less than or equal to the max
            logging.info("Applying setting from config. Setting is less than or equal to the maximum allowed")
            pass
        elif int(page_size) > api_conf.max_alerts_page:
            # Returns an error if the size of the page passed is greater than the max
            logging.error("Alerts page size has a max of: {0}".format(api_conf.max_alerts_page))
            logging.error("Please ensure that the value in config.ini is less than or equal to this")
            exit(1)

    return page_size
