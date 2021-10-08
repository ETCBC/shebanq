/* eslint-env jquery */
/* globals Config, PG, VS */

/**
 * @module material
 */

import { colorDefault, closeDialog } from "./helpers.js"
import { Notes } from "./notes.js"
import { SelectLanguage, SelectPassage, SelectResultPage } from "./select.js"
import { Message } from "./message.js"
import { MaterialContent } from "./materialcontent.js"
import { MaterialSettings } from "./materialsettings.js"
import { FeatureSettings } from "./featuresettings.js"

/**
 * Controls the main area of the page.
 *
 * @see [M:MATERIAL][materials.MATERIAL]
 * @see page elements:
 * *    [∈ book][elem-book],
 * *    [∈ chapter][elem-chapter],
 * *    [∈ page][elem-page],
 * *    [∈ goto-chapter][elem-goto-chapter],
 */
export class Material {
  constructor() {
    this.name = "material"
    this.hid = `#${this.name}`
    this.selectLanguage = new SelectLanguage()
    this.selectPassage = new SelectPassage()
    this.selectResultPage = new SelectResultPage()
    this.message = new Message()
    this.content = new MaterialContent()
    this.materialSettings = new MaterialSettings(this.content)
    this.featureSettings = new FeatureSettings()
    this.message.msg("choose a passage or a query or a word")
  }

  adapt() {
    this.fetch()
  }

  apply() {
    /* apply ViewSettings to current material
     */
    const { bookLangs, bookTrans } = Config
    PG.version = VS.version()
    PG.mr = VS.mr()
    PG.qw = VS.qw()
    PG.iid = VS.iid()
    if (
      PG.mr != PG.prev["mr"] ||
      PG.qw != PG.prev["qw"] ||
      PG.version != PG.prev["version"] ||
      (PG.mr == "m" &&
        (VS.book() != PG.prev["book"] ||
          VS.chapter() != PG.prev["chapter"] ||
          VS.verse() != PG.prev["verse"])) ||
      (PG.mr == "r" && (PG.iid != PG.prev["iid"] || VS.page() != PG.prev["page"]))
    ) {
      PG.materialStatusReset()
      const mrPrev = PG.prev["mr"]
      const qwPrev = PG.prev["qw"]
      const iidPrev = PG.prev["iid"]
      if (mrPrev == "r" && PG.mr == "m") {
        const vals = {}
        if (qwPrev != "n") {
          vals[iidPrev] =
            VS.colorMap(qwPrev)[iidPrev] || colorDefault(qwPrev == "q", iidPrev)
          VS.setColor(qwPrev, vals)
        }
      }
    }
    this.selectLanguage.apply()
    this.selectPassage.apply()
    this.selectResultPage.apply()
    this.materialSettings.apply()
    const book = VS.book()
    const chapter = VS.chapter()
    const page = VS.page()
    $("#thelang").html(bookLangs[VS.lang()][1])
    $("#thebook").html(book != "x" ? bookTrans[VS.lang()][book] : "book")
    $("#thechapter").html(chapter > 0 ? chapter : "chapter")
    $("#thepage").html(page > 0 ? `${page}` : "")
    for (const x in VS.getMaterial()) {
      PG.prev[x] = VS.getMaterial()[x]
    }
  }

