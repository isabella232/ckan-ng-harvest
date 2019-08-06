from logs import logger
import config
from libs.ckan_dataset_adapters import DataJSONSchema1_1
from libs.data_gov_api import CKANPortalAPI
import json
from datetime import datetime
import pytz
import hashlib


def hash_dataset(datasetdict):
    # hash the dataset.
    # We change the way that previous harvester do this
    #  https://github.com/GSA/ckanext-datajson/blob/datagov/ckanext/datajson/harvester_base.py#L730
    dmp_dataset = json.dumps(datasetdict, sort_keys=True)
    str_to_hash = dmp_dataset.encode('utf-8')
    return hashlib.sha1(str_to_hash).hexdigest()


def assing_collection_pkg_id(rows):
    """ detect new CKAN ids for collections """

    # create a list of datajson identifiers -> CKAN indetifiers
    # to detect collection IDs
    related_ids = {}
    missing_rows = []
    for row in rows:
        comparison_results = row['comparison_results']
        action = comparison_results['action']
        if action != 'update':  # just resources
            yield row
        else:
            datajson_dataset = comparison_results['new_data']
            old_identifier = datajson_dataset['identifier']  # ID at data.json
            new_identifier = row['id']  # ID at CKAN
            related_ids[old_identifier] = new_identifier

            # if dataset was marked as a collection, set its CKAN id
            if datajson_dataset.get('collection_pkg_id', None) is None:
                yield row
            else:
                old_identifier = datajson_dataset['identifier']  # ID at data.json
                new_identifier = related_ids.get(old_identifier, None)
                if new_identifier is not None:
                    datajson_dataset['collection_pkg_id'] = new_identifier
                    yield row
                else:
                    # the CKAN ID is not loaded at related_ids at the moment. Try it later
                    missing_rows.append(row)

    for row in missing_rows:
        comparison_results = row['comparison_results']
        datajson_dataset = comparison_results['new_data']
        old_identifier = datajson_dataset['identifier']  # ID at data.json
        new_identifier = related_ids.get(old_identifier, None)
        if new_identifier is not None:
            datajson_dataset['collection_pkg_id'] = new_identifier
        else:
            # it's an error. We must have a CKAN ID
            datajson_dataset['collection_pkg_id'] = ''  # later we  notify the error in results

        yield row


