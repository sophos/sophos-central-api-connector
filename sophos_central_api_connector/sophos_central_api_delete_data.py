import logging
import requests


def delete_local_site(del_dict, tenant_url_data):
    logging.info("Delete selected sites from local site data")
    processed_del_dict = dict()

    for ten_id, ten_item in tenant_url_data.items():
        tenant_id = ten_id
        logging.info("Deleting local sites for tenant: {0}".format(tenant_id))
        for site_id, site_item in del_dict.items():
            tenant_ref = site_item['tenantId']
            if tenant_ref == tenant_id:
                orig_url = ten_item['orig_url']
                headers = ten_item['headers']
                ls_url = "{0}/{1}".format(orig_url, site_id)
                del_ls = requests.delete(ls_url, headers=headers)
                del_data = del_ls.json()
                del_status = del_data['deleted']
                del_date = del_ls.headers['date']
                logging.debug("Local Site ID: {0}, Deletion Status: {1}".format(site_id, del_status))
            processed_del_dict[site_id] = {"tenantId": site_item['tenantId'], "intelixRisk": site_item['intelixRisk'],
                                           "url": site_item['url'], "delStatus": del_status, "date": del_date}
        logging.info("Completed deletion of local sites for tenant: {0}".format(tenant_id))
    return processed_del_dict
