/* eslint-env jquery */
/* globals Config, P, L */

import { colorDefault } from "./helpers.js"
import { Material } from "./material.js"
import { Sidebars } from "./sidebars.js"
import { LSettings } from "./materiallib.js"

export const setHeightW = () => {
  /* the heights of the sidebars are set, depending on the height of the window
   */
  const subtractw = 80
  const standard_heightw = window.innerHeight - subtractw
  $("#words").css("height", `${standard_heightw}px`)
  $("#letters").css("height", `${standard_heightw}px`)
}

export class LStorage {
  constructor() {
    const vws = $.initNamespaceStorage("viewStoredNotes")
    this.viewStoredNotes = vws.localStorage
    const nsq = $.initNamespaceStorage("muting_q")
    this.muting_q = nsq.localStorage
    const nsn = $.initNamespaceStorage("muting_n")
    this.muting_n = nsn.localStorage
    /* on the Queries page the user can "mute" queries. Which queries are muted,
     * is stored as key value pairs in this local storage bucket.
     * When shebanq shows relevant queries next to a page, muting is taken into account.
     */
  }
}

export class Page {
  /* the one and only page object
   */
  constructor(viewState) {

    this.mqlSmallHeight = "10em"
    /* height of mql query body in sidebar
     */
    this.mqlSmallWidth = "97%"
    /* height of mql query body in sidebar and in dialog
     */
    this.mqlBigWidthDia = "60%"
    /* width of query info in dialog mode
     */
    this.mqlBigWidth = "100%"
    /* width of mql query body in sidebar and in dialog
     */
    this.editSideWidth = "55%"
    /* the desired width of the sidebar when editing a query body
     */
    this.editMainWidth = "40%"
    /* the desired width of the main area when editing a query body
     */
    this.chartWidth = "400px"
    /* dialog width for charts
     */
    this.viewState = viewState
    /* the viewstate
     */
    History.Adapter.bind(window, "statechange", this.viewState.goback.bind(this.viewState))
    this.picker2 = {}
    this.picker1 = { q: {}, w: {} }
    /* will collect the two ColorPicker1 objects, indexed as q w
     */
    this.picker1list = { q: {}, w: {} }
    /* will collect the two lists of ColorPicker1 objects,
     * index as q w and then by iid
     */
  }

  setHeight() {
    /* the heights of the sidebars are set, depending on the height of the window
     */
    const subtractm = 150
    const { tabViews } = Config
    const windowHeight = window.innerHeight
    this.windowHeight = windowHeight
    const standardHeight = windowHeight - subtractm
    this.standardHeight = standardHeight
    this.half_standard_height = `${0.4 * standardHeight}px`

    $("#material_txtp").css("height", `${standardHeight}px`)
    for (let i = 1; i <= tabViews; i++) {
      $(`#material_txt${i}`).css("height", `${standardHeight}px`)
    }
    $("#side_material_mq").css("max-height", `${0.6 * standardHeight}px`)
    $("#side_material_mw").css("max-height", `${0.35 * standardHeight}px`)
    $("#words").css("height", `${standardHeight}px`)
    $("#letters").css("height", `${standardHeight}px`)
  }

  getWidth() {
    /* save the orginal widths of sidebar and main area
     */
    this.sideWidthOld = $(".span3").css("width")
    this.mainWidthOld = $(".span9").css("width")
  }

  reset_main_width() {
    /* restore the orginal widths of sidebar and main area
     */
    const { mainWidthOld, sideWidthOld } = this
    if (sideWidthOld != $(".span3").css("width")) {
      $(".span3").css("width", sideWidthOld)
      $(".span3").css("max-width", sideWidthOld)
      $(".span9").css("width", mainWidthOld)
      $(".span9").css("max-width", mainWidthOld)
    }
  }

  set_edit_width() {
    /* switch to increased sidebar width
     */
    this.getWidth()
    const { editMainWidth, editSideWidth } = this
    $(".span3").css("width", editSideWidth)
    $(".span9").css("width", editMainWidth)
  }

  reset_material_status() {
    const { tabViews } = Config

    this.material_fetched = { txtp: false }
    this.material_kind = { txtp: "" }
    for (let i = 1; i <= tabViews; i++) {
      this.material_fetched[`txt${i}`] = false
      this.material_kind[`txt${i}`] = ""
    }
  }

