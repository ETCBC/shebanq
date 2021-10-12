from selenium.webdriver.common.by import By

# from selenium.webdriver.common.keys import Keys


def test_words(wordsPage):
    """Tests the word page

    *   check the page title
    *   check the number of words starting with alef
    *   check the big alef
    """

    (browser, waits, version) = wordsPage
    getElem = waits["elem"]
    getTitle = waits["title"]

    assert getTitle("Words")

    numberElem = getElem(By.ID, "nwords")
    expNumber = 833 if version == "2017" else 831 if version == "2021" else 0
    assert numberElem.get_attribute("textContent") == f"{expNumber} words"

    firstResult = getElem(By.CSS_SELECTOR, "h1.dletterh")
    assert firstResult.get_attribute("textContent") == "א"


def test_word(wordsPage):
    """Tests an individual word from the list.

    We pick the first word in the list and do this

    *   check the gloss and the text  of the entry
        in the two separate forms (with and without trailing `/`)
    *   check which one of the two forms is displayed
    *   switch to the other display by clicking on the gloss
    *   check again which one of the two forms is displayed
    *   navigate to the record page of the word by clicking on the word
    *   find the link to navigate back to the overview page
    *   click that link
    *   go to the selected word on the overview page
        and check that the gloss is "father"

    """

    (browser, waits, version) = wordsPage
    getElem = waits["elem"]

    infoElems = {}
    for (att, expected) in (
        ("gi", "father"),
        ("wi", "אב"),
        ("wii", "אב/"),
    ):
        wordElem = getElem(By.CSS_SELECTOR, f"""a[{att}="1ABn"]""")
        assert wordElem.get_attribute("textContent") == expected
        infoElems[att] = wordElem

    for att in ["wi", "wii"]:
        wordElem = infoElems[att]
        assert (
            wordElem.value_of_css_property("display") == "inline"
            if att == "wi"
            else "none"
        )

    infoElems["gi"].click()
    for att in ["wi", "wii"]:
        wordElem = infoElems[att]
        assert (
            wordElem.value_of_css_property("display") == "none"
            if att == "wi"
            else "inline"
        )
    linkElem = infoElems["wii"]
    linkElem.click()
    gobackElem = getElem(By.ID, "gobackw")
    gobackElem.click()
    selectedElem = getElem(By.CSS_SELECTOR, ".d.selecthlw")
    infoElem = selectedElem.find_element(By.CSS_SELECTOR, "[gi]")
    assert infoElem.get_attribute("textContent") == "father"
