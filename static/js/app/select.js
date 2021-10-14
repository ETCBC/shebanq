/* eslint-env jquery */
/* globals Config, PG, VS */

/**
 * @module select
 */

import { closeDialog, DOC_NAME } from "./helpers.js"

/**
 * Handles book and chapter selection
 */
export class SelectPassage {

  constructor() {
    this.name = "select_passage"
    this.hid = `#${this.name}`
    this.book = new SelectBook()
    this.select = new SelectItems("chapter")
    $("#self_link").hide()
  }

  /** apply current passage selection
   *
   * New material is fetched from the current data version;
   *
   * The link to the feature documentation is adapted the
   * data version.
   *
   * !!! caution
   *     But currently the docs are no longer
   *     dependent on the data version.
   *
   * The links to other applications are adapted to the
   * new passage selection:
   *
   * *   bol = [Bible Online Learner]({{bol}})
   * *   pbl = [ParaBible]({{parabible}})
   *
   * @see Page elements:
   *
   * *   [∈ info][elem-info]
   * *   [∈ version][elem-version]
   * *   [∈ links][elem-links]
   */
  apply() {
    const { versions, featureHost, bolUrl, pblUrl } = Config

    const thisFeaturehost = `${featureHost}/${DOC_NAME}`
    $(".source").attr("href", thisFeaturehost)
    $(".source").attr("title", "BHSA feature documentation")
    $(".mvradio").removeClass("ison")
    $(`#version_${PG.version}`).addClass("ison")
    const bolElem = $("#bol_lnk")
    const pblElem = $("#pbl_lnk")

    for (const v of versions) {
      this.selectVersion(v)
    }
    if (PG.mr == "m") {
      this.book.apply()
      this.select.apply()
      $(this.hid).show()
      const book = VS.book()
      const chapter = VS.chapter()
      if (book != "x" && chapter > 0) {
        bolElem.attr("href", `${bolUrl}/ETCBC4/${book}/${chapter}`)
        bolElem.show()
        pblElem.attr("href", `${pblUrl}/${book}/${chapter}`)
        pblElem.show()
      } else {
        bolElem.hide()
        pblElem.hide()
      }
    } else {
      $(this.hid).hide()
      bolElem.hide()
      pblElem.hide()
    }
  }

  /**
   * Switch to another version of the ETCBC data, such as 4b or 2021
   *
   * *   [∈ version][elem-version]
   */
  selectVersion(v) {
    const { sidebars } = PG

    $(`#version_${v}`).off("click").click(e => {
      e.preventDefault()
      sidebars.sideFetched["mw"] = false
      sidebars.sideFetched["mq"] = false
      sidebars.sideFetched["mn"] = false
      VS.setMaterial({ version: v })
      PG.go()
    })
  }
}

/**
 * Handles selection of a result page
 */
export class SelectResultPage {
  constructor() {
    this.name = "select_pages"
    this.hid = `#${this.name}`
    this.select = new SelectItems("page")
  }

  apply() {
    /* apply result page selection: fill in headings on the page
     */
    if (PG.mr == "r") {
      this.select.apply()
      $(this.hid).show()
    } else {
      $(this.hid).hide()
    }
  }

  add(response) {
    /* add the content portion of the response to the content portion of the page
     */
    const select = "#select_contents_page"
    if (PG.mr == "r") {
      $(select).html(response.find(select).html())
    }
  }
}

/**
 * Handles selection of the language in which the names
 * of bible books are presented.
 *
 * @see [M:blang][blang].
 * @see [∈ language][elem-language].
 */
export class SelectLanguage {
  constructor() {
    this.name = "select_contents_lang"
    this.hid = `#${this.name}`
    this.control = "#select_control_lang"
    $(this.control).off("click").click(e => {
      e.preventDefault()
      $(this.hid).dialog("open")
    })
  }

  present() {
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose language",
      width: "250px",
    })
  }

  genHtml() {
    /* generate a new lang selector
     */
    const { bookLangs } = Config

    const theLang = VS.lang()
    const nItems = bookLangs.length
    this.lastItem = nItems
    let html = ""
    html += '<table class="pagination">'
    const langs = Object.keys(bookLangs).sort()
    for (const lng of langs) {
      const langInfo = bookLangs[lng]
      const nameEN = langInfo[0]
      const nameOwn = langInfo[1]
      const activeCls = theLang == lng ? ' class="active"' : ""
      html += `
      <tr>
        <td${activeCls}>
          <a class="itemnav" href="#" item="${lng}">${nameOwn}
        </td>
        <td${activeCls}>
          <a class="itemnav" href="#" item="${lng}">${nameEN}</td>
      </tr>`
    }
    html += "</table>"
    $(this.hid).html(html)
    return nItems
  }

  addItem(item) {
    item.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const above = elem.closest("li")
      const isloaded = above.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals["lang"] = elem.attr("item")
        VS.setMaterial(vals)
        this.updateVerseLabels()
        VS.addHist()
        PG.material.apply()
      }
    })
  }

  updateVerseLabels() {
    const { bookTrans } = Config

    $("span[book]").each((i, el) => {
      const elem = $(el)
      elem.html(bookTrans[VS.lang()][elem.attr("book")])
    })
  }

  apply() {
    this.genHtml()
    $("#select_contents_lang .itemnav").each((i, el) => {
      const elem = $(el)
      this.addItem(elem)
    })
    $(this.control).show()
    this.present()
  }
}

