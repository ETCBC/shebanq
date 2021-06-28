/* eslint-env jquery */
/* globals Config, P */

import { close_dialog, defcolor } from "./helpers.js"

const docName = "0_home"

const chart_cols = 30
/* number of chapters in a row in a chart
 */

export class MSelect {
  /* for book and chapter selection
   */

  constructor() {
    this.name = "select_passage"
    this.hid = `#${this.name}`
    this.book = new SelectBook()
    this.select = new SelectItems("chapter")
    $("#self_link").hide()
  }

  apply() {
    /* apply material viewsettings to current material
     */
    const { versions, featurehost, bol_url, pbl_url } = Config

    const thisFeaturehost = `${featurehost}/${docName}`
    $(".source").attr("href", thisFeaturehost)
    $(".source").attr("title", "BHSA feature documentation")
    $(".mvradio").removeClass("ison")
    $(`#version_${P.version}`).addClass("ison")
    const bol = $("#bol_lnk")
    const pbl = $("#pbl_lnk")

    for (const v of versions) {
      this.set_vselect(v)
    }
    if (P.mr == "m") {
      this.book.apply()
      this.select.apply()
      $(this.hid).show()
      const book = P.vs.book()
      const chapter = P.vs.chapter()
      if (book != "x" && chapter > 0) {
        bol.attr("href", `${bol_url}/ETCBC4/${book}/${chapter}`)
        bol.show()
        pbl.attr("href", `${pbl_url}/${book}/${chapter}`)
        pbl.show()
      } else {
        bol.hide()
        pbl.hide()
      }
    } else {
      $(this.hid).hide()
      bol.hide()
      pbl.hide()
    }
  }

  set_vselect(v) {
    const { sidebars } = P

      $(`#version_${v}`).click(e => {
        e.preventDefault()
        sidebars.side_fetched["mw"] = false
        sidebars.side_fetched["mq"] = false
        sidebars.side_fetched["mn"] = false
        P.vs.mstatesv({ version: v })
        P.go()
      })
  }
}

export class PSelect {
  /* for result page selection
   */
  constructor() {
    this.name = "select_pages"
    this.hid = `#${this.name}`
    this.select = new SelectItems("page")
  }

  apply() {
    /* apply result page selection: fill in headings on the page
     */
    if (P.mr == "r") {
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
    if (P.mr == "r") {
      $(select).html(response.find(select).html())
    }
  }
}

export class LSelect {
  /* language selection
   */
  constructor() {
    this.name = "select_contents_lang"
    this.hid = `#${this.name}`
    this.control = "#select_control_lang"
    $(this.control).click(e => {
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

  gen_html() {
    /* generate a new lang selector
     */
    const { booklangs } = Config

    const thelang = P.vs.lang()
    const nitems = booklangs.length
    this.lastitem = nitems
    let ht = ""
    ht += '<table class="pagination">'
    const langs = Object.keys(booklangs).sort()
    for (const item of langs) {
      const langinfo = booklangs[item]
      const name_en = langinfo[0]
      const name_own = langinfo[1]
      const clactive = thelang == item ? ' class="active"' : ""
      ht += `
      <tr>
        <td${clactive}>
          <a class="itemnav" href="#" item="${item}">${name_own}
        </td>
        <td${clactive}>
          <a class="itemnav" href="#" item="${item}">${name_en}</td>
      </tr>`
    }
    ht += "</table>"
    $(this.hid).html(ht)
    return nitems
  }

  add_item(item) {
    item.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const newobj = elem.closest("li")
      const isloaded = newobj.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals["lang"] = elem.attr("item")
        P.vs.mstatesv(vals)
        this.update_vlabels()
        P.vs.addHist()
        P.material.apply()
      }
    })
  }

  update_vlabels() {
    const { booktrans } = Config

    $("span[book]").each((i, el) => {
      const elem = $(el)
      elem.html(booktrans[P.vs.lang()][elem.attr("book")])
    })
  }

  apply() {
    this.gen_html()
    $("#select_contents_lang .itemnav").each((i, el) => {
      const elem = $(el)
      this.add_item(elem)
    })
    $(this.control).show()
    this.present()
  }
}

class SelectBook {
  /* book selection
   */
  constructor() {
    this.name = "select_contents_book"
    this.hid = `#${this.name}`
    this.control = "#select_control_book"
    $(this.control).click(e => {
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

  gen_html() {
    /* generate a new book selector
     */
    const { booktrans, booksorder } = Config

    const thebook = P.vs.book()
    const lang = P.vs.lang()
    const thisbooksorder = booksorder[P.version]
    const nitems = thisbooksorder.length

    this.lastitem = nitems

    let ht = ""
    ht += '<div class="pagination"><ul>'
    for (const item of thisbooksorder) {
      const itemrep = booktrans[lang][item]
      const liCls = thebook == item ? ' class="active"' : ""
      ht += `
        <li${liCls}>
          <a class="itemnav" href="#" item="${item}">${itemrep}</a>
        </li>`
    }
    ht += "</ul></div>"
    $(this.hid).html(ht)
    return nitems
  }

  add_item(item) {
    item.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const newobj = elem.closest("li")
      const isloaded = newobj.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals["book"] = elem.attr("item")
        vals["chapter"] = "1"
        vals["verse"] = "1"
        P.vs.mstatesv(vals)
        P.vs.addHist()
        P.go()
      }
    })
  }

