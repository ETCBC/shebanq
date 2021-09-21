/* eslint-env jquery */
/* globals Config, P */

import { colorDefault, closeDialog } from "./helpers.js"
import { Notes } from "./notesm.js"
import { LSelect, MSelect, PSelect } from "./select.js"
import { MMessage, MContent, MSettings } from "./materiallib.js"


export class Material {
  /* Object corresponding to everything that controls the material in the main part
   * (not in the side bars)
   */
  constructor() {
    this.name = "material"
    this.hid = `#${this.name}`
    this.lselect = new LSelect()
    this.mselect = new MSelect()
    this.pselect = new PSelect()
    this.message = new MMessage()
    this.content = new MContent()
    this.msettings = new MSettings(this.content)
    this.message.msg("choose a passage or a query or a word")
  }

  adapt() {
    this.fetch()
  }

  apply() {
    /* apply ViewSettings to current material
     */
    const { bookLangs, bookTrans } = Config
    P.version = P.viewState.version()
    P.mr = P.viewState.mr()
    P.qw = P.viewState.qw()
    P.iid = P.viewState.iid()
    if (
      P.mr != P.prev["mr"] ||
      P.qw != P.prev["qw"] ||
      P.version != P.prev["version"] ||
      (P.mr == "m" &&
        (P.viewState.book() != P.prev["book"] ||
          P.viewState.chapter() != P.prev["chapter"] ||
          P.viewState.verse() != P.prev["verse"])) ||
      (P.mr == "r" && (P.iid != P.prev["iid"] || P.viewState.page() != P.prev["page"]))
    ) {
      P.reset_material_status()
      const p_mr = P.prev["mr"]
      const p_qw = P.prev["qw"]
      const p_iid = P.prev["iid"]
      if (p_mr == "r" && P.mr == "m") {
        const vals = {}
        if (p_qw != "n") {
          vals[p_iid] = P.viewState.colormap(p_qw)[p_iid] || colorDefault(p_qw == "q", p_iid)
          P.viewState.cstatesv(p_qw, vals)
        }
      }
    }
    this.lselect.apply()
    this.mselect.apply()
    this.pselect.apply()
    this.msettings.apply()
    const book = P.viewState.book()
    const chapter = P.viewState.chapter()
    const page = P.viewState.page()
    $("#thelang").html(bookLangs[P.viewState.lang()][1])
    $("#thebook").html(book != "x" ? bookTrans[P.viewState.lang()][book] : "book")
    $("#thechapter").html(chapter > 0 ? chapter : "chapter")
    $("#thepage").html(page > 0 ? `${page}` : "")
    for (const x in P.viewState.mstate()) {
      P.prev[x] = P.viewState.mstate()[x]
    }
  }

