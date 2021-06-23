/* eslint-env jquery */
/* eslint-disable no-var, camelcase */

/*globals booklangs, versions*/

/* GLOBALS
 *
 */

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = "/"

const docName = "0_home"
const nsq = $.initNamespaceStorage("muting_q")
const muting_q = nsq.localStorage
const nsn = $.initNamespaceStorage("muting_n")
const muting_n = nsn.localStorage
/* on the Queries page the user can "mute" queries. Which queries are muted,
 * is stored as key value pairs in this local storage bucket.
 * When shebanq shows relevant queries next to a page, muting is taken into account.
 */

/* state variables */

/* globals vcolors, vdefaultcolors, dncols, dnrows, thebooks, thebooksorder,
   viewinit, style, featurehost, markdown, ccolors, q, w, n, msgs
  */
/* parameters dumped by the server, mostly in json form
 */
let side_fetched, material_fetched, material_kind
/* transitory flags indicating whether kinds of material and sidebars
 * have loaded content
 */
var wb
/* holds the one and only page object
 */

/* url values for AJAX calls from this application
 * urls from which to fetch additional material through AJAX,
 * the values come from the server
 */
/* globals host, view_url, material_url, data_url, side_url, item_url, chart_url,
  words_url, notes_url, cnotes_url, field_url, fields_url, bol_url, pbl_url
 */

/* globals pref */
/* prefix for the cookie names, in order to distinguish
 * settings by the user or settings from clicking on a share link
 */

/* fixed dimensions, measures, heights, widths, etc */

const subtractm = 150
/* the canvas holding the material gets a height
 * equal to the window height minus this amount
 */
const subtractw = 80
/* the canvas holding the material gets a height
 * equal to the window height minus this amount
 */
let window_height
let standard_height
let half_standard_height
/* height of canvas
 */
let standard_heightw
/* height of canvas
 */
const mql_small_height = "10em"
/* height of mql query body in sidebar
 */
const mql_small_width = "97%"
/* height of mql query body in sidebar and in dialog
 */
const mql_big_width_dia = "60%"
/* width of query info in dialog mode
 */
const mql_big_width = "100%"
/* width of mql query body in sidebar and in dialog
 */
let orig_side_width, orig_main_width
/* the widths of sidebar and main area just after loading the initial page
 */
const edit_side_width = "55%"
/* the desired width of the sidebar when editing a query body
 */
const edit_main_width = "40%"
/* the desired width of the main area when editing a query body
 */
const chart_width = "400px"
/* dialog width for charts
 */
const chart_cols = 30
/* number of chapters in a row in a chart
 */

/* globals tp_labels, tab_info, tab_views, next_tp
 */
/* number of tab views and dictionary to go cyclically from a text view to the next
 */

/* globals tr_labels, tr_info, next_tr
 */
/* number of tab views and dictionary to go cyclically from a text view to the next
 */

/* globals nt_statclass, nt_statsym, nt_statnext
 */
/* characteristics for tabbed views with notes
 */

/* globals booktrans
 */
/* translation tables for book names
 */

// TOP LEVEL: DYNAMICS, PAGE, WINDOW, SKELETON

/* exported dynamics */

function dynamics() {
  // top level function, called when the page has loaded
  // msg = new Msg("material_settings")
  // a place where ajax messages can be shown to the user
  wb = new Page(new ViewState(viewinit, pref))
  // wb is the handle to manipulate the whole page
  wb.init()
  wb.go()
}

const set_height = () => {
  // the heights of the sidebars are set, depending on the height of the window
  window_height = window.innerHeight
  standard_height = window_height - subtractm
  half_standard_height = 0.4 * standard_height + "px"
  $("#material_txt_p").css("height", standard_height + "px")
  for (let i = 1; i <= tab_views; i++) {
    $("#material_txt_tb" + i).css("height", standard_height + "px")
  }
  $("#side_material_mq").css("max-height", 0.6 * standard_height + "px")
  $("#side_material_mw").css("max-height", 0.35 * standard_height + "px")
  $("#words").css("height", standard_height + "px")
  $("#letters").css("height", standard_height + "px")
}

/* exported set_heightw */

function set_heightw() {
  // the heights of the sidebars are set, depending on the height of the window
  standard_heightw = window.innerHeight - subtractw
  $("#words").css("height", standard_heightw + "px")
  $("#letters").css("height", standard_heightw + "px")
}

const get_width = () => {
  // save the orginal widths of sidebar and main area
  orig_side_width = $(".span3").css("width")
  orig_main_width = $(".span9").css("width")
}

const reset_main_width = () => {
  // restore the orginal widths of sidebar and main area
  if (orig_side_width != $(".span3").css("width")) {
    $(".span3").css("width", orig_side_width)
    $(".span3").css("max-width", orig_side_width)
    $(".span9").css("width", orig_main_width)
    $(".span9").css("max-width", orig_main_width)
  }
}

const set_edit_width = () => {
  // switch to increased sidebar width
  get_width()
  $(".span3").css("width", edit_side_width)
  $(".span9").css("width", edit_main_width)
}

class Page {
  /* the one and only page object
   */
  constructor(vs) {
    this.vs = vs // the viewstate
    History.Adapter.bind(window, "statechange", this.vs.goback)
    this.picker2 = {}
    this.picker1 = { q: {}, w: {} }
    /* will collect the two Colorpicker1 objects, indexed as q w
     */
    this.picker1list = { q: {}, w: {} }
    /* will collect the two lists of Colorpicker1 objects,
     * index as q w and then by iid
     */
  }

  init() {
    // dress up the skeleton, initialize state variables
    this.material = new Material()
    this.sidebars = new Sidebars()
    set_height()
    get_width()
    this.listsettings = {}
    for (const qw of ["q", "w", "n"]) {
      this.listsettings[qw] = new ListSettings(qw)
      if (qw != "n") {
        this.picker2[qw] = this.listsettings[qw].picker2
      }
    }
    this.prev = {}
    for (const x in this.vs.mstate()) {
      this.prev[x] = null
    }
    reset_material_status()
  }

  apply() {
    // apply the viewstate: hide and show material as prescribed by the viewstate
    this.material.apply()
    this.sidebars.apply()
  }
  go() {
    // go to another page view, check whether initial content has to be loaded
    reset_main_width()
    this.apply()
  }
  go_material() {
    // load other material, whilst keeping the sidebars the same
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
    const qw = origin.qw
    const code = origin.code
    const active = wb.vs.active(qw)
    if (active == "hlreset") {
      // all viewsettings for either queries or words are restored to 'factory' settings
      this.vs.cstatexx(qw)
      this.vs.hstatesv(qw, { active: "hlcustom", sel_one: defcolor(qw, null) })
      this.listsettings[qw].apply()
      return
    }
    const hlradio = $("." + qw + "hradio")
    const activeo = $("#" + qw + active)
    hlradio.removeClass("ison")
    activeo.addClass("ison")
    const cmap = this.vs.colormap(qw)

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
      const iid = origin.iid
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
    const selclr = wb.vs.sel_one(qw)
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
      $("#side_list_" + qw + " li").each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (!muting_q.isSet(iid + "")) {
          const monads = $.parseJSON($("#" + qw + iid).attr("monads"))
          if (wb.vs.iscolor(qw, iid)) {
            custitems[iid] = monads
          } else {
            plainitems[iid] = monads
          }
        }
      })
    } else if (qw == "w") {
      // Words: they are disjoint, no priority needed
      $("#side_list_" + qw + " li").each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (wb.vs.iscolor(qw, iid)) {
          custitems[iid] = 1
        } else {
          plainitems[iid] = 1
        }
        const all = $("#" + qw + iid)
        if (active == "hlmany" || wb.vs.iscolor(qw, iid)) {
          all.show()
        } else {
          all.hide()
        }
      })
    }
    const chunks = [custitems, plainitems]

    const clselect = iid => {
      // assigns a color to an individual monad, based on the viewsettings
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
    // Execute a series of computed paint instructions
    const stl = style[qw]["prop"]
    const container = "#material_" + wb.vs.tp()
    const att = qw == "q" ? "m" : "l"
    for (const item in paintings) {
      const color = paintings[item]
      $(container + " span[" + att + '="' + item + '"]').css(stl, vcolors[color][qw])
    }
  }
}

// MATERIAL

class Material {
  /* Object corresponding to everything that controls the material in the main part
   * (not in the side bars)
   */
  constructor() {
    this.name = "material"
    this.hid = "#" + this.name
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
    wb.version = wb.vs.version()
    wb.mr = wb.vs.mr()
    wb.qw = wb.vs.qw()
    wb.iid = wb.vs.iid()
    if (
      wb.mr != wb.prev["mr"] ||
      wb.qw != wb.prev["qw"] ||
      wb.version != wb.prev["version"] ||
      (wb.mr == "m" &&
        (wb.vs.book() != wb.prev["book"] ||
          wb.vs.chapter() != wb.prev["chapter"] ||
          wb.vs.verse() != wb.prev["verse"])) ||
      (wb.mr == "r" && (wb.iid != wb.prev["iid"] || wb.vs.page() != wb.prev["page"]))
    ) {
      reset_material_status()
      const p_mr = wb.prev["mr"]
      const p_qw = wb.prev["qw"]
      const p_iid = wb.prev["iid"]
      if (p_mr == "r" && wb.mr == "m") {
        const vals = {}
        if (p_qw != "n") {
          vals[p_iid] = wb.vs.colormap(p_qw)[p_iid] || defcolor(p_qw == "q", p_iid)
          wb.vs.cstatesv(p_qw, vals)
        }
      }
    }
    this.lselect.apply()
    this.mselect.apply()
    this.pselect.apply()
    this.msettings.apply()
    const book = wb.vs.book()
    const chapter = wb.vs.chapter()
    const page = wb.vs.page()
    $("#thelang").html(booklangs[wb.vs.lang()][1])
    $("#thebook").html(book != "x" ? booktrans[wb.vs.lang()][book] : "book")
    $("#thechapter").html(chapter > 0 ? chapter : "chapter")
    $("#thepage").html(page > 0 ? "" + page : "")
    for (const x in wb.vs.mstate()) {
      wb.prev[x] = wb.vs.mstate()[x]
    }
  }

