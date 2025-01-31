# flake8: noqa
import pytest
from harvesters.csw.harvester import CSWSource
from owslib.csw import CatalogueServiceWeb


class TestCSWClass(object):

    base_url = 'https://datopian.gitlab.io/ckan-ng-harvest'

    # TODO mock a CSW object
    url_services = [
            # 'http://metadata.arcticlcc.org/csw',
            'http://data.nconemap.com/geoportal/csw?Request=GetCapabilities&Service=CSW&Version=2.0.2',
            'http://metadata.usace.army.mil/geoportal/csw?Request=GetCapabilities&Service=CSW&Version=2.0.2',
            'https://meta.geo.census.gov/data/existing/decennial/GEO/GPMB/TIGERline/TIGER2017/arealm/',
            'http://geonode.state.gov/catalogue/csw?service=CSW&version=2.0.2&request=GetRecords&typenames=csw:Record&elementsetname=brief',
            # 'https://portal.opentopography.org/geoportal/csw'
        ]

    def test_clean_url(self):
        csw = CSWSource(url='http://data.nconemap.com/geoportal/csw?Request=GetCapabilities&Service=CSW&Version=2.0.2')
        url = csw.get_cleaned_url()
        new_url = 'http://data.nconemap.com/geoportal/csw'
        assert url == new_url

    def test_base_service_csw(self):
        """ Read https://github.com/geopython/OWSLib/blob/5d057e6b58c3a7ce873ac81c4e574df3c35ad6fa/tests/test_ows_interfaces.py#L26 """
        for url in self.url_services:

            csw = CSWSource(url=url)
            try:
                csw.fetch()
                connected = True
            except Exception as e:
                connected = False
            # since we use remote URLs, if fails to connect is not our error, is a CSW source failing
            if connected and csw.errors == []:

                service = csw.csw
                # Check each service instance conforms to OWSLib interface
                service.alias = 'CSW'
                isinstance(service, CatalogueServiceWeb)
                # URL attribute
                # assert service.url == csw.url
                assert service.url == csw.get_cleaned_url()
                # we change the URL (clean)

                # version attribute
                assert service.version == '2.0.2'
                # Identification object
                assert hasattr(service, 'identification')
                # Check all ServiceIdentification attributes
                assert service.identification.type == 'CSW'
                for attribute in ['type', 'version', 'title', 'abstract', 'keywords', 'accessconstraints', 'fees']:
                    assert hasattr(service.identification, attribute)
                # Check all ServiceProvider attributes
                for attribute in ['name', 'url', 'contact']:
                    assert hasattr(service.provider, attribute)
                # Check all operations implement IOperationMetadata
                for op in service.operations:
                    for attribute in ['name', 'formatOptions', 'methods']:
                        assert hasattr(op, attribute)
                # Check all contents implement IContentMetadata as a dictionary
                # CSW does not work in this way so use dummy
                service.contents = {'dummy': '1'}
                isinstance(service.contents, dict)
                # Check any item (WCS coverage, WMS layer etc) from the contents of each service
                # Check it conforms to IContentMetadata interface
                # CSW does not conform to this
