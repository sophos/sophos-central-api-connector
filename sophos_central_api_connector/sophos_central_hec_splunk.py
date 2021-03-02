import requests
import json
import logging
import configparser as cp
from time import sleep
from os import path
from sys import exit
from sophos_central_api_connector import sophos_central_api_polling as api_poll
from sophos_central_api_connector.config import sophos_central_api_config as api_conf


def send_to_splunk(api, splunk_events, splunk_creds, sourcetype_value, tenant_id, from_str, to_str, alerts_exists,
                   temp_exists, alertids_exists, poll):
    # Generate the Splunk URL to be used to send the data to.
    splunk_conf_path = api_conf.splunk_conf_path
    splunk_final_path = get_file_location(splunk_conf_path)
    splunk_conf = cp.ConfigParser()
    splunk_conf.read(splunk_final_path)
    main_splunk_url, channel = set_main_splunk_url()
    splunk_headers = {"Authorization": "Splunk {0}".format(splunk_creds)}

    # Check indexer acknowledgement settings
    request_ack = splunk_conf.get('splunk_hec', 'verify_ack_result')

    if api == "common":
        # if the api is common post the alerts to splunk
        logging.info("Length of splunk events passed to post_alerts: {0}".format(len(splunk_events)))
        post_alerts(from_str, temp_exists, poll, splunk_events, main_splunk_url, request_ack, channel, splunk_headers,
                    tenant_id)
    elif api == "endpoint":
        # if the api is endpoint post the inventory data to splunk
        logging.info("Length of splunk events passed to post_inventory: {0}".format(len(splunk_events)))
        post_inventory(splunk_events, main_splunk_url, request_ack, channel, splunk_headers, poll)
    else:
        logging.error("No api function available for: {0}".format(api))


def set_main_splunk_url():
    splunk_conf_path = api_conf.splunk_conf_path
    splunk_final_path = get_file_location(splunk_conf_path)
    splunk_conf = cp.ConfigParser()
    splunk_conf.read(splunk_final_path)
    # construct the main splunk url from the config information
    splunk_url = splunk_conf.get('splunk_hec', 'splunk_url')
    channel = splunk_conf.get('splunk_hec', 'channel')
    splunk_ack_enabled = splunk_conf.get('splunk_hec', 'splunk_ack_enabled')

    if splunk_ack_enabled == "1":
        # if the token has the splunk acknowledgement enabled we need to pass a channel GUID to be successful
        # this is provided from the splunk_config.ini file
        logging.info("Indexer Acknowledgement set on HEC token, applying correct URI")
        main_splunk_url = "{0}?channel={1}".format(splunk_url, channel)
    elif splunk_ack_enabled == "0":
        # if no splunk acknowledgement is set then simply use the base splunk url provided in the config
        logging.info("No Indexer Acknowledgement set on HEC token, applying correct URI")
        main_splunk_url = splunk_url

    return main_splunk_url, channel


def post_alerts(from_str, temp_exists, poll, spl_events, main_splunk_url, request_ack, channel, splunk_headers,
                tenant_id):
    if poll:
        # If polling is set prepare the events to be sent to Splunk
        logging.info("Prep alert events for polling")
        spl_events = api_poll.prepare_poll(spl_events, temp_exists, from_str)
    else:
        # if no polling parameter has been passed then this is skipped
        logging.info("No alert polling set")

    if spl_events is None:
        # if there are no events to process then we return to process the next tenant if any
        logging.info("spl_events is 'None'")
        return
    elif len(spl_events) == 0:
        # if there are no events to process then we return to process the next tenant if any
        logging.info("Length of spl_events is: 0")
        return
    else:
        # if there are events we run a for loop to send the events to splunk
        logging.info("Length of splunk events being passed to splunk: {0}".format(len(spl_events)))

    # Go through the list of events and attempt to send to Splunk
    send_count = 0
    logging.info("Iterating through events and sending to Splunk...")
    logging.info("Length of events sent: {0}".format(len(spl_events)))
    for spl_event in spl_events.values():
        # Extract the events id. tenant and raised at values
        logging.debug(spl_event)
        event_id = spl_event['event']['id']
        event_tenant_id = spl_event['event']['tenant']['id']
        raised_at = spl_event['event']['raisedAt']
        event_data = {event_id: {"raised_at": raised_at, "tenant_id": event_tenant_id}}
        spl_event = json.dumps(spl_event)
        send_count += 1
        # send the extracted information to splunk
        hec_response_code, failed_id = post_events_to_splunk(spl_event, splunk_headers,
                                                             main_splunk_url, send_count,
                                                             request_ack, event_data,
                                                             event_id, poll, channel)