  fetch() {
    // get the material by AJAX if needed, and process the material afterward
    let vars =
      `?version=${wb.version}&mr=${wb.mr}&tp=${wb.vs.tp()}&tr=${wb.vs.tr()}` +
      `&qw=${wb.qw}&lang=${wb.vs.lang()}`
    let do_fetch = false
    if (wb.mr == "m") {
      vars += `&book=${wb.vs.book()}&chapter=${wb.vs.chapter()}`
      do_fetch = wb.vs.book() != "x" && wb.vs.chapter() > 0
    } else {
      vars += `&iid=${wb.iid}&page=${wb.vs.page()}`
      do_fetch = wb.qw == "q" ? wb.iid >= 0 : wb.iid != "-1"
    }
    const tp = wb.vs.tp()
    const tr = wb.vs.tr()
    if (
      do_fetch &&
      (!material_fetched[tp] || !(tp in material_kind) || material_kind[tp] != tr)
    ) {
      this.message.msg("fetching data ...")
      wb.sidebars.after_material_fetch()
      $.get(
        material_url + vars,
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
      wb.highlight2({ code: "5", qw: "w" })
      wb.highlight2({ code: "5", qw: "q" })
      this.msettings.hebrewsettings.apply()
      this.goto_verse()
    }
  }
  goto_verse() {
    // go to the selected verse
    $(".vhl").removeClass("vhl")
    const xxx = wb.mr == "r" ? "div[tvid]" : `div[tvid="${wb.vs.verse()}"]`
    const vtarget = $(`#material_${wb.vs.tp()}>${xxx}`).filter(":first")
    if (vtarget != undefined && vtarget[0] != undefined) {
      vtarget[0].scrollIntoView()
      $("#navbar")[0].scrollIntoView()
      vtarget.addClass("vhl")
    }
  }
  process() {
    /* process new material obtained by an AJAX call
     */
    let mf = 0
    const tp = wb.vs.tp()
    const tr = wb.vs.tr()
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
    const newcontent = $("#material_" + tp)
    const textcontent = $(".txt_p,.txt_tb1,.txt_tb2,.txt_tb3")
    const ttextcontent = $(".t1_txt,.lv2")
    if (wb.vs.tr() == "hb") {
      textcontent.removeClass("pho")
      textcontent.removeClass("phox")
      ttextcontent.removeClass("pho")
      textcontent.addClass("heb")
      textcontent.addClass("hebx")
      ttextcontent.addClass("heb")
    } else if (wb.vs.tr() == "ph") {
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
    if (wb.mr == "r") {
      this.pselect.apply()
      if (wb.qw != "n") {
        wb.picker1[wb.qw].adapt(wb.iid, true)
      }
      $("a.cref").click(e => {
        e.preventDefault()
        const elem = $(e.target)
        wb.vs.mstatesv({
          book: elem.attr("book"),
          chapter: elem.attr("chapter"),
          verse: elem.attr("verse"),
          mr: "m",
        })
        wb.vs.addHist()
        wb.go()
      })
    } else {
      this.add_word_actions(newcontent, mf)
    }
    this.add_vrefs(newcontent, mf)
    if (wb.vs.tp() == "txt_il") {
      this.msettings.hebrewsettings.apply()
    } else if (wb.vs.tp() == "txt_tb1") {
      this.add_cmt(newcontent)
    }
  }

  add_cmt(newcontent) {
    /* add actions for the tab1 view
     */
    this.notes = new Notes(newcontent)
  }

  add_vrefs(newcontent, mf) {
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
      const base_tp = wb.vs.tp()
      const dat = $("#" + base_tp + "_txt_il_" + bk + "_" + ch + "_" + vs)
      const txt = $("#" + base_tp + "_" + bk + "_" + ch + "_" + vs)
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
          dat.html("fetching data for " + bk + " " + ch + ":" + vs + " ...")
          dat.load(
            `${data_url}?version=${wb.version}&book=${bk}&chapter=${ch}&verse=${vs}`,
            () => {
              dat.attr("lf", "v")
              this.msettings.hebrewsettings.apply()
              if (wb.mr == "r") {
                if (wb.qw != "n") {
                  wb.picker1[wb.qw].adapt(wb.iid, true)
                }
              } else {
                wb.highlight2({ code: "5", qw: "w" })
                wb.highlight2({ code: "5", qw: "q" })
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
      if (wb.vs.iscolor(qw, iid)) {
        wb.vs.cstatex(qw, iid)
        all.hide()
      } else {
        const vals = {}
        vals[iid] = defcolor(false, iid)
        wb.vs.cstatesv(qw, vals)
        all.show()
      }
      const active = wb.vs.active(qw)
      if (active != "hlcustom" && active != "hlmany") {
        wb.vs.hstatesv(qw, { active: "hlcustom" })
      }
      if (wb.vs.get("w") == "v") {
        if (iid in wb.picker1list["w"]) {
          /* should not happen but it happens when changing data versions
           */
          wb.picker1list["w"][iid].apply(false)
        }
      }
      wb.highlight2({ code: "4", qw })
      wb.vs.addHist()
    })
    if (mf > 1) {
      /* Initially, material gets highlighted once the sidebars have been loaded.
       * But when we load a different representation of material (data, tab),
       * the sidebars are still there,
       * and after loading the material, highlighs have to be applied.
       */
      wb.highlight2({ code: "5", qw: "q" })
      wb.highlight2({ code: "5", qw: "w" })
    }
  }
}

// MATERIAL: Notes

class Notes {
  constructor(newcontent) {
    this.show = false
    this.verselist = {}
    this.version = wb.version
    this.sav_controls = $("span.nt_main_sav")
    this.sav_c = this.sav_controls.find('a[tp="s"]')
    this.rev_c = this.sav_controls.find('a[tp="r"]')
    this.logged_in = false
    this.cctrl = $("a.nt_main_ctrl")

    newcontent.find(".vradio").each((i, el) => {
      const elem = $(el)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const topl = elem.closest("div")
      this.verselist[`${bk} ${ch}:${vs}`] = new Notev(
        this.version,
        bk,
        ch,
        vs,
        topl.find("span.nt_ctrl"),
        topl.find("table.t1_table")
      )
    })
    const { verselist } = this
    this.msgn = new Msg("nt_main_msg", () => {
      for (const notev of Object.values(verselist)) {
        notev.clear_msg()
      }
    })
    this.cctrl.click(e => {
      e.preventDefault()
      wb.vs.hstatesv("n", { get: wb.vs.get("n") == "v" ? "x" : "v" })
      this.apply()
    })
    this.rev_c.click(e => {
      e.preventDefault()
      for (const notev of Object.values(verselist)) {
        notev.revert()
      }
    })
    this.sav_c.click(e => {
      e.preventDefault()
      for (const notev of Object.values(verselist)) {
        notev.save()
      }
      this.msgn.msg(["special", "Done"])
    })
    this.msgn.clear()
    $("span.nt_main_sav").hide()
    this.apply()
  }

  apply() {
    const { verselist } = this

    if (wb.vs.get("n") == "v") {
      this.cctrl.addClass("nt_loaded")
      for (const notev of Object.values(verselist)) {
        notev.show_notes(false)
        this.logged_in = notev.logged_in
      }
      if (this.logged_in) {
        this.sav_controls.show()
      }
    } else {
      this.cctrl.removeClass("nt_loaded")
      this.sav_controls.hide()
      for (const notev of Object.values(verselist)) {
        notev.hide_notes()
      }
    }
  }

}

class Notev {
  constructor(vr, bk, ch, vs, ctrl, dest) {
    this.loaded = false
    this.nnotes = 0
    this.mnotes = 0
    this.show = false
    this.edt = false
    this.dirty = false
    this.version = vr
    this.book = bk
    this.chapter = ch
    this.verse = vs
    this.ctrl = ctrl
    this.dest = dest
    this.msgn = new Msg("nt_msg_" + this.book + "_" + this.chapter + "_" + this.verse)
    this.cctrl = this.ctrl.find("a.nt_ctrl")
    this.sav_controls = this.ctrl.find("span.nt_sav")
    this.sav_c = this.sav_controls.find('a[tp="s"]')
    this.edt_c = this.sav_controls.find('a[tp="e"]')
    this.rev_c = this.sav_controls.find('a[tp="r"]')

    this.sav_c.click(e => {
      e.preventDefault()
      this.save()
    })
    this.edt_c.click(e => {
      e.preventDefault()
      this.edit()
    })
    this.rev_c.click(e => {
      e.preventDefault()
      this.revert()
    })
    this.cctrl.click(e => {
      e.preventDefault()
      this.is_dirty()
      if (this.show) {
        this.hide_notes()
      } else {
        this.show_notes(true)
      }
    })

    this.dest.find("tr.nt_cmt").hide()
    $("span.nt_main_sav").hide()
    this.sav_controls.hide()
  }

  fetch(adjust_verse) {
    const { version, book, chapter, verse, edt } = this
    const senddata = { version, book, chapter, verse, edit: edt }
    this.msgn.msg(["info", "fetching notes ..."])
    $.post(cnotes_url, senddata, data => {
      this.loaded = true
      this.msgn.clear()
      for (const m of data.msgs) {
        this.msgn.msg(m)
      }
      const { good, users, notes, nkey_index, changed, logged_in } = data
      if (good) {
        this.process(
          users,
          notes,
          nkey_index,
          changed,
          logged_in
        )
        if (adjust_verse) {
          if (wb.mr == "m") {
            wb.vs.mstatesv({ verse: this.verse })
            wb.material.goto_verse()
          }
        }
      }
    })
  }

  process(users, notes, nkey_index, changed, logged_in) {
    if (changed) {
      if (wb.mr == "m") {
        side_fetched["mn"] = false
        wb.sidebars.sidebar["mn"].content.apply()
      }
    }
    this.orig_users = users
    this.orig_notes = notes
    this.orig_nkey_index = nkey_index
    this.orig_edit = []
    this.logged_in = logged_in
    this.gen_html(true)
    this.dirty = false
    this.apply_dirty()
    this.decorate()
  }

  decorate() {
    this.dest
      .find("td.nt_stat")
      .find("a")
      .click(e => {
        e.preventDefault()
        const elem = $(e.target)
        const statcode = elem.attr("code")
        const nextcode = nt_statnext[statcode]
        const nextsym = nt_statsym[nextcode]
        const row = elem.closest("tr")
        for (const c in nt_statclass) {
          row.removeClass(nt_statclass[c])
        }
        for (const c in nt_statsym) {
          elem.removeClass(`fa-${nt_statsym[c]}`)
        }
        row.addClass(nt_statclass[nextcode])
        elem.attr("code", nextcode)
        elem.addClass(`fa-${nextsym}`)
      })
    this.dest
      .find("td.nt_pub")
      .find("a")
      .click(e => {
        e.preventDefault()
        const elem = $(e.target)
        if (elem.hasClass("ison")) {
          elem.removeClass("ison")
        } else {
          elem.addClass("ison")
        }
      })
    this.dest.find("tr.nt_cmt").show()
    if (this.logged_in) {
      $("span.nt_main_sav").show()
      this.sav_controls.show()
      if (this.edt) {
        this.sav_c.show()
        this.edt_c.hide()
      } else {
        this.sav_c.hide()
        this.edt_c.show()
      }
    }
    decorate_crossrefs(this.dest)
  }

  gen_html_ca(canr) {
    const vr = this.version
    const notes = this.orig_notes[canr]
    const nkey_index = this.orig_nkey_index
    let html = ""
    this.nnotes += notes.length
    for (let n = 0; n < notes.length; n++) {
      const nline = notes[n]
      const kwtrim = $.trim(nline.kw)
      const kws = kwtrim.split(/\s+/)
      const uid = nline.uid
      let mute = false
      for (const kw of kws) {
        const nkid = nkey_index[`${uid} ${kw}`]
        if (muting_n.isSet(`n${nkid}`)) {
          mute = true
          break
        }
      }
      if (mute) {
        this.mnotes += 1
        continue
      }
      const user = this.orig_users[uid]
      const nid = nline.nid
      const pubc = nline.pub ? "ison" : ""
      const sharedc = nline.shared ? "ison" : ""
      const statc = nt_statclass[nline.stat]
      const statsym = nt_statsym[nline.stat]
      const ro = nline.ro
      const edit_att = ro ? "" : ' edit="1"'
      const edit_class = ro ? "" : " edit"
      html += (
        `<tr class="nt_cmt nt_info ${statc}${edit_class}" nid="${nid}"
          ncanr="${canr}"${edit_att}">`
      )
      if (ro) {
        html += (
          `<td class="nt_stat">
            <span class="fa fa-${statsym} fa-fw" code="${nline.stat}"></span>
          </td>`
        )
        html += `<td class="nt_kw">${escapeHTML(nline.kw)}</td>`
        const ntxt = special_links(markdown.toHTML(markdownEscape(nline.ntxt)))
        html += `<td class="nt_cmt">${ntxt}</td>`
        html += `<td class="nt_user" colspan="3" uid="${uid}">${escapeHTML(user)}</td>`
        html += '<td class="nt_pub">'
        html += `<span class="ctrli pradio fa fa-share-alt fa-fw ${sharedc}"
          title="shared?"></span>`
        html += `<span class="ctrli pradio fa fa-quote-right fa-fw ${pubc}"
          title="published?"></span>`
      } else {
        this.orig_edit.push({ canr, note: nline })
        html += `<td class="nt_stat">
          <a href="#" title="set status" class="fa fa-${statsym} fa-fw"
          code="${nline.stat}"></a></td>`
        html += `<td class="nt_kw"><textarea>${nline.kw}</textarea></td>`
        html += `<td class="nt_cmt"><textarea>${nline.ntxt}</textarea></td>`
        html += `<td class="nt_user" colspan="3" uid="{uid}">${escapeHTML(user)}</td>`
        html += '<td class="nt_pub">'
        html += `<a class="ctrli pradio fa fa-share-alt fa-fw ${sharedc}"
          href="#" title="shared?"></a>`
        html += `<span>${vr}</span>`
        html += `<a class="ctrli pradio fa fa-quote-right fa-fw ${pubc}"
          href="#" title="published?"></a>`
      }
      html += "</td></tr>"
    }
    return html
  }

  gen_html(replace) {
    this.mnotes = 0
    if (replace) {
      this.dest.find("tr[ncanr]").remove()
    }
    for (const canr in this.orig_notes) {
      const target = this.dest.find(`tr[canr="${canr}"]`)
      const html = this.gen_html_ca(canr)
      target.after(html)
    }
    if (this.nnotes == 0) {
      this.cctrl.addClass("nt_empty")
    } else {
      this.cctrl.removeClass("nt_empty")
    }
    if (this.mnotes == 0) {
      this.cctrl.removeClass("nt_muted")
    } else {
      this.cctrl.addClass("nt_muted")
      this.msgn.msg(["special", `muted notes: ${this.mnotes}`])
    }
  }

  sendnotes(senddata) {
    $.post(
      cnotes_url,
      senddata,
      data => {
        const { good, users, notes, nkey_index, changed, logged_in } = data
        this.msgn.clear()
        for (const m of data.msgs) {
          this.msgn.msg(m)
        }
        if (good) {
          this.dest.find("tr[ncanr]").remove()
          this.process(
            users,
            notes,
            nkey_index,
            changed,
            logged_in
          )
        }
      },
      "json"
    )
  }

  is_dirty() {
    let dirty = false
    if (this.orig_edit == undefined) {
      this.dirty = false
      return
    }
    for (let n = 0; n < this.orig_edit.length; n++) {
      const canr = this.orig_edit[n].canr
      const o_note = this.orig_edit[n].note
      const nid = o_note.nid
      const n_note =
        nid == 0
          ? this.dest.find(`tr[nid="0"][ncanr="${canr}"]`)
          : this.dest.find(`tr[nid="${nid}"]`)
      const o_stat = o_note.stat
      const n_stat = n_note.find("td.nt_stat a").attr("code")
      const o_kw = $.trim(o_note.kw)
      const n_kw = $.trim(n_note.find("td.nt_kw textarea").val())
      const o_ntxt = o_note.ntxt
      const n_ntxt = $.trim(n_note.find("td.nt_cmt textarea").val())
      const o_shared = o_note.shared
      const n_shared = n_note.find("td.nt_pub a").first().hasClass("ison")
      const o_pub = o_note.pub
      const n_pub = n_note.find("td.nt_pub a").last().hasClass("ison")
      if (
        o_stat != n_stat ||
        o_kw != n_kw ||
        o_ntxt != n_ntxt ||
        o_shared != n_shared ||
        o_pub != n_pub
      ) {
        dirty = true
        break
      }
    }
    this.dirty = dirty
    this.apply_dirty()
  }

  apply_dirty() {
    if (this.dirty) {
      this.cctrl.addClass("dirty")
    } else if (this.cctrl.hasClass("dirty")) {
      this.cctrl.removeClass("dirty")
    }
  }
  save() {
    this.edt = false
    const { version, book, chapter, verse, edt } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    const notelines = []
    if (this.orig_edit == undefined) {
      return
    }
    for (let n = 0; n < this.orig_edit.length; n++) {
      const canr = this.orig_edit[n].canr
      const o_note = this.orig_edit[n].note
      const nid = o_note.nid
      const uid = o_note.uid
      const n_note =
        nid == 0
          ? this.dest.find(`tr[nid="0"][ncanr="${canr}"]`)
          : this.dest.find(`tr[nid="${nid}"]`)
      const o_stat = o_note.stat
      const n_stat = n_note.find("td.nt_stat a").attr("code")
      const o_kw = $.trim(o_note.kw)
      const n_kw = $.trim(n_note.find("td.nt_kw textarea").val())
      const o_ntxt = o_note.ntxt
      const n_ntxt = $.trim(n_note.find("td.nt_cmt textarea").val())
      const o_shared = o_note.shared
      const n_shared = n_note.find("td.nt_pub a").first().hasClass("ison")
      const o_pub = o_note.pub
      const n_pub = n_note.find("td.nt_pub a").last().hasClass("ison")
      if (
        o_stat != n_stat ||
        o_kw != n_kw ||
        o_ntxt != n_ntxt ||
        o_shared != n_shared ||
        o_pub != n_pub
      ) {
        notelines.push({
          nid,
          canr,
          stat: n_stat,
          kw: n_kw,
          ntxt: n_ntxt,
          uid,
          shared: n_shared,
          pub: n_pub,
        })
      }
    }
    if (notelines.length > 0) {
      data["notes"] = JSON.stringify(notelines)
    } else {
      this.msgn.msg(["warning", "No changes"])
    }
    this.sendnotes(data)
  }

  edit() {
    this.edt = true
    this.fetch(true)
  }

  revert() {
    this.edt = false
    const { version, book, chapter, verse, edt } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    data["notes"] = JSON.stringify([])
    this.sendnotes(data)
  }

  hide_notes() {
    this.show = false
    this.cctrl.removeClass("nt_loaded")
    this.sav_controls.hide()
    this.dest.find("tr.nt_cmt").hide()
    this.msgn.hide()
  }

  show_notes(adjust_verse) {
    this.show = true
    this.cctrl.addClass("nt_loaded")
    this.msgn.show()
    if (!this.loaded) {
      this.fetch(adjust_verse)
    } else {
      this.dest.find("tr.nt_cmt").show()
      if (this.logged_in) {
        this.sav_controls.show()
        if (this.edt) {
          this.sav_c.show()
          this.edt_c.hide()
        } else {
          this.sav_c.hide()
          this.edt_c.show()
        }
      }
      if (wb.mr == "m") {
        wb.vs.mstatesv({ verse: this.verse })
        wb.material.goto_verse()
      }
    }
  }

  clear_msg() {
    this.msgn.clear()
  }
}

/* MATERIAL: SELECTION
 *
 */

class MSelect {
  /* for book and chapter selection
   */

  constructor() {
    this.name = "select_passage"
    this.hid = "#" + this.name
    this.book = new SelectBook()
    this.select = new SelectItems("chapter")
    for (const v in versions) {
      this.set_vselect(v)
    }
    $("#self_link").hide()
  }

  apply() {
    /* apply material viewsettings to current material
     */
    const thisFeaturehost = `${featurehost}/${docName}`
    $(".source").attr("href", thisFeaturehost)
    $(".source").attr("title", "BHSA feature documentation")
    $(".mvradio").removeClass("ison")
    $("#version_" + wb.version).addClass("ison")
    const bol = $("#bol_lnk")
    const pbl = $("#pbl_lnk")

    if (wb.mr == "m") {
      this.book.apply()
      this.select.apply()
      $(this.hid).show()
      const book = wb.vs.book()
      const chapter = wb.vs.chapter()
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
    if (versions[v]) {
      $(`#version_${v}`).click(e => {
        e.preventDefault()
        side_fetched["mw"] = false
        side_fetched["mq"] = false
        side_fetched["mn"] = false
        wb.vs.mstatesv({ version: v })
        wb.go()
      })
    }
  }
}

class PSelect {
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
    if (wb.mr == "r") {
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
    if (wb.mr == "r") {
      $(select).html(response.find(select).html())
    }
  }
}

class LSelect {
  /* language selection
   */
  constructor() {
    this.name = "select_contents_lang"
    this.hid = "#" + this.name
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
    const thelang = wb.vs.lang()
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
        wb.vs.mstatesv(vals)
        this.update_vlabels()
        wb.vs.addHist()
        wb.material.apply()
      }
    })
  }

  update_vlabels() {
    $("span[book]").each((i, el) => {
      const elem = $(el)
      elem.html(booktrans[wb.vs.lang()][elem.attr("book")])
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
  // book selection
  constructor() {
    this.name = "select_contents_book"
    this.hid = "#" + this.name
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
    const thebook = wb.vs.book()
    const lang = wb.vs.lang()
    const thisbooksorder = thebooksorder[wb.version]
    const nitems = thisbooksorder.length

    this.lastitem = nitems

    let ht = ""
    ht += '<div class="pagination"><ul>'
    for (const item of thisbooksorder) {
      const itemrep = booktrans[lang][item]
      const liCls = thebook == item ? ' class="active"' : ''
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
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
        wb.go()
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
    this.name = "select_contents_" + this.key
    this.other_name = "select_contents_" + this.other_key
    this.hid = "#" + this.name
    this.other_hid = "#" + this.other_name
    this.control = "#select_control_" + this.key
    this.prev = $("#prev_" + this.key)
    this.next = $("#next_" + this.key)

    this.prev.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      wb.vs.mstatesv(vals)
      wb.vs.addHist()
      this.go()
    })
    this.next.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const vals = {}
      vals[this.key] = elem.attr("contents")
      vals["verse"] = "1"
      wb.vs.mstatesv(vals)
      wb.vs.addHist()
      this.go()
    })
    $(this.control).click(e => {
      e.preventDefault()
      $(this.hid).dialog("open")
    })
  }

  go() {
    if (this.key == "chapter") {
      wb.go()
    } else {
      wb.go_material()
    }
  }

  present() {
    close_dialog($(this.other_hid))
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose " + this.key,
      width: "200px",
    })
  }

  gen_html() {
    /* generate a new page selector
     */
    let theitem
    let itemlist
    let nitems

    if (this.key == "chapter") {
      const thebook = wb.vs.book()
      theitem = wb.vs.chapter()
      nitems = thebook != "x" ? thebooks[wb.version][thebook] : 0
      this.lastitem = nitems
      itemlist = new Array(nitems)
      for (let i = 0; i < nitems; i++) {
        itemlist[i] = i + 1
      }
    } else {
      /* 'page'
       */
      theitem = wb.vs.page()
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
          const liCls = theitem == item ? ' class="active"' : ''
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
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
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
      const thisitem = parseInt(this.key == "page" ? wb.vs.page() : wb.vs.chapter())
      if (thisitem == undefined || thisitem == 1) {
        this.prev.hide()
      } else {
        this.prev.attr("contents", "" + (thisitem - 1))
        this.prev.show()
      }
      if (thisitem == undefined || thisitem == this.lastitem) {
        this.next.hide()
      } else {
        this.next.attr("contents", "" + (thisitem + 1))
        this.next.show()
      }
    }
    this.present()
  }
}