  /**
   * get the material by AJAX if needed, and process the material afterward
   *
   * @see Triggers [C:hebrew.material][controllers.hebrew.material]
   */
  fetch() {
    const { pageMaterialUrl } = Config
    const { materialFetched, materialKind } = PG

    let vars =
      `?version=${PG.version}&mr=${PG.mr}&tp=${VS.tp()}&tr=${VS.tr()}` +
      `&qw=${PG.qw}&lang=${VS.lang()}`
    let doFetch = false
    if (PG.mr == "m") {
      vars += `&book=${VS.book()}&chapter=${VS.chapter()}`
      doFetch = VS.book() != "x" && VS.chapter() > 0
    } else {
      vars += `&iid=${PG.iid}&page=${VS.page()}`
      doFetch = PG.qw == "q" ? PG.iid >= 0 : PG.iid != "-1"
    }
    const tp = VS.tp()
    const tr = VS.tr()
    if (
      doFetch &&
      (!materialFetched[tp] || !(tp in materialKind) || materialKind[tp] != tr)
    ) {
      this.message.msg("fetching data ... ")
      PG.sidebars.afterMaterialFetch()
      $.get(
        `${pageMaterialUrl}${vars}`,
        html => {
          const response = $(html)
          this.selectResultPage.add(response)
          this.message.add(response)
          this.content.add(response)
          materialFetched[tp] = true
          materialKind[tp] = tr
          this.process()
          this.gotoVerse()
        },
        "html"
      )
    } else {
      PG.highlight2({ code: "5", qw: "w" })
      PG.highlight2({ code: "5", qw: "q" })
      this.featureSettings.apply()
      this.gotoVerse()
    }
  }
  gotoVerse() {
    /* go to the selected verse
     */
    $(".versehighlight").removeClass("versehighlight")
    const xxx = PG.mr == "r" ? "div[tvid]" : `div[tvid="${VS.verse()}"]`
    const verseTarget = $(`#material_${VS.tp()}>${xxx}`).filter(":first")
    if (verseTarget != undefined && verseTarget[0] != undefined) {
      verseTarget[0].scrollIntoView()
      $("#navbar")[0].scrollIntoView()
      verseTarget.addClass("versehighlight")
    }
  }
  process() {
    /* process new material obtained by an AJAX call
     */
    const { materialFetched, materialKind } = PG

    let mf = 0
    const tp = VS.tp()
    const tr = VS.tr()
    for (const isFetched of Object.values(materialFetched)) {
      if (isFetched) {
        mf += 1
      }
    }
    /* count how many versions of this material already have been fetched
     */
    if (materialKind[tp] != "" && materialKind != tr) {
      /* and also whether the material has already been fetched
       * in another transcription
       */
      mf += 1
    }
    const contentNew = $(`#material_${tp}`)
    const textContent = $(".txtp,.txt1,.txt2,.txt3")
    const tTextContent = $(".t1_txt,.lv2")
    if (VS.tr() == "hb") {
      textContent.removeClass("pho")
      textContent.removeClass("phox")
      tTextContent.removeClass("pho")
      textContent.addClass("heb")
      textContent.addClass("hebx")
      tTextContent.addClass("heb")
    } else if (VS.tr() == "ph") {
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
    if (PG.mr == "r") {
      this.selectResultPage.apply()
      if (PG.qw != "n") {
        PG.picker1[PG.qw].adapt(PG.iid, true)
      }
      $("a.cref").off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        VS.setMaterial({
          book: elem.attr("book"),
          chapter: elem.attr("chapter"),
          verse: elem.attr("verse"),
          mr: "m",
        })
        VS.addHist()
        PG.go()
      })
    } else {
      this.addWordActions(contentNew, mf)
    }
    this.addVerseRefs(contentNew, mf)
    if (VS.tp() == "txtd") {
      this.featureSettings.apply()
    } else if (VS.tp() == "txt1") {
      this.addNoteActions(contentNew)
    }
  }

  addNoteActions(contentNew) {
    /* add actions for the tab1 view
     */
    this.notes = new Notes(contentNew)
  }

  /**
   * add a click event to the verse number by which
   * linguistic features for the words in that verse
   * can be retrieved from the server.
   *
   * @see Triggers [C:hebrew.verse][controllers.hebrew.verse].
   *
   * @see [∈ show-verse-data][elem-show-verse-data]
  */
  addVerseRefs(contentNew, mf) {
    const { verseFeaturesUrl } = Config

    const verseRefs = contentNew.find(".vradio")
    verseRefs.each((i, el) => {
      const elem = $(el)
      elem.attr("title", "interlinear data")
    })
    verseRefs.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const baseTp = VS.tp()
      const dataDest = $(`#${baseTp}_txtd_${bk}_${ch}_${vs}`)
      const textDest = $(`#${baseTp}_${bk}_${ch}_${vs}`)
      const legend = $("#datalegend")
      const legendCtl = $("#datalegend_control")
      if (elem.hasClass("ison")) {
        elem.removeClass("ison")
        elem.attr("title", "interlinear data")
        legend.hide()
        closeDialog(legend)
        legendCtl.hide()
        dataDest.hide()
        textDest.show()
      } else {
        elem.addClass("ison")
        elem.attr("title", "text/tab")
        legendCtl.show()
        dataDest.show()
        textDest.hide()
        if (dataDest.attr("lf") == "x") {
          dataDest.html(`fetching data for ${bk} ${ch}:${vs} ...`)
          dataDest.load(
            `${verseFeaturesUrl}?version=${PG.version}&book=${bk}&chapter=${ch}&verse=${vs}`,
            () => {
              dataDest.attr("lf", "v")
              this.featureSettings.apply()
              if (PG.mr == "r") {
                if (PG.qw != "n") {
                  PG.picker1[PG.qw].adapt(PG.iid, true)
                }
              } else {
                PG.highlight2({ code: "5", qw: "w" })
                PG.highlight2({ code: "5", qw: "q" })
                this.addWordActions(dataDest, mf)
              }
            },
            "html"
          )
        }
      }
    })
  }

  addWordActions(contentNew, mf) {
    /* Make words clickable, so that they show up in the sidebar
     */
    contentNew.find("span[l]").off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const iid = elem.attr("l")
      const qw = "w"
      const all = $(`#${qw}${iid}`)
      if (VS.isColor(qw, iid)) {
        VS.delColor(qw, iid)
        all.hide()
      } else {
        const vals = {}
        vals[iid] = colorDefault(false, iid)
        VS.setColor(qw, vals)
        all.show()
      }
      const active = VS.active(qw)
      if (active != "hlcustom" && active != "hlmany") {
        VS.setHighlight(qw, { active: "hlcustom" })
      }
      if (VS.get("w") == "v") {
        if (iid in PG.picker1List["w"]) {
          /* should not happen but it happens when changing data versions
           */
          PG.picker1List["w"][iid].apply(false)
        }
      }
      PG.highlight2({ code: "4", qw })
      VS.addHist()
    })
    if (mf > 1) {
      /* Initially, material gets highlighted once the sidebars have been loaded.
       * But when we load a different representation of material (data, tab),
       * the sidebars are still there,
       * and after loading the material, highlighs have to be applied.
       */
      PG.highlight2({ code: "5", qw: "q" })
      PG.highlight2({ code: "5", qw: "w" })
    }
  }
}
