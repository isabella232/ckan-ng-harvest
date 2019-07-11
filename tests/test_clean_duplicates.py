"""
Tests all functions used in flow file
"""
import unittest
import config
from functions import (get_data_json_from_url, 
                            clean_duplicated_identifiers,
                            get_current_ckan_resources_from_api,
                            dbg_packages,
                            compare_resources
                            )


base_url = 'https://avdata99.gitlab.io/andres-harvesting-experiments-v2'

class FunctionsDuplicatesTestClass(unittest.TestCase):

    def test_clean_duplicated_identifiers_bad_field(self):
        rows = [{'bad_field_identifier': 'ya/&54'}]

        with self.assertRaises(KeyError):
            for dataset in clean_duplicated_identifiers(rows):
                self.assertIsInstance(dataset, dict)
    
    def test_clean_duplicated_identifiers(self):
        rows = [{'identifier': 'ya/&54'}]

        total_ok = 0
        for dataset in clean_duplicated_identifiers(rows):
            self.assertIsInstance(dataset, dict)
            total_ok += 1
        
        total_duplicates = len(rows) - total_ok

        self.assertEqual(total_ok, 1)
        self.assertEqual(total_duplicates, 0)

    def test_clean_duplicated_identifiers2(self):
        rows = [{'identifier': 'ya/&54'}, {'identifier': 'ya/&54', 'other field': 99}]

        total_ok = 0
        for dataset in clean_duplicated_identifiers(rows):
            self.assertIsInstance(dataset, dict)
            total_ok += 1
        
        total_duplicates = len(rows) - total_ok

        self.assertEqual(total_ok, 1)
        self.assertEqual(total_duplicates, 1)
    

    def test_clean_duplicated_identifiers3(self):
        rows = [{'identifier': 'ya/&54'},
                {'identifier': 'ya/&54', 'other field': 99},
                {'identifier': 'VVVVVV', 'other field': 99}]

        total_ok = 0
        for dataset in clean_duplicated_identifiers(rows):
            self.assertIsInstance(dataset, dict)
            total_ok += 1
        
        total_duplicates = len(rows) - total_ok

        self.assertEqual(total_ok, 2)
        self.assertEqual(total_duplicates, 1)
    
        