class CSelect {
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
    if (!this.loaded[`${this.qw}_${wb.iid}`]) {
      if (
        $(`#select_contents_chart_${this.vr}_${this.qw}_${wb.iid}`).length ==
        0
      ) {
        $(this.select).append(
          `<span id="select_contents_chart_${this.vr}_${this.qw}_${wb.iid}"></span>`
        )
      }
      this.fetch(wb.iid)
    } else {
      this.show()
    }
  }

  fetch(iid) {
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
      wb.vs.mstatesv(vals)
      wb.vs.addHist()
      wb.go()
    })
    $("#theitemc").html(
      `Back to ${$("#theitem").html()} (version ${this.vr})`
    )
    /* fill in the Back to query/word line in a chart
     */
    this.present(iid)
    this.show(iid)
  }

  present(iid) {
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
        const ch_range = block_info[1] + "-" + block_info[2]
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
          sz = " (" + blsize + "%)"
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
      wb.vs.mstatesv(vals)
      wb.vs.hstatesv("q", { sel_one: "white", active: "hlcustom" })
      wb.vs.hstatesv("w", { sel_one: "black", active: "hlcustom" })
      wb.vs.cstatexx("q")
      wb.vs.cstatexx("w")
      if (this.qw != "n") {
        vals = {}
        vals[iid] = wb.vs.colormap(this.qw)[iid] || defcolor(this.qw == "q", iid)
        wb.vs.cstatesv(this.qw, vals)
      }
      wb.vs.addHist()
      wb.go()
    })
  }
}