  apply() {
    this.gen_html()
    $("#select_contents_book .itemnav").each((i, el) => {
      const elem = $(el)
      this.add_item(elem)
    })
    $(this.control).show()
    this.present()
  }
}

class SelectItems {
  /* both for chapters and for result pages
   */
  constructor(key) {
    this.key = key
    this.other_key = key == "chapter" ? "page" : "chapter"
    this.name = `select_contents_${this.key}`
    this.other_name = `select_contents_${this.other_key}`
    this.hid = `#${this.name}`
    this.other_hid = `#${this.other_name}`
    this.control = `#select_control_${this.key}`
    this.prev = $(`#prev_${this.key}`)
    this.next = $(`#next_${this.key}`)

    this.prev.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      P.vs.mstatesv(vals)
      P.vs.addHist()
      this.go()
    })
    this.next.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      P.vs.mstatesv(vals)
      P.vs.addHist()
      this.go()
    })
    $(this.control).click(e => {
      e.preventDefault()
      $(this.hid).dialog("open")
    })
  }

  go() {
    if (this.key == "chapter") {
      P.go()
    } else {
      P.go_material()
    }
  }

  present() {
    close_dialog($(this.other_hid))
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: `choose ${this.key}`,
      width: "200px",
    })
  }

  gen_html() {
    /* generate a new page selector
     */
    const { books } = Config

    let theitem
    let itemlist
    let nitems

    if (this.key == "chapter") {
      const thebook = P.vs.book()
      theitem = P.vs.chapter()
      nitems = thebook != "x" ? books[P.version][thebook] : 0
      this.lastitem = nitems
      itemlist = new Array(nitems)
      for (let i = 0; i < nitems; i++) {
        itemlist[i] = i + 1
      }
    } else {
      /* 'page'
       */
      theitem = P.vs.page()
      nitems = $("#rp_pages").val()
      this.lastitem = nitems
      itemlist = []
      if (nitems) {
        itemlist = $.parseJSON($("#rp_pagelist").val())
      }
    }

    let ht = ""
    if (nitems != undefined) {
      if (nitems != 0) {
        ht = '<div class="pagination"><ul>'
        for (const item of itemlist) {
          const liCls = theitem == item ? ' class="active"' : ""
          ht += `
          <li${liCls}>
            <a class="itemnav" href="#" item="${item}">${item}</a>
          </li>`
        }
        ht += "</ul></div>"
      }
      $(this.hid).html(ht)
    }
    return nitems
  }

  add_item(item) {
    item.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const newobj = elem.closest("li")
      const isloaded = newobj.hasClass("active")
      if (!isloaded) {
        const vals = {}
        vals[this.key] = elem.attr("item")
        vals["verse"] = "1"
        P.vs.mstatesv(vals)
        P.vs.addHist()
        this.go()
      }
    })
  }

  apply() {
    const showit = this.gen_html() > 0
    if (!showit) {
      $(this.control).hide()
    } else {
      $(`#select_contents_${this.key} .itemnav`).each((i, el) => {
        const elem = $(el)
        this.add_item(elem)
      })
      $(this.control).show()
      const thisitem = parseInt(this.key == "page" ? P.vs.page() : P.vs.chapter())
      if (thisitem == undefined || thisitem == 1) {
        this.prev.hide()
      } else {
        this.prev.attr("contents", `${thisitem - 1}`)
        this.prev.show()
      }
      if (thisitem == undefined || thisitem == this.lastitem) {
        this.next.hide()
      } else {
        this.next.attr("contents", `${thisitem + 1}`)
        this.next.show()
      }
    }
    this.present()
  }
}

export class CSelect {
  /* for chart selection
   */
  constructor(vr, qw) {
    this.vr = vr
    this.qw = qw
    this.control = `#select_control_chart_${vr}_${qw}`
    this.select = `#select_contents_chart_${vr}_${qw}`
    this.loaded = {}
  }

  init() {
    $(this.control).click(e => {
      e.preventDefault()
      this.apply()
    })
  }

