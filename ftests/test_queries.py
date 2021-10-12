from selenium.webdriver.common.by import By

# from selenium.webdriver.common.keys import Keys


def test_queries(queriesPage):
    """Tests the word page

    *   check the page title
    *   change to advanced mode
    *   check the number of queries
    """

    (browser, waits) = queriesPage
    getElem = waits["elem"]
    getTitle = waits["title"]

    assert getTitle("Queries")

    exampleQuery = getElem(By.CSS_SELECTOR, """[query_id="968"]""", maxWait=10)
    assert exampleQuery.get_attribute("textContent") == "D Roorda: Qamets Qatan"

    advancedElem = getElem(By.ID, "c_view_advanced")
    advancedElem.click()

    totalElem = getElem(By.CSS_SELECTOR, ".total", maxWait=10)
    assert totalElem.get_attribute("textContent") == "1203"
