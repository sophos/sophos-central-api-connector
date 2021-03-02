import logging
import json
import requests
from urllib3.util.retry import Retry
from time import sleep
from sophos_central_api_connector import sophos_central_api_get_data as get_api

api = "live-discover"
page_size = "250"


def live_discover(tenant_data, input_type, input_value, search_filter, variables):
    def gather_ld():
        # build the payload to post
        logging.info("Building payload information for saved search")
        payload_dict = build_json_payload(input_type, input_value, query_det, search_filter, variables)

        # post run
        logging.info("Start posting saved queries")
        post_dict = post_ld_run(tenant_data, payload_dict)
        logging.debug("post dict: {0}".format(post_dict))

        # run checker
        logging.info("Start checking query status")
        run_info = multi_query_run_checker(tenant_data, post_dict)
        logging.debug("Run info: {0}".format(run_info))

        # get endpoint data
        logging.info("Gather endpoint information")
        ep_info = get_ld_endpoints(tenant_data, run_info)
        logging.debug("Endpoint information: {0}".format(ep_info))

        # get run results
        logging.info("Gather results based on run ids")
        size = 1000
        result_dict = get_run_results(tenant_data, run_info, size)
        logging.debug("Result data: {0}".format(result_dict))

        return run_info, ep_info, result_dict

    if input_type == "saved":
        # Get saved query details
        logging.info("Getting saved search details")
        query_det = get_queries(tenant_data, True, input_value)
        if not variables:
            for s_id, s_val in query_det.items():
                if s_val['template_variables']:
                    variables = s_val['template_variables']
                else:
                    pass
        else:
            pass

        ld_data, ep_data, result_data = gather_ld()
        return ld_data, ep_data, result_data

    elif input_type == "adhoc":
        logging.info("Coming soon")
        # todo: check the size of the adhoc query
        exit(1)
    elif input_type == "list":
        query_list = get_queries(tenant_data, False, None)
        return query_list


def data_lake():
    logging.info("Coming soon")
    exit(1)


def get_queries(tenant_url_data, query_find, query_det):
    def find_query(query_dict, query_info, tenant, fdict):
        logging.info("Looking for saved query in dictionary")

        for num, item in query_dict.items():
            if item.get('name') == query_info:
                logging.info("Found saved query: '{0}' for tenant: {1}".format(query_det, tenant))
                q_id = item['id']
                if item['variables']:
                    fdict[q_id] = {"name": item['name'], "description": item['description'], "tenant_id": tenant,
                                   "template_variables": item['variables']}
                else:
                    fdict[q_id] = {"name": item['name'], "description": item['description'], "tenant_id": tenant,
                                   "template_variables": None}
                logging.debug("Query details: {0}".format(fdict))
            else:
                pass

        return fdict

    def list_queries(query_list, tenant, qdict):
        for key, val in query_list.items():
            q_id = val.get('id')
            q_name = val.get('name')
            q_desc = val.get('description')
            q_var = val.get('variables')
            qdict[q_id] = {"name": q_name, "description": q_desc, "variables": q_var, "tenant_id": tenant}

        return qdict

    # Gather the queries for the tenants
    new_dict = dict()

    for ten_id, ten_item in tenant_url_data.items():
        # Pass the ten_url_data and gather the queries
        logging.info("Attempting to get Live Discover queries")
        tenant_id = ten_id
        # get data information for the tenant in the loop
        json_data = get_api.get_data(tenant_url_data, page_size, tenant_id, api)
        # Check if query name passed is valid and present
        if query_find:
            new_dict = find_query(json_data, query_det, tenant_id, new_dict)
        else:
            # Print list of available queries
            new_dict = list_queries(json_data, tenant_id, new_dict)

    return new_dict


def build_json_payload(input_type, input_value, query_data, filters, variables):
    # Open find query json if available
    rebuild_dict = dict()

    for s_id, s_det in query_data.items():
        q_name = s_det['name']
        q_desc = s_det['description']
        q_ten = s_det['tenant_id']
        if variables:
            try:
                if input_type == "saved":
                    con_json = {"matchEndpoints": {"filters": [filters]}, "savedQuery": {"queryId": s_id},
                                "variables": variables}
                elif input_type == "adhoc":
                    con_json = {"matchEndpoints": {"filters": [filters]}, "adHocQuery": {"template": input_value},
                                "variables": variables}
                else:
                    logging.error("Input type is not valid, please review variables passed")
                    exit(1)

                json.dumps(con_json)
            except ValueError as err:
                logging.error("JSON has failed validation test")
                logging.error(con_json)
                raise err
            else:
                logging.info("JSON has been validated successfully")
                logging.debug("JSON Passed: {0}".format(con_json))
                logging.info("Adding payload to query dict")
                rebuild_dict[s_id] = {"name": q_name, "description": q_desc, "tenant_id": q_ten, "payload": con_json}

        elif not variables:
            try:
                if input_type == "saved":
                    con_json = {"matchEndpoints": {"filters": [filters]}, "savedQuery": {"queryId": s_id}}
                elif input_type == "adhoc":
                    con_json = {"matchEndpoints": {"filters": [filters]}, "adHocQuery": {"template": input_value}}
                else:
                    logging.error("Input type is not valid, please review variables passed")
                    exit(1)

                json.dumps(con_json)
            except ValueError as err:
                logging.error("JSON has failed validation test")
                logging.error(con_json)
                raise err
            else:
                logging.info("JSON has been validated successfully")
                logging.info("Adding payload to query dict")
                rebuild_dict[s_id] = {"name": q_name, "description": q_desc, "tenant_id": q_ten, "payload": con_json}
        else:
            pass

    return rebuild_dict