  apply() {
    if (!this.loaded[`${this.qw}_${P.iid}`]) {
      if ($(`#select_contents_chart_${this.vr}_${this.qw}_${P.iid}`).length == 0) {
        $(this.select).append(
          `<span id="select_contents_chart_${this.vr}_${this.qw}_${P.iid}"></span>`
        )
      }
      this.fetch(P.iid)
    } else {
      this.show()
    }
  }

  fetch(iid) {
    const { chart_url } = Config

    const vars = `?version=${this.vr}&qw=${this.qw}&iid=${iid}`
    $(`${this.select}_${iid}`).load(
      `${chart_url}${vars}`,
      () => {
        this.loaded[`${this.qw}_${iid}`] = true
        this.process(iid)
      },
      "html"
    )
  }

  process(iid) {
    this.gen_html(iid)
    $(`${this.select}_${iid} .cnav`).each((i, el) => {
      const elem = $(el)
      this.add_item(elem, iid)
    })
    $("#theitemc").click(e => {
      e.preventDefault()
      const vals = {}
      vals["iid"] = iid
      vals["mr"] = "r"
      vals["version"] = this.vr
      vals["qw"] = this.qw
      P.vs.mstatesv(vals)
      P.vs.addHist()
      P.go()
    })
    $("#theitemc").html(`Back to ${$("#theitem").html()} (version ${this.vr})`)
    /* fill in the Back to query/word line in a chart
     */
    this.present(iid)
    this.show(iid)
  }

  present(iid) {
    const { style } = Config
    const { chart_width } = P

    $(`${this.select}_${iid}`).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      close: () => {
        this.loaded[`${this.qw}_${iid}`] = false
        $(`${this.select}_${iid}`).html("")
      },
      modal: false,
      title: `chart for ${style[this.qw]["tag"]} (version ${this.vr})`,
      width: chart_width,
      position: { my: "left top", at: "left top", of: window },
    })
  }

  show(iid) {
    $(`${this.select}_${iid}`).dialog("open")
  }

  gen_html(iid) {
    /* generate a new chart
     */
    const { style, ccolors } = Config

    let nbooks = 0
    let booklist = $(`#r_chartorder${this.qw}`).val()
    let bookdata = $(`#r_chart${this.qw}`).val()
    if (booklist) {
      booklist = $.parseJSON(booklist)
      bookdata = $.parseJSON(bookdata)
      nbooks = booklist.length
    } else {
      booklist = []
      bookdata = {}
    }
    let ht = ""
    ht += `
      <p>
        <a id="theitemc"
          title="back to ${style[this.qw]["tag"]} (version ${this.vr})"
          href="#">back</a>
        </p>
        <table class="chart">`

    const ccl = ccolors.length
    for (const book of booklist) {
      const blocks = bookdata[book]
      ht += `
        <tr>
          <td class="bnm">${book}</td>
          <td class="chp"><table class="chp">
        <tr>`
      let l = 0
      for (let i = 0; i < blocks.length; i++) {
        if (l == chart_cols) {
          ht += "</tr><tr>"
          l = 0
        }
        const block_info = blocks[i]
        const chnum = block_info[0]
        const ch_range = `${block_info[1]}-${block_info[2]}`
        const blres = block_info[3]
        const blsize = block_info[4]
        const blres_select = blres >= ccl ? ccl - 1 : blres
        const z = ccolors[blres_select]
        let s = "&nbsp;"
        let sz = ""
        let sc = ""
        if (blsize < 25) {
          s = "="
          sc = "s1"
        } else if (blsize < 75) {
          s = "-"
          sc = "s5"
        }
        if (blsize < 100) {
          sz = ` (${blsize}%)`
        }
        ht += `
          <td class="${z}">
            <a
              title="${ch_range}${sz}: ${blres}"
              class="cnav ${sc}"
              href="#"
              b=${book} ch="${chnum}"
            >${s}</a>
          </td>`
        l++
      }
      ht += "</tr></table></td></tr>"
    }
    ht += "</table>"
    $(`${this.select}_${iid}`).html(ht)
    return nbooks
  }

  add_item(item, iid) {
    item.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      let vals = {}
      vals["book"] = elem.attr("b")
      vals["chapter"] = elem.attr("ch")
      vals["mr"] = "m"
      vals["version"] = this.vr
      P.vs.mstatesv(vals)
      P.vs.hstatesv("q", { sel_one: "white", active: "hlcustom" })
      P.vs.hstatesv("w", { sel_one: "black", active: "hlcustom" })
      P.vs.cstatexx("q")
      P.vs.cstatexx("w")
      if (this.qw != "n") {
        vals = {}
        vals[iid] = P.vs.colormap(this.qw)[iid] || defcolor(this.qw == "q", iid)
        P.vs.cstatesv(this.qw, vals)
      }
      P.vs.addHist()
      P.go()
    })
  }
}
