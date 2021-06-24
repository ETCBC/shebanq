/* eslint-env jquery */
/* eslint-disable camelcase */

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

/* the one and only page object
 */
/* globals P */

/* config settings dumped by the server
 */
/* globals Config */

/* result data
 */
/* globals State */

/* the markdown object
 */
/* globals markdown */

let side_fetched, material_fetched, material_kind
/* transitory flags indicating whether kinds of material and sidebars
 * have loaded content
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

/* TOP LEVEL: DYNAMICS, PAGE, WINDOW, SKELETON
 */

/* exported setup, dynamics */

function setup() {
  /* top level function, called when the page has loaded
   * P is the handle to manipulate the whole page
   */
  const { viewinit, pref } = Config
  const P = new Page(new ViewState(viewinit, pref))
  return P
}

function dynamics(P) {
  /* top level function, called when the page has loaded
   * P is the handle to manipulate the whole page
   */
  P.init()
  P.go()
}

const set_height = () => {
  /* the heights of the sidebars are set, depending on the height of the window
   */
  const { tab_views } = Config
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
  /* the heights of the sidebars are set, depending on the height of the window
   */
  standard_heightw = window.innerHeight - subtractw
  $("#words").css("height", standard_heightw + "px")
  $("#letters").css("height", standard_heightw + "px")
}

const get_width = () => {
  /* save the orginal widths of sidebar and main area
   */
  orig_side_width = $(".span3").css("width")
  orig_main_width = $(".span9").css("width")
}

const reset_main_width = () => {
  /* restore the orginal widths of sidebar and main area
   */
  if (orig_side_width != $(".span3").css("width")) {
    $(".span3").css("width", orig_side_width)
    $(".span3").css("max-width", orig_side_width)
    $(".span9").css("width", orig_main_width)
    $(".span9").css("max-width", orig_main_width)
  }
}

const set_edit_width = () => {
  /* switch to increased sidebar width
   */
  get_width()
  $(".span3").css("width", edit_side_width)
  $(".span9").css("width", edit_main_width)
}

class Page {
  /* the one and only page object
   */
  constructor(vs) {
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

  init() {
    /* dress up the skeleton, initialize state variables
     */
    const { vs, picker2 } = this

    this.material = new Material()
    this.sidebars = new Sidebars()
    set_height()
    get_width()
    const listsettings = {}
    this.listsettings = listsettings

    for (const qw of ["q", "w", "n"]) {
      listsettings[qw] = new ListSettings(qw)
      if (qw != "n") {
        picker2[qw] = listsettings[qw].picker2
      }
    }
    const prev = {}
    this.prev = prev
    for (const x in vs.mstate()) {
      prev[x] = null
    }
    reset_material_status()
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
    reset_main_width()
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
    const hlradio = $("." + qw + "hradio")
    const activeo = $("#" + qw + active)
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
      $("#side_list_" + qw + " li").each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (!muting_q.isSet(iid + "")) {
          const monads = $.parseJSON($("#" + qw + iid).attr("monads"))
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
      $("#side_list_" + qw + " li").each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        if (P.vs.iscolor(qw, iid)) {
          custitems[iid] = 1
        } else {
          plainitems[iid] = 1
        }
        const all = $("#" + qw + iid)
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
    const container = "#material_" + P.vs.tp()
    const att = qw == "q" ? "m" : "l"
    for (const item in paintings) {
      const color = paintings[item]
      $(container + " span[" + att + '="' + item + '"]').css(stl, vcolors[color][qw])
    }
  }
}

/* MATERIAL
 */

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
      reset_material_status()
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
    $("#thepage").html(page > 0 ? "" + page : "")
    for (const x in P.vs.mstate()) {
      P.prev[x] = P.vs.mstate()[x]
    }
  }