def post_ld_run(tenant_url_data, ld_dict):
    def post_query(query_data, url, headers):
        q_payload = query_data['payload']
        try:
            logging.info("Posting query")
            post_res = requests.post(url, headers=headers, json=q_payload)
            post_res.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            if post_res.status_code == 404:
                logging.error("Item not found. Please verify your filter")
                raise http_err
            elif post_res.status_code == 400:
                logging.error(post_res.text)
                raise http_err
            else:
                logging.error("Error whilst posting search query, response: {0}".format(post_res.status_code))
                raise http_err
        else:
            logging.info("Post successful, making note of post id")
            p_data = post_res.json()
            logging.debug(json.dumps(p_data, indent=2))
            return p_data

    # Prep for posting queries to live discover
    post_url = "/runs"
    pq_dict = dict()

    for key, value in tenant_url_data.items():
        pq_url = "{0}{1}".format(value['orig_url'], post_url)
        tenant = key
        p_headers = value['headers']
        p_headers['Content-Type'] = "application/json"
        for q_key, q_val in ld_dict.items():
            if tenant == q_val['tenant_id']:
                ten_id = q_val['tenant_id']
                logging.info("Search found for tenant: {0}, search name: {1}".format(ten_id, q_val['name']))
                post_data = post_query(q_val, pq_url, p_headers)
                if post_data:
                    pq_id = post_data['id']
                    pq_created = post_data['createdAt']
                    pq_status = post_data['status']
                    ep_count = post_data['endpointCounts']['total']
                    pq_data = {q_key: {"name": q_val['name'], "description": q_val['description'], "tenant_id": ten_id,
                                       "payload": q_val['payload'],
                                       "post_data": {"pq_id": pq_id, "createdAt": pq_created, "status": pq_status,
                                                     "ep_count": ep_count}}}
                    pq_dict.update(pq_data)
            else:
                logging.info("No searches found in list for tenant: {0}".format(tenant))

    return pq_dict


def multi_query_run_checker(tenant_url_data, ld_dict):
    def loop_check():
        logging.debug("loop check")
        run_check = True
        for sid, val in ld_dict.items():
            new_status = val['post_data']['status']
            t_remaining = val['post_data']['time_remaining']
            if new_status != "finished":
                if t_remaining == 0:
                    logging.error("Max query duration reached. Query '{0}' will be terminated".format(sid))
                    val['post_data']['terminated'] = True
                    pass
                else:
                    val['post_data']['terminated'] = False
                    logging.info("Time remaining before query, {0}: {1}, is automatically terminated: {2} "
                                 "seconds".format(val['name'], sid, t_remaining))
                    run_check = False

        return run_check

    # Check the run status of the queries being run
    q_fin = False
    logging.info("Checking status of run(s). Check every 10s until all have finished")
    while not q_fin:
        # For loop to go through dict and check all run ids
        for s_id, s_vals in ld_dict.items():
            run_id = s_vals['post_data']['pq_id']
            tenant = s_vals['tenant_id']
            run_status = get_ld_run_status(tenant_url_data, tenant, run_id)
            # todo: need to work out what to do when it fails
            status = run_status['status']
            logging.debug("run status: {0}".format(status))
            s_vals['post_data']['status'] = status
            s_vals['post_data']['time_remaining'] = run_status['timeRemainingInSeconds']
            s_vals['post_data']['finishedAt'] = run_status.get('finishedAt', None)
            s_vals['post_data']['statuses'] = run_status['endpointCounts']['statuses']

        q_fin = loop_check()
        if not q_fin:
            logging.debug("Sleep for 10s")
            sleep(10)
    else:
        logging.info("All query runs have finished")
        return ld_dict


def get_ld_run_status(tenant_url_data, tenant, run_id):
    url_ext = "/runs/{0}".format(run_id)

    for key, value in tenant_url_data.items():
        if key == tenant:
            url = "{0}{1}".format(value['orig_url'], url_ext)
            headers = value['headers']
            headers['Content-Type'] = "application/json"
            logging.info("Check run id: {0}".format(run_id))
            run_status = get_api.get_page(url, headers)

    return run_status


