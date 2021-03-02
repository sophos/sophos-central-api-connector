from pathlib import PurePath

# Static URI Variables
auth_uri = 'https://id.sophos.com/api/v2/oauth2/token'
whoami_uri = 'https://api.central.sophos.com/whoami/v1'
tenants_ptr_uri = 'https://api.central.sophos.com/partner/v1/tenants'
tenants_org_uri = 'https://api.central.sophos.com/organization/v1/tenants'
alerts_uri = '/common/v1/alerts'
endpoints_uri = '/endpoint/v1/endpoints'
directory_uri = '/common/v1/directory'
settings_uri = '/endpoint/v1/settings'
livediscover_uri = '/live-discover/v1/queries'


# Default Value
max_alerts_page = 100
max_inv_page = 500
max_localsite_page = 100

# Regex Variables
uuid_regex = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'

# Path locations
sophos_conf_path = PurePath("/config/sophos_config.ini")
splunk_conf_path = PurePath("/config/splunk_config.ini")
intelix_conf_path = PurePath("/config/intelix_config.ini")
misp_conf_path = PurePath("/config/misp_config.ini")
output_inv_path = PurePath("/output/get_inventory")
output_al_path = PurePath("/output/get_alerts")
output_ls_path = PurePath("/output/get_local_sites")
output_intx_path = PurePath("/output/intelix")
output_intx_del_path = PurePath("/output/intelix/delete_local_sites")
poll_conf_path = PurePath("/polling/poll_config.json")
poll_alerts_path = PurePath("/polling/alert_ids.json")
poll_temp_path = PurePath("/polling/temp_alert_ids.json")
poll_path = PurePath("/polling")
logging_path = PurePath("/logs/failed_events.json")
temp_path = PurePath("/tmp")