  decorate_crossrefs(dest) {
    const crossrefs = dest.find("a[b]")
    crossrefs.click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const vals = {}
      vals["book"] = elem.attr("b")
      vals["chapter"] = elem.attr("c")
      vals["verse"] = elem.attr("v")
      vals["mr"] = "m"
      this.viewState.mstatesv(vals)
      this.viewState.addHist()
      this.go()
    })
    crossrefs.addClass("crossref")
  }

  set_csv(vr, mr, qw, iid, extraGiven) {
    const { tpLabels, shbStyle } = Config

    if (mr == "r") {
      const tasks = { t: "txtp", d: "txtd" }
      if (qw != "n") {
        tasks["b"] = P.viewState.tp()
      }

      for (const task in tasks) {
        const tp = tasks[task]
        const tpLab = tpLabels[tp]
        const csvctl = $(`#csv${task}_lnk_${vr}_${qw}`)
        if (task != "b" || (tp != "txtp" && tp != "txtd")) {
          const tit = csvctl.attr("ftitle")
          let extra
          if (extraGiven == undefined) {
            extra = csvctl.attr("extra")
          } else {
            csvctl.attr("extra", extraGiven)
            extra = extraGiven
          }
          csvctl.attr("href", P.viewState.csvUrl(vr, mr, qw, iid, tp, extra))
          csvctl.attr(
            "title",
            `${vr}_${shbStyle[qw]["t"]}_${iid}_${extra}_${tpLab}.csv${tit} (${tpLab})`
          )
          csvctl.show()
        } else {
          csvctl.hide()
        }
      }
    }
  }

  init() {
    /* dress up the skeleton, initialize state variables
     */
    const { viewState, picker2 } = this

    this.material = new Material()
    this.sidebars = new Sidebars()
    this.setHeight()
    this.getWidth()
    const listsettings = {}
    this.listsettings = listsettings

    for (const qw of ["q", "w", "n"]) {
      listsettings[qw] = new LSettings(qw)
      if (qw != "n") {
        picker2[qw] = listsettings[qw].picker2
      }
    }
    const prev = {}
    this.prev = prev
    for (const x in viewState.mstate()) {
      prev[x] = null
    }
    this.reset_material_status()
  }

  apply() {
    /* apply the viewstate: hide and show material as prescribed by the viewstate
     */
    this.material.apply()
    this.sidebars.apply()
  }
  go() {
    /* go to another page view, check whether initial content has to be loaded
     */
    this.reset_main_width()
    this.apply()
  }
  go_material() {
    /* load other material, whilst keeping the sidebars the same
     */
    this.material.apply()
  }

  /*
   * the origin must be an object which has a member indicating
   * the type of origin and the kind of page.

   * 1: a color picker 1 from an item in a list
   * 1a: the color picker 1 on an item page
   * 2: a color picker 2 on a list page
   * 3: a button of the list view settings
   * 4: a click on a word in the text
   * 5: when the data or text representation is loaded
   */
  highlight2(origin) {
    /* all highlighting goes through this function
        highlighting is holistic: when the user changes a view settings,
        all highlights have to be reevaluated.
        The only reduction is that word highlighting is completely orthogonal
        to query result highlighting.
    */
    const { shbStyle } = Config

    const { qw, iid, code } = origin
    const { muting_q } = L
    const { viewState, listsettings } = this
    const active = P.viewState.active(qw)
    if (active == "hlreset") {
      /* all ViewSettings for either queries or words are restored to 'factory' settings
       */
      viewState.cstatexx(qw)
      viewState.hstatesv(qw, { active: "hlcustom", sel_one: colorDefault(qw, null) })
      listsettings[qw].apply()
      return
    }
    const hlradio = $(`.${qw}hradio`)
    const activeo = $(`#${qw}${active}`)
    hlradio.removeClass("ison")
    activeo.addClass("ison")
    const colorMap = viewState.colormap(qw)

    const paintings = {}

    /* first we are going to compute what to paint,
     * resulting in a list of paint instructions.
       Then we apply the paint instructions in one batch.
     */

    /* computing the paint instructions */

    if (code == "1a") {
      /* highlights on an r-page (with a single query or word),
       * coming from the associated ColorPicker1
       * This is simple coloring, using a single color.
       */
      const paint = colorMap[iid] || colorDefault(qw == "q", iid)
      if (qw == "q") {
        $($.parseJSON($("#theslots").val())).each((i, m) => {
          paintings[m] = paint
        })
      } else if (qw == "w") {
        paintings[iid] = paint
      }
      this.paint(qw, paintings)
      return
    }

    /* all other cases: highlights on an m-page, responding to a user action
     * This is complex coloring, using multiple colors.
     * First we determine which slots need to be highlighted.
     */
    const selectColor = P.viewState.sel_one(qw)
    const custitems = {}
    const plainitems = {}

    if (qw == "q") {
      /* Queries: highlight customised items with priority over uncustomised items
       * If a word belongs to several query results,
       * the last-applied coloring determines the color that the user sees.
       * We want to promote the customised colors over the non-customized ones,
       * so we compute customized coloring after
       * uncustomized coloring.
       * Skip the muted queries
       */
      $(`#side_list_${qw} li`).each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (!muting_q.isSet(`${iid}`)) {
          const slots = $.parseJSON($(`#${qw}${iid}`).attr("slots"))
          if (P.viewState.iscolor(qw, iid)) {
            custitems[iid] = slots
          } else {
            plainitems[iid] = slots
          }
        }
      })
    } else if (qw == "w") {
      /* Words: they are disjoint, no priority needed
       */
      $(`#side_list_${qw} li`).each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (P.viewState.iscolor(qw, iid)) {
          custitems[iid] = 1
        } else {
          plainitems[iid] = 1
        }
        const all = $(`#${qw}${iid}`)
        if (active == "hlmany" || P.viewState.iscolor(qw, iid)) {
          all.show()
        } else {
          all.hide()
        }
      })
    }
    const chunks = [custitems, plainitems]

    const clselect = iid => {
      /* assigns a color to an individual slot, based on the ViewSettings
       */
      let paint = ""
      if (active == "hloff") {
        paint = shbStyle[qw]["off"]
      } /*
                viewsetting says: do not color any item */ else if (
        active == "hlone"
      ) {
        paint = selectColor
      } else if (active == "hlmany") {
        /* viewsetting says: color every applicable item with the same color */
        paint = colorMap[iid] || colorDefault(qw == "q", iid)
      } else if (active == "hlcustom") {
        /* viewsetting says:
         * color every item with customized color (if customized)
         * else with query/word-dependent default color
         */
        paint = colorMap[iid] || selectColor
      } else {
        /* viewsetting says:
         * color every item with customized color (if customized)
         * else with a single chosen color
         */
        paint = selectColor
      } /*
                but this should not occur */
      return paint
    }

    if (qw == "q") {
      /* Queries: compute the slots to be painted and the colors needed for it
       */
      for (let c = 0; c < 2; c++) {
        const chunk = chunks[c]
        for (const iid in chunk) {
          const color = clselect(iid)
          const slots = chunk[iid]
          for (const m in slots) {
            const slot = slots[m]
            if (!(slot in paintings)) {
              paintings[slot] = color
            }
          }
        }
      }
    } else if (qw == "w") {
      /* Words: gather the lexicon_ids to be painted and the colors needed for it
       */
      for (let c = 0; c < 2; c++) {
        const chunk = chunks[c]
        for (const iid in chunk) {
          let color = shbStyle[qw]["off"]
          if (c == 0) {
            /* do not color the plain items when dealing with words
             * (as opposed to queries)
             */
            color = clselect(iid)
          }
          paintings[iid] = color
        }
      }
    }
    /* maybe the selection of words of queries has changed for the same material,
     * so wipe previous coloring
     */
    const slots = $("#material span[m]")
    const stl = shbStyle[qw]["prop"]
    const clr_off = shbStyle[qw]["off"]
    slots.css(stl, clr_off)

    /* finally, the computed colors are applied */
    this.paint(qw, paintings)
  }

  paint(qw, paintings) {
    /* Execute a series of computed paint instructions
     */
    const { shbStyle, colors } = Config

    const stl = shbStyle[qw]["prop"]
    const container = `#material_${P.viewState.tp()}`
    const att = qw == "q" ? "m" : "l"
    for (const item in paintings) {
      const color = paintings[item]
      $(`${container} span[${att}="${item}"]`).css(stl, colors[color][qw])
    }
  }
}
