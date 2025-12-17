import pytest


def test_import_crawlers():
    from crawlers.gem_crawler import GeMAIECrawler
    from crawlers.powergrid_crawler import POWERGRIDCrawler
    from crawlers.state_seb_crawler import StateElectricityCrawler
    from crawlers.ntpc_crawler import NTPCCrawler
    assert GeMAIECrawler and POWERGRIDCrawler and StateElectricityCrawler and NTPCCrawler
