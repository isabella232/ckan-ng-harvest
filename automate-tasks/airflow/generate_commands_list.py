"""
generate a list of the commands to harvest
"""
import argparse
# from settings import APP_PATH
APP_PATH = '/home/hudson/dev/datopian/harvesting-data-json-v2'
import sys
sys.path.append(APP_PATH)
import shlex
from harvester.data_gov_api import CKANPortalAPI
from harvester.logs import logger
from jinja2 import Template
from settings import CKAN_BASE_URL, CKAN_API_KEY, PYTHON_ENV_PATH

catalog_url = CKAN_BASE_URL
catalog_api_key = CKAN_API_KEY

parser = argparse.ArgumentParser()
parser.add_argument("--source_type", type=str, default='datajson', help="Tipe of harvest source: datajson|csw|waf etc")
args = parser.parse_args()
source_type = args.source_type

cpa = CKANPortalAPI(base_url=catalog_url, api_key=catalog_api_key)
urls = []

templated_harvest_command = """
            source {{ env_path }}/bin/activate
            cd {{ app_path }}
            python harvest.py \
                --name {{ name }} \
                --url {{ data_json_url }} \
                --harvest_source_id {{ harvest_source_id }} \
                --ckan_owner_org_id {{ ckan_org_id }} \
                --catalog_url {{ catalog_url }} \
                --ckan_api_key {{ ckan_api_key }}
            """

results = cpa.search_harvest_packages(rows=1000, harvest_type='harvest', source_type=source_type)
for datasets in results:
    for harvest_source in datasets:

        url = harvest_source['url']
        if url in urls:  # avoid duplicates
            continue
        urls.append(url)

        organization = harvest_source['organization']
        name = harvest_source['name']
        # this is the ID of the organization at the external source
        # we need to get our local organizaion ID
        ckan_org_id = harvest_source['owner_org']
        context = {
            'env_path': PYTHON_ENV_PATH,
            'app_path': APP_PATH,
            'name': name,
            'data_json_url': shlex.quote(url),
            'harvest_source_id': harvest_source['id'],  # check if this is the rigth ID
            'ckan_org_id': ckan_org_id,
            'catalog_url': shlex.quote(catalog_url),
            'ckan_api_key': catalog_api_key
            }

        template = Template(templated_harvest_command)
        print(template.render(**context))