def get_ld_endpoints(tenant_url_data, run_data):
    def get_runid_eps():
        for key, value in tenant_url_data.items():
            if key == tenant:
                url = "{0}{1}".format(value['orig_url'], url_ext)
                pagetotal_url = "{0}?pageSize={1}&pageTotal=true".format(url, page_size)
                headers = value['headers']
                headers['Content-Type'] = "application/json"
                ten_data = dict()
                ten_data[key] = {'filename': value['filename'], 'url': value['url'], 'orig_url': url,
                                 'pageurl': pagetotal_url, 'name': value['name'], 'headers': headers}
                # Get the page totals
                logging.debug("get_runid_eps loop ten info orig_url: {0}".format(ten_data[key]['orig_url']))
                page_data = get_api.get_data(ten_data, page_size, tenant, api)
                logging.debug("get_runid_eps loop, page data: {0}".format(page_data))
                return page_data

    ld_ep_dict = dict()

    for r_id, r_value in run_data.items():
        run_id = r_value['post_data']['pq_id']
        tenant = r_value['tenant_id']
        url_ext = "/runs/{0}/endpoints".format(run_id)
        pg_info = get_runid_eps()
        ld_ep_dict[run_id] = pg_info

    return ld_ep_dict


def get_run_results(tenant_url_data, run_data, size):
    def get_results():
        for key, value in tenant_url_data.items():
            if key == tenant:
                url = "{0}{1}".format(value['orig_url'], url_ext)
                pagetotal_url = "{0}?pageSize={1}&pageTotal=true".format(url, size)
                headers = value['headers']
                headers['Content-Type'] = "application/json"
                ten_data = dict()
                ten_data[key] = {'filename': value['filename'], 'url': value['url'], 'orig_url': url,
                                 'pageurl': pagetotal_url, 'name': value['name'], 'headers': headers}
                # Get the page totals
                logging.info("Gather page data for results")
                page_data = get_api.get_data(ten_data, size, tenant, api)
                return page_data

    q_res_dict = dict()

    # For loop to go through the dict and check all run ids
    for s_id, s_vals in run_data.items():
        run_id = s_vals['post_data']['pq_id']
        url_ext = "/runs/{0}/results".format(run_id)
        success_withdata = s_vals['post_data']['statuses']['finished']['succeeded']['withData']
        terminated = s_vals['post_data']['terminated']
        logging.info("Checking whether any endpoints completed with data")
        if success_withdata > 0:
            logging.info("Some endpoints have returned data")
            logging.info("Waiting 2 minutes to start gathering results")
            tenant = s_vals['tenant_id']
            sleep(120)
            res_data = get_results()
            q_res_dict[s_id] = res_data
        elif terminated:
            logging.info("This query was terminated, skipping")
            pass
        else:
            logging.info("No results have been returned for this run id: '{0}'".format(s_vals['post_data']['pq_id']))
            q_res_dict[s_id] = {"tenant": s_vals['tenant_id'], "results": "No EPs completed with data"}

    return q_res_dict


def build_run_report():
    logging.info("Coming soon")
    exit(1)
    # todo: Based on the results build a report


def get_misp_attributes(misp_url, search_type, search_val, misp_tok, wildcard):
    # create body to search for the attributes
    if search_type == "eventid":
        http_body = {"returnFormat": "json", "eventid": "{0}".format(search_val), "type": {"OR": ["ip-src", "ip-dst",
                                                                                                  "md5", "sha256",
                                                                                                  "filename", "domain",
                                                                                                  "uri", "hostname"]}}
    elif search_type == "tag":
        http_body = {"returnFormat": "json", "tags": "{0}".format(search_val), "type": {"OR": ["ip-src", "ip-dst",
                                                                                               "md5", "sha256",
                                                                                               "filename", "domain",
                                                                                               "uri", "hostname"]}}
    else:
        logging.error("Search type not yet set. Update function: 'get_misp_attributes' with new type")
        return None

    misp_headers = dict()
    misp_headers["Authorization"] = "{0}".format(misp_tok)
    misp_headers["Accept"] = "application/json"
    misp_headers["Content-Type"] = "application/json"

    res_sess = requests.session()
    retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504, 429])
    res_sess.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))

    try:
        misp_res = res_sess.post(misp_url, headers=misp_headers, json=http_body)
        misp_res.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logging.error(http_err)
        exit(1)
    finally:
        attr_list = list()
        attr_dict = dict()
        json_res = misp_res.json()
        json_resp = json_res['response']
        json_att = json_resp['Attribute']
        for item in json_att:
            if item['type'] == "ip-src" or item['type'] == "ip-dst":
                ind_type = "ip"
            elif item['type'] == "uri":
                ind_type = "url"
            elif item['type'] == "hostname":
                ind_type = "domain"
            else:
                ind_type = item['type']

            if wildcard:
                attr_list.append(
                    {"indicator_type": ind_type, "misp_type": item['type'], "data": "%{0}%".format(item['value'])})
            else:
                attr_list.append(
                    {"indicator_type": ind_type, "misp_type": item['type'], "data": "{0}".format(item['value'])})

        attr_dict['ioc_data'] = attr_list
        attrib = json.dumps(attr_dict)
        res_sess.close()

        return attrib
