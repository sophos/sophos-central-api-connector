import json
import logging
from datetime import datetime
from os import path, remove, makedirs
from sophos_central_api_connector import sophos_central_api_connector_utils as api_utils
from sophos_central_api_connector.config import sophos_central_api_config as api_conf


def polling_alerts(alerts_exists, temp_exists, reset_flag, day_flag, days):
    # Polling argument has been passed. Need to determine what the current state of polling is
    if not alerts_exists:
        # What to do if there is no polling config file present
        logging.info("Polling not previously run, creating config")
        # calculate the to and from dates
        to_str, from_str = api_utils.calculate_from_to(days, poll_date=None)
        # generate the new polling config
        alerts_exists = create_poll_config(to_str)
    elif alerts_exists is True and day_flag is True and reset_flag is True:
        # the correct parameters have been passed to reset the polling config. Understood that this may produce dupes
        logging.info("Polling config exits. Applying reset parameter")
        # calculate the to and from dates
        to_str, from_str = api_utils.calculate_from_to(days, poll_date=None)
        logging.debug("from: {0}, to: {1}".format(from_str, to_str))
        # recreate the polling config
        alerts_exists = create_poll_config(to_str)
        poll_tf_path = api_conf.poll_temp_path
        poll_temp_path = get_file_location(poll_tf_path)
        if alerts_exists and reset_flag:
            # If the polling config is set and the reset flag is passed. Prepare for the next run
            logging.info("Deleting alert_ids log")
            # delete the old alert_ids.json. This will remove the last events successfully sent
            poll_alerts = api_conf.poll_alerts_path
            final_poll_alerts_path = get_file_location(poll_alerts)
            remove(final_poll_alerts_path)
        if temp_exists and reset_flag:
            # If the temp file exists then it will be deleted if the reset flag is set
            logging.info("Deleting temp_alert_ids log")
            remove(poll_temp_path)
        logging.info("Setting reset_flag to 'False'")
        # set the reset_flag to false to avoid it being reset again on the next pass
        reset_flag = False
    elif alerts_exists is True and reset_flag is False:
        # Determines that polling has been run previously with no reset passed.
        logging.info("Poll config already exists and no reset flag has been set.")
        # determine when to poll alerts from to calculate the to and from datetime
        to_str, from_str = polling_from(days)
    elif alerts_exists is True and day_flag is True and reset_flag is False:
        # In order to pass the days flag with polling it must be run with the reset flag
        logging.error("You must raise a reset flag to pass days with poll_alerts when a poll config already exists")
        exit(1)
    elif alerts_exists is True and reset_flag is True and day_flag is False:
        # Required to pass days flag when reset and polling are passed to calculate correctly the datetimes
        logging.error("You must raise a days flag to pass reset with poll_alerts when a poll config already exists")
        exit(1)

    if alerts_exists:
        # only return the variables if the polling config exists
        return to_str, from_str, reset_flag
    else:
        exit(1)


def create_poll_config(to_str):
    # create the polling config
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    poll_dir = api_conf.poll_path
    poll_dir = get_file_location(poll_dir)
    if not path.exists(poll_dir):
        makedirs(poll_dir)
    poll_dict = {'last_run_datetime': '{0}'.format(to_str),
                 'firsttime_run': 'True', 'last_run_success_bool': '', 'last_run_success_datetime': '',
                 'first_loop': 'True', 'failures_seen': 'False'}
    with open(final_poll_conf_path, 'w', encoding='utf-8') as pa_file:
        json.dump(poll_dict, pa_file, ensure_ascii=False, indent=2)

    # re-check whether the polling config is set in order to return correctly
    alerts_exists = path.isfile(final_poll_conf_path)
    return alerts_exists


