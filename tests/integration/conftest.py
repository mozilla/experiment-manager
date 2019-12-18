import pytest
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from pages.home import Home


@pytest.fixture
def capabilities(capabilities):
    capabilities["acceptInsecureCerts"] = True
    return capabilities


@pytest.fixture
def firefox_options(firefox_options):
    """Set Firefox Options."""
    firefox_options.headless = True
    firefox_options.log.level = 'trace'
    return firefox_options


@pytest.fixture(scope="session", autouse=True)
def _verify_url(request, base_url):
    """Verifies the base URL"""
    verify = request.config.option.verify_base_url
    if base_url and verify:
        session = requests.Session()
        retries = Retry(backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount(base_url, HTTPAdapter(max_retries=retries))
        session.get(base_url, verify=False)


@pytest.fixture
def fill_overview(selenium, base_url):
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.name = "This is a test"
    experiment.short_description = "Testing in here"
    experiment.public_name = "Public Name"
    experiment.public_description = "Public Description"
    experiment.bugzilla_url = "http://bugzilla.com/show_bug.cgi?id=1234"
    return experiment
