"""
Get updated list of resources from a data.json file
Get the actual list of resources in data.gov
Compare both and upgrade data.gov 

Using:
 - DataFlows: https://github.com/datahq/dataflows/blob/master/TUTORIAL.md
 - DataPackages: https://frictionlessdata.io/data-packages/ + https://github.com/frictionlessdata/datapackage-py
"""

from dataflows import Flow, printer, dump_to_path, load, update_resource
# from dataflows.join import join_with_self
import json
import os
from logs import logger
from functions_v2 import (get_data_json_from_url, 
                            clean_duplicated_identifiers,
                            get_actual_ckan_resources_from_api,
                            dbg_packages
                            )
import config
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--url", type=str, help="URL of the data.json")
parser.add_argument("--name", type=str, help="Name of the resource (for generate the containing folder)")
parser.add_argument("--force_download", action='store_true',
                                        help="Force download or just use local data.json prevously downloaded")
parser.add_argument("--harvest_source_id", type=str, help="Source ID for filter CKAN API")

args = parser.parse_args()

config.SOURCE_NAME = args.name  # Nice name of the source
config.SOURCE_ID = args.harvest_source_id
config.SOURCE_URL = args.url  # data.json final URL

Flow(
    # not working (why?) => load(load_source=url, name='datajson'),
    get_data_json_from_url(config.SOURCE_URL, name=config.SOURCE_NAME,
                            data_json_path=config.get_datajson_cache_path()),  
    
    # I like to split _headers_ and ['dataset'] as two different resources. Then valid the headers from one side and process the ['dataset'] as rows independently. It's a good idea?
    update_resource('res_1', name='datajson'),
    
    clean_duplicated_identifiers,  # when a processor has a _rows_ param, How do you know from which resource specifically the rows should be processed?
    # replace with "join_with_self" join_with_self(source_name, source_key, target_name, fields),
    
    dbg_packages,  # get info about packaghes

    # add other resource to this process. The packages list from data.gov
    get_actual_ckan_resources_from_api(harvest_source_id=config.SOURCE_ID,
                                        results_json_path=config.get_ckan_results_cache_path()),
    update_resource('res_2', name='ckanapi'),
    
    dbg_packages,  # get info about updated packaghes
    
    dump_to_path(config.get_base_path()),
    # printer(num_rows=1), # , tablefmt='html')
    
).process()[1]