/* MATERIAL (messages when retrieving, storing the contents)
 *
 */

class MMessage {
  // diagnostic output
  //
  constructor() {
    this.name = "material_message"
    this.hid = "#" + this.name
  }

  add(response) {
    $(this.hid).html(response.children(this.hid).html())
  }

  msg(m) {
    $(this.hid).html(m)
  }
}

class MContent {
  /* the actual Hebrew content, either plain text or tabbed data
   */
  constructor() {
    this.name_content = "#material_content"
    this.select = () => {}
  }

  add(response) {
    $(`#material_${wb.vs.tp()}`).html(response.children(this.name_content).html())
  }

  show() {
    const this_tp = wb.vs.tp()
    for (const tp in next_tp) {
      const this_material = $(`#material_${tp}`)
      if (this_tp == tp) {
        this_material.show()
      } else {
        this_material.hide()
      }
    }
  }
}

/* MATERIAL SETTINGS (for choosing between plain text and tabbed data)
 *
 */

class MSettings {
  constructor(content) {
    const hltext = $("#mtxt_p")
    const hltabbed = $("#mtxt_tb1")
    this.legend = $("#datalegend")
    this.legendc = $("#datalegend_control")
    this.name = "material_settings"
    this.hid = `#${this.name}`
    this.content = content
    this.hebrewsettings = new HebrewSettings()

    hltext.show()
    hltabbed.show()

    this.legendc.click(e => {
      e.preventDefault()
      $("#datalegend")
        .find("a[fname]")
        .each((i, el) => {
          const elem = $(el)
          const url = `${featurehost}/${elem.attr("fname")}`
          elem.attr("href", url)
        })
      this.legend.dialog({
        autoOpen: true,
        dialogClass: "legend",
        closeOnEscape: true,
        modal: false,
        title: "legend",
        width: "600px",
      })
    })

    $(".mhradio").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const old_tp = wb.vs.tp()
      let new_tp = elem.attr("id").substring(1)
      if (old_tp == "txt_p") {
        if (old_tp == new_tp) {
          return
        }
      } else if (old_tp == new_tp) {
        new_tp = next_tp[old_tp]
        if (new_tp == "txt_p") {
          new_tp = next_tp[new_tp]
        }
      }
      wb.vs.mstatesv({ tp: new_tp })
      wb.vs.addHist()
      this.apply()
    })

    $(".mtradio").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const old_tr = wb.vs.tr()
      let new_tr = elem.attr("id").substring(1)
      if (old_tr == new_tr) {
        new_tr = next_tr[old_tr]
      }

      wb.vs.mstatesv({ tr: new_tr })
      wb.vs.addHist()
      this.apply()
    })

    for (let i = 1; i <= tab_views; i++) {
      const mc = $(`#mtxt_tb${i}`)
      mc.attr("title", tab_info[`txt_tb${i}`])
      if (i == 1) {
        mc.show()
      } else {
        mc.hide()
      }
    }

    for (const l in tr_labels) {
      const t = tr_info[l]
      const mc = $(`#m${t}`)
      mc.attr("title", tr_labels[t])
      if (l == "hb") {
        mc.show()
      } else {
        mc.hide()
      }
    }
  }

  apply() {
    const hlradio = $(".mhradio")
    const plradio = $(".mtradio")
    const new_tp = wb.vs.tp()
    const new_tr = wb.vs.tr()
    const newc = $(`#m${new_tp}`)
    const newp = $(`#m${new_tr}`)
    hlradio.removeClass("ison")
    plradio.removeClass("ison")
    if (new_tp != "txt_p" && new_tp != "txt_il") {
      for (let i = 1; i <= tab_views; i++) {
        const mc = $(`#mtxt_tb${i}`)
        if (`txt_tb${i}` == new_tp) {
          mc.show()
        } else {
          mc.hide()
        }
      }
    }
    newc.show()
    newp.show()
    newc.addClass("ison")
    newp.addClass("ison")
    this.content.show()
    this.legend.hide()
    close_dialog(this.legend)
    this.legendc.hide()
    wb.material.adapt()
  }
}

