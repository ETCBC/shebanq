"""Set up testing the SHEBANQ site

Here we set up the scene.
By means of
[fixtures]({{pytestFixtures}})
we define the web-app objects
to be tested and the web clients to exercise functions in those objects.

We use [selenium]({{selenium}}) to drive the web-browser.

"""

import pytest
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By

from .helpers import getWaits


# import magic  # noqa


BASE_URL = "https://127.0.0.1:8100/shebanq"


@pytest.fixture(scope="session")
def browser():
    """The browser driver

    We launch the SHEBANQ site in preparation of doing many tests.

    We do not only deliver a driver, but also a wait object.
    """

    with Safari() as driver:
        yield driver

    print("Closing test browser")


@pytest.fixture(scope="module", params=["2017", "2021"])
def wordsPage(browser, request):
    """The words page, loaded in the browser.

    We parametrize it with the ETCBC data versions 2017 and 2021.
    That means, we have separate fixtures for the words page in these two versions.

    We also compose the `waits` dictionary, from which the test functions
    can derive methods for getting elements with proper waiting built into them.

    And we return the version.
    """

    waits = getWaits(browser)
    getElem = waits["elem"]

    theUrl = f"{BASE_URL}/hebrew/words?version={request.param}"
    testId = "letters"

    browser.get(theUrl)
    getElem(By.ID, testId)

    return (browser, waits, request.param)


@pytest.fixture(scope="module")
def queriesPage(browser, request):
    """The queries page, loaded in the browser.

    We parametrize it with the ETCBC data versions 2017 and 2021.
    That means, we have separate fixtures for the words page in these two versions.

    We also compose the `waits` dictionary, from which the test functions
    can derive methods for getting elements with proper waiting built into them.

    And we return the version.
    """

    waits = getWaits(browser)
    getElem = waits["elem"]

    theUrl = f"{BASE_URL}/hebrew/queries"
    testId = "recentq"

    browser.get(theUrl)
    getElem(By.ID, testId)

    return (browser, waits)
