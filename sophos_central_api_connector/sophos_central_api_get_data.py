import logging
import requests
from time import sleep
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils


def get_data(tenant_url_data, page_size, tenant_id, api):
    # start the process to get the information from the api, this is standard function and is based on the url
    # the calculation is done through building the urls in sophos_central_api_connector_utils.py
    pageurl = tenant_url_data[tenant_id]['pageurl']
    orig_url = tenant_url_data[tenant_id]['orig_url']
    headers = tenant_url_data[tenant_id]['headers']
    json_items = dict()

    if api != "common":
        # get the page total
        pagetotal_url = "{0}?pageSize={1}&pageTotal=true".format(orig_url, page_size)
        pagetotal_res = requests.get(pagetotal_url, headers=headers)
        pg_data = pagetotal_res.json()
        pg_total = pg_data['pages']['total']
    else:
        pg_total = None

    # get the first page of data from central api
    ep_data = get_page(pageurl, headers)

    # attribute the retrieved data from the json to item and page data variables
    ep_item_data = ep_data['items']
    ep_page_data = ep_data['pages']
    if api == "local-sites":
        page_no = ep_data['pages']['current']
    else:
        page_no = None

    if len(ep_item_data) == 0:
        # Checks if any events have been obtained. If not then sets the next key to false
        logging.info("There are no events to process for this Tenant ID: '{0}'".format(tenant_id))
        next_key = False
    elif page_no == pg_total:
        # Checks if any events have been obtained. If not then sets the next key to false
        logging.info("There are no further pages to process for this Tenant ID: '{0}'".format(tenant_id))
        next_key = False
    else:
        # Does further checks if there is data. to verify whether we need to send for the next page of events
        if 'nextKey' in ep_page_data.keys():
            # Only if the nextkey is present will we send further requests for data
            logging.debug("Next page to process")
            next_key = True
        elif page_no is not None and page_no < pg_total:
            # If the api does not contain a nextkey check whether it has more pages to process
            logging.debug("Current page is lower than the total number of pages. Continue processing")
            next_key = True
        else:
            # No nextkey is present we set next_key to false
            logging.debug("There is no 'next' key present")
            next_key = False

    # set the event count to 0
    event_count = 0
    # build the json data for the items retrieved
    json_items, event_count = api_utils.build_json_data(ep_item_data, json_items, event_count)
    logging.debug("Length of json: {0}".format(len(json_items)))

    # Check if there is a next page to process
    while next_key:
        # this will only trigger if the next_key variable is True
        # send the relevant information to obtain the next page
        next_key, pageurl = process_next_page(ep_page_data, page_size, orig_url, api, page_no, pg_total)
        if pageurl:
            # will only run if the pageurl is not None
            ep_data = get_page(pageurl, headers)
            ep_item_data = ep_data['items']
            ep_page_data = ep_data['pages']
            if api == "local-sites":
                page_no = ep_data['pages']['current']
            else:
                page_no = None
            # add the events obtained to the json data dictionary
            json_items, event_count = api_utils.build_json_data(ep_item_data, json_items, event_count)
            logging.debug("Length of json: {0}".format(len(json_items)))
        else:
            logging.info("No further pages to process")

    # Once the next_key is false return the json_items retrieved
    return json_items


def get_page(pageurl, headers):
    # attempt to get data from sophos central api
    try:
        ep_res = requests.get(pageurl, headers=headers)
    except requests.exceptions.HTTPError as err_http:
        logging.error("HTTP Error:", err_http)
        logging.info(err_http)
    # if rate limit is hit then attempt to restrict
    if ep_res.status_code == 429:
        error = True
        logging.info("Error {0}: Backing off!".format(ep_res.status_code))
        while error:
            try:
                ep_res = requests.get(pageurl, headers=headers)
            except requests.exceptions.HTTPError as err_http:
                logging.error("HTTP Error:", err_http)
                logging.info(err_http)
                if ep_res.status_code == 200:
                    ep_data = ep_res.json()
                    return ep_data
                elif ep_res.status_code == 429:
                    logging.error("Still hitting the rate limit!")
                    sleep(delay_time)
                    delay_time = delay_time * 2
                    logging.info("Delayed by: {0}".format(delay_time))
                elif ep_res.status_code != 200:
                    logging.error("Response code is not 200")
                    raise Exception('API response: {0}'.format(ep_res.status_code))
    elif ep_res.status_code == 200:
        # success response pass back data to build json
        logging.debug(ep_res.headers)
        ep_data = ep_res.json()
        return ep_data
    else:
        # details on the response code and error
        logging.error("Response Code: {0}".format(ep_res.status_code))
        logging.error("Error Details: {0}".format(ep_res.content))


def process_next_page(ep_page_data, page_size, orig_url, api, page_no, pg_total):
    # if a next_key has been provided the process next page function is called to construct the url based on api type
    if api == "endpoint":
        if 'nextKey' in ep_page_data.keys():
            # builds new url is next_key present
            ep_nextkey = ep_page_data['nextKey']
            logging.info(
                "There is another page to process, resending request with new page from key: {0}".format(ep_nextkey))
            pageurl = "{0}?pageFromKey={1}&pageSize={2}".format(orig_url, ep_nextkey, page_size)
            next_key = True
            return next_key, pageurl
        else:
            # if there is no next_key then returns the next page as false to break out of while loop
            next_key = False
            pageurl = None
            return next_key, pageurl
    elif api == "common":
        if 'nextKey' in ep_page_data.keys():
            # builds new url is next_key present
            ep_nextkey = ep_page_data['nextKey']
            logging.info(
                "There is another page to process, resending request with new page from key: {0}".format(ep_nextkey))
            pageurl = "{0}&pageFromKey={1}&pageSize={2}".format(orig_url, ep_nextkey, page_size)
            next_key = True
            return next_key, pageurl
        else:
            # if there is no next_key then returns the next page as false to break out of while loop
            next_key = False
            pageurl = None
            return next_key, pageurl
    elif api == "local-sites":
        if page_no < pg_total:
            # builds new url if page no. hasn't reached page total
            page_no += 1
            pageurl = "{0}?page={1}&pageSize={2}".format(orig_url, page_no, page_size)
            logging.info("There is another page to process, resending request with new page value: {0}".format(page_no))
            next_key = True
            return next_key, pageurl
        else:
            # if there is no further pages then returns the next page as false to break out of while loop
            next_key = False
            pageurl = None
            return next_key, pageurl