/* HEBREW DATA (which fields to show if interlinear text is displayed)
 *
 */

class HebrewSettings {
  constructor() {
    for (const fld in wb.vs.ddata()) {
      this[fld] = new HebrewSetting(fld)
    }
  }

  apply() {
    for (const fld in wb.vs.ddata()) {
      this[fld].apply()
    }
    for (const v in versions) {
      set_csv(v, wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
    }
  }
}

class HebrewSetting {
  constructor(fld) {
    this.name = fld
    this.hid = `#${this.name}`
    $(this.hid).click(e => {
      const elem = $(e.target)
      const vals = {}
      vals[fld] = elem.prop("checked") ? "v" : "x"
      wb.vs.dstatesv(vals)
      wb.vs.addHist()
      this.applysetting()
      for (const v in versions) {
        set_csv(v, wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
      }
    })
  }

  apply() {
    const val = wb.vs.ddata()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }

  applysetting() {
    if (wb.vs.ddata()[this.name] == "v") {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.show()
      })
    } else {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.hide()
      })
    }
  }
}

/* SIDEBARS
 *
 */

class Sidebars {
  // TOP LEVEL: all four kinds of sidebars
  constructor() {
    this.sidebar = {}
    for (const mr of ["m", "r"]) {
      for (const qw of ["q", "w", "n"]) {
        this.sidebar[`${mr}${qw}`] = new Sidebar(mr, qw)
      }
    }
    side_fetched = {}
  }

  apply() {
    for (const mr of ["m", "r"]) {
      for (const qw of ["q", "w", "n"]) {
        this.sidebar[`${mr}${qw}`].apply()
      }
    }
  }

  after_material_fetch() {
    for (const qw of ["q", "w", "n"]) {
      side_fetched[`m${qw}`] = false
    }
  }

  after_item_fetch() {
    for (const qw of ["q", "w", "n"]) {
      side_fetched[`r${qw}`] = false
    }
  }
}

/* SPECIFIC sidebars, the [mr][qw] type is frozen into the object
 *
 */

class Sidebar {
  /* the individual sidebar, parametrized with qr and mw
   * to specify one of the four kinds
   */
  constructor(mr, qw) {
    this.mr = mr
    this.qw = qw
    this.name = `side_bar_${mr}${qw}`
    this.hid = `#${this.name}`
    this.hide = $(`#side_hide_${mr}${qw}`)
    this.show = $(`#side_show_${mr}${qw}`)
    this.content = new SContent(mr, qw)

    if (mr == "r") {
      this.cselect = {}
      for (const v in versions) {
        if (versions[v]) {
          this.add_version(v)
        }
      }
    }
    this.show.click(e => {
      e.preventDefault()
      wb.vs.hstatesv(this.qw, { get: "v" })
      wb.vs.addHist()
      this.apply()
    })

    this.hide.click(e => {
      e.preventDefault()
      wb.vs.hstatesv(this.qw, { get: "x" })
      wb.vs.addHist()
      this.apply()
    })
  }

  add_version(v) {
    const { qw } = this
    this.cselect[v] = new CSelect(v, qw)
  }

  apply() {
    const { mr, qw, hide, show } = this
    const thebar = $(this.hid)
    const thelist = $(`#side_material_${mr}${qw}`)
    const theset = $(`#side_settings_${mr}${qw}`)
    if (this.mr != wb.mr || (this.mr == "r" && this.qw != wb.qw)) {
      thebar.hide()
    } else {
      thebar.show()
      theset.show()
      if (this.mr == "m") {
        if (wb.vs.get(this.qw) == "x") {
          thelist.hide()
          theset.hide()
          hide.hide()
          show.show()
        } else {
          thelist.show()
          theset.show()
          hide.show()
          show.hide()
        }
      } else {
        hide.hide()
        show.hide()
      }
      this.content.apply()
    }
  }
}

/* SIDELIST MATERIAL
 *
 */

class SContent {
  // the contents of an individual sidebar
  constructor(mr, qw) {
    this.mr = mr
    this.qw = qw
    this.other_mr = this.mr == "m" ? "r" : "m"
    const thebar = $(this.hid)
    const hide = $("#side_hide_" + mr + qw)
    const show = $("#side_show_" + mr + qw)
    this.name = "side_material_" + mr + qw
    this.hid = "#" + this.name

    if (mr == "r") {
      if (qw != "n") {
        wb.picker1[qw] = new Colorpicker1(qw, null, true, false)
      }
    }
  }

  msg(m) {
    $(this.hid).html(m)
  }

  set_vselect(v) {
    if (versions[v]) {
      $(`#version_s_${v}`).click(e => {
        e.preventDefault()
        wb.vs.mstatesv({ version: v })
        wb.go()
      })
    }
  }

