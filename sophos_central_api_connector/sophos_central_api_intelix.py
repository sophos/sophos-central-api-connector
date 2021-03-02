import intelix
import logging
import configparser as cp
from datetime import datetime
from ipaddress import ip_address
from sophos_central_api_connector import sophos_central_api_output as api_output, sophos_central_api_connector_utils \
    as api_utils
from sophos_central_api_connector.config import sophos_central_api_config as api_conf


def local_site_check(intelix_client_id, intelix_client_secret, request_data, tenant_id):
    logging.info("Checking local-sites against SophosLabs Intelix API")
    # dedup the urls from the data so we dont get site data twice
    output_data = dedup_url(request_data)

    # initiate authentication with intelix api
    logging.info("Authenticating with Intelix API")
    intx = intelix.client(intelix_client_id, intelix_client_secret)

    # iterate through the dictionary of urls and output
    intelix_dict = dict()

    logging.info("Pass URL data to Intelix for evaluation")
    for url_id, url_value in output_data.items():
        # check if the url_value is an ip
        try:
            ip_address(url_value)
            ip_val = True
        except:
            ip_val = False

        if ip_val:
            # send to ip_lookup
            intx.ip_lookup(url_value)
            ip_cat = intx.category
            maxRisk = get_ip_category_risk(ip_cat)
            intx_data = {"lookup_type": "ip", "requestId": intx.requestId, "ipCategory": intx.category, "riskLevel":
                maxRisk}
            intelix_dict[url_value] = intx_data
        elif not ip_val:
            # send_url_lookup
            intx.url_lookup(url_value)
            intx_data = {"lookup_type": "url", "requestId": intx.requestId,
                         "productivityCategory": intx.productivityCategory,
                         "securityCategory": intx.securityCategory, "riskLevel": intx.riskLevel}
            intelix_dict[url_value] = intx_data
        else:
            pass

    # keep record of results from intelix lookups
    date = datetime.now().strftime('%Y%m%d_%H%M%S')
    intx_filename = "{0}_intelix_results.json".format(date)
    logging.info("Saving JSON of Intelix results")
    api_output.process_output_json(intelix_dict, filename=intx_filename, api="intelix")

    # compare against site list
    compared_dict = site_comparison(intelix_dict, request_data, tenant_id)
    return compared_dict


def get_ip_category_risk(ip_cat):
    # get config information
    intelix_conf_path = api_conf.intelix_conf_path
    intelix_final_path = api_utils.get_file_location(intelix_conf_path)
    intelix_conf = cp.ConfigParser(allow_no_value=True)
    intelix_conf.read(intelix_final_path)

    if type(ip_cat) == str:
        maxRisk = intelix_conf.get('ip_lookup_risk', ip_cat)
    elif type(ip_cat) == list:
        ip_risk_dict = dict()
        for item in ip_cat:
            riskLevel = intelix_conf.get('ip_lookup_risk', item)
            ip_risk_dict[item] = riskLevel
        maxRisk = max(ip_risk_dict.values())

    # determine the risk as a string
    if maxRisk == "0":
        maxRisk = "UNCLASSIFIED"
    elif maxRisk == "1":
        maxRisk = "TRUSTED"
    elif maxRisk == "2":
        maxRisk = "LOW"
    elif maxRisk == "3":
        maxRisk = "MEDIUM"
    elif maxRisk == "4":
        maxRisk = "HIGH"

    return maxRisk


def dedup_url(request_data):
    logging.info("Deduplicating URLs from tenants")
    output_data = dict()
    for key, value in request_data.items():
        if value['url'] not in output_data.values():
            output_data[key] = value['url']

    return output_data


def site_comparison(intelix_dict, site_dict, tenant_id):
    # add details to the site dictionary from intelix output
    logging.info("Combine Intelix and Local-Sites information")
    combined_dict = dict()
    for site_key, site_val in site_dict.items():
        for intx_key, intx_val in intelix_dict.items():
            if site_val['url'] == intx_key:
                if intx_val['lookup_type'] == 'url':
                    intx_data = {"local-site": site_val}, {"intelix": {"intelixCategory": intx_val.setdefault(
                        'productivityCategory', 'null'), "intelixRisk": intx_val.setdefault('riskLevel', 'null'),
                        "intelixSecurity": intx_val.setdefault('securityCategory', 'null')}}
                    combined_dict[site_key] = intx_data
                elif intx_val['lookup_type'] == 'ip':
                    intx_data = {"local-site": site_val}, {"intelix": {"intelixCategory": intx_val.setdefault(
                        'ipCategory', 'null'), "intelixRisk": intx_val.setdefault('riskLevel', 'null')}}
                    combined_dict[site_key] = intx_data
                else:
                    pass
            else:
                pass

    date = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = "{0}_results_combined.json".format(date)
    logging.info("Saving JSON of Intelix and local-site results combined")
    api_output.process_output_json(combined_dict, filename=filename, api="intelix")
    return combined_dict


