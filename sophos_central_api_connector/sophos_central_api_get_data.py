import logging
import requests
from urllib.parse import quote_plus
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils


def get_data(tenant_url_data, page_size, tenant_id, api):
    # start the process to get the information from the api, this is standard function and is based on the url
    # the calculation is done through building the urls in sophos_central_api_connector_utils.py
    logging.debug("get data tenant info orig_url: {0}".format(tenant_url_data[tenant_id]['orig_url']))
    pageurl = tenant_url_data[tenant_id]['pageurl']
    orig_url = tenant_url_data[tenant_id]['orig_url']
    headers = tenant_url_data[tenant_id]['headers']
    logging.debug("Tenant URL data: {0}".format(tenant_url_data))
    json_items = dict()

    # gather page total information
    if api == "common":
        logging.info("No page totals available for this api: {0}".format(api))
        pg_total = None
    else:
        logging.info("Getting page totals for api: {0}".format(api))
        pagetotal_url = "{0}?pageTotal=true&pageSize={1}".format(orig_url, page_size)
        logging.info("page total url: {0}".format(pagetotal_url))
        pg_total = get_page_totals(pagetotal_url, headers)

    # get the first page of data from central api
    if api == "roles":
        ep_data = get_page(orig_url, headers)
    else:
        ep_data = get_page(pageurl, headers)

    # attribute the retrieved data from the json to item and page data variables
    if not ep_data or ep_data.get('error'):
        ep_item_data = None
    else:
        ep_item_data = ep_data['items']
        logging.debug(ep_item_data)
        ep_page_data = ep_data.get('pages')
        logging.debug("ep_page_data: {0}".format(ep_page_data))

        if isinstance(ep_page_data, dict):
            page_no = ep_page_data['current']
        else:
            page_no = None

    if not ep_item_data:
        # Checks if any events have been obtained. If not then sets the next key to false
        logging.info("No data returned for this Tenant ID: '{0}'".format(tenant_id))
        next_key = False
        logging.debug(next_key)
    elif len(ep_item_data) == 0:
        # Checks if any events have been obtained. If not then sets the next key to false
        logging.info("There are no pages to process for this Tenant ID: '{0}'".format(tenant_id))
        next_key = False
        logging.debug(next_key)
    elif page_no == pg_total and (page_no is not None and pg_total is not None):
        # Checks if any events have been obtained. If not then sets the next key to false
        logging.info("There are no further pages to process for this Tenant ID: '{0}'".format(tenant_id))
        next_key = False
        logging.debug(next_key)
    else:
        # Does further checks if there is data. to verify whether we need to send for the next page of events
        if isinstance(ep_page_data, dict):
            findkey = 'nextKey'
            if findkey in ep_page_data:
                # Only if the nextkey is present will we send further requests for data
                logging.debug("Another page to process")
                next_key = True
                logging.debug(next_key)
            elif page_no is not None and page_no < pg_total:
                # If the api does not contain a nextkey check whether it has more pages to process
                logging.debug("Current page is lower than the total number of pages. Continue processing")
                next_key = True
                logging.debug(next_key)
            else:
                # No nextkey is present we set next_key to false
                logging.debug("There is no 'next' key present")
                next_key = False
                logging.debug(next_key)
        else:
            logging.info("There is no 'next' key present")
            next_key = False

    # set the event count to 0
    event_count = 0
    # build the json data for the items retrieved
    if not ep_item_data:
        pass
    else:
        json_items, event_count = api_utils.build_json_data(ep_item_data, json_items, event_count)
        logging.debug("Length of json: {0}".format(len(json_items)))

    # Check if there is a next page to process
    while next_key:
        # this will only trigger if the next_key variable is True
        # send the relevant information to obtain the next page
        next_key, pageurl = process_next_page(ep_page_data, page_size, orig_url, page_no, pg_total, api)
        logging.debug("ep_page_data: {0}".format(ep_page_data))
        if pageurl:
            # will only run if the pageurl is not None
            ep_data = get_page(pageurl, headers)
            logging.debug(ep_data)
            ep_item_data = ep_data.get('items')
            ep_page_data = ep_data.get('pages')
            if 'current' in ep_page_data.keys():
                page_no = ep_data.get('pages', {}).get('current')
            else:
                page_no = None
            # add the events obtained to the json data dictionary
            json_items, event_count = api_utils.build_json_data(ep_item_data, json_items, event_count)
            logging.debug("Length of json: {0}".format(len(json_items)))
        else:
            logging.info("No further pages to process")

    # Once the next_key is false return the json_items retrieved
    logging.debug("JSON Data from get data: {0}".format(json_items))
    return json_items