  process() {
    const { mr, qw } = this

    wb.sidebars.after_item_fetch()
    this.sidelistitems()
    if (this.mr == "m") {
      wb.listsettings[this.qw].apply()
    } else {
      for (const v in versions) {
        if (versions[v]) {
          wb.sidebars.sidebar[`r${this.qw}`].cselect[v].init()
        }
      }

      const vr = wb.version
      const iid = wb.vs.iid()

      $(".moredetail").click(e => {
        e.preventDefault()
        const elem = $(e.target)
        toggle_detail(elem)
      })
      $(".detail").hide()
      $(`div[version="${vr}"]`)
        .find(".detail")
        .show()

      this.msgo = new Msg(`dbmsg_${qw}`)

      let ufname, ulname

      if (qw == "q") {
        this.info = q
        $("#theqid").html(q.id)
        ufname = escapeHTML(q.ufname || "")
        ulname = escapeHTML(q.ulname || "")
        const qname = escapeHTML(q.name || "")
        $("#itemtag").val(`${ufname} ${ulname}: ${qname}`)
        this.msgov = new Msg("dbmsg_qv")
        $("#is_pub_c").show()
        $("#is_pub_ro").hide()
      } else if (qw == "w") {
        this.info = w
        if ("versions" in w) {
          const wvr = w.versions[vr]
          const wentryh = escapeHTML(wvr.entry_heb)
          const wentryid = escapeHTML(wvr.entryid)
          $("#itemtag").val(`${wentryh}: ${wentryid}`)
          $("#gobackw").attr(
            "href",
            `${words_url}?lan=${wvr.lan}&` +
            `letter=${wvr.entry_heb.charCodeAt(0)}&goto=${w.id}`
          )
        }
      } else if (qw == "n") {
        this.info = n
        if ("versions" in n) {
          ufname = escapeHTML(n.ufname)
          ulname = escapeHTML(n.ulname)
          const kw = escapeHTML(n.kw)
          const nvr = n.versions[vr]
          $("#itemtag").val(`${ufname} ${ulname}: ${kw}`)
          $("#gobackn").attr("href", `${notes_url}?goto=${n.id}`)
        }
      }
      if ("versions" in this.info) {
        for (const v in this.info.versions) {
          const extra = qw == "w" ? "" : `${ufname}_${ulname}`
          this.set_vselect(v)
          set_csv(v, mr, qw, iid, extra)
        }
      }
      for (const m of msgs) {
        this.msgo.msg(m)
      }
    }

    let thistitle
    if (this.mr == "m") {
      thistitle =
        `[${wb.vs.version()}] ${wb.vs.book()} ${wb.vs.chapter()}:${wb.vs.verse()}`
    } else {
      thistitle = $("#itemtag").val()
      $("#theitem").html(`${thistitle} `)
      /* fill in the title of the query/word/note above the verse material
       * and put it in the page title as well
       */
    }
    document.title = thistitle

    if (this.qw == "q") {
      if (this.mr == "m") {
        /* in the sidebar list of queries:
         * the mql query body can be popped up as a dialog for viewing it
         * in a larger canvas
         */
        $(".fullc").click(e => {
          e.preventDefault()
          const elem = $(e.target)
          const thisiid = elem.attr("iid")
          const mqlq = $(`#area_${thisiid}`)
          const dia = $(`#bigq_${thisiid}`).dialog({
            dialogClass: "mql_dialog",
            closeOnEscape: true,
            close: () => {
              dia.dialog("destroy")
              const mqlq = $(`#area_${thisiid}`)
              mqlq.css("height", mql_small_height)
              mqlq.css("width", mql_small_width)
            },
            modal: false,
            title: "mql query body",
            position: { my: "left top", at: "left top", of: window },
            width: mql_big_width_dia,
            height: window_height,
          })
          mqlq.css("height", standard_height)
          mqlq.css("width", mql_big_width)
        })
      } else {
        /* in the sidebar item view of a single query:
         * the mql query body can be popped up as a dialog for viewing it
         * in a larger canvas
         */
        const vr = wb.version
        const fullc = $(".fullc")
        const editq = $("#editq")
        const execq = $("#execq")
        const saveq = $("#saveq")
        const cancq = $("#cancq")
        const doneq = $("#doneq")
        const nameq = $("#nameq")
        const descm = $("#descm")
        const descq = $("#descq")
        const mqlq = $("#mqlq")
        const pube = $("#is_pub_c")
        const pubr = $("#is_pub_ro")
        const is_pub = "versions" in q && vr in q.versions && q.versions[vr].is_published

        fullc.click(e => {
          e.preventDefault()
          fullc.hide()
          const dia = $("#bigger")
            .closest("div")
            .dialog({
              dialogClass: "mql_dialog",
              closeOnEscape: true,
              close: () => {
                dia.dialog("destroy")
                mqlq.css("height", mql_small_height)
                descm.removeClass("desc_dia")
                descm.addClass("desc")
                descm.css("height", mql_small_height)
                fullc.show()
              },
              modal: false,
              title: "description and mql query body",
              position: { my: "left top", at: "left top", of: window },
              width: mql_big_width_dia,
              height: window_height,
            })
          mqlq.css("height", half_standard_height)
          descm.removeClass("desc")
          descm.addClass("desc_dia")
          descm.css("height", half_standard_height)
        })

        $("#is_pub_c").click(e => {
          const elem = $(e.target)
          const val = elem.prop("checked")
          this.sendval(
            q.versions[vr],
            elem,
            val,
            vr,
            elem.attr("qid"),
            "is_published",
            val ? "T" : ""
          )
        })

        $("#is_shared_c").click(e => {
          const elem = $(e.target)
          const val = elem.prop("checked")
          this.sendval(
            q,
            elem,
            val,
            vr,
            elem.attr("qid"),
            "is_shared",
            val ? "T" : ""
          )
        })

        nameq.hide()
        descq.hide()
        descm.show()
        editq.show()
        if (is_pub) {
          execq.hide()
        } else {
          execq.show()
        }
        saveq.hide()
        cancq.hide()
        doneq.hide()
        pube.show()
        pubr.hide()

        editq.click(e => {
          e.preventDefault()
          const is_pub = q.versions[vr].is_published
          this.saved_name = nameq.val()
          this.saved_desc = descq.val()
          this.saved_mql = mqlq.val()
          set_edit_width()
          if (!is_pub) {
            nameq.show()
          }
          descq.show()
          descm.hide()
          editq.hide()
          saveq.show()
          cancq.show()
          doneq.show()
          pubr.show()
          pube.hide()
          mqlq.prop("readonly", is_pub)
          mqlq.css("height", "20em")
        })

        cancq.click(e => {
          e.preventDefault()
          nameq.val(this.saved_name)
          descq.val(this.saved_desc)
          mqlq.val(this.saved_mql)
          reset_main_width()
          nameq.hide()
          descq.hide()
          descm.show()
          editq.show()
          saveq.hide()
          cancq.hide()
          doneq.hide()
          pube.show()
          pubr.hide()
          mqlq.prop("readonly", true)
          mqlq.css("height", "10em")
        })

        doneq.click(e => {
          e.preventDefault()
          reset_main_width()
          nameq.hide()
          descq.hide()
          descm.show()
          editq.show()
          saveq.hide()
          cancq.hide()
          doneq.hide()
          pube.show()
          pubr.hide()
          mqlq.prop("readonly", true)
          mqlq.css("height", "10em")
          const data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          this.sendvals(data)
        })

        saveq.click(e => {
          e.preventDefault()
          const data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          this.sendvals(data)
        })
        execq.click(e => {
          e.preventDefault()
          execq.addClass("fa-spin")
          const msg = this.msgov
          msg.clear()
          msg.msg(["special", "executing query ..."])
          const data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: true,
          }
          this.sendvals(data)
        })
      }
    }
  }

  setstatus(vr, cls) {
    const statq = cls != null ? cls : $(`#statq${vr}`).attr("class")
    const statm =
      statq == "good"
        ? "results up to date"
        : statq == "error"
        ? "results outdated"
        : "never executed"
    $("#statm").html(statm)
  }

  sendval(q, checkbx, newval, vr, iid, fname, val) {
    const senddata = {}
    senddata.version = vr
    senddata.qid = iid
    senddata.fname = fname
    senddata.val = val

    $.post(
      field_url,
      senddata,
      data => {
        const { good, mod_dates, mod_cls, extra, msgs } = data

        if (good) {
          for (const mod_date_fld in mod_dates) {
            $(`#${mod_date_fld}`).html(mod_dates[mod_date_fld])
          }
          for (const mod_cl in mod_cls) {
            const cl = mod_cls[mod_cl]
            const dest = $(mod_cl)
            dest.removeClass("fa-check fa-close published")
            dest.addClass(cl)
          }
          q[fname] = newval
        } else {
          checkbx.prop("checked", !newval)
        }

        for (const fld in extra) {
          const instr = extra[fld]
          const prop = instr[0]
          const val = instr[1]

          if (prop == "check") {
            const dest = $(`#${fld}_c`)
            dest.prop("checked", val)
          } else if (prop == "show") {
            const dest = $(`#${fld}`)
            if (val) {
              dest.show()
            } else {
              dest.hide()
            }
          }
        }
        const msg = fname == "is_shared" ? this.msgo : this.msgov
        msg.clear()
        for (const m of msgs) {
          msg.msg(m)
        }
      },
      "json"
    )
  }

  sendvals(senddata) {
    const { execute, version: vr } = senddata

    $.post(
      fields_url,
      senddata,
      data => {
        const { good, q, msgs } = data

        const msg = this.msgov
        msg.clear()

        for (const m of msgs) {
          msg.msg(m)
        }

        if (good) {
          const { oldeversions } = data
          const qx = q.versions[vr]
          $("#nameqm").html(escapeHTML(q.name || ""))
          $("#nameq").val(q.name)
          const d_md = special_links(q.description_md)
          const descm = $("#descm")
          descm.html(d_md)
          decorate_crossrefs(descm)
          $("#descq").val(q.description)
          $("#mqlq").val(qx.mql)
          const ev = $("#eversion")
          const evtd = ev.closest("td")
          ev.html(qx.eversion)
          if (qx.eversion in oldeversions) {
            evtd.addClass("oldexeversion")
            evtd.attr("title", "this is not the newest version")
          } else {
            evtd.removeClass("oldexeversion")
            evtd.attr("title", "this is the newest version")
          }
          $("#executed_on").html(qx.executed_on)
          $("#xmodified_on").html(qx.xmodified_on)
          $("#qresults").html(qx.results)
          $("#qresultmonads").html(qx.resultmonads)
          $("#statq").removeClass("error warning good").addClass(qx.status)
          this.setstatus("", qx.status)
          wb.sidebars.sidebar["rq"].content.info = q
        }
        if (execute) {
          reset_material_status()
          wb.material.adapt()
          const show_chart = close_dialog(
            $(`#select_contents_chart_${vr}_q_${q.id}`)
          )
          if (show_chart) {
            wb.sidebars.sidebar["rq"].cselect[vr].apply()
          }
          $("#execq").removeClass("fa-spin")
        }
      },
      "json"
    )
  }

  apply() {
    if (wb.mr == this.mr && (this.mr == "r" || wb.vs.get(this.qw) == "v")) {
      this.fetch()
    }
  }

  fetch() {
    const { version, iid } = wb
    const { mr, qw } = this
    const thelist = $("#side_material_" + mr + qw)

    let vars = `?version=${version}&mr={mr}&qw=${qw}`

    let do_fetch = false
    let extra = ""

    if (mr == "m") {
      vars += `&book=${wb.vs.book()}&chapter=${wb.vs.chapter()}`
      if (qw == "q" || qw == "n") {
        vars += `&${qw}pub=${wb.vs.pub(qw)}`
      }
      do_fetch = wb.vs.book() != "x" && wb.vs.chapter() > 0
      extra = "m"
    } else {
      vars += `&iid=${iid}`
      do_fetch = wb.qw == "q" ? iid >= 0 : iid != "-1"
      extra = `${qw}m`
    }
    if (do_fetch && !side_fetched[`${mr}${qw}`]) {
      const tag = `tag${mr == "m" ? "s" : ""}`
      this.msg(`fetching ${style[qw][tag]} ...`)
      if (mr == "m") {
        thelist.load(
          `${side_url}${extra}${vars}`,
          () => {
            side_fetched[`${mr}${qw}`] = true
            this.process()
          },
          "html"
        )
      } else {
        $.get(
          `${side_url}${extra}${vars}`,
          html => {
            thelist.html(html)
            side_fetched[`${mr}${qw}`] = true
            this.process()
          },
          "html"
        )
      }
    }
  }

  sidelistitems() {
    /* the list of items in an m-sidebar
    */
    const { mr, qw } = this

    if (mr == "m") {
      if (qw != "n") {
        wb.picker1list[qw] = {}
      }
      const qwlist = $(`#side_list_${qw} li`)
      qwlist.each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        this.sidelistitem(iid)
        if (qw != "n") {
          wb.picker1list[qw][iid] = new Colorpicker1(qw, iid, false, false)
        }
      })
    }
  }

  sidelistitem(iid) {
    /* individual item in an m-sidebar
     */
    const { qw } = this

    const itop = $(`#${qw}${iid}`)
    const more = $(`#m_${qw}${iid}`)
    const desc = $(`#d_${qw}${iid}`)
    const item = $(`#item_${qw}${iid}`)
    const all = $(`#${qw}${iid}`)

    desc.hide()

    more.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      toggle_detail(elem, desc, qw == "q" ? put_markdown : undefined)
    })

    item.click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const { qw } = this
      wb.vs.mstatesv({ mr: this.other_mr, qw, iid: elem.attr("iid"), page: 1 })
      wb.vs.addHist()
      wb.go()
    })

    if (qw == "w") {
      if (!wb.vs.iscolor(qw, iid)) {
        all.hide()
      }
    } else if (qw == "q") {
      if (muting_q.isSet(`q${iid}`)) {
        itop.hide()
      } else {
        itop.show()
      }
    } else if (qw == "n") {
      if (muting_n.isSet(`n${iid}`)) {
        itop.hide()
      } else {
        itop.show()
      }
    }
  }
}

