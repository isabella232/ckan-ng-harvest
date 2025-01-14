import base64
import json
import logging
from abc import ABC, abstractmethod
from harvester_adapters.ckan.api import CKANPortalAPI
from harvester_ng.logs import logger


logger = logging.getLogger(__name__)


class HarvestDestination(ABC):
    """ main harvest destination class to inherit """
    def __init__(self, *args, **kwargs):
        self.source = None  # class who call use this class as destination
        # configuration (e.g: CKAN uses validator_schema)
        config = kwargs.get('config', {})  # configuration (e.g validation_schema)
        if type(config) == str:
            self.config = json.loads(config)

    @abstractmethod
    def yield_datasets(self):
        """ get datasets to compare and analyze differences """
        pass

    ''' moved to flows file. Fails when using as dataflows processor 
    @abstractmethod
    def write_results(self):
        """ save final dataset to destination """
        pass
    '''

    @abstractmethod
    def destination_type(self):
        """ class name """
        pass
    
    def __str__(self):
        return self.destination_type()



class CKANHarvestDestination(HarvestDestination):
    """ CKAN destination for harvested data """
    def __init__(self, catalog_url, api_key, organization_id, harvest_source_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_url = catalog_url
        self.api_key = api_key
        self.organization_id = organization_id
        self.harvest_source_id = harvest_source_id
        logger.info(f'Harvest destination set: {catalog_url}')
    
    def destination_type(self):
        return "CKAN"

    def yield_datasets(self, harvest_source_id, save_results_json_path=None):
        
        logger.info(f'Extracting from harvest source id: {harvest_source_id}')
        cpa = CKANPortalAPI(base_url=self.catalog_url)
        resources = 0

        page = 0
        for datasets in cpa.search_harvest_packages(harvest_source_id=harvest_source_id):
            # getting resources in pages of packages
            page += 1
            logger.info('PAGE {} from harvest source id: {}'.format(page, harvest_source_id))
            for dataset in datasets:
                pkg_resources = len(dataset['resources'])
                resources += pkg_resources
                yield(dataset)

        logger.info('{} total resources in harvest source id: {}'.format(resources, harvest_source_id))
        if save_results_json_path is not None:
            cpa.save_packages_list(path=save_results_json_path)