  fetch() {
    /* get the material by AJAX if needed, and process the material afterward
     */
    const { materialUrl } = Config
    const { material_fetched, material_kind } = P

    let vars =
      `?version=${P.version}&mr=${P.mr}&tp=${P.viewState.tp()}&tr=${P.viewState.tr()}` +
      `&qw=${P.qw}&lang=${P.viewState.lang()}`
    let do_fetch = false
    if (P.mr == "m") {
      vars += `&book=${P.viewState.book()}&chapter=${P.viewState.chapter()}`
      do_fetch = P.viewState.book() != "x" && P.viewState.chapter() > 0
    } else {
      vars += `&iid=${P.iid}&page=${P.viewState.page()}`
      do_fetch = P.qw == "q" ? P.iid >= 0 : P.iid != "-1"
    }
    const tp = P.viewState.tp()
    const tr = P.viewState.tr()
    if (
      do_fetch &&
      (!material_fetched[tp] || !(tp in material_kind) || material_kind[tp] != tr)
    ) {
      this.message.msg("fetching data ...")
      P.sidebars.after_material_fetch()
      $.get(
        `${materialUrl}${vars}`,
        html => {
          const response = $(html)
          this.pselect.add(response)
          this.message.add(response)
          this.content.add(response)
          material_fetched[tp] = true
          material_kind[tp] = tr
          this.process()
          this.goto_verse()
        },
        "html"
      )
    } else {
      P.highlight2({ code: "5", qw: "w" })
      P.highlight2({ code: "5", qw: "q" })
      this.msettings.hebrewsettings.apply()
      this.goto_verse()
    }
  }
  goto_verse() {
    /* go to the selected verse
     */
    $(".vhl").removeClass("vhl")
    const xxx = P.mr == "r" ? "div[tvid]" : `div[tvid="${P.viewState.verse()}"]`
    const verseTarget = $(`#material_${P.viewState.tp()}>${xxx}`).filter(":first")
    if (verseTarget != undefined && verseTarget[0] != undefined) {
      verseTarget[0].scrollIntoView()
      $("#navbar")[0].scrollIntoView()
      verseTarget.addClass("vhl")
    }
  }
  process() {
    /* process new material obtained by an AJAX call
     */
    const { material_fetched, material_kind } = P

    let mf = 0
    const tp = P.viewState.tp()
    const tr = P.viewState.tr()
    for (const x in material_fetched) {
      if (material_fetched[x]) {
        mf += 1
      }
    }
    /* count how many versions of this material already have been fetched
     */
    if (material_kind[tp] != "" && material_kind != tr) {
      /* and also whether the material has already been fetched
       * in another transcription
       */
      mf += 1
    }
    const contentNew = $(`#material_${tp}`)
    const textContent = $(".txtp,.txt1,.txt2,.txt3")
    const tTextContent = $(".t1_txt,.lv2")
    if (P.viewState.tr() == "hb") {
      textContent.removeClass("pho")
      textContent.removeClass("phox")
      tTextContent.removeClass("pho")
      textContent.addClass("heb")
      textContent.addClass("hebx")
      tTextContent.addClass("heb")
    } else if (P.viewState.tr() == "ph") {
      textContent.removeClass("heb")
      textContent.removeClass("hebx")
      tTextContent.removeClass("heb")
      textContent.addClass("pho")
      textContent.addClass("phox")
      tTextContent.addClass("pho")
    }
    /* because some processes like highlighting and assignment of verse number clicks
     * must be suppressed on first time or on subsequent times
     */
    if (P.mr == "r") {
      this.pselect.apply()
      if (P.qw != "n") {
        P.picker1[P.qw].adapt(P.iid, true)
      }
      $("a.cref").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        P.viewState.mstatesv({
          book: elem.attr("book"),
          chapter: elem.attr("chapter"),
          verse: elem.attr("verse"),
          mr: "m",
        })
        P.viewState.addHist()
        P.go()
      })
    } else {
      this.add_word_actions(contentNew, mf)
    }
    this.add_vrefs(contentNew, mf)
    if (P.viewState.tp() == "txtd") {
      this.msettings.hebrewsettings.apply()
    } else if (P.viewState.tp() == "txt1") {
      this.add_cmt(contentNew)
    }
  }

  add_cmt(contentNew) {
    /* add actions for the tab1 view
     */
    this.notes = new Notes(contentNew)
  }

  add_vrefs(contentNew, mf) {
    const { dataUrl } = Config

    const vrefs = contentNew.find(".vradio")
    vrefs.each((i, el) => {
      const elem = $(el)
      elem.attr("title", "interlinear data")
    })
    vrefs.click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const base_tp = P.viewState.tp()
      const dat = $(`#${base_tp}_txtd_${bk}_${ch}_${vs}`)
      const txt = $(`#${base_tp}_${bk}_${ch}_${vs}`)
      const legend = $("#datalegend")
      const legendc = $("#datalegend_control")
      if (elem.hasClass("ison")) {
        elem.removeClass("ison")
        elem.attr("title", "interlinear data")
        legend.hide()
        closeDialog(legend)
        legendc.hide()
        dat.hide()
        txt.show()
      } else {
        elem.addClass("ison")
        elem.attr("title", "text/tab")
        legendc.show()
        dat.show()
        txt.hide()
        if (dat.attr("lf") == "x") {
          dat.html(`fetching data for ${bk} ${ch}:${vs} ...`)
          dat.load(
            `${dataUrl}?version=${P.version}&book=${bk}&chapter=${ch}&verse=${vs}`,
            () => {
              dat.attr("lf", "v")
              this.msettings.hebrewsettings.apply()
              if (P.mr == "r") {
                if (P.qw != "n") {
                  P.picker1[P.qw].adapt(P.iid, true)
                }
              } else {
                P.highlight2({ code: "5", qw: "w" })
                P.highlight2({ code: "5", qw: "q" })
                this.add_word_actions(dat, mf)
              }
            },
            "html"
          )
        }
      }
    })
  }

  add_word_actions(contentNew, mf) {
    /* Make words clickable, so that they show up in the sidebar
     */
    contentNew.find("span[l]").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const iid = elem.attr("l")
      const qw = "w"
      const all = $(`#${qw}${iid}`)
      if (P.viewState.iscolor(qw, iid)) {
        P.viewState.cstatex(qw, iid)
        all.hide()
      } else {
        const vals = {}
        vals[iid] = colorDefault(false, iid)
        P.viewState.cstatesv(qw, vals)
        all.show()
      }
      const active = P.viewState.active(qw)
      if (active != "hlcustom" && active != "hlmany") {
        P.viewState.hstatesv(qw, { active: "hlcustom" })
      }
      if (P.viewState.get("w") == "v") {
        if (iid in P.picker1list["w"]) {
          /* should not happen but it happens when changing data versions
           */
          P.picker1list["w"][iid].apply(false)
        }
      }
      P.highlight2({ code: "4", qw })
      P.viewState.addHist()
    })
    if (mf > 1) {
      /* Initially, material gets highlighted once the sidebars have been loaded.
       * But when we load a different representation of material (data, tab),
       * the sidebars are still there,
       * and after loading the material, highlighs have to be applied.
       */
      P.highlight2({ code: "5", qw: "q" })
      P.highlight2({ code: "5", qw: "w" })
    }
  }
}