// SIDELIST VIEW SETTINGS

function ListSettings(qw) {
  // the view controls belonging to a side bar with a list of items
  var that = this
  this.qw = qw
  var hlradio = $("." + qw + "hradio")

  this.apply = function () {
    if (wb.vs.get(this.qw) == "v") {
      if (this.qw != "n") {
        for (var iid in wb.picker1list[this.qw]) {
          wb.picker1list[this.qw][iid].apply(false)
        }
        wb.picker2[this.qw].apply(true)
      }
    }
    if (this.qw == "q" || this.qw == "n") {
      var pradio = $("." + this.qw + "pradio")
      if (wb.vs.pub(qw) == "v") {
        pradio.addClass("ison")
      } else {
        pradio.removeClass("ison")
      }
    }
  }
  if (this.qw != "n") {
    this.picker2 = new Colorpicker2(this.qw, false)
    hlradio.click(function (e) {
      e.preventDefault()
      wb.vs.hstatesv(that.qw, { active: $(this).attr("id").substring(1) })
      wb.vs.addHist()
      wb.highlight2({ code: "3", qw: that.qw })
    })
  }
  if (qw == "q" || qw == "n") {
    var pradio = $("." + this.qw + "pradio")
    pradio.click(function (e) {
      e.preventDefault()
      wb.vs.hstatesv(that.qw, { pub: wb.vs.pub(that.qw) == "x" ? "v" : "x" })
      side_fetched["m" + that.qw] = false
      wb.sidebars.sidebar["m" + that.qw].content.apply()
    })
  }
}

function set_csv(vr, mr, qw, iid, extra) {
  if (mr == "r") {
    var tasks = { t: "txt_p", d: "txt_il" }
    if (qw != "n") {
      tasks["b"] = wb.vs.tp()
    }

    for (var task in tasks) {
      var tp = tasks[task]
      var csvctrl = $("#csv" + task + "_lnk_" + vr + "_" + qw)
      if (task != "b" || (tp != "txt_p" && tp != "txt_il")) {
        var ctit = csvctrl.attr("ftitle")
        if (extra == undefined) {
          extra = csvctrl.attr("extra")
        } else {
          csvctrl.attr("extra", extra)
        }
        csvctrl.attr("href", wb.vs.csv_url(vr, mr, qw, iid, tp, extra))
        csvctrl.attr(
          "title",
          vr +
            "_" +
            style[qw]["t"] +
            "_" +
            iid +
            "_" +
            extra +
            "_" +
            tp_labels[tp] +
            ".csv" +
            ctit
        )
        csvctrl.show()
      } else {
        csvctrl.hide()
      }
    }
  }
}

function Colorpicker1(qw, iid, is_item, do_highlight) {
  // the colorpicker associated with individual items
  /*
    These pickers show up
        in lists of items (in mq and mw sidebars) and
        near individual items (in rq and rw sidebars)

    They also have a checkbox, stating whether the color counts as customized.
    Customized colors are held in a global colormap, which is saved in a cookie upon every picking action.

    All actions are processed by the highlight2 (!) method of the associated Settings object.
*/
  var that = this
  this.code = is_item ? "1a" : "1"
  this.qw = qw
  this.iid = iid
  var is_item = is_item
  var pointer = is_item ? "me" : iid
  var stl = style[this.qw]["prop"]
  var sel = $("#sel_" + this.qw + pointer)
  var selw = $("#sel_" + this.qw + pointer + ">a")
  var selc = $("#selc_" + this.qw + pointer)
  var picker = $("#picker_" + this.qw + pointer)

  this.adapt = function (iid, do_highlight) {
    this.iid = iid
    this.apply(do_highlight)
  }
  this.apply = function (do_highlight) {
    var color = wb.vs.color(this.qw, this.iid) || defcolor(this.qw == "q", this.iid)
    var target = this.qw == "q" ? sel : selw
    if (color) {
      target.css(stl, vcolors[color][this.qw]) // apply state to the selected cell
    }
    selc.prop("checked", wb.vs.iscolor(this.qw, this.iid)) // apply state to the checkbox
    if (do_highlight) {
      wb.highlight2(this)
    }
  }

  sel.click(function (e) {
    e.preventDefault()
    picker.dialog({
      dialogClass: "picker_dialog",
      closeOnEscape: true,
      modal: true,
      title: "choose a color",
      position: { my: "right top", at: "left top", of: selc },
      width: "200px",
    })
  })
  selc.click(function (e) {
    // process a click on the selectbox of the picker
    var was_cust = wb.vs.iscolor(that.qw, that.iid)
    close_dialog(picker)
    if (was_cust) {
      wb.vs.cstatex(that.qw, that.iid)
    } else {
      var vals = {}
      vals[that.iid] = defcolor(that.qw == "q", that.iid)
      wb.vs.cstatesv(that.qw, vals)
      var active = wb.vs.active(that.qw)
      if (active != "hlcustom" && active != "hlmany") {
        wb.vs.hstatesv(that.qw, { active: "hlcustom" })
      }
    }
    wb.vs.addHist()
    that.apply(true)
  })
  $(".c" + this.qw + "." + this.qw + pointer + ">a").click(function (e) {
    e.preventDefault()
    // process a click on a colored cell of the picker
    close_dialog(picker)
    var vals = {}
    vals[that.iid] = $(this).html()
    wb.vs.cstatesv(that.qw, vals)
    wb.vs.hstatesv(that.qw, { active: "hlcustom" })
    wb.vs.addHist()
    that.apply(true)
  })
  picker.hide()
  $(".c" + this.qw + "." + this.qw + pointer + ">a").each((i, el) => {
    //initialize the individual color cells in the picker
    const elem = $(el)
    var target = that.qw == "q" ? elem.closest("td") : elem
    target.css(stl, vcolors[elem.html()][that.qw])
  })
  this.apply(do_highlight)
}

function Colorpicker2(qw, do_highlight) {
  // the colorpicker associated with the view settings in a sidebar
  /*
    These pickers show up at the top of the individual sidebars, only on mq and mw sidebars.
    They are used to control the uniform color with which the results are to be painted.
    They can be configured for dealing with background or foreground painting.
    The paint actions depend on the mode of coloring that the user has selected in settings.
    So the paint logic is more involved.
    But there is no associated checkbox.
    The selected color is stored in the highlight settings, which are synchronized in a cookie. 

    All actions are processed by the highlight2 method of the associated Settings object.
*/
  var that = this
  this.code = "2"
  this.qw = qw
  var stl = style[this.qw]["prop"]
  var sel = $("#sel_" + this.qw + "one")
  var selw = $("#sel_" + this.qw + "one>a")
  var picker = $("#picker_" + this.qw + "one")

  this.apply = function (do_highlight) {
    var color = wb.vs.sel_one(this.qw) || defcolor(this.qw, null)
    var target = this.qw == "q" ? sel : selw
    target.css(stl, vcolors[color][this.qw]) // apply state to the selected cell
    if (do_highlight) {
      wb.highlight2(this)
    }
  }
  sel.click(function (e) {
    e.preventDefault()
    picker.dialog({
      dialogClass: "picker_dialog",
      closeOnEscape: true,
      modal: true,
      title: "choose a color",
      position: { my: "right top", at: "left top", of: sel },
      width: "200px",
    })
  })
  $(".c" + this.qw + "." + this.qw + "one>a").click(function (e) {
    e.preventDefault()
    // process a click on a colored cell of the picker
    close_dialog(picker)
    var current_active = wb.vs.active(that.qw)
    if (current_active != "hlone" && current_active != "hlcustom") {
      wb.vs.hstatesv(that.qw, { active: "hlcustom", sel_one: $(this).html() })
    } else {
      wb.vs.hstatesv(that.qw, { sel_one: $(this).html() })
    }
    wb.vs.addHist()
    that.apply(true)
  })
  picker.hide()
  $(".c" + this.qw + "." + this.qw + "one>a").each((i, el) => {
    //initialize the individual color cells in the picker
    const elem = $(el)
    var target = that.qw == "q" ? elem.closest("td") : elem
    target.css(stl, vcolors[elem.html()][that.qw])
  })
  this.apply(do_highlight)
}

