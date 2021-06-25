/* eslint-env jquery */
/* globals Config, P, L */

import { defcolor } from "./helpers.js"
import { Material } from "./material.js"
import { Sidebars } from "./sidebars.js"
import { LSettings } from "./materiallib.js"

export const set_heightw = () => {
  /* the heights of the sidebars are set, depending on the height of the window
   */
  const subtractw = 80
  const standard_heightw = window.innerHeight - subtractw
  $("#words").css("height", `${standard_heightw}px`)
  $("#letters").css("height", `${standard_heightw}px`)
}

export class LStorage {
  constructor() {
    const vws = $.initNamespaceStorage("nsview")
    this.nsview = vws.localStorage
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
  constructor(vs) {

    this.mql_small_height = "10em"
    /* height of mql query body in sidebar
     */
    this.mql_small_width = "97%"
    /* height of mql query body in sidebar and in dialog
     */
    this.mql_big_width_dia = "60%"
    /* width of query info in dialog mode
     */
    this.mql_big_width = "100%"
    /* width of mql query body in sidebar and in dialog
     */
    this.edit_side_width = "55%"
    /* the desired width of the sidebar when editing a query body
     */
    this.edit_main_width = "40%"
    /* the desired width of the main area when editing a query body
     */
    this.chart_width = "400px"
    /* dialog width for charts
     */
    this.vs = vs
    /* the viewstate
     */
    History.Adapter.bind(window, "statechange", this.vs.goback.bind(this.vs))
    this.picker2 = {}
    this.picker1 = { q: {}, w: {} }
    /* will collect the two Colorpicker1 objects, indexed as q w
     */
    this.picker1list = { q: {}, w: {} }
    /* will collect the two lists of Colorpicker1 objects,
     * index as q w and then by iid
     */
  }

  set_height() {
    /* the heights of the sidebars are set, depending on the height of the window
     */
    const subtractm = 150
    const { tab_views } = Config
    const window_height = window.innerHeight
    this.window_height = window_height
    const standard_height = window_height - subtractm
    this.standard_height = standard_height
    this.half_standard_height = `${0.4 * standard_height}px`

    $("#material_txt_p").css("height", `${standard_height}px`)
    for (let i = 1; i <= tab_views; i++) {
      $(`#material_txt_tb${i}`).css("height", `${standard_height}px`)
    }
    $("#side_material_mq").css("max-height", `${0.6 * standard_height}px`)
    $("#side_material_mw").css("max-height", `${0.35 * standard_height}px`)
    $("#words").css("height", `${standard_height}px`)
    $("#letters").css("height", `${standard_height}px`)
  }

  get_width() {
    /* save the orginal widths of sidebar and main area
     */
    this.orig_side_width = $(".span3").css("width")
    this.orig_main_width = $(".span9").css("width")
  }

  reset_main_width() {
    /* restore the orginal widths of sidebar and main area
     */
    const { orig_main_width, orig_side_width } = this
    if (orig_side_width != $(".span3").css("width")) {
      $(".span3").css("width", orig_side_width)
      $(".span3").css("max-width", orig_side_width)
      $(".span9").css("width", orig_main_width)
      $(".span9").css("max-width", orig_main_width)
    }
  }

  set_edit_width() {
    /* switch to increased sidebar width
     */
    this.get_width()
    const { edit_main_width, edit_side_width } = this
    $(".span3").css("width", edit_side_width)
    $(".span9").css("width", edit_main_width)
  }

  reset_material_status() {
    const { tab_views } = Config

    this.material_fetched = { txt_p: false }
    this.material_kind = { txt_p: "" }
    for (let i = 1; i <= tab_views; i++) {
      this.material_fetched[`txt_tb${i}`] = false
      this.material_kind[`txt_tb${i}`] = ""
    }
  }

  decorate_crossrefs(dest) {
    const crossrefs = dest.find("a[b]")
    crossrefs.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const vals = {}
      vals["book"] = elem.attr("b")
      vals["chapter"] = elem.attr("c")
      vals["verse"] = elem.attr("v")
      vals["mr"] = "m"
      this.vs.mstatesv(vals)
      this.vs.addHist()
      this.go()
    })
    crossrefs.addClass("crossref")
  }

  set_csv(vr, mr, qw, iid, extraGiven) {
    const { tp_labels } = Config

    if (mr == "r") {
      const tasks = { t: "txt_p", d: "txt_il" }
      if (qw != "n") {
        tasks["b"] = P.vs.tp()
      }

      for (const task in tasks) {
        const tp = tasks[task]
        const csvctrl = $(`#csv${task}_lnk_${vr}_${qw}`)
        if (task != "b" || (tp != "txt_p" && tp != "txt_il")) {
          const ctit = csvctrl.attr("ftitle")
          let extra
          if (extraGiven == undefined) {
            extra = csvctrl.attr("extra")
          } else {
            csvctrl.attr("extra", extraGiven)
            extra = extraGiven
          }
          csvctrl.attr("href", P.vs.csv_url(vr, mr, qw, iid, tp, extra))
          csvctrl.attr(
            "title",
            `${vr}_$[style[qw]["t"]}_${iid}_${extra}_${tp_labels[tp]}.csv${ctit}`
          )
          csvctrl.show()
        } else {
          csvctrl.hide()
        }
      }
    }
  }

  init() {
    /* dress up the skeleton, initialize state variables
     */
    const { vs, picker2 } = this

    this.material = new Material()
    this.sidebars = new Sidebars()
    this.set_height()
    this.get_width()
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
    for (const x in vs.mstate()) {
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
    const { style } = Config

    const { qw, iid, code } = origin
    const { muting_q } = L
    const { vs, listsettings } = this
    const active = P.vs.active(qw)
    if (active == "hlreset") {
      /* all viewsettings for either queries or words are restored to 'factory' settings
       */
      vs.cstatexx(qw)
      vs.hstatesv(qw, { active: "hlcustom", sel_one: defcolor(qw, null) })
      listsettings[qw].apply()
      return
    }
    const hlradio = $(`.${qw}hradio`)
    const activeo = $(`#${qw}${active}`)
    hlradio.removeClass("ison")
    activeo.addClass("ison")
    const cmap = vs.colormap(qw)

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
      const paint = cmap[iid] || defcolor(qw == "q", iid)
      if (qw == "q") {
        $($.parseJSON($("#themonads").val())).each((i, m) => {
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
     * First we determine which monads need to be highlighted.
     */
    const selclr = P.vs.sel_one(qw)
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
          const monads = $.parseJSON($(`#${qw}${iid}`).attr("monads"))
          if (P.vs.iscolor(qw, iid)) {
            custitems[iid] = monads
          } else {
            plainitems[iid] = monads
          }
        }
      })
    } else if (qw == "w") {
      /* Words: they are disjoint, no priority needed
       */
      $(`#side_list_${qw} li`).each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (P.vs.iscolor(qw, iid)) {
          custitems[iid] = 1
        } else {
          plainitems[iid] = 1
        }
        const all = $(`#${qw}${iid}`)
        if (active == "hlmany" || P.vs.iscolor(qw, iid)) {
          all.show()
        } else {
          all.hide()
        }
      })
    }
    const chunks = [custitems, plainitems]

    const clselect = iid => {
      /* assigns a color to an individual monad, based on the viewsettings
       */
      let paint = ""
      if (active == "hloff") {
        paint = style[qw]["off"]
      } /*
                viewsetting says: do not color any item */ else if (
        active == "hlone"
      ) {
        paint = selclr
      } else if (active == "hlmany") {
        /* viewsetting says: color every applicable item with the same color */
        paint = cmap[iid] || defcolor(qw == "q", iid)
      } else if (active == "hlcustom") {
        /* viewsetting says:
         * color every item with customized color (if customized)
         * else with query/word-dependent default color
         */
        paint = cmap[iid] || selclr
      } else {
        /* viewsetting says:
         * color every item with customized color (if customized)
         * else with a single chosen color
         */
        paint = selclr
      } /*
                but this should not occur */
      return paint
    }

    if (qw == "q") {
      /* Queries: compute the monads to be painted and the colors needed for it
       */
      for (let c = 0; c < 2; c++) {
        const chunk = chunks[c]
        for (const iid in chunk) {
          const color = clselect(iid)
          const monads = chunk[iid]
          for (const m in monads) {
            const monad = monads[m]
            if (!(monad in paintings)) {
              paintings[monad] = color
            }
          }
        }
      }
    } else if (qw == "w") {
      /* Words: gather the lexeme_ids to be painted and the colors needed for it
       */
      for (let c = 0; c < 2; c++) {
        const chunk = chunks[c]
        for (const iid in chunk) {
          let color = style[qw]["off"]
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
    const monads = $("#material span[m]")
    const stl = style[qw]["prop"]
    const clr_off = style[qw]["off"]
    monads.css(stl, clr_off)

    /* finally, the computed colors are applied */
    this.paint(qw, paintings)
  }

  paint(qw, paintings) {
    /* Execute a series of computed paint instructions
     */
    const { style, vcolors } = Config

    const stl = style[qw]["prop"]
    const container = `#material_${P.vs.tp()}`
    const att = qw == "q" ? "m" : "l"
    for (const item in paintings) {
      const color = paintings[item]
      $(`${container} span[${att}="${item}"]`).css(stl, vcolors[color][qw])
    }
  }
}