def intelix_report_info(intelix_results, intelix, intx_clean_level, intx_dry_run):
    # set main values
    report_dict = dict()
    high_risk = 0
    medium_risk = 0
    low_risk = 0
    trusted_risk = 0
    unclass_risk = 0
    total_risk = 0
    null_risk = 0

    for site_val in intelix_results.values():
        if intelix == "report":
            intx_data = site_val[1]['intelix']
            ls_data = site_val[0]['local-site']
            risk = intx_data.get('intelixRisk')
            tenant_id = ls_data.get('tenantId')
        elif intx_dry_run:
            risk = site_val.get('intelixRisk')
            tenant_id = site_val.get('tenantId')

        if risk == "HIGH":
            total_risk += 1
            high_risk += 1
        elif risk == "MEDIUM":
            total_risk += 1
            medium_risk += 1
        elif risk == "LOW":
            total_risk += 1
            low_risk += 1
        elif risk == "TRUSTED":
            total_risk += 1
            trusted_risk += 1
        elif risk == "UNCLASSIFIED":
            total_risk += 1
            unclass_risk += 1
        elif risk is None:
            total_risk += 1
            null_risk += 1
        else:
            total_risk += 1
            null_risk += 1
        report_data = {"Totals": {"High Risk": high_risk, "Medium Risk": medium_risk,
                                  "Low Risk": low_risk, "Trusted": trusted_risk,
                                  "Unclassified": unclass_risk, "NULL": null_risk,
                                  "Total": total_risk}}

    if intelix == "report":
        logging.info("Generating report for Intelix results")
        intx_filename = "{0}_intelix_report.json".format(tenant_id)
        report_dict.update(report_data)
        api_output.process_output_json(report_dict, filename=intx_filename, api="intelix")
        return report_dict
    elif intx_dry_run:
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        intx_filename = "{0}_{1}_{2}_dry_run_report.json".format(tenant_id, date, intx_clean_level)
        dryrun_dict = {**intelix_results, **report_data}
        api_output.process_output_json(dryrun_dict, filename=intx_filename, api="intelix")
        return dryrun_dict
    else:
        pass


def intelix_del_info(deletion_data, tenant_url_data):
    logging.info("Generate outcome of local site deletion")
    del_report = dict()
    deleted = 0
    failed = 0
    unknown = 0
    for ten_id, ten_item in tenant_url_data.items():
        tenant_id = ten_id
        for site_id, site_value in deletion_data.items():
            tenant_ref = site_value['tenantId']
            if tenant_ref == tenant_id:
                del_status = site_value['delStatus']
                if del_status == "True":
                    deleted += 1
                elif del_status == "False":
                    failed += 1
                else:
                    unknown += 1
        del_report[tenant_id] = {"Deleted": deleted, "Failed": failed, "Unknown": unknown}

    date = datetime.now().strftime('%Y%m%d_%H%M%S')
    del_filename = "{0}_deletion_details.json".format(date)
    del_report_filename = "{0}_deletion_report.json".format(date)
    api_output.process_output_json(deletion_data, filename=del_filename, api="intelix_del")
    api_output.process_output_json(del_report, filename=del_report_filename, api="intelix_del")


def test(intelix_client_id, intelix_client_secret, test_url):
    intx = intelix.client(intelix_client_id, intelix_client_secret)

    # check if the url_value is an ip
    try:
        ip_address(url_value)
        ip_val = True
    except:
        ip_val = False

    if ip_val:
        # send to ip_lookup
        intx.ip_lookup(test_url)
        intx_data = {"requestId": intx.requestId, "ipCategory": intx.category}
    elif not ip_val:
        # send_url_lookup
        intx.url_lookup(test_url)
        intx_data = {"requestId": intx.requestId, "productivityCategory": intx.productivityCategory,
                     "securityCategory": intx.securityCategory, "riskLevel": intx.riskLevel}


def prepare_del_dict(intx_clean_level, combined_results):
    # go through the combined list and extract the entries which match clean-level
    del_dict = dict()
    logging.info("Prepare the dictionary for local-site clean up")
    logging.info("Option to delete '{0}' has been passed".format(intx_clean_level))
    for site_key, site_val in combined_results.items():
        intx_data = site_val[1]
        ls_data = site_val[0]
        risk = intx_data['intelix']['intelixRisk']
        url = ls_data['local-site']['url']
        tenant_id = ls_data['local-site']['tenantId']
        if intx_clean_level == "ALL":
            # gather all of the valid entries bar unclassified and null. These should remain
            if risk == "HIGH" or risk == "MEDIUM" or risk == "LOW" or risk == "TRUSTED":
                del_dict[site_key] = {"tenantId": tenant_id, "intelixRisk": risk, "url": url}
            else:
                pass
        elif intx_clean_level == "HIGH":
            if risk == "HIGH":
                del_dict[site_key] = {"tenantId": tenant_id, "intelixRisk": risk, "url": url}
            else:
                pass
        elif intx_clean_level == "HIGH_MEDIUM":
            if risk == "HIGH" or risk == "MEDIUM":
                del_dict[site_key] = {"tenantId": tenant_id, "intelixRisk": risk, "url": url}
            else:
                pass
        elif intx_clean_level == "MEDIUM":
            if risk == "MEDIUM":
                del_dict[site_key] = {"tenantId": tenant_id, "intelixRisk": risk, "url": url}
            else:
                pass
        elif intx_clean_level == "LOW":
            if risk == "LOW":
                del_dict[site_key] = {"tenantId": tenant_id, "intelixRisk": risk, "url": url}
            else:
                pass
        else:
            pass

    return del_dict