def write_results_to_ckan(rows):
    """ each row it's a dataset to delete/update/create """

    actions = {}
    c = 0
    for row in rows:
        c += 1

        comparison_results = row['comparison_results']
        action = comparison_results['action']
        if action not in actions.keys():
            actions[action] = {'total': 0, 'success': 0, 'fails': 0}
        actions[action]['total'] += 1

        dump_comp_res = json.dumps(comparison_results, indent=4)
        # logger.info(f'Previous results {dump_comp_res}')
        """ comparison_results is something like this
        row['comparison_results'] {
            "action": "update" | "delete" | "create",
            "ckan_id": "1bfc8520-17b0-46b9-9940-a6646615436c",
            "new_data": {data json dataset format},
            "reason": "Some reason for the action"
            }
        """

        results = {'success': False, 'warnings': [], 'errors': []}
        comparison_results['action_results'] = results

        if action == 'error':
            results['errors'].append(comparison_results['reason'])
            yield row
            continue

        # if it's an update we need to merge internal resources
        if action == 'update':
            existing_resources = row['resources']
        elif action == 'create':
            existing_resources = None

        if action in ['update', 'create']:
            datajson_dataset = comparison_results['new_data']

            # add required extras
            # set catalog extras
            for key, value in datajson_dataset['headers'].items():
                if key in ['@context', '@id', 'conformsTo', 'describedBy']:
                    datajson_dataset[f'catalog_{key}'] = value

            schema_version = datajson_dataset['headers']['schema_version']  # 1.1 or 1.0
            assert schema_version in ['1.0', '1.1']  # main error
            datajson_dataset['source_schema_version'] = schema_version
            datajson_dataset['source_hash'] = hash_dataset(datasetdict=datajson_dataset)

            # harvest extras
            # check if a local harvest source is required
            # https://github.com/ckan/ckanext-harvest/blob/master/ckanext/harvest/logic/action/create.py#L27
            datajson_dataset['harvest_ng_source_title'] = config.SOURCE_NAME
            datajson_dataset['harvest_ng_source_id'] = config.SOURCE_ID

            # CKAN hides this extras if we not define as harvest type
            # if https://github.com/ckan/ckanext-harvest/blob/3a72337f1e619bf9ea3221037ca86615ec22ae2f/ckanext/harvest/plugin.py#L125
            datajson_dataset['harvest_source_title'] = config.SOURCE_NAME
            datajson_dataset['harvest_source_id'] = config.SOURCE_ID

            if schema_version == '1.1':
                djss = DataJSONSchema1_1(original_dataset=datajson_dataset)
            else:
                results['errors'].append('We are not ready to harvest 1.0 schema datasets. Add it to harvester')
                yield row
                continue
                # raise Exception('We are not ready to harvest 1.0 schema datasets. Check if this kind of dataset still exists')
            # ORG is required!
            djss.ckan_owner_org_id = config.CKAN_OWNER_ORG

            if datajson_dataset.get('collection_pkg_id', None) == '':
                results['warnings'].append('Failed to get the collection_pkg_id')

            ckan_dataset = djss.transform_to_ckan_dataset(existing_resources=existing_resources)

        if action == 'create':
            cpa = CKANPortalAPI(base_url=config.CKAN_CATALOG_URL,
                                api_key=config.CKAN_API_KEY)

            try:
                ckan_response = cpa.create_package(ckan_package=ckan_dataset)
            except Exception as e:
                ckan_response = {'success': False, 'error': str(e)}

            results = {'success': ckan_response['success']}
            results['ckan_response'] = ckan_response

            if ckan_response['success']:
                actions[action]['success'] += 1
            else:
                actions[action]['fails'] += 1

        elif action == 'update':
            cpa = CKANPortalAPI(base_url=config.CKAN_CATALOG_URL,
                                api_key=config.CKAN_API_KEY)

            try:
                ckan_response = cpa.update_package(ckan_package=ckan_dataset)
            except Exception as e:
                ckan_response = {'success': False, 'error': str(e)}

            results = {'success': ckan_response['success']}
            results['ckan_response'] = ckan_response

            if ckan_response['success']:
                actions[action]['success'] += 1
            else:
                actions[action]['fails'] += 1

        elif action == 'delete':
            ckan_id = row['comparison_results']['ckan_id']
            cpa = CKANPortalAPI(base_url=config.CKAN_CATALOG_URL, api_key=config.CKAN_API_KEY)

            try:
                ckan_response = cpa.delete_package(ckan_package_ir_or_name=ckan_id)
            except Exception as e:
                ckan_response = {'success': False, 'error': str(e)}

            results = {'success': ckan_response['success']}
            results['ckan_response'] = ckan_response

            if ckan_response['success']:
                actions[action]['success'] += 1
            else:
                actions[action]['fails'] += 1

        elif action == 'ignore':
            continue
            results = {'success': True}

        else:
            error = 'Unexpected action for this dataset: {}'.format(action)
            results = {'success': False, 'error': error}

        results['timestamp'] = datetime.now(pytz.utc).isoformat()  # iso format move as string to save to disk
        yield row

    logger.info(f'Actions detected {actions}')


def write_final_report():
    """ take all generated data and write a final report """
    pass

def build_validation_error_email(error_items):
    #header errors
    errors = {}
    header_errors_path = config.get_datajson_headers_validation_errors_path()
    f = open(header_errors_path, "r")
    header_errors = f.read()
    errors['header_errors'] = header_errors

    #dataset errors
    errors['dataset_errors'] = []
    for item in error_items:
        if len(item['comparison_results']['new_data']['validation_errors']) > 0:
            errors['dataset_errors'].append(item['comparison_results']['new_data']['validation_errors'])

    #duplicate errors
    # TODO add duplicate errors to email

    #send validation email
    send_validation_error_email(errors)


def send_validation_error_email(errors):
    """ take all errors and send to organization admins """
    if len(errors) > 0:
        msg = errors
        admin_users = get_admin_users()
        recipients = []
        for user in admin_users:
            member_details = get_user_info(user[0])
            if member_details['email']:
                recipients.append({
                    'name': member_details['name'],
                    'email': member_details['email']
                })

            for recipient in recipients:
                email = {'recipient_name': recipient['name'],
                         'recipient_email': recipient['email'],
                         'subject': 'Harvesting Job - Error Notification',
                         'body': msg}
                # TODO find email server to send email
                # try:
                #     mail_recipient(**email)
                # except MailerException:
                #     logger.error('Sending Harvest-Notification-Mail failed. Message: ' + msg)
                # except Exception as e:
                #     logger.error(e)


def get_admin_users():
    """ fetch admin users from an organization """
    owner_org = config.CKAN_OWNER_ORG
    cpa = CKANPortalAPI(base_url=config.CKAN_CATALOG_URL,
                        api_key=config.CKAN_API_KEY)
    res = cpa.get_admin_users(organization_id=owner_org)
    return res['result']


def get_user_info(user_id):
    """ fetch admin users from an organization """
    cpa = CKANPortalAPI(base_url=config.CKAN_CATALOG_URL,
                        api_key=config.CKAN_API_KEY)
    res = cpa.get_user_info(user_id=user_id)
    return res['result']