def get_page(pageurl, headers):
    # attempt to get data from sophos central api
    logging.debug("get_page url passed: {0}".format(pageurl))
    res_sess = requests.session()
    retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504, 429])
    #retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[502, 503, 504, 429])
    res_sess.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        logging.debug("Attempting to get page: {0}".format(pageurl))
        ep_res = res_sess.get(pageurl, headers=headers)
        ep_res.raise_for_status()
        logging.info(ep_res.headers)
    except requests.exceptions.HTTPError as err_http:
        if ep_res.status_code == 403:
            logging.error(ep_res.json)
            resp_json = ep_res.json()
            resp_msg = resp_json.get('message')
            logging.error(resp_msg)
            pass
        else:
            logging.error("Error Code: {0}".format(err_http.response))
            logging.error("Error Message: {0}".format(ep_res.json()))
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(conn_err)
    finally:
        # success response pass back data to build json
        if ep_res:
            ep_data = ep_res.json()
        else:
            ep_data = None

        ep_res.close()
        return ep_data


def process_next_page(ep_page_data, page_size, orig_url, page_no, pg_total, api):
    # if a next_key has been provided the process next page function is called to construct the url based on api type
    if 'nextKey' in ep_page_data.keys():
        # builds new url is next_key present
        d_ep_nextkey = ep_page_data['nextKey']
        # encode next key
        ep_nextkey = quote_plus(d_ep_nextkey)
        logging.info(
            "There is another page to process, resending request with new page from key: {0}".format(ep_nextkey))
        if api == "common":
            pageurl = "{0}&pageFromKey={1}&pageSize={2}".format(orig_url, ep_nextkey, page_size)
        elif api == "endpoint":
            pageurl = "{0}?pageFromKey={1}&pageSize={2}&view=full".format(orig_url, ep_nextkey, page_size)
        else:
            pageurl = "{0}?pageFromKey={1}&pageSize={2}".format(orig_url, ep_nextkey, page_size)
        logging.debug(pageurl)
        next_key = True
        return next_key, pageurl
    elif page_no is not None and page_no < pg_total:
        # builds new url if page no. hasn't reached page total
        page_no += 1
        pageurl = "{0}?page={1}&pageSize={2}".format(orig_url, page_no, page_size)
        logging.info("There is another page to process, resending request with new page value: {0}".format(page_no))
        next_key = True
        return next_key, pageurl
    else:
        # if there is no next_key then returns the next page as false to break out of while loop
        next_key = False
        pageurl = None
        return next_key, pageurl


def get_page_totals(url, headers):
    logging.info("start gathering page totals")
    try:
        pagetotal_res = requests.get(url, headers=headers)
        pagetotal_res.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if pagetotal_res.status_code == 403:
            logging.error(http_err)
            logging.error(pagetotal_res.json())
            pass
        elif pagetotal_res.status_code == 500:
            logging.error(http_err)
            logging.error(pagetotal_res.json())
            pass
        else:
            logging.error(http_err)
            pg_total = None
            return pg_total
    else:
        pg_info = pagetotal_res.json()
        pg_data = pg_info.get('pages')
        logging.debug("pg_data info: {0}".format(pg_data))
        if pg_data:
            pg_total = pg_data.get('total')
            logging.debug("page total data: {0}".format(pg_data))
            return pg_total
        else:
            pg_total = None
            return pg_total
