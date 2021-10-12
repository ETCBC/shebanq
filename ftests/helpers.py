from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
    title_is,
)


def getWaits(driver):
    """Inspection methods that need a wait

    We define methods to get an element and to verify the window title.
    They will be invoked on a `wait` object, so that they execute
    when the conditions under which they can run have been met.

    Parameters
    ----------
    driver
        A driver object.

    Returns
    -------
    waits
        A dictionary keyed by a short name of the method, and valued
        by functions bound to the wait object, that find something
        on the page.
    """

    def getElem(method, address, maxWait=1):
        wait = WebDriverWait(driver, timeout=maxWait)
        return wait.until(presence_of_element_located((method, address)))

    def getTitle(title, maxWait=1):
        wait = WebDriverWait(driver, timeout=maxWait)
        return wait.until(title_is(title))

    return dict(elem=getElem, title=getTitle)
