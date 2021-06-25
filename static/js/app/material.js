/* eslint-env jquery */
/* globals Config, P */

import { defcolor, close_dialog } from "./helpers.js"
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
    /* apply viewsettings to current material
     */
    const { booklangs, booktrans } = Config
    P.version = P.vs.version()
    P.mr = P.vs.mr()
    P.qw = P.vs.qw()
    P.iid = P.vs.iid()
    if (
      P.mr != P.prev["mr"] ||
      P.qw != P.prev["qw"] ||
      P.version != P.prev["version"] ||
      (P.mr == "m" &&
        (P.vs.book() != P.prev["book"] ||
          P.vs.chapter() != P.prev["chapter"] ||
          P.vs.verse() != P.prev["verse"])) ||
      (P.mr == "r" && (P.iid != P.prev["iid"] || P.vs.page() != P.prev["page"]))
    ) {
      P.reset_material_status()
      const p_mr = P.prev["mr"]
      const p_qw = P.prev["qw"]
      const p_iid = P.prev["iid"]
      if (p_mr == "r" && P.mr == "m") {
        const vals = {}
        if (p_qw != "n") {
          vals[p_iid] = P.vs.colormap(p_qw)[p_iid] || defcolor(p_qw == "q", p_iid)
          P.vs.cstatesv(p_qw, vals)
        }
      }
    }
    this.lselect.apply()
    this.mselect.apply()
    this.pselect.apply()
    this.msettings.apply()
    const book = P.vs.book()
    const chapter = P.vs.chapter()
    const page = P.vs.page()
    $("#thelang").html(booklangs[P.vs.lang()][1])
    $("#thebook").html(book != "x" ? booktrans[P.vs.lang()][book] : "book")
    $("#thechapter").html(chapter > 0 ? chapter : "chapter")
    $("#thepage").html(page > 0 ? `${page}` : "")
    for (const x in P.vs.mstate()) {
      P.prev[x] = P.vs.mstate()[x]
    }
  }

  fetch() {
    /* get the material by AJAX if needed, and process the material afterward
     */
    const { material_url } = Config
    const { material_fetched, material_kind } = P

    let vars =
      `?version=${P.version}&mr=${P.mr}&tp=${P.vs.tp()}&tr=${P.vs.tr()}` +
      `&qw=${P.qw}&lang=${P.vs.lang()}`
    let do_fetch = false
    if (P.mr == "m") {
      vars += `&book=${P.vs.book()}&chapter=${P.vs.chapter()}`
      do_fetch = P.vs.book() != "x" && P.vs.chapter() > 0
    } else {
      vars += `&iid=${P.iid}&page=${P.vs.page()}`
      do_fetch = P.qw == "q" ? P.iid >= 0 : P.iid != "-1"
    }
    const tp = P.vs.tp()
    const tr = P.vs.tr()
    if (
      do_fetch &&
      (!material_fetched[tp] || !(tp in material_kind) || material_kind[tp] != tr)
    ) {
      this.message.msg("fetching data ...")
      P.sidebars.after_material_fetch()
      $.get(
        `${material_url}${vars}`,
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
    const xxx = P.mr == "r" ? "div[tvid]" : `div[tvid="${P.vs.verse()}"]`
    const vtarget = $(`#material_${P.vs.tp()}>${xxx}`).filter(":first")
    if (vtarget != undefined && vtarget[0] != undefined) {
      vtarget[0].scrollIntoView()
      $("#navbar")[0].scrollIntoView()
      vtarget.addClass("vhl")
    }
  }
  process() {
    /* process new material obtained by an AJAX call
     */
    const { material_fetched, material_kind } = P

    let mf = 0
    const tp = P.vs.tp()
    const tr = P.vs.tr()
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
    const newcontent = $(`#material_${tp}`)
    const textcontent = $(".txt_p,.txt_tb1,.txt_tb2,.txt_tb3")
    const ttextcontent = $(".t1_txt,.lv2")
    if (P.vs.tr() == "hb") {
      textcontent.removeClass("pho")
      textcontent.removeClass("phox")
      ttextcontent.removeClass("pho")
      textcontent.addClass("heb")
      textcontent.addClass("hebx")
      ttextcontent.addClass("heb")
    } else if (P.vs.tr() == "ph") {
      textcontent.removeClass("heb")
      textcontent.removeClass("hebx")
      ttextcontent.removeClass("heb")
      textcontent.addClass("pho")
      textcontent.addClass("phox")
      ttextcontent.addClass("pho")
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
        const elem = $(e.target)
        P.vs.mstatesv({
          book: elem.attr("book"),
          chapter: elem.attr("chapter"),
          verse: elem.attr("verse"),
          mr: "m",
        })
        P.vs.addHist()
        P.go()
      })
    } else {
      this.add_word_actions(newcontent, mf)
    }
    this.add_vrefs(newcontent, mf)
    if (P.vs.tp() == "txt_il") {
      this.msettings.hebrewsettings.apply()
    } else if (P.vs.tp() == "txt_tb1") {
      this.add_cmt(newcontent)
    }
  }

  add_cmt(newcontent) {
    /* add actions for the tab1 view
     */
    this.notes = new Notes(newcontent)
  }

  add_vrefs(newcontent, mf) {
    const { data_url } = Config

    const vrefs = newcontent.find(".vradio")
    vrefs.each((i, el) => {
      const elem = $(el)
      elem.attr("title", "interlinear data")
    })
    vrefs.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const base_tp = P.vs.tp()
      const dat = $(`#${base_tp}_txt_il_${bk}_${ch}_${vs}`)
      const txt = $(`#${base_tp}_${bk}_${ch}_${vs}`)
      const legend = $("#datalegend")
      const legendc = $("#datalegend_control")
      if (elem.hasClass("ison")) {
        elem.removeClass("ison")
        elem.attr("title", "interlinear data")
        legend.hide()
        close_dialog(legend)
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
            `${data_url}?version=${P.version}&book=${bk}&chapter=${ch}&verse=${vs}`,
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

  add_word_actions(newcontent, mf) {
    /* Make words clickable, so that they show up in the sidebar
     */
    newcontent.find("span[l]").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const iid = elem.attr("l")
      const qw = "w"
      const all = $(`#${qw}${iid}`)
      if (P.vs.iscolor(qw, iid)) {
        P.vs.cstatex(qw, iid)
        all.hide()
      } else {
        const vals = {}
        vals[iid] = defcolor(false, iid)
        P.vs.cstatesv(qw, vals)
        all.show()
      }
      const active = P.vs.active(qw)
      if (active != "hlcustom" && active != "hlmany") {
        P.vs.hstatesv(qw, { active: "hlcustom" })
      }
      if (P.vs.get("w") == "v") {
        if (iid in P.picker1list["w"]) {
          /* should not happen but it happens when changing data versions
           */
          P.picker1list["w"][iid].apply(false)
        }
      }
      P.highlight2({ code: "4", qw })
      P.vs.addHist()
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
