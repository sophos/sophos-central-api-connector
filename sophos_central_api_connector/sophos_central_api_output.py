import json
import logging
import os
import configparser as cp
from sophos_central_api_connector.config import sophos_central_api_config as api_conf
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils


def process_output(output, json_items, tenant_url_data, tenant_id, api, sourcetype_value):
    # verifies which output argument has been passed and directs it to the correct function for processing
    logging.info("Verifying output parameter passed")
    logging.debug(output)
    if output == "stdout":
        # the results will be sent to stdout to print out the results to the terminal
        process_output_stdout(json_items)
        # we return no events as no further action is required
        events = None
        return events
    elif output == "json":
        # json has been specified to output to file
        # the filename is constructed from the tenant name and id so the files are unique
        filename = tenant_url_data[tenant_id]['filename']
        process_output_json(json_items, filename, api)
        # we return no events as no further action is required
        events = None
        return events
    elif output == "splunk" or output == "splunk_trans":
        # the events need to be processed for sending the events to splunk
        events = process_output_splunk(json_items, output, sourcetype_value)
        # events are returned after processing
        return events
    elif None:
        pass


def process_output_json(json_items, filename, api):
    if api == "endpoint":
        logging.debug("JSON file output, appending inventory data")
        # a new folder is created to store the files
        inv_path = api_conf.output_inv_path
        final_inv_path = api_utils.get_file_location(inv_path)
        if not os.path.exists(final_inv_path):
            os.makedirs(final_inv_path)
        with open(os.path.join(final_inv_path, filename), "w", encoding='utf-8') as ep_file:
            json.dump(json_items, ep_file, ensure_ascii=False, indent=2)
    elif api == "common":
        al_path = api_conf.output_al_path
        final_al_path = api_utils.get_file_location(al_path)
        logging.debug("JSON file output, appending alerts data")
        # a new folder is created to store the files
        if not os.path.exists(final_al_path):
            os.makedirs(final_al_path)
        with open(os.path.join(final_al_path, filename), "w", encoding='utf-8') as ep_file:
            json.dump(json_items, ep_file, ensure_ascii=False, indent=2)
    elif api == "local-sites":
        ls_path = api_conf.output_ls_path
        final_ls_path = api_utils.get_file_location(ls_path)
        logging.debug("JSON file output, appending local-sites data")
        # a new folder is created to store the files
        if not os.path.exists(final_ls_path):
            os.makedirs(final_ls_path)
        with open(os.path.join(final_ls_path, filename), "w", encoding='utf-8') as ls_file:
            json.dump(json_items, ls_file, ensure_ascii=False, indent=2)
    elif api == "intelix":
        intx_path = api_conf.output_intx_path
        final_intx_path = api_utils.get_file_location(intx_path)
        logging.debug("JSON file output, intelix local site check")
        # a new folder is created to store the files
        if not os.path.exists(final_intx_path):
            os.makedirs(final_intx_path)
        with open(os.path.join(final_intx_path, filename), "w", encoding='utf-8') as intx_file:
            json.dump(json_items, intx_file, ensure_ascii=False, indent=2)
    elif api == "intelix_del":
        del_path = api_conf.output_intx_del_path
        final_intx_del_path = api_utils.get_file_location(del_path)
        if not os.path.exists(final_intx_del_path):
            os.makedirs(final_intx_del_path)
        with open(os.path.join(final_intx_del_path, filename), "w", encoding='utf-8') as intx_file:
            json.dump(json_items, intx_file, ensure_ascii=False, indent=2)


def process_output_stdout(json_items):
    logging.debug(type(json_items))
    if len(json_items) == 0:
        # if there are no events then this process is passed.
        pass
    else:
        # if there are events these are printed to the terminal
        for item in json_items.values():
            print(json.dumps(item, indent=2))


def process_output_splunk(json_items, output, sourcetype_value):
    logging.debug("Send to Splunk: Building dictionary")

    def splunk_output(spl_events):
        # No changes are required to the event. Information in the transforms will be used.
        processed_events = dict()
        event_count = 0
        logging.debug("Standard Splunk output selected.")
        for event in spl_events.values():
            # construct new event
            pre_event = {"event": event}
            event_count += 1
            # add the constructed event to the processed_events dictionary
            processed_events["{0}".format(event_count)] = pre_event
        # return the processed events
        return processed_events

    def splunk_trans_output(spl_events, transforms_source):
        # apply the new transform information to the events
        logging.debug("Transformation selected. Applying settings from config to event.")
        processed_events = dict()
        event_count = 0

        # load and read the config file
        logging.info("Parsing the Splunk Configuration")
        splunk_conf_path = api_conf.splunk_conf_path
        splunk_final_path = api_utils.get_file_location(splunk_conf_path)
        splunk_conf = cp.ConfigParser()
        splunk_conf.read(splunk_final_path)

        # splunk_trans config info
        host = splunk_conf.get('splunk_transform', 'host')
        source = splunk_conf.get('splunk_transform', 'source')
        sourcetype = splunk_conf.get('splunk_transform', 'sourcetype')

        for event in spl_events.values():
            logging.debug("Standard Splunk output selected.")
            # construct new event
            pre_event = {"host": host, "source": source, "sourcetype": "{0}{1}".format(sourcetype, transforms_source),
                         "event": event}
            event_count += 1
            # add the constructed event to the processed_events dictionary
            processed_events["{0}".format(event_count)] = pre_event
        return processed_events

    # Determine which splunk action is required before returning the events to be sent to splunk
    if output == "splunk":
        splunk_events = splunk_output(json_items)
    elif output == "splunk_trans":
        splunk_events = splunk_trans_output(json_items, sourcetype_value)

    return splunk_events


def process_output_temp(tmp_dict, filename):
    try:
        tmp_path = api_conf.temp_path
        final_tmp_path = api_utils.get_file_location(tmp_path)
        # noinspection PyPep8
        logging.info("Attempting to write file: {0}\{1}".format(final_tmp_path, filename))
        if not os.path.exists(final_tmp_path):
            os.makedirs(final_tmp_path)
        with open(os.path.join(final_tmp_path, filename), "w", encoding='utf-8') as tmp_file:
            json.dump(tmp_dict, tmp_file, ensure_ascii=False, indent=2)
    except IOError:
        logging.error("Unable to write file: {0}\{1}".format(final_tmp_path, filename))
        return False
    else:
        tmp_file.close()
        return True
