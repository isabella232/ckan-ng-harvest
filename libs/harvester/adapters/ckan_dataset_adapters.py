''' transform datasets to CKAN datasets '''
from slugify import slugify
from abc import ABC, abstractmethod
from harvester.settings import ckan_settings


class CKANDatasetAdapter(ABC):
    ''' transform other datasets objects into CKAN datasets '''

    def __init__(self, original_dataset):
        self.original_dataset = original_dataset
        self.ckan_dataset = self.get_base_ckan_dataset()

    def get_base_ckan_dataset(self):
        # creates the Dict base for a CKAN dataset
        # Check for required fields: https://docs.ckan.org/en/2.8/api/#ckan.logic.action.create.package_create

        pkg = {
            'name': '',  # no spaces, just lowercases, - and _
            'title': '',
            'owner_org': '',  # (string) – the id of the dataset’s owning organization, see organization_list() or organization_list_for_user() for available values. This parameter can be made optional if the config option ckan.auth.create_unowned_dataset is set to True.
            'private': False,
            'author': None,  # (string) – the name of the dataset’s author (optional)
            'author_email': None,  # (string) – the email address of the dataset’s author (optional)
            'maintainer': None,  # (string) – the name of the dataset’s maintainer (optional)
            'maintainer_email': None,  # (string) – the email address of the dataset’s maintainer (optional)
            # just aded when license exists
            # 'license_id': None,  # (license id string) – the id of the dataset’s license, see license_list() for available values (optional)
            'notes':  None,  # (string) – a description of the dataset (optional)
            'url': None,  # (string) – a URL for the dataset’s source (optional)
            'version': None,  # (string, no longer than 100 characters) – (optional)
            'state': 'active',  # (string) – the current state of the dataset, e.g. 'active' or 'deleted'
            'type': None,  # (string) – the type of the dataset (optional), IDatasetForm plugins associate themselves with different dataset types and provide custom dataset handling behaviour for these types
            'resources': None,  # (list of resource dictionaries) – the dataset’s resources, see resource_create() for the format of resource dictionaries (optional)
            'tags': None,  # (list of tag dictionaries) – the dataset’s tags, see tag_create() for the format of tag dictionaries (optional)
            'extras': [  # (list of dataset extra dictionaries) – the dataset’s extras (optional), extras are arbitrary (key: value) metadata items that can be added to datasets, each extra dictionary should have keys 'key' (a string), 'value' (a string)
                {'key': 'resource-type', 'value': 'Dataset'}
            ],
            'relationships_as_object': None,  # (list of relationship dictionaries) – see package_relationship_create() for the format of relationship dictionaries (optional)
            'relationships_as_subject': None,  # (list of relationship dictionaries) – see package_relationship_create() for the format of relationship dictionaries (optional)
            'groups': None,  # (list of dictionaries) – the groups to which the dataset belongs (optional), each group dictionary should have one or more of the following keys which identify an existing group: 'id' (the id of the group, string), or 'name' (the name of the group, string), to see which groups exist call group_list()
        }

        return pkg

    @abstractmethod
    def transform_to_ckan_dataset(self):
        pass

    def identify_origin_element(self, raw_field):
        # get the original value in original dict (the one to convert) to put in CKAN dataset.
        # Consider the __ separator
        # in 'contactPoint__hasEmail' gets in_dict['contactPoint']['hasEmail'] if exists
        # in 'licence' gets in_dict['licence'] if exists

        parts = raw_field.split('__')
        if parts[0] not in self.original_dataset:
            return None
        origin = self.original_dataset[parts[0]]
        if len(parts) > 1:
            for part in parts[1:]:
                if part in origin:
                    origin = origin[part]
                else:  # drop
                    return None
        return origin

    def validate_final_dataset(self):
        # check required https://docs.ckan.org/en/2.8/api/#ckan.logic.action.create.package_create

        if 'private' not in self.ckan_dataset:
            return False, 'private is a required field'
        if 'name' not in self.ckan_dataset:
            return False, 'name is a required field'

        return True, None

    def set_destination_element(self, raw_field, new_value):
        # in 'extras__issued' gets or creates self.ckan_dataset[extras][key][issued] and assing new_value to self.ckan_dataset[extras][value]
        # in 'title' assing new_value to self.ckan_dataset[title]
        # returns dict modified

        parts = raw_field.split('__')
        if parts[0] not in self.ckan_dataset:
            raise Exception(f'Not found field "{parts[0]}" at CKAN destination dict')
        if len(parts) == 1:
            self.ckan_dataset[raw_field] = self.fix_fields(field=raw_field,
                                                             value=new_value)
            return self.ckan_dataset
        elif len(parts) == 2:
            if parts[0] != 'extras':
                raise Exception(f'Unknown field estructure: "{raw_field}" at CKAN destination dict')

            # check if extra already exists
            for extra in self.ckan_dataset['extras']:

                if extra['key'] == parts[1]:
                    extra['value'] = new_value
                    return self.ckan_dataset

            # this extra do not exists already
            new_extra = {'key': parts[1], 'value': None}
            new_extra['value'] = new_value
            self.ckan_dataset['extras'].append(new_extra)
            return self.ckan_dataset
        else:
            raise Exception(f'Unknown fields length estructure for "{raw_field}" at CKAN destination dict')

    def build_tags(self, tags):
        # create a CKAN tag
        # Help https://docs.ckan.org/en/2.8/api/#ckan.logic.action.create.tag_create
        ret = []
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                tag = slugify(tag[:ckan_settings.MAX_TAG_NAME_LENGTH])
                ret.append({"name": tag})
        return ret

    def set_extra(self, key, value):
        found = False
        for extra in self.ckan_dataset['extras']:
            if extra['key'] == key:
                extra['value'] = value
                found = True
        if not found:
            self.ckan_dataset['extras'].append({'key': key, 'value': value})
        return self.ckan_dataset