/**
 * Handles book selection
 *
 * @see [∈ book][elem-book]
 */
class SelectBook {
  constructor() {
    this.name = "select_contents_book"
    this.hid = `#${this.name}`
    this.control = "#select_control_book"
    $(this.control).off("click").click(e => {
      e.preventDefault()
      $(this.hid).dialog("open")
    })
  }

  present() {
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose book",
      width: "110px",
    })
  }

  genHtml() {
    /* generate a new book selector
     */
    const { bookTrans, bookOrder } = Config

    const theBook = VS.book()
    const lng = VS.lang()
    const theseBooksOrder = bookOrder[PG.version]
    const nItems = theseBooksOrder.length

    this.lastItem = nItems

    let html = ""
    html += '<div class="pagination"><ul>'
    for (const book of theseBooksOrder) {
      const itemRep = bookTrans[lng][book]
      const bookCls = theBook == book ? ' class="active"' : ""
      html += `
        <li${bookCls}>
          <a class="itemnav" href="#" item="${book}">${itemRep}</a>
        </li>`
    }
    html += "</ul></div>"
    $(this.hid).html(html)
    return nItems
  }

  addItem(item) {
    item.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const above = elem.closest("li")
      const isloaded = above.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals["book"] = elem.attr("item")
        vals["chapter"] = "1"
        vals["verse"] = "1"
        VS.setMaterial(vals)
        VS.addHist()
        PG.go()
      }
    })
  }

  apply() {
    this.genHtml()
    $("#select_contents_book .itemnav").each((i, el) => {
      const elem = $(el)
      this.addItem(elem)
    })
    $(this.control).show()
    this.present()
  }
}

/**
 * Handles selection of chapters and result pages.
 *
 * @see [∈ chapter][elem-chapter], [∈ page][elem-page]
 */
class SelectItems {
  constructor(key) {
    this.key = key
    this.keyOther = key == "chapter" ? "page" : "chapter"
    this.name = `select_contents_${this.key}`
    this.nameOther = `select_contents_${this.keyOther}`
    this.hid = `#${this.name}`
    this.hidOther = `#${this.nameOther}`
    this.control = `#select_control_${this.key}`
    this.prev = $(`#prev_${this.key}`)
    this.next = $(`#next_${this.key}`)

    this.prev.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      VS.setMaterial(vals)
      VS.addHist()
      this.go()
    })
    this.next.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      VS.setMaterial(vals)
      VS.addHist()
      this.go()
    })
    $(this.control).off("click").click(e => {
      e.preventDefault()
      $(this.hid).dialog("open")
    })
  }

  go() {
    if (this.key == "chapter") {
      PG.go()
    } else {
      PG.go_material()
    }
  }

  present() {
    closeDialog($(this.hidOther))
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: `choose ${this.key}`,
      width: "200px",
    })
  }

  genHtml() {
    /* generate a new page selector
     */
    const { books } = Config

    let theItem
    let itemList
    let nItems

    if (this.key == "chapter") {
      const theBook = VS.book()
      theItem = VS.chapter()
      nItems = theBook != "x" ? books[PG.version][theBook] : 0
      this.lastItem = nItems
      itemList = new Array(nItems)
      for (let i = 0; i < nItems; i++) {
        itemList[i] = i + 1
      }
    } else {
      /* 'page'
       */
      theItem = VS.page()
      nItems = $("#rp_pages").val()
      this.lastItem = nItems
      itemList = []
      if (nItems) {
        itemList = $.parseJSON($("#rp_pagelist").val())
      }
    }

    let html = ""
    if (nItems != undefined) {
      if (nItems != 0) {
        html = '<div class="pagination"><ul>'
        for (const itm of itemList) {
          const itemCls = theItem == itm ? ' class="active"' : ""
          html += `
          <li${itemCls}>
            <a class="itemnav" href="#" item="${itm}">${itm}</a>
          </li>`
        }
        html += "</ul></div>"
      }
      $(this.hid).html(html)
    }
    return nItems
  }

  addItem(item) {
    item.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const above = elem.closest("li")
      const isloaded = above.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals[this.key] = elem.attr("item")
        vals["verse"] = "1"
        VS.setMaterial(vals)
        VS.addHist()
        this.go()
      }
    })
  }

  apply() {
    const showit = this.genHtml() > 0
    if (!showit) {
      $(this.control).hide()
    } else {
      $(`#select_contents_${this.key} .itemnav`).each((i, el) => {
        const elem = $(el)
        this.addItem(elem)
      })
      $(this.control).show()
      const thisItem = parseInt(
        this.key == "page" ? VS.page() : VS.chapter()
      )
      if (thisItem == undefined || thisItem == 1) {
        this.prev.hide()
      } else {
        this.prev.attr("contents", `${thisItem - 1}`)
        this.prev.show()
      }
      if (thisItem == undefined || thisItem == this.lastItem) {
        this.next.hide()
      } else {
        this.next.attr("contents", `${thisItem + 1}`)
        this.next.show()
      }
    }
    this.present()
  }
}