function defcolor(qw, iid) {
  // compute the default color
  /*
    The data for the computation comes from the server and is stored in the javascript global variables
        vdefaultcolors
        dncols, dnrows
*/
  var result
  if (qw in style) {
    result = style[qw]["default"]
  } else if (qw) {
    var mod = iid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  } else {
    var iidstr = iid == null ? "" : iid
    var sumiid = 0
    for (var i = 0; i < iidstr.length; i++) {
      sumiid += iidstr.charCodeAt(i)
    }
    var mod = sumiid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  }
  return result
}

// VIEW STATE

function ViewState(init, pref) {
  var that = this
  this.data = init
  this.pref = pref
  this.from_push = false

  this.getvars = function () {
    var vars = ""
    var sep = "?"
    for (var group in this.data) {
      var extra = group == "colormap" ? "c_" : ""
      for (var qw in this.data[group]) {
        for (var name in this.data[group][qw]) {
          vars += sep + extra + qw + name + "=" + this.data[group][qw][name]
          sep = "&"
        }
      }
    }
    return vars
  }
  this.csv_url = function (vr, mr, qw, iid, tp, extra) {
    var vars =
      "?version=" +
      vr +
      "&mr=" +
      mr +
      "&qw=" +
      qw +
      "&iid=" +
      iid +
      "&tp=" +
      tp +
      "&extra=" +
      extra
    var data = wb.vs.ddata()
    for (var name in data) {
      vars += "&" + name + "=" + data[name]
    }
    return item_url + vars
  }
  this.goback = function () {
    var state = History.getState()
    if (!that.from_push && state && state.data) {
      that.apply(state)
    }
  }
  this.addHist = function () {
    var title
    if (that.mr() == "m") {
      title =
        "[" +
        that.version() +
        "] " +
        that.book() +
        " " +
        that.chapter() +
        " " +
        that.verse()
    } else {
      title = style[that.qw()]["Tag"] + " " + that.iid() + " p" + that.page()
    }
    that.from_push = true
    History.pushState(that.data, title, view_url)
    that.from_push = false
  }
  this.apply = function (state, load_it) {
    if (state.data != undefined) {
      that.data = state.data
    }
    wb.go()
  }
  this.delsv = function (group, qw, name) {
    delete this.data[group][qw][name]
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  this.setsv = function (group, qw, values) {
    for (var mb in values) {
      this.data[group][qw][mb] = values[mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  this.resetsv = function (group, qw) {
    for (var mb in this.data[group][qw]) {
      delete this.data[group][qw][mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }
  this.mstatesv = function (values) {
    this.setsv("material", "", values)
  }
  this.dstatesv = function (values) {
    this.setsv("hebrewdata", "", values)
  }
  this.hstatesv = function (qw, values) {
    this.setsv("highlights", qw, values)
  }
  this.cstatesv = function (qw, values) {
    this.setsv("colormap", qw, values)
  }
  this.cstatex = function (qw, name) {
    this.delsv("colormap", qw, name)
  }
  this.cstatexx = function (qw) {
    this.resetsv("colormap", qw)
  }

  this.mstate = function () {
    return this.data["material"][""]
  }
  this.ddata = function () {
    return this.data["hebrewdata"][""]
  }
  this.mr = function () {
    return this.data["material"][""]["mr"]
  }
  this.qw = function () {
    return this.data["material"][""]["qw"]
  }
  this.tp = function () {
    return this.data["material"][""]["tp"]
  }
  this.tr = function () {
    return this.data["material"][""]["tr"]
  }
  this.lang = function () {
    return this.data["material"][""]["lang"]
  }
  this.iid = function () {
    return this.data["material"][""]["iid"]
  }
  this.version = function () {
    return this.data["material"][""]["version"]
  }
  this.book = function () {
    return this.data["material"][""]["book"]
  }
  this.chapter = function () {
    return this.data["material"][""]["chapter"]
  }
  this.verse = function () {
    return this.data["material"][""]["verse"]
  }
  this.page = function () {
    return this.data["material"][""]["page"]
  }
  this.get = function (qw) {
    return this.data["highlights"][qw]["get"]
  }
  this.active = function (qw) {
    return this.data["highlights"][qw]["active"]
  }
  this.sel_one = function (qw) {
    return this.data["highlights"][qw]["sel_one"]
  }
  this.pub = function (qw) {
    return this.data["highlights"][qw]["pub"]
  }
  this.colormap = function (qw) {
    return this.data["colormap"][qw]
  }
  this.color = function (qw, id) {
    return this.data["colormap"][qw][id]
  }
  this.iscolor = function (qw, cl) {
    return cl in this.data["colormap"][qw]
  }

  this.addHist()
}

function close_dialog(dia) {
  var was_open = Boolean(
    dia && dia.length && dia.dialog("instance") && dia.dialog("isOpen")
  )
  if (was_open) {
    dia.dialog("close")
  }
  return was_open
}

function reset_material_status() {
  material_fetched = { txt_p: false }
  material_kind = { txt_p: "" }
  for (var i = 1; i <= tab_views; i++) {
    material_fetched["txt_tb" + i] = false
    material_kind["txt_tb" + i] = ""
  }
}

/* GENERIC */

var escapeHTML = (function () {
  "use strict"
  var chr = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }
  return function (text) {
    return text.replace(/[&<>]/g, function (a) {
      return chr[a]
    })
  }
})()

function toggle_detail(wdg, detail, extra) {
  var thedetail = detail == undefined ? wdg.closest("div").find(".detail") : detail
  thedetail.toggle()
  if (extra != undefined) {
    extra(wdg)
  }
  var thiscl, othercl
  if (wdg.hasClass("fa-chevron-right")) {
    thiscl = "fa-chevron-right"
    othercl = "fa-chevron-down"
  } else {
    thiscl = "fa-chevron-down"
    othercl = "fa-chevron-right"
  }
  wdg.removeClass(thiscl)
  wdg.addClass(othercl)
}

/* MARKDOWN and CROSSREFS */

function decorate_crossrefs(dest) {
  var crossrefs = dest.find("a[b]")
  crossrefs.click(function (e) {
    e.preventDefault()
    var vals = {}
    vals["book"] = $(this).attr("b")
    vals["chapter"] = $(this).attr("c")
    vals["verse"] = $(this).attr("v")
    vals["mr"] = "m"
    wb.vs.mstatesv(vals)
    wb.vs.addHist()
    wb.go()
  })
  crossrefs.addClass("crossref")
}

function special_links(d_md) {
  d_md = d_md.replace(
    /<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)(<\/a>)/g,
    '<br/><img src="$1"/><br/>$2<br/>'
  )
  d_md = d_md.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="$4" href="#" class="fa fw" $5>&#xf100;$6&#xf101;$7'
  )
  d_md = d_md.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="1" href="#" class="fa fw" $4>&#xf100;$5&#xf101;$6'
  )
  d_md = d_md.replace(
    /(href=['"])shebanq:([^)\n\t '"]+)(['"])/g,
    "$1" + host + '$2$3 class="fa fw fa-bookmark" '
  )
  d_md = d_md.replace(
    /(href=['"])feature:([^)\n\t '"]+)(['"])/g,
    "$1" + featurehost + '/$2$3 target="_blank" class="fa fw fa-file-text" '
  )
  return special_links_m(d_md)
}

function special_links_m(ntxt) {
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(image[\n\t ]+([^)\n\t '"]+)\)/g,
    '<br/><img src="$2"/><br/>$1<br/>'
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="$4" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="1" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(shebanq:([^)\n\t '"]+)\)/g,
    '<a href="' + host + '$2" class="fa fw">&#xf02e;$1</a>'
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(feature:([^)\n\t '"]+)\)/g,
    '<a target="_blank" href="' + featurehost + '/$2" class="fa fw">$1&#xf15c;</a>'
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)\)/g,
    '<a target="_blank" href="$2" class="fa fw">$1&#xf08e;</a>'
  )
  return ntxt
}

function mEscape(ns) {
  return ns.replace(/_/g, "\\_")
}

function markdownEscape(ntxt) {
  return ntxt.replace(/\[[^\]\n\t]+\]\([^\)]*\)/g, mEscape)
}

function put_markdown(wdg) {
  var did = wdg.attr("did")
  var src = $("#dv_" + did)
  var mdw = $("#dm_" + did)
  mdw.html(special_links(markdown.toHTML(src.val())))
}

function Msg(destination, on_clear) {
  var that = this
  this.destination = $("#" + destination)
  this.trashc = $("#trash_" + destination)
  this.clear = function () {
    this.destination.html("")
    if (on_clear != undefined) {
      on_clear()
    }
    this.trashc.hide()
  }
  this.hide = function () {
    this.destination.hide()
    this.trashc.hide()
  }
  this.show = function () {
    this.destination.show()
    if (this.destination.html() != "") {
      this.trashc.show()
    }
  }
  this.trashc.click(function (e) {
    e.preventDefault()
    that.clear()
  })
  this.msg = function (msgobj) {
    var mtext = this.destination.html()
    this.destination.html(mtext + '<p class="' + msgobj[0] + '">' + msgobj[1] + "</p>")
    this.trashc.show()
  }
  this.trashc.hide()
}