def polling_from(days):
    # If the polling config is already available checks are made to determine the last state of the run to correctly
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    # determine the from and to datetimes
    with open(final_poll_conf_path) as pa_file:
        poll_dict = json.loads(pa_file.read())
        if poll_dict['last_run_success_bool'] == 'False':
            # If the last run was not successful it uses the last successful datetime for the from datetime
            poll_date = datetime.strptime(poll_dict['last_run_success_datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            to_str, from_str = api_utils.calculate_from_to(days, poll_date)
        elif poll_dict['last_run_success_bool'] == 'True' and poll_dict['firsttime_run'] == 'False':
            # if the last run was succesful and it isnt the first time polling has been run then it will use the last
            # run datetime for from
            poll_date = datetime.strptime(poll_dict['last_run_datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            logging.debug("poll_date={0}".format(poll_date))
            to_str, from_str = api_utils.calculate_from_to(days, poll_date)
        elif poll_dict['last_run_success_bool'] == '':
            # If there is no information on the last successful run time then it will use the last run datetime
            poll_date = datetime.strptime(poll_dict['last_run_datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            # this is then passed to calculate the correct datetime
            to_str, from_str = api_utils.calculate_from_to(days, poll_date)
    return to_str, from_str


def prepare_poll(events, temp_exists, from_str):
    poll_al_ids_path = api_conf.poll_alerts_path
    poll_alerts_path = get_file_location(poll_al_ids_path)
    # re-check whether the alert_ids json file exists
    alertids_exists = path.isfile(poll_alerts_path)
    logging.info("Does the alert_ids.json file exist? {0}".format(alertids_exists))

    # Open the poll config to configure polling
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    with open(final_poll_conf_path, 'r') as pa_file:
        poll_dict = json.load(pa_file)

    if not alertids_exists:
        # If the alert_ids file does not already exist return unless not first time run or loop
        if poll_dict['firsttime_run'] == "True" and poll_dict['first_loop'] == "True":
            # Set the first loop to false if it is the first time run and the first loop
            logging.info("Polling not previously run")
            # set the first loop to false to determine behaviour on next loop
            poll_dict.update({"first_loop": "False"})

            with open(final_poll_conf_path, 'w+') as pa_file:
                json.dump(poll_dict, pa_file, ensure_ascii=False, indent=2)

            return events
        elif poll_dict['firsttime_run'] == "False" and poll_dict['first_loop'] == "False":
            # send the events to be checked if this isnt the first time that polling has been run and is not the first loop
            logging.info("alert_ids.json file doesnt exist. Polling config shows this is not the first time run"
                         " and is not the first loop")
            # send for checks
            spl_events = alert_file_checks(poll_dict, events, temp_exists, from_str)
            # return the checked events for processing
            return spl_events
        elif poll_dict['first_loop'] == "False":
            # just return the events
            return events
    elif alertids_exists:
        # If the file exists, check existing alerts sent returned and prepared to ensure duplicates are not sent
        logging.info("alert_ids file found, running checks")
        logging.debug("First time run: {0}".format(poll_dict['firsttime_run']))
        logging.debug("First loop: {0}".format(poll_dict['first_loop']))
        # send for checks
        spl_events = alert_file_checks(poll_dict, events, temp_exists, from_str)
        return spl_events


def alert_file_checks(poll_dict, events, temp_exists, from_str):
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    # only run checks if the alert_ids file exists
    if poll_dict['firsttime_run'] == "True" and poll_dict['first_loop'] == "True":
        poll_dict.update({"first_loop": "False"})
        with open(final_poll_conf_path, 'w+') as pa_file:
            json.dump(poll_dict, pa_file, ensure_ascii=False, indent=2)
        # if this is the firstime run and first loop, then just return the events
        return events
    elif poll_dict['firsttime_run'] == "True" and poll_dict['first_loop'] == "False":
        logging.debug("First time run is: {0}".format(poll_dict['firsttime_run']))
        # if this is the firstime run then just return the events
        return events
    elif poll_dict['firsttime_run'] == "False" and poll_dict['first_loop'] == "True":
        logging.debug("First time run is: {0} and first loop: {1}".format(poll_dict['firsttime_run'],
                                                                          poll_dict['first_loop']))

        # Prep first loop to get events and calculate datetime.
        from_datetime, process_alerts = first_loop_prep(temp_exists, from_str)

        # Go through existing alerts and delete events older than time frame being gathered
        processed_existing_events = remove_old_alert_ids(from_datetime, process_alerts)

        # Write the necessary events to file
        poll_tf_path = api_conf.poll_temp_path
        poll_temp_path = get_file_location(poll_tf_path)
        with open(poll_temp_path, 'w+', encoding='utf-8') as new_id_file:
            json.dump(processed_existing_events, new_id_file, ensure_ascii=False, indent=2)

        # Reset first loop to ensure events are maintained on next pass
        poll_dict.update({"first_loop": "False"})
        with open(final_poll_conf_path, 'w+') as pa_file:
            json.dump(poll_dict, pa_file, ensure_ascii=False, indent=2)

        logging.info("deleting alert_ids.json")
        poll_al_ids_path = api_conf.poll_alerts_path
        poll_alerts_path = get_file_location(poll_al_ids_path)
        remove(poll_alerts_path)

        # Go through events gathered from Sophos Central and remove entries already sent
        spl_events = process_poll_events(events)

        return spl_events
    elif poll_dict['firsttime_run'] == "False" and poll_dict['first_loop'] == "False":
        logging.info("Continue to process poll events")
        # Go through events gathered from Sophos Central and remove entries already sent
        spl_events = process_poll_events(events)

        return spl_events


def first_loop_prep(temp_exists, from_str):
    # Check whether the temp alert file has been already created from previous run
    if temp_exists:
        # if the file exists clear it down for this new run
        logging.info("temp alerts file exists, clear it down")
        poll_tf_path = api_conf.poll_temp_path
        poll_temp_path = get_file_location(poll_tf_path)
        with open(poll_temp_path, 'w', encoding='utf-8') as reset_temp:
            temp_dict = {}
            json.dump(temp_dict, reset_temp)

    # Open the alert ids and load into json for checking
    poll_al_ids_path = api_conf.poll_alerts_path
    poll_alerts_path = get_file_location(poll_al_ids_path)
    with open(poll_alerts_path, 'r', encoding='utf-8') as existing_alerts:
        # Load the file as json
        process_alerts = json.load(existing_alerts)
        logging.debug(process_alerts)
        logging.info("Length of events from alert_ids.json: {0}".format(len(process_alerts)))

        # Set the correct from string to a datetime and create new list and reset the count
        logging.debug(from_str)
        from_datetime = datetime.strptime(from_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        return from_datetime, process_alerts


def remove_old_alert_ids(from_datetime, process_alerts):
    # Loop through the id_alerts and compare the datetime. If the alert is greater or equal to the
    # from string then keep this alert id and append to new list
    new_ids = {}
    for (event_id, event_value) in process_alerts.items():
        logging.debug("key: {0}, value: {1}".format(event_id, event_value))
        value_date = datetime.strptime(event_value['raised_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        logging.debug("{0} >= {1}".format(value_date, from_datetime))
        if value_date >= from_datetime:
            id_data = {event_id: {'raised_at': event_value['raised_at'], 'tenant_id': event_value['tenant_id']}}
            new_ids.update(id_data)

    logging.info("Length of events from alert_ids.json after old ones removed: {0}".format(len(new_ids)))

    return new_ids


def process_poll_events(events):
    # Search and remove any ids which have already been sent and build new json
    poll_tf_path = api_conf.poll_temp_path
    poll_temp_path = get_file_location(poll_tf_path)
    logging.info("Begin processing events...")
    with open(poll_temp_path, 'r') as check_alerts:
        temp_alert_ids = json.load(check_alerts)
        new_spl_events = {}

    # check for matching ids and only add missing ones
    for (new_event_id, new_event_value) in events.items():
        if new_event_value.get('event', {}).get('id') or new_event_value.get('id', None) in temp_alert_ids.keys():
            # if the id matches the key then skip
            pass
        else:
            # if there is no match add event to new_spl_events
            new_ev = {new_event_id: new_event_value}
            new_spl_events.update(new_ev)

    logging.info("Length of new_spl_events: {0}".format(len(new_spl_events)))
    logging.debug("new_spl_events type is: {0}".format(type(new_spl_events)))

    # determine length of the new alerts after checking
    if len(new_spl_events) > 0 or len(new_spl_events) != "0":
        # if the number of alerts is not zero then return the events
        return new_spl_events
    else:
        # if the number of events is zero then set the new_spl_events to None so it is dealt with accordingly
        logging.info("No events to send")
        new_spl_events = None
        return new_spl_events


def gen_idalerts(event_data):
    # When an event has been successfully sent to splunk the event data is written to file
    poll_al_ids_path = api_conf.poll_alerts_path
    poll_alerts_path = get_file_location(poll_al_ids_path)
    alertids_exists = path.isfile(poll_alerts_path)
    if alertids_exists:
        # if the alert_ids.json file already exists load the existing information to a variable
        with open(poll_alerts_path, 'r') as alerts_file:
            alert_ids = json.load(alerts_file)

        alerts_file.close()

        # update the dictionary with the new event information that was successfully sent to
        alert_ids.update(event_data)
        with open(poll_alerts_path, 'w', encoding='utf-8') as id_file:
            json.dump(alert_ids, id_file, ensure_ascii=False, indent=2)

    else:
        # if the file doesnt yet exist then create it with the event data
        with open(poll_alerts_path, 'w', encoding='utf-8') as alerts_file:
            json.dump(event_data, alerts_file, ensure_ascii=False, indent=2)


def finalise_polling(poll, to_str):
    poll_path = api_conf.poll_conf_path
    final_poll_conf_path = get_file_location(poll_path)
    poll_al_ids_path = api_conf.poll_alerts_path
    poll_alerts_path = get_file_location(poll_al_ids_path)
    poll_tf_path = api_conf.poll_temp_path
    poll_temp_path = get_file_location(poll_tf_path)
    # once there are no further events to process for all of the tenants need to finalise the polling information
    # ready for the next run
    exists = path.isfile(final_poll_conf_path)
    temp_exists = path.isfile(poll_temp_path)
    main_exists = path.isfile(poll_alerts_path)

    def get_old_alerts():
        # gather the old sent alerts from the temp file if any
        if temp_exists:
            with open(poll_temp_path, 'r') as check_alerts:
                temp_alert_ids = json.load(check_alerts)
            return temp_alert_ids
        else:
            temp_alert_ids = None
            return temp_alert_ids

    def get_new_alerts():
        # gather the new events that have been sent if any
        if main_exists:
            with open(poll_alerts_path, 'r') as new_alerts:
                alerts = json.load(new_alerts)
            return alerts
        else:
            alerts = None
            return alerts

    if temp_exists:
        # combine the new and old events into one file if temp exists
        logging.info("Combining old and new events into new alert_ids.json file")
        # gather old events
        old_alerts = get_old_alerts()
        logging.debug("old_alerts type: {0}".format(type(old_alerts)))
        # gather new events
        new_alerts = get_new_alerts()
        logging.debug("new_alerts type: {0}".format(type(new_alerts)))

        if new_alerts is None:
            # if there are no new alerts then just dump the old alerts to alert_ids.json
            with open(poll_alerts_path, 'w', encoding='utf-8') as maintain_alerts:
                json.dump(old_alerts, maintain_alerts, ensure_ascii=False, indent=2)
        else:
            # if there are new alerts then go through old alerts and add them to the new events in alert_ids.json
            for (old_id, old_id_value) in old_alerts.items():
                old_ev = {old_id: old_id_value}
                new_alerts.update(old_ev)

            with open(poll_alerts_path, 'w', encoding='utf-8') as combined_alerts:
                json.dump(new_alerts, combined_alerts, ensure_ascii=False, indent=2)
    else:
        # if the temp file doesnt exist then skip this part
        pass

    if exists and poll:
        # if the polling config exists and the polling is set then update the config according to the result of the pass
        logging.info("Update poll_config information")
        with open(final_poll_conf_path, 'r') as pa_file:
            poll_dict = json.load(pa_file)

            logging.debug(poll_dict)

            if poll_dict['failures_seen'] == "False":
                # if there were no failures seen then update the relevant entries for success
                logging.info("No failures seen")
                poll_dict['last_run_success_bool'] = 'True'
                poll_dict['last_run_success_datetime'] = to_str
                poll_dict['first_loop'] = 'True'
                poll_dict['firsttime_run'] = 'False'
                poll_dict['last_run_datetime'] = to_str
            elif poll_dict['failures_seen'] == "True":
                # if there were failures seen then update the relevant entries for failure so we capture them in the
                # next pass
                logging.info("Failures seen, setting config")
                poll_dict['last_run_success_bool'] = 'False'
                poll_dict['first_loop'] = 'True'
                poll_dict['firsttime_run'] = 'False'

        # write the changes to the polling config
        with open(final_poll_conf_path, 'w') as pa_file:
            json.dump(poll_dict, pa_file, indent=2)
    else:
        pass


def get_file_location(process_path):
    dir_name = path.dirname(__file__)
    final_path = "{0}{1}".format(dir_name, process_path)
    return final_path
