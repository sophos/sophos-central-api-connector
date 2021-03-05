## Alert/Event Information

To gather alerts for your tenants you can pass the alerts option when running the --get parameter. Some additional options are available
when gathering alerts above calling the inventory of machines:

- --days
- --poll_alerts
- --reset

As with calling the inventory option, you can pull alerts for a specific tenant or all of the tenants. In addition you can specify the number of days of events you would like to pull back by using the days parameter.

Sophos Central holds event data for 90 days, so when calling the days parameter you can specifiy days as an integer from 1-90. If no days parameter is passed a default of 1 day is set. below is an example of passing the days parameter:
```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --output <output_option>
```

### Polling Alert Information
The polling option is available for alert events. This is so you can gather alerts over a period of time and maintain a list of events in Splunk.

The correct syntax to poll for alert events is as follows:
```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --poll_alerts --output <splunk or splunk_trans>
```
On the initial run of this syntax the following files will be created:
- poll_config.json
- alert_ids.json

The poll_config.json maintains the results of the last poll attempt and also from when the next poll should get events from and to. Along with maintaining the state of the current run and logging whether any failures have occurred.

When running the poll_alerts for a second time a new file will be generated called:
- temp_alert_ids.json

This file maintains a list of events which have already been successfully sent to Splunk and will be removed from the alerts obtained from the Sophos Central API.

### Resetting Polling
If you need to reset the polling and start re-pulling in events you can pass the reset parameter to initiate this. Along with the reset parameter you can also pass the days parameter in order to specify how many days should be pulled using the API. Syntax on how to pass this is as follows:

```python
python sophos_central_main.py --auth <auth_option> --get alerts --days <integer: 1-90> --reset --poll_alerts --output <splunk or splunk_trans>
```

Running this syntax will delete the files:
- poll_config.json
- alert_ids.json
- temp_alert_ids.json