def post_inventory(splunk_events, main_splunk_url, request_ack, channel, splunk_headers, poll):
    # Go through the list of events and attempt to send to Splunk
    send_count = 0
    raised_at = None
    logging.info("Iterating through events and sending to Splunk...")
    logging.info("Length of events sent: {0}".format(len(splunk_events)))
    for spl_event in splunk_events.values():
        # Extract the events id. tenant and raised at values
        logging.debug(spl_event)
        event_id = spl_event['event']['id']
        event_tenant_id = spl_event['event']['tenant']['id']
        event_data = {event_id: {"tenant_id": event_tenant_id}}
        spl_event = json.dumps(spl_event)
        send_count += 1
        hec_response_code, failed_id = post_events_to_splunk(spl_event, splunk_headers,
                                                             main_splunk_url, send_count,
                                                             request_ack, event_data,
                                                             event_id, poll, channel)


def post_events_to_splunk(spl_event, splunk_headers, main_splunk_url, send_count, request_ack, event_data, event_id,
                          poll, channel):
    logging.debug("Event data content in post: {0}".format(event_data))
    try:
        # attempt to send the event to splunk
        hec_res = requests.post(main_splunk_url, headers=splunk_headers, data=spl_event)
        logging.debug(hec_res.status_code)
        hec_data = hec_res.json()
        logging.debug(hec_data)
        hec_response_code = hec_data['code']
        hec_response_text = hec_data['text']
        logging.debug(hec_data['text'])
        # If the sending of the data is successful to Splunk evaluate whether to check indexer acknowledgement
        if hec_response_code == 0:
            # if the event is successfully sent then check if the polling parameter has been passed to add the event id
            logging.debug("EventID: '{0}' has been sent to splunk".format(event_id))
            failed_id = None
            if poll:
                # add the event data to the alert_ids.json
                api_poll.gen_idalerts(event_data)
            else:
                pass
            return hec_response_code, failed_id
        elif hec_response_code == 8 or hec_response_code == 9:
            logging.error("Event failed to send to Splunk with error: {0}".format(hec_response_text))
            logging.debug(splunk_headers)
            # if the server is busy then send for a retry
            hec_retry_code, failed_id = hec_post_retry(spl_event, main_splunk_url, splunk_headers, event_id)
            return hec_response_code, failed_id
        elif hec_response_code != 0:
            failed_id = True
            # send to failure
            event_failure(spl_event, poll, failed_id)
    except requests.exceptions.HTTPError as err_http:
        logging.error("HTTP Error:", err_http)
    exit(1)


def hec_post_retry(spl_event, main_splunk_url, splunk_headers, event_id):
    # We will only try to resend the event a max of three times
    logging.debug(splunk_headers)
    max_retries = 3
    retries = 0
    retry = True
    while retry is True:
        # Attempt to send the event to Splunk again
        logging.info("Retrying to send ID: '{0}' to splunk. Attempt: {1}".format(event_id, retries))
        sleep(1)
        retries += 1
        logging.debug("Retry: {0}".format(retries))
        hec_res = requests.post(main_splunk_url, headers=splunk_headers, data=spl_event)
        hec_retry_data = hec_res.json()
        hec_retry_code = hec_retry_data['code']
        hec_retry_text = hec_retry_data['text']
        logging.debug(hec_retry_data)
        if hec_retry_code == 0:
            # If successful set the retry to false to break out of the loop
            logging.info("Retry successfully sent to Splunk ID: '{0}'".format(event_id))
            retry = False
            failed_id = False
            return hec_retry_code, failed_id
        elif retries == max_retries:
            logging.error("ID: '{0}' failed to send to Splunk. "
                          "This will be sent to the event failure def".format(event_id))
            retry = False
            failed_id = True
            return hec_retry_code, failed_id
        elif hec_retry_code == 8 or hec_retry_code == 9:
            # Retry sending back to the start of the loop
            retry = True
        elif hec_retry_code != 8 or hec_retry_code != 9:
            # This is due to a major failure so we need to break out completely
            logging.error("Failed to send the event failing out: {0}".format(hec_retry_text))
            exit(1)


def event_failure(spl_event, poll, failed_id):
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    # if the event failure is true check whether the polling config exists
    exists = path.isfile(final_poll_conf_path)
    if exists and poll:
        # if the polling config exists and the polling parameter is true then write failure to the config
        try:
            with open(final_poll_conf_path, 'r') as pa_file:
                poll_dict = json.load(pa_file)
                for item in poll_dict:
                    if item['last_run_success_bool'] in ['True']:
                        item['last_run_success_bool'] = 'False'
                    if item['failures_seen'] in ['True']:
                        item['failures_seen'] = 'True'
            with open(final_poll_conf_path, 'w') as pa_file:
                json.dump(poll_dict, pa_file, indent=2)
        except Exception as exc:
            print("Exception raised: {0}".format(exc))
    else:
        log_path = api_conf.logging_path
        final_logging_path = get_file_location(log_path)
        # Set the failed event to a file for retry later or just report
        with open(final_logging_path, 'r') as fail_file:
            failed_events = json.load(fail_file)

        # update the dictionary with the new event information that failed
        failed_events.update(failed_id)
        with open(final_logging_path, 'w') as new_fails:
            json.dump(failed_events, new_fails, ensure_ascii=False, indent=2)


def get_file_location(process_path):
    dir_name = path.dirname(__file__)
    final_path = "{0}{1}".format(dir_name, process_path)
    return final_path
