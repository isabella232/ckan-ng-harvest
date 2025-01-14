import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from harvester_ng import helpers
from harvester_ng.logs import logger
from tools.results.harvested_source import HarvestedSource
from slugify import slugify


logger = logging.getLogger(__name__)


class HarvestSource(ABC):
    """ main harvester class to inherit """
    def __init__(self, name, destination, *args, **kwargs):
        """
            name: custom name for the resource that is harvested
            destination: Object where to get dataset to compare and write results 
        """
        self.name = name  # name of the harvest source
        self.destination = destination
        self.destination.source = self
        self.url = kwargs.get('url', None)  # url to harvest from
        config = kwargs.get('config', {})  # configuration (e.g validation_schema)
        if type(config) == str:
            self.config = json.loads(config)
        else:
            self.config = config
        
        # limit the number of resources to harvest
        self.limit_datasets = 0
    
    @abstractmethod
    def download(self):
        """ donwload, validate and save as data packages
        Returns a DataFlows resource """
        pass

    def save_download_results(self, flow_results):
        """ save results (data package and final datasets results) """
        dest = self.get_download_result_path()
        logger.info(f'Saving downloaded results to {dest}')
        dmp = json.dumps(flow_results[0][0], indent=2)
        f = open(dest, 'w')
        f.write(dmp)
        f.close()

        pkg = flow_results[1]  # package returned
        pkg.save(self.get_data_package_result_path())

    @abstractmethod
    def compare(self):
        """ compare downloaded with destination and define if we need to create or update """
        pass

    def save_compare_results(self, flow_results):
        dest = self.get_comparison_result_path()
        logger.info(f'Saving compared results to {dest}')
        dmp = json.dumps(flow_results[0][0], indent=2)
        f = open(dest, 'w')
        f.write(dmp)
        f.close()

        pkg = flow_results[1]  # package returned
        pkg.save(self.get_comparison_data_package_result_path())

    @abstractmethod
    def write_destination(self):
        """ save changes to destination """
        pass

    def save_write_results(self, flow_results):
        """ save results """
        path = self.get_comparison_result_path()
        logger.info(f'Saving write results to {path}, res {flow_results[0][0]}')
        dmp = json.dumps(flow_results[0][0], indent=2)
        f = open(path, 'w')
        f.write(dmp)
        f.close()

    def write_final_report(self):
        dest = self.get_final_json_results_for_report_path()
        logger.info(f'Generating final report to {dest}')
        # write final process result as JSON
        hs = HarvestedSource(harvest_source_obj=self)
        hs.process_results()

        # write results
        results = hs.get_json_data()
        f = open(dest, 'w')
        f.write(json.dumps(results, indent=2))
        f.close()

        hs.render_template(save=True)

    def get_base_path(self):
        """ Get path for some resource (described as string).
            If none, return the base folder """
        nice_name = slugify(self.name)
        base_path = os.path.join('data', nice_name)

        if not os.path.isdir(base_path):
            os.makedirs(base_path)

        return base_path

    def get_file(self, resource, create=True):
        path = os.path.join(self.get_base_path(), resource)
        if create and not os.path.isfile(path):
            open(path, 'w').close()
        return path
    
    def get_data_packages_folder_path(self):
        """ local path for datapackages """
        data_packages_folder_path = os.path.join(self.get_base_path(), 'data-packages')
        if not os.path.isdir(data_packages_folder_path):
            os.makedirs(data_packages_folder_path)

        return data_packages_folder_path
    
    def get_download_result_path(self, create=True):
        """ local path for flow1 results file """
        return self.get_file(resource='download-results.json', create=create)

    def get_data_package_result_path(self, create=True):
        """ local path for flow1 file """
        return self.get_file(resource='data-package-result.json', create=create)
    
    def get_ckan_results_cache_path(self, create=True):
        """ local path for ckan results file """
        return self.get_file(resource='ckan-results.json', create=create)
    
    def get_comparison_result_path(self, create=True):
        return self.get_file(resource='compare-datasets-results.json', create=create)
    
    def get_comparison_data_package_result_path(self, create=True):
        """ local path for data packages comparison results file """
        return self.get_file(resource='comparison-data-package-result.json', create=create)
        
    def get_data_cache_path(self, create=True):
        """ local path for json source file """
        return self.get_file(resource='data.json', create=create)
        
    def get_errors_path(self, create=True):
        """ local path for errors """
        return self.get_file(resource='errors.json', create=create)
    
    def get_final_json_results_for_report_path(self, create=True):
        return self.get_file(resource='final-results.json', create=create)
    
    def get_html_report_path(self, create=True):
        return self.get_file(resource='final-report.html', create=create)
        
    def get_json_data_or_none(self, path):
        if not os.path.isfile(path):
            return None
        else:
            f = open(path, 'r')
            try:
                j = json.load(f)
            except Exception as e:
                j = {'error': str(e)}
            f.close()
            return j

    def get_report_files(self):
        """ Collect important files to write a final report """
        data_file = self.get_data_cache_path(create=False)
        results_file = self.get_comparison_result_path(create=False)
        errors_file = self.get_errors_path(create=False)

        return {'data': self.get_json_data_or_none(data_file),
                'results': self.get_json_data_or_none(results_file),
                'errors': self.get_json_data_or_none(errors_file)
                }