  fetch() {
    /* get the material by AJAX if needed, and process the material afterward
     */
    const { material_url } = Config

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
    const newcontent = $("#material_" + tp)
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

/* MATERIAL: Notes
 */

class Notes {
  constructor(newcontent) {
    this.show = false
    this.verselist = {}
    this.version = P.version
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
      P.vs.hstatesv("n", { get: P.vs.get("n") == "v" ? "x" : "v" })
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

    if (P.vs.get("n") == "v") {
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

    const { book, chapter, verse } = this
    this.msgn = new Msg(`nt_msg_${book}_${chapter}_${verse}`)
    this.cctrl = ctrl.find("a.nt_ctrl")
    this.sav_controls = ctrl.find("span.nt_sav")

    const { sav_controls } = this
    this.sav_c = sav_controls.find('a[tp="s"]')
    this.edt_c = sav_controls.find('a[tp="e"]')
    this.rev_c = sav_controls.find('a[tp="r"]')

    const { sav_c, edt_c, rev_c, cctrl } = this

    sav_c.click(e => {
      e.preventDefault()
      this.save()
    })
    edt_c.click(e => {
      e.preventDefault()
      this.edit()
    })
    rev_c.click(e => {
      e.preventDefault()
      this.revert()
    })
    cctrl.click(e => {
      e.preventDefault()
      this.is_dirty()
      if (this.show) {
        this.hide_notes()
      } else {
        this.show_notes(true)
      }
    })

    dest.find("tr.nt_cmt").hide()
    $("span.nt_main_sav").hide()
    sav_controls.hide()
  }

  fetch(adjust_verse) {
    const { cnotes_url } = Config

    const { version, book, chapter, verse, edt, msgn } = this
    const senddata = { version, book, chapter, verse, edit: edt }
    msgn.msg(["info", "fetching notes ..."])
    $.post(cnotes_url, senddata, data => {
      this.loaded = true
      msgn.clear()
      for (const m of data.msgs) {
        msgn.msg(m)
      }
      const { good, users, notes, nkey_index, changed, logged_in } = data
      if (good) {
        this.process(users, notes, nkey_index, changed, logged_in)
        if (adjust_verse) {
          if (P.mr == "m") {
            P.vs.mstatesv({ verse })
            P.material.goto_verse()
          }
        }
      }
    })
  }

  process(users, notes, nkey_index, changed, logged_in) {
    if (changed) {
      if (P.mr == "m") {
        side_fetched["mn"] = false
        P.sidebars.sidebar["mn"].content.apply()
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
    const { nt_statclass, nt_statsym, nt_statnext } = Config
    const { dest, logged_in, sav_controls, edt, sav_c, edt_c } = this
    dest
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
    dest
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
    dest.find("tr.nt_cmt").show()
    if (logged_in) {
      $("span.nt_main_sav").show()
      sav_controls.show()
      if (edt) {
        sav_c.show()
        edt_c.hide()
      } else {
        sav_c.hide()
        edt_c.show()
      }
    }
    decorate_crossrefs(dest)
  }

  gen_html_ca(canr) {
    const { nt_statclass, nt_statsym } = Config
    const vr = this.version
    const notes = this.orig_notes[canr]
    const nkey_index = this.orig_nkey_index
    let html = ""
    this.nnotes += notes.length
    for (let n = 0; n < notes.length; n++) {
      const nline = notes[n]
      const { uid, nid, pub, shared, ro } = nline
      const kwtrim = $.trim(nline.kw)
      const kws = kwtrim.split(/\s+/)
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
      const pubc = pub ? "ison" : ""
      const sharedc = shared ? "ison" : ""
      const statc = nt_statclass[nline.stat]
      const statsym = nt_statsym[nline.stat]
      const edit_att = ro ? "" : ' edit="1"'
      const edit_class = ro ? "" : " edit"
      html += `<tr class="nt_cmt nt_info ${statc}${edit_class}" nid="${nid}"
          ncanr="${canr}"${edit_att}">`
      if (ro) {
        html += `<td class="nt_stat">
            <span class="fa fa-${statsym} fa-fw" code="${nline.stat}"></span>
          </td>`
        html += `<td class="nt_kw">${escHT(nline.kw)}</td>`
        const ntxt = special_links(markdown.toHTML(markdownEscape(nline.ntxt)))
        html += `<td class="nt_cmt">${ntxt}</td>`
        html += `<td class="nt_user" colspan="3" uid="${uid}">${escHT(user)}</td>`
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
        html += `<td class="nt_user" colspan="3" uid="{uid}">${escHT(user)}</td>`
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
    const { cnotes_url } = Config

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
          this.process(users, notes, nkey_index, changed, logged_in)
        }
      },
      "json"
    )
  }

  is_dirty() {
    let dirty = false
    const { orig_edit } = this
    if (orig_edit == undefined) {
      this.dirty = false
      return
    }
    for (let n = 0; n < orig_edit.length; n++) {
      const { canr, note: o_note } = orig_edit[n]
      const { nid } = o_note
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
    const { version, book, chapter, verse, edt, orig_edit } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    const notelines = []
    if (orig_edit == undefined) {
      return
    }
    for (let n = 0; n < orig_edit.length; n++) {
      const { canr, note: o_note } = orig_edit[n]
      const { nid, uid } = o_note
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
      if (P.mr == "m") {
        P.vs.mstatesv({ verse: this.verse })
        P.material.goto_verse()
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
    const { versions } = Config
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
    const { featurehost, bol_url, pbl_url } = Config

    const thisFeaturehost = `${featurehost}/${docName}`
    $(".source").attr("href", thisFeaturehost)
    $(".source").attr("title", "BHSA feature documentation")
    $(".mvradio").removeClass("ison")
    $("#version_" + P.version).addClass("ison")
    const bol = $("#bol_lnk")
    const pbl = $("#pbl_lnk")

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
    const { versions } = Config

    if (versions[v]) {
      $(`#version_${v}`).click(e => {
        e.preventDefault()
        side_fetched["mw"] = false
        side_fetched["mq"] = false
        side_fetched["mn"] = false
        P.vs.mstatesv({ version: v })
        P.go()
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
      title: "choose " + this.key,
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

/* MATERIAL (messages when retrieving, storing the contents)
 *
 */

class MMessage {
  /* diagnostic output
   */
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
    $(`#material_${P.vs.tp()}`).html(response.children(this.name_content).html())
  }

  show() {
    const { next_tp } = Config

    const this_tp = P.vs.tp()
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
    const { featurehost } = Config

    const { next_tp, next_tr, tab_info, tab_views, tr_info, tr_labels } = Config

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
      const old_tp = P.vs.tp()
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
      P.vs.mstatesv({ tp: new_tp })
      P.vs.addHist()
      this.apply()
    })

    $(".mtradio").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const old_tr = P.vs.tr()
      let new_tr = elem.attr("id").substring(1)
      if (old_tr == new_tr) {
        new_tr = next_tr[old_tr]
      }

      P.vs.mstatesv({ tr: new_tr })
      P.vs.addHist()
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
    const { tab_views } = Config

    const hlradio = $(".mhradio")
    const plradio = $(".mtradio")
    const new_tp = P.vs.tp()
    const new_tr = P.vs.tr()
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
    P.material.adapt()
  }
}

/* HEBREW DATA (which fields to show if interlinear text is displayed)
 *
 */

class HebrewSettings {
  constructor() {
    for (const fld in P.vs.ddata()) {
      this[fld] = new HebrewSetting(fld)
    }
  }

  apply() {
    const { versions } = Config

    for (const fld in P.vs.ddata()) {
      this[fld].apply()
    }
    for (const v in versions) {
      set_csv(v, P.vs.mr(), P.vs.qw(), P.vs.iid())
    }
  }
}

class HebrewSetting {
  constructor(fld) {
    const { versions } = Config

    this.name = fld
    this.hid = `#${this.name}`
    $(this.hid).click(e => {
      const elem = $(e.target)
      const vals = {}
      vals[fld] = elem.prop("checked") ? "v" : "x"
      P.vs.dstatesv(vals)
      P.vs.addHist()
      this.applysetting()
      for (const v in versions) {
        set_csv(v, P.vs.mr(), P.vs.qw(), P.vs.iid())
      }
    })
  }

  apply() {
    const val = P.vs.ddata()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }

  applysetting() {
    if (P.vs.ddata()[this.name] == "v") {
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
  /* TOP LEVEL: all four kinds of sidebars
   */
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
    const { versions } = Config

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
      P.vs.hstatesv(this.qw, { get: "v" })
      P.vs.addHist()
      this.apply()
    })

    this.hide.click(e => {
      e.preventDefault()
      P.vs.hstatesv(this.qw, { get: "x" })
      P.vs.addHist()
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
    if (this.mr != P.mr || (this.mr == "r" && this.qw != P.qw)) {
      thebar.hide()
    } else {
      thebar.show()
      theset.show()
      if (this.mr == "m") {
        if (P.vs.get(this.qw) == "x") {
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
  /* the contents of an individual sidebar
   */
  constructor(mr, qw) {
    this.mr = mr
    this.qw = qw
    this.other_mr = this.mr == "m" ? "r" : "m"
    this.name = "side_material_" + mr + qw
    this.hid = "#" + this.name

    if (mr == "r") {
      if (qw != "n") {
        P.picker1[qw] = new Colorpicker1(qw, null, true, false)
      }
    }
  }

  msg(m) {
    $(this.hid).html(m)
  }

  set_vselect(v) {
    const { versions } = Config

    if (versions[v]) {
      $(`#version_s_${v}`).click(e => {
        e.preventDefault()
        P.vs.mstatesv({ version: v })
        P.go()
      })
    }
  }

  process() {
    const { versions, words_url, notes_url } = Config

    const { mr, qw } = this

    P.sidebars.after_item_fetch()
    this.sidelistitems()
    if (this.mr == "m") {
      P.listsettings[this.qw].apply()
    } else {
      for (const v in versions) {
        if (versions[v]) {
          P.sidebars.sidebar[`r${this.qw}`].cselect[v].init()
        }
      }

      const vr = P.version
      const iid = P.vs.iid()

      $(".moredetail").click(e => {
        e.preventDefault()
        const elem = $(e.target)
        toggle_detail(elem)
      })
      $(".detail").hide()
      $(`div[version="${vr}"]`).find(".detail").show()

      this.msgo = new Msg(`dbmsg_${qw}`)

      let ufname, ulname

      if (qw == "q") {
        const { q } = State
        this.info = q
        $("#theqid").html(q.id)
        ufname = escHT(q.ufname || "")
        ulname = escHT(q.ulname || "")
        const qname = escHT(q.name || "")
        $("#itemtag").val(`${ufname} ${ulname}: ${qname}`)
        this.msgov = new Msg("dbmsg_qv")
        $("#is_pub_c").show()
        $("#is_pub_ro").hide()
      } else if (qw == "w") {
        const { w } = State
        this.info = w
        if ("versions" in w) {
          const wvr = w.versions[vr]
          const wentryh = escHT(wvr.entry_heb)
          const wentryid = escHT(wvr.entryid)
          $("#itemtag").val(`${wentryh}: ${wentryid}`)
          $("#gobackw").attr(
            "href",
            `${words_url}?lan=${wvr.lan}&` +
              `letter=${wvr.entry_heb.charCodeAt(0)}&goto=${w.id}`
          )
        }
      } else if (qw == "n") {
        const { n } = State
        this.info = n
        if ("versions" in n) {
          ufname = escHT(n.ufname)
          ulname = escHT(n.ulname)
          const kw = escHT(n.kw)
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
      if (qw) {
        const { msgs } = State
        for (const m of msgs) {
          this.msgo.msg(m)
        }
      }
    }

    let thistitle
    if (this.mr == "m") {
      thistitle = `[${P.vs.version()}] ${P.vs.book()} ${P.vs.chapter()}:${P.vs.verse()}`
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
        const { q } = State
        const vr = P.version
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
        const is_pub =
          "versions" in q && vr in q.versions && q.versions[vr].is_published

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
          this.sendval(q, elem, val, vr, elem.attr("qid"), "is_shared", val ? "T" : "")
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
            version: P.version,
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
            version: P.version,
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
            version: P.version,
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
    const { field_url } = Config

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
    const { fields_url } = Config

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
          $("#nameqm").html(escHT(q.name || ""))
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
          P.sidebars.sidebar["rq"].content.info = q
        }
        if (execute) {
          reset_material_status()
          P.material.adapt()
          const show_chart = close_dialog($(`#select_contents_chart_${vr}_q_${q.id}`))
          if (show_chart) {
            P.sidebars.sidebar["rq"].cselect[vr].apply()
          }
          $("#execq").removeClass("fa-spin")
        }
      },
      "json"
    )
  }

  apply() {
    if (P.mr == this.mr && (this.mr == "r" || P.vs.get(this.qw) == "v")) {
      this.fetch()
    }
  }

  fetch() {
    const { style, side_url } = Config
    const { version, iid } = P

    const { mr, qw } = this
    const thelist = $("#side_material_" + mr + qw)

    let vars = `?version=${version}&mr={mr}&qw=${qw}`

    let do_fetch = false
    let extra = ""

    if (mr == "m") {
      vars += `&book=${P.vs.book()}&chapter=${P.vs.chapter()}`
      if (qw == "q" || qw == "n") {
        vars += `&${qw}pub=${P.vs.pub(qw)}`
      }
      do_fetch = P.vs.book() != "x" && P.vs.chapter() > 0
      extra = "m"
    } else {
      vars += `&iid=${iid}`
      do_fetch = P.qw == "q" ? iid >= 0 : iid != "-1"
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
        P.picker1list[qw] = {}
      }
      const qwlist = $(`#side_list_${qw} li`)
      qwlist.each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        this.sidelistitem(iid)
        if (qw != "n") {
          P.picker1list[qw][iid] = new Colorpicker1(qw, iid, false, false)
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
      P.vs.mstatesv({ mr: this.other_mr, qw, iid: elem.attr("iid"), page: 1 })
      P.vs.addHist()
      P.go()
    })

    if (qw == "w") {
      if (!P.vs.iscolor(qw, iid)) {
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

/* SIDELIST VIEW SETTINGS
 *
 */

class ListSettings {
  /* the view controls belonging to a side bar with a list of items
   */
  constructor(qw) {
    this.qw = qw

    if (qw != "n") {
      this.picker2 = new Colorpicker2(this.qw, false)
      const hlradio = $(`.${qw}hradio`)
      hlradio.click(e => {
        e.preventDefault()
        const elem = $(e.target)
        P.vs.hstatesv(this.qw, { active: elem.attr("id").substring(1) })
        P.vs.addHist()
        P.highlight2({ code: "3", qw: this.qw })
      })
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      pradio.click(e => {
        e.preventDefault()
        P.vs.hstatesv(this.qw, { pub: P.vs.pub(this.qw) == "x" ? "v" : "x" })
        side_fetched[`m${this.qw}`] = false
        P.sidebars.sidebar[`m${this.qw}`].content.apply()
      })
    }
  }

  apply() {
    const { qw } = this
    if (P.vs.get(qw) == "v") {
      if (qw != "n") {
        for (const iid in P.picker1list[qw]) {
          P.picker1list[qw][iid].apply(false)
        }
        P.picker2[qw].apply(true)
      }
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      if (P.vs.pub(qw) == "v") {
        pradio.addClass("ison")
      } else {
        pradio.removeClass("ison")
      }
    }
  }
}

const set_csv = (vr, mr, qw, iid, extraGiven) => {
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

class Colorpicker1 {
  /* the colorpicker associated with individual items
   *
   * These pickers show up in lists of items (in mq and mw sidebars) and
   * near individual items (in rq and rw sidebars).
   * They also have a checkbox, stating whether the color counts as customized.
   * Customized colors are held in a global colormap,
   * which is saved in a cookie upon every picking action.
   *
   * All actions are processed by the highlight2 (!) method
   * of the associated Settings object.
   */
  constructor(qw, iid, is_item, do_highlight) {
    const { style, vcolors } = Config

    const pointer = is_item ? "me" : iid
    this.code = is_item ? "1a" : "1"
    this.qw = qw
    this.iid = iid
    this.picker = $(`#picker_${qw}${pointer}`)
    this.stl = style[qw]["prop"]
    this.sel = $(`#sel_${qw}${pointer}`)
    this.selw = $(`#sel_${qw}${pointer}>a`)
    this.selc = $(`#selc_${qw}${pointer}`)

    this.sel.click(e => {
      e.preventDefault()
      this.picker.dialog({
        dialogClass: "picker_dialog",
        closeOnEscape: true,
        modal: true,
        title: "choose a color",
        position: { my: "right top", at: "left top", of: this.selc },
        width: "200px",
      })
    })

    this.selc.click(() => {
      /* process a click on the selectbox of the picker
       */
      const { qw, iid, picker } = this
      const was_cust = P.vs.iscolor(qw, iid)
      close_dialog(picker)
      if (was_cust) {
        P.vs.cstatex(qw, iid)
      } else {
        const vals = {}
        vals[iid] = defcolor(qw == "q", iid)
        P.vs.cstatesv(qw, vals)
        const active = P.vs.active(qw)
        if (active != "hlcustom" && active != "hlmany") {
          P.vs.hstatesv(qw, { active: "hlcustom" })
        }
      }
      P.vs.addHist()
      this.apply(true)
    })

    $(`.c${qw}.${qw}${pointer}>a`).click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.target)
      const { picker } = this
      close_dialog(picker)

      const { qw, iid } = this
      const vals = {}
      vals[iid] = elem.html()
      P.vs.cstatesv(qw, vals)
      P.vs.hstatesv(qw, { active: "hlcustom" })
      P.vs.addHist()
      this.apply(true)
    })

    this.picker.hide()
    $(`.c${qw}.${qw}${pointer}>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(this.stl, vcolors[elem.html()][qw])
    })
    this.apply(do_highlight)
  }

  adapt(iid, do_highlight) {
    this.iid = iid
    this.apply(do_highlight)
  }

  apply(do_highlight) {
    const { vcolors } = Config

    const { qw, iid, stl, sel, selc, selw } = this
    const color = P.vs.color(qw, iid) || defcolor(qw == "q", iid)
    const target = qw == "q" ? sel : selw
    if (color) {
      target.css(stl, vcolors[color][qw])
      /* apply state to the selected cell
       */
    }
    selc.prop("checked", P.vs.iscolor(qw, iid))
    /* apply state to the checkbox
     */
    if (do_highlight) {
      P.highlight2(this)
    }
  }
}

class Colorpicker2 {
  /* the colorpicker associated with the view settings in a sidebar
   *
   * These pickers show up at the top of the individual sidebars,
   * only on mq and mw sidebars.
   * They are used to control the uniform color with which
   * the results are to be painted.
   * They can be configured for dealing with background or foreground painting.
   * The paint actions depend on the mode of coloring
   * that the user has selected in settings.
   * So the paint logic is more involved.
   * But there is no associated checkbox.
   * The selected color is stored in the highlight settings,
   * which are synchronized in a cookie.
   * All actions are processed by the highlight2 method
   * of the associated Settings object.
   */
  constructor(qw, do_highlight) {
    const { style, vcolors } = Config

    this.code = "2"
    this.qw = qw
    this.picker = $(`#picker_${qw}one`)
    this.stl = style[this.qw]["prop"]
    this.sel = $(`#sel_${qw}one`)
    this.selw = $(`#sel_${qw}one>a`)

    this.sel.click(e => {
      e.preventDefault()
      this.picker.dialog({
        dialogClass: "picker_dialog",
        closeOnEscape: true,
        modal: true,
        title: "choose a color",
        position: { my: "right top", at: "left top", of: this.sel },
        width: "200px",
      })
    })

    $(`.c${qw}.${qw}one>a`).click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.target)
      const { picker } = this
      close_dialog(picker)
      const { qw } = this
      const current_active = P.vs.active(qw)
      if (current_active != "hlone" && current_active != "hlcustom") {
        P.vs.hstatesv(qw, { active: "hlcustom", sel_one: elem.html() })
      } else {
        P.vs.hstatesv(qw, { sel_one: elem.html() })
      }
      P.vs.addHist()
      this.apply(true)
    })

    this.picker.hide()

    $(`.c${qw}.${qw}one>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw, stl } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(stl, vcolors[elem.html()][qw])
    })
    this.apply(do_highlight)
  }

  apply(do_highlight) {
    const { vcolors } = Config

    const { qw, stl, sel, selw } = this
    const color = P.vs.sel_one(qw) || defcolor(qw, null)
    const target = qw == "q" ? sel : selw
    target.css(stl, vcolors[color][qw])
    /* apply state to the selected cell
     */
    if (do_highlight) {
      P.highlight2(this)
    }
  }
}

const defcolor = (qw, iid) => {
  /* compute the default color
   *
   * The data for the computation comes from the server
   * and is stored in the javascript global variable Config
   * vdefaultcolors, dncols, dnrows
   */
  const { style, vdefaultcolors, dncols, dnrows } = Config

  let result
  if (qw in style) {
    result = style[qw]["default"]
  } else if (qw) {
    const mod = iid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  } else {
    const iidstr = iid == null ? "" : iid
    let sumiid = 0
    for (let i = 0; i < iidstr.length; i++) {
      sumiid += iidstr.charCodeAt(i)
    }
    const mod = sumiid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  }
  return result
}

/* VIEW STATE
 *
 */

class ViewState {
  constructor(init, pref) {
    this.data = init
    this.pref = pref
    this.from_push = false

    this.addHist()
  }

  getvars() {
    const { data } = this
    let vars = ""
    let sep = "?"
    for (const group in data) {
      const extra = group == "colormap" ? "c_" : ""
      for (const qw in data[group]) {
        for (const name in data[group][qw]) {
          vars += `${sep}${extra}${qw}${name}=${data[group][qw][name]}`
          sep = "&"
        }
      }
    }
    return vars
  }

  csv_url(vr, mr, qw, iid, tp, extra) {
    const { item_url } = Config

    let vars = `?version=${vr}&mr=${mr}&qw=${qw}&iid=${iid}&tp=${tp}&extra=${extra}`
    const data = P.vs.ddata()
    for (const name in data) {
      vars += `&${name}=${data[name]}`
    }
    return `${item_url}${vars}`
  }

  goback() {
    const state = History.getState()
    if (!this.from_push && state && state.data) {
      this.apply(state)
    }
  }

  addHist() {
    const { style, view_url } = Config

    let title
    if (this.mr() == "m") {
      title = `[${this.version()}] ${this.book()} ${this.chapter()}:${this.verse()}`
    } else {
      title = `${style[this.qw()]["Tag"]} ${this.iid()} p${this.page()}`
    }
    this.from_push = true
    History.pushState(this.data, title, view_url)
    this.from_push = false
  }

  apply(state) {
    if (state.data != undefined) {
      this.data = state.data
    }
    P.go()
  }

  delsv(group, qw, name) {
    delete this.data[group][qw][name]
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  setsv(group, qw, values) {
    for (const mb in values) {
      this.data[group][qw][mb] = values[mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  resetsv(group, qw) {
    for (const mb in this.data[group][qw]) {
      delete this.data[group][qw][mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  mstatesv(values) {
    this.setsv("material", "", values)
  }
  dstatesv(values) {
    this.setsv("hebrewdata", "", values)
  }
  hstatesv(qw, values) {
    this.setsv("highlights", qw, values)
  }
  cstatesv(qw, values) {
    this.setsv("colormap", qw, values)
  }
  cstatex(qw, name) {
    this.delsv("colormap", qw, name)
  }
  cstatexx(qw) {
    this.resetsv("colormap", qw)
  }

  mstate() {
    return this.data["material"][""]
  }
  ddata() {
    return this.data["hebrewdata"][""]
  }
  mr() {
    return this.data["material"][""]["mr"]
  }
  qw() {
    return this.data["material"][""]["qw"]
  }
  tp() {
    return this.data["material"][""]["tp"]
  }
  tr() {
    return this.data["material"][""]["tr"]
  }
  lang() {
    return this.data["material"][""]["lang"]
  }
  iid() {
    return this.data["material"][""]["iid"]
  }
  version() {
    return this.data["material"][""]["version"]
  }
  book() {
    return this.data["material"][""]["book"]
  }
  chapter() {
    return this.data["material"][""]["chapter"]
  }
  verse() {
    return this.data["material"][""]["verse"]
  }
  page() {
    return this.data["material"][""]["page"]
  }
  get(qw) {
    return this.data["highlights"][qw]["get"]
  }
  active(qw) {
    return this.data["highlights"][qw]["active"]
  }
  sel_one(qw) {
    return this.data["highlights"][qw]["sel_one"]
  }
  pub(qw) {
    return this.data["highlights"][qw]["pub"]
  }
  colormap(qw) {
    return this.data["colormap"][qw]
  }
  color(qw, id) {
    return this.data["colormap"][qw][id]
  }
  iscolor(qw, cl) {
    return cl in this.data["colormap"][qw]
  }
}

const close_dialog = dia => {
  const was_open = Boolean(
    dia && dia.length && dia.dialog("instance") && dia.dialog("isOpen")
  )
  if (was_open) {
    dia.dialog("close")
  }
  return was_open
}

const reset_material_status = () => {
  const { tab_views } = Config

  material_fetched = { txt_p: false }
  material_kind = { txt_p: "" }
  for (let i = 1; i <= tab_views; i++) {
    material_fetched["txt_tb" + i] = false
    material_kind["txt_tb" + i] = ""
  }
}

/* GENERIC */

const escHT = text => {
  const chr = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }
  return text.replace(/[&<>]/g, a => chr[a])
}

function toggle_detail(wdg, detail, extra) {
  const thedetail = detail == undefined ? wdg.closest("div").find(".detail") : detail
  thedetail.toggle()
  if (extra != undefined) {
    extra(wdg)
  }
  let thiscl, othercl
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
  const crossrefs = dest.find("a[b]")
  crossrefs.click(e => {
    e.preventDefault()
    const elem = $(e.target)
    const vals = {}
    vals["book"] = elem.attr("b")
    vals["chapter"] = elem.attr("c")
    vals["verse"] = elem.attr("v")
    vals["mr"] = "m"
    P.vs.mstatesv(vals)
    P.vs.addHist()
    P.go()
  })
  crossrefs.addClass("crossref")
}

function special_links(d_mdGiven) {
  const { featurehost, host } = Config

  let d_md = d_mdGiven
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
    `$1${host}$2$3 class="fa fw fa-bookmark" `
  )
  d_md = d_md.replace(
    /(href=['"])feature:([^)\n\t '"]+)(['"])/g,
    `$1${featurehost}/$2$3 target="_blank" class="fa fw fa-file-text" `
  )
  return special_links_m(d_md)
}

function special_links_m(ntxtGiven) {
  const { featurehost, host } = Config

  let ntxt = ntxtGiven
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
    `<a href="${host}$2" class="fa fw">&#xf02e;$1</a>`
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(feature:([^)\n\t '"]+)\)/g,
    `<a target="_blank" href="${featurehost}/$2" class="fa fw">$1&#xf15c;</a>`
  )
  ntxt = ntxt.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)\)/g,
    '<a target="_blank" href="$2" class="fa fw">$1&#xf08e;</a>'
  )
  return ntxt
}

const mEscape = ns => ns.replace(/_/g, "\\_")

const markdownEscape = ntxt => ntxt.replace(/\[[^\]\n\t]+\]\([^)]*\)/g, mEscape)

const put_markdown = wdg => {
  const did = wdg.attr("did")
  const src = $(`#dv_${did}`)
  const mdw = $(`#dm_${did}`)
  mdw.html(special_links(markdown.toHTML(src.val())))
}

class Msg {
  constructor(destination, on_clear) {
    this.destination = $(`#${destination}`)
    this.trashc = $(`#trash_${destination}`)
    this.on_clear = on_clear

    this.trashc.click(e => {
      e.preventDefault()
      this.clear()
    })
    this.trashc.hide()
  }

  clear() {
    this.destination.html("")
    if (this.on_clear != undefined) {
      this.on_clear()
    }
    this.trashc.hide()
  }
  hide() {
    this.destination.hide()
    this.trashc.hide()
  }
  show() {
    this.destination.show()
    if (this.destination.html() != "") {
      this.trashc.show()
    }
  }
  msg(msgobj) {
    const mtext = this.destination.html()
    this.destination.html(`${mtext}<p class="${msgobj[0]}">${msgobj[1]}</p>`)
    this.trashc.show()
  }
}
