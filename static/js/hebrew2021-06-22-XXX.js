/*eslint-env jquery*/
/*eslint-disable no-var*/

/*globals booklangs, versions*/

/* GLOBALS */

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = "/"

const nsq = $.initNamespaceStorage("muting_q")
const mutingQ = nsq.localStorage
const nsn = $.initNamespaceStorage("muting_n")
const mutingN = nsn.localStorage
/* on the Queries page the user can "mute" queries.
 * Which queries are muted, is stored as key value pairs
 * in this local storage bucket.
 * When shebanq shows relevant queries next to a page, muting is taken into account.
 */

/* state variables */

var vcolors, vdefaultcolors, dncols, dnrows, thebooks, thebooksorder, viewinit, style

/* parameters dumped by the server, mostly in json form*/

var viewfluid, sideFetched, materialFetched, materialKind

/* transitory flags indicating whether
 * kinds of material and sidebars have loaded content
 */

var wb, msg

/* wb holds the one and only page object
 * msg messages object
 */

var host,
  statichost,
  pageViewUrl,
  queryUrl,
  wordUrl,
  viewUrl,
  materialUrl,
  dataUrl,
  sideUrl,
  itemUrl,
  chartUrl,
  queriesUrl,
  wordsUrl,
  notesUrl,
  cnotesUrl,
  fieldUrl,
  fieldsUrl,
  bolUrl,
  pblUrl

/* url values for AJAX calls from this application
 * urls from which to fetch additional material through AJAX,
 * the values come from the server
 */

/* prefix for the cookie names, in order to distinguish settings by the user
 * from settings from clicking on a share link
 */
var pref

/* fixed dimensions, measures, heights, widths, etc */
const subtract = 150
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */
const subtractw = 80
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */

var windowHeight, standardHeight, standardHeightw, halfStandardHeight

/*  height and width of canvas, height of window
 */

const mqlSmallHeight = "10em"
/* height of mql query body in sidebar
 */
const mqlSmallWidth = "97%"
/* height of mql query body in sidebar and in dialog
 */
const mqlBigWidthDia = "60%"
/* width of query info in dialog mode
 */
const mqlBigWidth = "100%"
/* width of mql query body in sidebar and in dialog
 */
const editSideWidth = "55%"
/* the desired width of the sidebar when editing a query body
 */
const editMainWidth = "40%"
/* the desired width of the main area when editing a query body
 */
const chartWidth = "400px"
/* dialog width for charts
 */
const chartCols = 30
/* number of chapters in a row in a chart
 */

var origSideWidth, origMainWidth
/* the widths of sidebar and main area just after loading the initial page
 */
var tpLabels, tabInfo, tabViews, nextTp
/* number of tab views and dictionary to go cyclically from a text view to the next
 */
var trLabels, trInfo, nextTr
/* number of tab views and dictionary to go cyclically from a text view to the next
 */
var ntStatclass, ntStatsym, ntStatnext
/* characteristics for tabbed views with notes
 */
var booktrans
/* translation tables for book names
 */

// TOP LEVEL: DYNAMICS, PAGE, WINDOW, SKELETON

function dynamics() {
  // top level function, called when the page has loaded
  viewfluid = {}
  msg = new Msg("material_settings") // a place where ajax messages can be shown to the user
  wb = new Page(new ViewState(viewinit, pref)) // wb is the handle to manipulate the whole page
  wb.init()
  wb.go()
}

function setHeight() {
  // the heights of the sidebars are set, depending on the height of the window
  windowHeight = window.innerHeight
  standardHeight = windowHeight - subtract
  halfStandardHeight = `${0.4 * standardHeight}px`
  $("#material_txt_p").css("height", `${standardHeight}px`)
  for (let i = 1; i <= tabViews; i++) {
    $(`#material_txt_tb${i}`).css("height", `${standardHeight}px`)
  }
  $("#side_material_mq").css("max-height", `${0.6 * standardHeight}px`)
  $("#side_material_mw").css("max-height", `${0.35 * standardHeight}px`)
  $("#words").css("height", `${standardHeight}px`)
  $("#letters").css("height", `${standardHeight}px`)
}

function setHeightw() {
  // the heights of the sidebars are set, depending on the height of the window
  standardHeightw = window.innerHeight - subtractw
  $("#words").css("height", `${standardHeightw}px`)
  $("#letters").css("height", `${standardHeightw}px`)
}

function getWidth() {
  // save the orginal widths of sidebar and main area
  origSideWidth = $(".span3").css("width")
  origMainWidth = $(".span9").css("width")
}

function resetMainWidth() {
  // restore the orginal widths of sidebar and main area
  if (origSideWidth != $(".span3").css("width")) {
    $(".span3").css("width", origSideWidth)
    $(".span3").css("max-width", origSideWidth)
    $(".span9").css("width", origMainWidth)
    $(".span9").css("max-width", origMainWidth)
  }
}

function setEditWidth() {
  // switch to increased sidebar width
  getWidth()
  $(".span3").css("width", editSideWidth)
  $(".span9").css("width", editMainWidth)
}

function Page(vs) {
  // the one and only page object
  this.vs = vs // the viewstate
  History.Adapter.bind(window, "statechange", this.vs.goback)

  this.init = function () {
    // dress up the skeleton, initialize state variables
    this.material = new Material()
    this.sidebars = new Sidebars()
    setHeight()
    getWidth()
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
    resetMaterialStatus()
  }
  this.apply = function () {
    // apply the viewstate: hide and show material as prescribed by the viewstate
    this.material.apply()
    this.sidebars.apply()
  }
  this.go = function () {
    // go to another page view, check whether initial content has to be loaded
    resetMainWidth()
    this.apply()
  }
  this.goMaterial = function () {
    // load other material, whilst keeping the sidebars the same
    this.material.apply()
  }

  /*

the origin must be an object which has a member indicating the type of origin and the kind of page.

1: a color picker 1 from an item in a list
1a: the color picker 1 on an item page
2: a color picker 2 on a list page
3: a button of the list view settings
4: a click on a word in the text
5: when the data or text representation is loaded

*/
  this.highlight2 = function (origin) {
    /* all highlighting goes through this function
        highlighting is holistic: when the user changes a view settings, all highlights have to be reevaluated.
        The only reduction is that word highlighting is completely orthogonal to query result highlighting.
    */
    var that = this
    var qw = origin.qw
    var code = origin.code
    var active = wb.vs.active(qw)
    if (active == "hlreset") {
      // all viewsettings for either queries or words are restored to 'factory' settings
      this.vs.cstatexx(qw)
      this.vs.hstatesv(qw, { active: "hlcustom", selOne: defcolor(qw, null) })
      this.listsettings[qw].apply()
      return
    }
    var hlradio = $(`.${qw}hradio`)
    var activeo = $(`#${qw}active`)
    hlradio.removeClass("ison")
    activeo.addClass("ison")
    var cmap = this.vs.colormap(qw)

    var paintings = {}

    /* first we are going to compute what to paint, resulting in a list of paint instructions.
        Then we apply the paint instructions in one batch.
        */

    /* computing the paint instructions */

    if (code == "1a") {
      /* highlights on an r-page (with a single query or word), coming from the associated ColorPicker1
                This is simple coloring, using a single color.
            */
      var iid = origin.iid
      var paint = cmap[iid] || defcolor(qw == "q", iid)
      if (qw == "q") {
        $($.parseJSON($("#themonads").val())).each(function (i, m) {
          paintings[m] = paint
        })
      } else if (qw == "w") {
        paintings[iid] = paint
      }
      this.paint(qw, paintings)
      return
    }

    /* all other cases: highlights on an m-page, responding to a user action
            This is complex coloring, using multiple colors.
            First we determine which monads need to be highlighted.
        */
    var selclr = wb.vs.selOne(qw)
    var custitems = {}
    var plainitems = {}

    if (qw == "q") {
      /* Queries: highlight customised items with priority over uncustomised items
                If a word belongs to several query results, the last-applied coloring determines the color that the user sees.
                We want to promote the customised colors over the non-customized ones, so we compute customized coloring after
                uncustomized coloring.
                Skip the muted queries
            */
      $(`#side_list_${qw} li`).each(function () {
        var iid = $(this).attr("iid")
        if (!mutingQ.isSet(`${iid}`)) {
          var monads = $.parseJSON($(`#${qw}${iid}`).attr("monads"))
          if (wb.vs.iscolor(qw, iid)) {
            custitems[iid] = monads
          } else {
            plainitems[iid] = monads
          }
        }
      })
    } else if (qw == "w") {
      // Words: they are disjoint, no priority needed
      $("#side_list_" + qw + " li").each(function () {
        var iid = $(this).attr("iid")
        if (wb.vs.iscolor(qw, iid)) {
          custitems[iid] = 1
        } else {
          plainitems[iid] = 1
        }
        var all = $("#" + qw + iid)
        if (active == "hlmany" || wb.vs.iscolor(qw, iid)) {
          all.show()
        } else {
          all.hide()
        }
      })
    }
    var chunks = [custitems, plainitems]

    var clselect = function (iid) {
      // assigns a color to an individual monad, based on the viewsettings
      var paint = ""
      if (active == "hloff") {
        paint = style[qw]["off"]
      } /*
                viewsetting says: do not color any item */ else if (
        active == "hlone"
      ) {
        paint = selclr
      } /*
                viewsetting says: color every applicable item with the same color */ else if (
        active == "hlmany"
      ) {
        paint = cmap[iid] || defcolor(qw == "q", iid)
      } /*
                viewsetting says:
                color every item with customized color (if customized) else with query/word-dependent default color */ else if (
        active == "hlcustom"
      ) {
        paint = cmap[iid] || selclr
      } /*
                viewsetting says:
                color every item with customized color (if customized) else with a single chosen color */ else {
        paint = selclr
      } /*
                but this should not occur */
      return paint
    }

    if (qw == "q") {
      // Queries: compute the monads to be painted and the colors needed for it
      for (let c = 0; c < 2; c++) {
        var chunk = chunks[c]
        for (const iid in chunk) {
          const color = clselect(iid)
          var monads = chunk[iid]
          for (let m in monads) {
            var monad = monads[m]
            if (!(monad in paintings)) {
              paintings[monad] = color
            }
          }
        }
      }
    } else if (qw == "w") {
      // Words: gather the lexemeIds to be painted and the colors needed for it
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
    /* maybe the selection of words of queries has changed for the same material, so wipe previous coloring */
    var monads = $("#material span[m]")
    var stl = style[qw]["prop"]
    var clrOff = style[qw]["off"]
    monads.css(stl, clrOff)

    /* finally, the computed colors are applied */
    this.paint(qw, paintings)
  }

  this.paint = function (qw, paintings) {
    // Execute a series of computed paint instructions
    var stl = style[qw]["prop"]
    var container = "#material_" + wb.vs.tp()
    var att = qw == "q" ? "m" : "l"
    for (const item in paintings) {
      var color = paintings[item]
      $(container + " span[" + att + '="' + item + '"]').css(stl, vcolors[color][qw])
    }
  }

  this.picker2 = {}
  this.picker1 = { q: {}, w: {} } // will collect the two Colorpicker1 objects, indexed as q w
  this.picker1list = { q: {}, w: {} } // will collect the two lists of Colorpicker1 objects, index as q w and then by iid
}

// MATERIAL

function Material() {
  // Object corresponding to everything that controls the material in the main part (not in the side bars)
  var that = this
  this.name = "material"
  this.hid = "#" + this.name
  this.lselect = new LSelect()
  this.mselect = new MSelect()
  this.pselect = new PSelect()
  this.message = new MMessage()
  this.content = new MContent()
  this.msettings = new MSettings(this.content)
  this.adapt = function () {
    this.fetch()
  }
  this.apply = function () {
    // apply viewsettings to current material
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
      resetMaterialStatus()
      var pMr = wb.prev["mr"]
      var pQw = wb.prev["qw"]
      var pIid = wb.prev["iid"]
      if (pMr == "r" && wb.mr == "m") {
        var vals = {}
        if (pQw != "n") {
          vals[pIid] = wb.vs.colormap(pQw)[pIid] || defcolor(pQw == "q", pIid)
          wb.vs.cstatesv(pQw, vals)
        }
      }
    }
    this.lselect.apply()
    this.mselect.apply()
    this.pselect.apply()
    this.msettings.apply()
    var book = wb.vs.book()
    var chapter = wb.vs.chapter()
    var page = wb.vs.page()
    $("#thelang").html(booklangs[wb.vs.lang()][1])
    $("#thebook").html(book != "x" ? booktrans[wb.vs.lang()][book] : "book")
    $("#thechapter").html(chapter > 0 ? chapter : "chapter")
    $("#thepage").html(page > 0 ? "" + page : "")
    for (const x in wb.vs.mstate()) {
      wb.prev[x] = wb.vs.mstate()[x]
    }
  }
  this.fetch = function () {
    // get the material by AJAX if needed, and process the material afterward
    var vars =
      "?version=" +
      wb.version +
      "&mr=" +
      wb.mr +
      "&tp=" +
      wb.vs.tp() +
      "&tr=" +
      wb.vs.tr() +
      "&qw=" +
      wb.qw +
      "&lang=" +
      wb.vs.lang()
    var doFetch = false
    if (wb.mr == "m") {
      vars += "&book=" + wb.vs.book()
      vars += "&chapter=" + wb.vs.chapter()
      doFetch = wb.vs.book() != "x" && wb.vs.chapter() > 0
    } else {
      vars += "&iid=" + wb.iid
      vars += "&page=" + wb.vs.page()
      doFetch = wb.qw == "q" ? wb.iid >= 0 : wb.iid != "-1"
    }
    var tp = wb.vs.tp()
    var tr = wb.vs.tr()
    if (
      doFetch &&
      (!materialFetched[tp] || !(tp in materialKind) || materialKind[tp] != tr)
    ) {
      this.message.msg("fetching data ...")
      wb.sidebars.afterMaterialFetch()
      $.get(
        materialUrl + vars,
        function (html) {
          var response = $(html)
          that.pselect.add(response)
          that.message.add(response)
          that.content.add(response)
          materialFetched[tp] = true
          materialKind[tp] = tr
          that.process()
          that.gotoVerse()
        },
        "html"
      )
    } else {
      wb.highlight2({ code: "5", qw: "w" })
      wb.highlight2({ code: "5", qw: "q" })
      if (true || wb.vs.tp() == "txt_il") {
        this.msettings.hebrewsettings.apply()
      }
      this.gotoVerse()
    }
  }
  this.gotoVerse = function () {
    // go to the selected verse
    $(".vhl").removeClass("vhl")
    var vtarget = $(
      "#material_" +
        wb.vs.tp() +
        ">" +
        (wb.mr == "r" ? "div[tvid]" : 'div[tvid="' + wb.vs.verse() + '"]')
    ).filter(":first")
    if (vtarget != undefined && vtarget[0] != undefined) {
      vtarget[0].scrollIntoView()
      $("#navbar")[0].scrollIntoView()
      vtarget.addClass("vhl")
    }
  }
  this.process = function () {
    // process new material obtained by an AJAX call
    var mf = 0
    var tp = wb.vs.tp()
    var tr = wb.vs.tr()
    for (const y of materialFetched) {
      if (y) {
        mf += 1
      }
    } // count how many versions of this material already have been fetched
    if (materialKind[tp] != "" && materialKind != tr) {
      // and also whether the material has already been fetched in another transcription
      mf += 1
    }
    var newcontent = $("#material_" + tp)
    var textcontent = $(".txt_p,.txt_tb1,.txt_tb2,.txt_tb3")
    var ttextcontent = $(".t1_txt,.lv2")
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
    // because some processes like highlighting and assignment of verse number clicks must be suppressed on first time or on subsequent times
    if (wb.mr == "r") {
      this.pselect.apply()
      if (wb.qw != "n") {
        wb.picker1[wb.qw].adapt(wb.iid, true)
      }
      $("a.cref").click(function (e) {
        e.preventDefault()
        wb.vs.mstatesv({
          book: $(this).attr("book"),
          chapter: $(this).attr("chapter"),
          verse: $(this).attr("verse"),
          mr: "m",
        })
        wb.vs.addHist()
        wb.go()
      })
    } else {
      this.addWordActions(newcontent, mf)
    }
    this.addVrefs(newcontent, mf)
    if (wb.vs.tp() == "txt_il") {
      this.msettings.hebrewsettings.apply()
    } else if (wb.vs.tp() == "txt_tb1") {
      this.addCmt(newcontent)
    }
  }
  this.addCmt = function (newcontent) {
    // add actions for the tab1 view
    this.notes = new Notes(newcontent)
  }

  this.addVrefs = function (newcontent, mf) {
    var vrefs = newcontent.find(".vradio")
    vrefs.each(function () {
      var book = $(this).attr("b")
      var chapter = $(this).attr("c")
      var verse = $(this).attr("v")
      $(this).attr("title", "interlinear data")
    })
    vrefs.click(function (e) {
      e.preventDefault()
      var bk = $(this).attr("b")
      var ch = $(this).attr("c")
      var vs = $(this).attr("v")
      var baseTp = wb.vs.tp()
      var dat = $("#" + baseTp + "_txt_il_" + bk + "_" + ch + "_" + vs)
      var txt = $("#" + baseTp + "_" + bk + "_" + ch + "_" + vs)
      var legend = $("#datalegend")
      var legendc = $("#datalegend_control")
      if ($(this).hasClass("ison")) {
        $(this).removeClass("ison")
        $(this).attr("title", "interlinear data")
        legend.hide()
        closeDialog(legend)
        legendc.hide()
        dat.hide()
        txt.show()
      } else {
        $(this).addClass("ison")
        $(this).attr("title", "text/tab")
        legendc.show()
        dat.show()
        txt.hide()
        if (dat.attr("lf") == "x") {
          dat.html("fetching data for " + bk + " " + ch + ":" + vs + " ...")
          dat.load(
            dataUrl +
              "?version=" +
              wb.version +
              "&book=" +
              bk +
              "&chapter=" +
              ch +
              "&verse=" +
              vs,
            function () {
              dat.attr("lf", "v")
              that.msettings.hebrewsettings.apply()
              if (wb.mr == "r") {
                if (wb.qw != "n") {
                  wb.picker1[wb.qw].adapt(wb.iid, true)
                }
              } else {
                wb.highlight2({ code: "5", qw: "w" })
                wb.highlight2({ code: "5", qw: "q" })
                that.addWordActions(dat, mf)
              }
            },
            "html"
          )
        }
      }
    })
  }
  this.addWordActions = function (newcontent, mf) {
    // Make words clickable, so that they show up in the sidebar
    newcontent.find("span[l]").click(function (e) {
      e.preventDefault()
      var iid = $(this).attr("l")
      var qw = "w"
      var all = $("#" + qw + iid)
      if (wb.vs.iscolor(qw, iid)) {
        wb.vs.cstatex(qw, iid)
        all.hide()
      } else {
        var vals = {}
        vals[iid] = defcolor(false, iid)
        wb.vs.cstatesv(qw, vals)
        all.show()
      }
      var active = wb.vs.active(qw)
      if (active != "hlcustom" && active != "hlmany") {
        wb.vs.hstatesv(qw, { active: "hlcustom" })
      }
      if (wb.vs.get("w") == "v") {
        if (iid in wb.picker1list["w"]) {
          // should not happen but it happens when changing data versions
          wb.picker1list["w"][iid].apply(false)
        }
      }
      wb.highlight2({ code: "4", qw: qw })
      wb.vs.addHist()
    })
    if (mf > 1) {
      /* Initially, material gets highlighted once the sidebars have been loaded.
But when we load a different representation of material (data, tab), the sidebars are still there,
and after loading the material, highlighs have to be applied.
*/
      wb.highlight2({ code: "5", qw: "q" })
      wb.highlight2({ code: "5", qw: "w" })
    }
  }
  this.message.msg("choose a passage or a query or a word")
}

// MATERIAL: Notes

function Notes(newcontent) {
  var that = this
  this.show = false
  this.verselist = {}
  this.version = wb.version
  this.savControls = $("span.nt_main_sav")
  this.savC = this.savControls.find('a[tp="s"]')
  this.revC = this.savControls.find('a[tp="r"]')
  this.loggedIn = false
  this.cctrl = $("a.nt_main_ctrl")

  newcontent.find(".vradio").each(function () {
    var bk = $(this).attr("b")
    var ch = $(this).attr("c")
    var vs = $(this).attr("v")
    var topl = $(this).closest("div")
    that.verselist[bk + " " + ch + ":" + vs] = new Notev(
      that.version,
      bk,
      ch,
      vs,
      topl.find("span.nt_ctrl"),
      topl.find("table.t1_table")
    )
  })
  this.msgn = new Msg("nt_main_msg", () => {
    for (const notev of that.verselist) {
      notev.clearMsg()
    }
  })
  this.apply = function () {
    if (wb.vs.get("n") == "v") {
      this.cctrl.addClass("nt_loaded")
      for (const notev of this.verselist) {
        notev.showNotes(false)
        this.loggedIn = notev.loggedIn
      }
      if (this.loggedIn) {
        this.savControls.show()
      }
    } else {
      this.cctrl.removeClass("nt_loaded")
      this.savControls.hide()
      for (const notev of this.verselist) {
        notev.hideNotes()
      }
    }
  }
  this.cctrl.click(e => {
    e.preventDefault()
    wb.vs.hstatesv("n", { get: wb.vs.get("n") == "v" ? "x" : "v" })
    that.apply()
  })
  this.revC.click(e => {
    e.preventDefault()
    for (const notev of that.verselist) {
      notev.revert()
    }
  })
  this.savC.click(e => {
    e.preventDefault()
    for (const notev of that.verselist) {
      notev.save()
    }
    that.msgn.msg(["special", "Done"])
  })
  this.msgn.clear()
  $("span.nt_main_sav").hide()
  this.apply()
}

function Notev(vr, bk, ch, vs, ctrl, dest) {
  var that = this
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
  this.savControls = this.ctrl.find("span.nt_sav")
  this.savC = this.savControls.find('a[tp="s"]')
  this.edtC = this.savControls.find('a[tp="e"]')
  this.revC = this.savControls.find('a[tp="r"]')

  this.fetch = function (adjustVerse) {
    var senddata = {
      version: this.version,
      book: this.book,
      chapter: this.chapter,
      verse: this.verse,
      edit: this.edt,
    }
    this.msgn.msg(["info", "fetching notes ..."])
    $.post(cnotesUrl, senddata, function (json) {
      that.loaded = true
      that.msgn.clear()
      json.msgs.forEach(function (m) {
        that.msgn.msg(m)
      })
      if (json.good) {
        that.process(
          json.users,
          json.notes,
          json.nkey_index,
          json.changed,
          json.logged_in
        )
        if (adjustVerse) {
          if (wb.mr == "m") {
            wb.vs.mstatesv({ verse: that.verse })
            wb.material.gotoVerse()
          }
        }
      }
    })
  }
  this.process = function (users, notes, nkeyIndex, changed, loggedIn) {
    if (changed) {
      if (wb.mr == "m") {
        sideFetched["mn"] = false
        wb.sidebars.sidebar["mn"].content.apply()
      }
    }
    this.origUsers = users
    this.origNotes = notes
    this.origNkeyIndex = nkeyIndex
    this.origEdit = []
    this.loggedIn = loggedIn
    this.genHtml(true)
    this.dirty = false
    this.applyDirty()
    this.decorate()
  }
  this.decorate = function () {
    this.dest
      .find("td.nt_stat")
      .find("a")
      .click(function (e) {
        e.preventDefault()
        var statcode = $(this).attr("code")
        var nextcode = ntStatnext[statcode]
        var nextsym = ntStatsym[nextcode]
        var row = $(this).closest("tr")
        for (const cl of ntStatclass) {
          row.removeClass(cl)
        }
        for (const cl of ntStatsym) {
          $(this).removeClass(`fa-${cl}`)
        }
        row.addClass(ntStatclass[nextcode])
        $(this).attr("code", nextcode)
        $(this).addClass("fa-" + nextsym)
      })
    this.dest
      .find("td.nt_pub")
      .find("a")
      .click(function (e) {
        e.preventDefault()
        if ($(this).hasClass("ison")) {
          $(this).removeClass("ison")
        } else {
          $(this).addClass("ison")
        }
      })
    this.dest.find("tr.nt_cmt").show()
    if (this.loggedIn) {
      mainSavControls.show()
      this.savControls.show()
      if (this.edt) {
        this.savC.show()
        this.edtC.hide()
      } else {
        this.savC.hide()
        this.edtC.show()
      }
    }
    decorateCrossrefs(this.dest)
  }
  this.genHtmlCa = function (canr) {
    var notes = this.origNotes[canr]
    var nkeyIndex = this.origNkeyIndex
    var html = ""
    this.nnotes += notes.length
    for (let n = 0; n < notes.length; n++) {
      var nline = notes[n]
      var kwtrim = $.trim(nline.kw)
      var kws = kwtrim.split(/\s+/)
      var uid = nline.uid
      var mute = false
      for (const kw of kws) {
        const nkid = nkeyIndex[uid + " " + kw]
        if (mutingN.isSet("n" + nkid)) {
          mute = true
          break
        }
      }
      if (mute) {
        this.mnotes += 1
        continue
      }
      var user = this.origUsers[uid]
      var nid = nline.nid
      var pubc = nline.pub ? "ison" : ""
      var sharedc = nline.shared ? "ison" : ""
      var statc = ntStatclass[nline.stat]
      var statsym = ntStatsym[nline.stat]
      var ro = nline.ro
      var editAtt = ro ? "" : ' edit="1"'
      var editClass = ro ? "" : " edit"
      html +=
        '<tr class="nt_cmt ntInfo ' +
        statc +
        editClass +
        '" nid="' +
        nid +
        '" ncanr="' +
        canr +
        '"' +
        editAtt +
        ">"
      if (ro) {
        html +=
          '<td class="nt_stat"><span class="fa fa-' +
          statsym +
          ' fa-fw" code="' +
          nline.stat +
          '"></span></td>'
        html += '<td class="nt_kw">' + escapeHTML(nline.kw) + "</td>"
        var ntxt = specialLinks(markdown.toHTML(markdownEscape(nline.ntxt)))
        //var ntxt = specialLinksM(escapeHTML(nline.ntxt))
        //ntxt = markdown.toHTML(ntxt)
        html += '<td class="nt_cmt">' + ntxt + "</td>"
        html +=
          '<td class="nt_user" colspan="3" uid="' +
          uid +
          '">' +
          escapeHTML(user) +
          "</td>"
        html += '<td class="nt_pub">'
        html +=
          '    <span class="ctrli pradio fa fa-share-alt fa-fw ' +
          sharedc +
          '" title="shared?"></span>'
        html +=
          '    <span class="ctrli pradio fa fa-quote-right fa-fw ' +
          pubc +
          '" title="published?"></span>'
      } else {
        this.origEdit.push({ canr: canr, note: nline })
        html +=
          '<td class="nt_stat"><a href="#" title="set status" class="fa fa-' +
          statsym +
          ' fa-fw" code="' +
          nline.stat +
          '"></a></td>'
        html += '<td class="nt_kw"><textarea>' + nline.kw + "</textarea></td>"
        html += '<td class="nt_cmt"><textarea>' + nline.ntxt + "</textarea></td>"
        html +=
          '<td class="nt_user" colspan="3" uid="' +
          uid +
          '">' +
          escapeHTML(user) +
          "</td>"
        html += '<td class="nt_pub">'
        html +=
          '    <a class="ctrli pradio fa fa-share-alt fa-fw ' +
          sharedc +
          '" href="#" title="shared?"></a>'
        html += "<span>" + vr + "</span>"
        html +=
          '    <a class="ctrli pradio fa fa-quote-right fa-fw ' +
          pubc +
          '" href="#" title="published?"></a>'
      }
      html += "</td></tr>"
    }
    return html
  }
  this.genHtml = function (replace) {
    this.mnotes = 0
    if (replace) {
      this.dest.find("tr[ncanr]").remove()
    }
    for (const canr in this.origNotes) {
      var target = this.dest.find("tr[canr=" + canr + "]")
      var html = this.genHtmlCa(canr)
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
      this.msgn.msg(["special", "muted notes: " + this.mnotes])
    }
  }
  this.sendnotes = function (senddata) {
    var good = false
    $.post(
      cnotesUrl,
      senddata,
      function (json) {
        good = json.good
        that.msgn.clear()
        json.msgs.forEach(function (m) {
          that.msgn.msg(m)
        })
        if (json.good) {
          that.dest.find("tr[ncanr]").remove()
          that.process(
            json.users,
            json.notes,
            json.nkey_index,
            json.changed,
            json.logged_in
          )
        }
      },
      "json"
    )
  }
  this.dest.find("tr.nt_cmt").hide()
  var mainSavControls = $("span.nt_main_sav")
  this.isDirty = function () {
    var notes = this.dest.find("tr[edit]")
    var dirty = false
    if (this.origEdit == undefined) {
      this.dirty = false
      return
    }
    for (let n = 0; n < this.origEdit.length; n++) {
      var canr = this.origEdit[n].canr
      var oNote = this.origEdit[n].note
      var nid = oNote.nid
      var uid = oNote.uid
      var nNote =
        nid == 0
          ? this.dest.find('tr[nid="0"][ncanr="' + canr + '"]')
          : this.dest.find('tr[nid="' + nid + '"]')
      var oStat = oNote.stat
      var nStat = nNote.find("td.nt_stat a").attr("code")
      var oKw = $.trim(oNote.kw)
      var nKw = $.trim(nNote.find("td.nt_kw textarea").val())
      var oNtxt = oNote.ntxt
      var nNtxt = $.trim(nNote.find("td.nt_cmt textarea").val())
      var oShared = oNote.shared
      var nShared = nNote.find("td.nt_pub a").first().hasClass("ison")
      var oPub = oNote.pub
      var nPub = nNote.find("td.nt_pub a").last().hasClass("ison")
      if (
        oStat != nStat ||
        oKw != nKw ||
        oNtxt != nNtxt ||
        oShared != nShared ||
        oPub != nPub
      ) {
        dirty = true
        break
      }
    }
    this.dirty = dirty
    this.applyDirty()
  }
  this.applyDirty = function () {
    if (this.dirty) {
      this.cctrl.addClass("dirty")
    } else if (this.cctrl.hasClass("dirty")) {
      this.cctrl.removeClass("dirty")
    }
  }
  this.savC.click(function (e) {
    e.preventDefault()
    that.save()
  })
  this.edtC.click(function (e) {
    e.preventDefault()
    that.edit()
  })
  this.revC.click(function (e) {
    e.preventDefault()
    that.revert()
  })
  this.save = function () {
    this.edt = false
    var data = {
      version: this.version,
      book: this.book,
      chapter: this.chapter,
      verse: this.verse,
      save: true,
      edit: this.edt,
    }
    var notes = this.dest.find("tr[edit]")
    var notelines = []
    if (this.origEdit == undefined) {
      return
    }
    for (let n = 0; n < this.origEdit.length; n++) {
      var canr = this.origEdit[n].canr
      var oNote = this.origEdit[n].note
      var nid = oNote.nid
      var uid = oNote.uid
      var nNote =
        nid == 0
          ? this.dest.find('tr[nid="0"][ncanr="' + canr + '"]')
          : this.dest.find('tr[nid="' + nid + '"]')
      var oStat = oNote.stat
      var nStat = nNote.find("td.nt_stat a").attr("code")
      var oKw = $.trim(oNote.kw)
      var nKw = $.trim(nNote.find("td.nt_kw textarea").val())
      var oNtxt = oNote.ntxt
      var nNtxt = $.trim(nNote.find("td.nt_cmt textarea").val())
      var oShared = oNote.shared
      var nShared = nNote.find("td.nt_pub a").first().hasClass("ison")
      var oPub = oNote.pub
      var nPub = nNote.find("td.nt_pub a").last().hasClass("ison")
      if (
        oStat != nStat ||
        oKw != nKw ||
        oNtxt != nNtxt ||
        oShared != nShared ||
        oPub != nPub
      ) {
        notelines.push({
          nid: nid,
          canr: canr,
          stat: nStat,
          kw: nKw,
          ntxt: nNtxt,
          uid: uid,
          shared: nShared,
          pub: nPub,
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
  this.edit = function () {
    this.edt = true
    this.fetch(true)
  }
  this.revert = function () {
    this.edt = false
    var data = {
      version: this.version,
      book: this.book,
      chapter: this.chapter,
      verse: this.verse,
      save: true,
      edit: this.edt,
    }
    data["notes"] = JSON.stringify([])
    this.sendnotes(data)
    //this.genHtml(this.origUsers, this.origNotes, true)
    //this.dirty = false
    //this.applyDirty()
    //this.decorate()
  }
  this.hideNotes = function () {
    this.show = false
    this.cctrl.removeClass("nt_loaded")
    this.savControls.hide()
    this.dest.find("tr.nt_cmt").hide()
    this.msgn.hide()
  }
  this.showNotes = function (adjustVerse) {
    this.show = true
    this.cctrl.addClass("nt_loaded")
    this.msgn.show()
    if (!this.loaded) {
      this.fetch(adjustVerse)
    } else {
      this.dest.find("tr.nt_cmt").show()
      if (this.loggedIn) {
        this.savControls.show()
        if (this.edt) {
          this.savC.show()
          this.edtC.hide()
        } else {
          this.savC.hide()
          this.edtC.show()
        }
      }
      if (wb.mr == "m") {
        wb.vs.mstatesv({ verse: that.verse })
        wb.material.gotoVerse()
      }
    }
  }
  this.clearMsg = function () {
    this.msgn.clear()
  }
  this.cctrl.click(function (e) {
    e.preventDefault()
    that.isDirty()
    if (that.show) {
      that.hideNotes()
    } else {
      that.showNotes(true)
    }
  })
  mainSavControls.hide()
  this.savControls.hide()
}

// MATERIAL: SELECTION

function MSelect() {
  // for book and chapter selection
  var that = this
  this.name = "select_passage"
  this.hid = "#" + this.name
  this.book = new SelectBook()
  this.select = new SelectItems("chapter")
  this.apply = function () {
    // apply material viewsettings to current material
    var thisFeaturehost = adaptDocBaseVersion(featurehost) + "/" + adaptDocName()
    $(".source").attr("href", thisFeaturehost)
    $(".source").attr("title", "BHSA feature documentation")
    $(".mvradio").removeClass("ison")
    $("#version_" + wb.version).addClass("ison")
    var bol = $("#bol_lnk")
    var pbl = $("#pbl_lnk")
    if (wb.mr == "m") {
      this.book.apply()
      this.select.apply()
      $(this.hid).show()
      var book = wb.vs.book()
      var chapter = wb.vs.chapter()
      if (book != "x" && chapter > 0) {
        bol.attr("href", bolUrl + "/ETCBC4/" + book + "/" + chapter)
        bol.show()
        pbl.attr("href", pblUrl + "/" + book + "/" + chapter)
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
  this.setVselect = function (v) {
    if (versions[v]) {
      $("#version_" + v).click(function (e) {
        e.preventDefault()
        sideFetched["mw"] = false
        sideFetched["mq"] = false
        sideFetched["mn"] = false
        wb.vs.mstatesv({ version: v })
        wb.go()
      })
    }
  }
  for (const v in versions) {
    this.setVselect(v)
  }
  $("#self_link").hide()
}

function PSelect() {
  // for result page selection
  var that = this
  var select = "#select_contents_page"
  this.name = "select_pages"
  this.hid = "#" + this.name
  this.select = new SelectItems("page")
  this.apply = function () {
    // apply result page selection: fill in headings on the page
    if (wb.mr == "r") {
      this.select.apply()
      $(this.hid).show()
    } else {
      $(this.hid).hide()
    }
  }
  this.add = function (response) {
    // add the content portion of the response to the content portion of the page
    if (wb.mr == "r") {
      $(select).html(response.find(select).html())
    }
  }
}

function LSelect() {
  // language selection
  var that = this
  this.name = "select_contents_lang"
  this.hid = "#" + this.name
  this.control = "#select_control_lang"
  this.present = function () {
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose language",
      width: "250px",
    })
  }
  this.genHtml = function () {
    // generate a new lang selector
    var thelang = wb.vs.lang()
    var nitems = booklangs.length
    this.lastitem = nitems
    var ht = ""
    ht += '<table class="pagination">'
    var langs = Object.keys(booklangs).sort()
    for (const item in langs) {
      var langinfo = booklangs[item]
      var nameEn = langinfo[0]
      var nameOwn = langinfo[1]
      var clactive = thelang == item ? ' class="active"' : ""
      ht +=
        "<tr><td" +
        clactive +
        '><a class="itemnav" href="#" item="' +
        item +
        '">' +
        nameOwn +
        "</td>"
      ht +=
        "<td" +
        clactive +
        '><a class="itemnav" href="#" item="' +
        item +
        '">' +
        nameEn +
        "</td></tr>"
    }
    ht += "</table>"
    $(this.hid).html(ht)
    return nitems
  }
  this.addItem = function (item) {
    item.click(function (e) {
      e.preventDefault()
      var newobj = $(this).closest("li")
      var isloaded = newobj.hasClass("active")
      if (!isloaded) {
        var vals = {}
        vals["lang"] = $(this).attr("item")
        wb.vs.mstatesv(vals)
        that.updateVlabels()
        wb.vs.addHist()
        wb.material.apply()
        //wb.go()
      }
    })
  }
  this.updateVlabels = function () {
    $("span[book]").each(function () {
      $(this).html(booktrans[wb.vs.lang()][$(this).attr("book")])
    })
  }

  this.apply = function () {
    var showit = false
    this.genHtml()
    $("#select_contents_lang .itemnav").each(function () {
      that.addItem($(this))
    })
    $(this.control).show()
    this.present()
  }
  $(this.control).click(function (e) {
    e.preventDefault()
    $(that.hid).dialog("open")
  })
}

function SelectBook() {
  // book selection
  var that = this
  this.name = "select_contents_book"
  this.hid = "#" + this.name
  this.control = "#select_control_book"
  this.present = function () {
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose book",
      width: "110px",
    })
  }
  this.genHtml = function () {
    // generate a new book selector
    var thebook = wb.vs.book()
    var lang = wb.vs.lang()
    var thisbooksorder = thebooksorder[wb.version]
    var nitems = thisbooksorder.length
    this.lastitem = nitems
    var ht = ""
    ht += '<div class="pagination"><ul>'
    for (const item of thisbooksorder) {
      var itemrep = booktrans[lang][item]
      if (thebook == item) {
        ht +=
          '<li class="active"><a class="itemnav" href="#" item="' +
          item +
          '">' +
          itemrep +
          "</a></li>"
      } else {
        ht +=
          '<li><a class="itemnav" href="#" item="' + item + '">' + itemrep + "</a></li>"
      }
    }
    ht += "</ul></div>"
    $(this.hid).html(ht)
    return nitems
  }
  this.addItem = function (item) {
    item.click(function (e) {
      e.preventDefault()
      var newobj = $(this).closest("li")
      var isloaded = newobj.hasClass("active")
      if (!isloaded) {
        var vals = {}
        vals["book"] = $(this).attr("item")
        vals["chapter"] = "1"
        vals["verse"] = "1"
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
        wb.go()
      }
    })
  }
  this.apply = function () {
    var showit = false
    this.genHtml()
    $("#select_contents_book .itemnav").each(function () {
      that.addItem($(this))
    })
    $(this.control).show()
    this.present()
  }
  $(this.control).click(function (e) {
    e.preventDefault()
    $(that.hid).dialog("open")
  })
}

function SelectItems(key) {
  // both for chapters and for result pages
  var that = this
  this.key = key
  this.otherKey = key == "chapter" ? "page" : "chapter"
  this.name = "select_contents_" + this.key
  this.otherName = "select_contents_" + this.otherKey
  this.hid = "#" + this.name
  this.otherHid = "#" + this.otherName
  this.control = "#select_control_" + this.key
  this.prev = $("#prev_" + this.key)
  this.next = $("#next_" + this.key)
  this.go = function () {
    if (this.key == "chapter") {
      wb.go()
    } else {
      wb.goMaterial()
    }
  }
  this.prev.click(function (e) {
    e.preventDefault()
    var vals = {}
    vals[that.key] = $(this).attr("contents")
    vals["verse"] = "1"
    wb.vs.mstatesv(vals)
    wb.vs.addHist()
    that.go()
  })
  this.next.click(function (e) {
    e.preventDefault()
    var vals = {}
    vals[that.key] = $(this).attr("contents")
    vals["verse"] = "1"
    wb.vs.mstatesv(vals)
    wb.vs.addHist()
    that.go()
  })
  this.present = function () {
    closeDialog($(this.otherHid))
    $(this.hid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      modal: false,
      title: "choose " + that.key,
      width: "200px",
    })
  }
  this.genHtml = function () {
    // generate a new page selector
    if (this.key == "chapter") {
      var thebook = wb.vs.book()
      var theitem = wb.vs.chapter()
      var nitems = thebook != "x" ? thebooks[wb.version][thebook] : 0
      this.lastitem = nitems
      var itemlist = new Array(nitems)
      for (let i = 0; i < nitems; i++) {
        itemlist[i] = i + 1
      }
    } else {
      // 'page'
      var theitem = wb.vs.page()
      var nitems = $("#rp_pages").val()
      this.lastitem = nitems
      var itemlist = []
      if (nitems) {
        itemlist = $.parseJSON($("#rp_pagelist").val())
      }
    }
    var ht = ""
    if (nitems != undefined) {
      if (nitems != 0) {
        ht = '<div class="pagination"><ul>'
        for (const item of itemlist) {
          if (theitem == item) {
            ht +=
              '<li class="active"><a class="itemnav" href="#" item="' +
              item +
              '">' +
              item +
              "</a></li>"
          } else {
            ht +=
              '<li><a class="itemnav" href="#" item="' +
              item +
              '">' +
              item +
              "</a></li>"
          }
        }
        ht += "</ul></div>"
      }
      $(this.hid).html(ht)
    }
    return nitems
  }
  this.addItem = function (item) {
    item.click(function (e) {
      e.preventDefault()
      var newobj = $(this).closest("li")
      var isloaded = newobj.hasClass("active")
      if (!isloaded) {
        var vals = {}
        vals[that.key] = $(this).attr("item")
        vals["verse"] = "1"
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
        that.go()
      }
    })
  }
  this.apply = function () {
    var showit = (showit = this.genHtml() > 0)
    if (!showit) {
      $(this.control).hide()
    } else {
      $("#select_contents_" + this.key + " .itemnav").each(function () {
        that.addItem($(this))
      })
      $(this.control).show()
      var thisitem = parseInt(this.key == "page" ? wb.vs.page() : wb.vs.chapter())
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
  $(this.control).click(function (e) {
    e.preventDefault()
    $(that.hid).dialog("open")
  })
}

function CSelect(vr, qw) {
  // for chart selection
  var that = this
  this.vr = vr
  this.qw = qw
  this.control = "#select_control_chart_" + vr + "_" + qw
  this.select = "#select_contents_chart_" + vr + "_" + qw
  this.loaded = {}
  this.init = function () {
    $(that.control).click(function (e) {
      e.preventDefault()
      that.apply()
    })
  }
  this.apply = function () {
    if (!that.loaded[that.qw + "_" + wb.iid]) {
      if (
        $("#select_contents_chart_" + that.vr + "_" + that.qw + "_" + wb.iid).length ==
        0
      ) {
        $(this.select).append(
          '<span id="select_contents_chart_' +
            that.vr +
            "_" +
            that.qw +
            "_" +
            wb.iid +
            '"></span>'
        )
      }
      this.fetch(wb.iid)
    } else {
      this.show()
    }
  }
  this.fetch = function (iid) {
    var vars = "?version=" + this.vr + "&qw=" + this.qw + "&iid=" + iid
    $(this.select + "_" + iid).load(
      chartUrl + vars,
      function () {
        that.loaded[that.qw + "_" + iid] = true
        that.process(iid)
      },
      "html"
    )
  }
  this.process = function (iid) {
    this.genHtml(iid)
    $(this.select + "_" + iid + " .cnav").each(function () {
      that.addItem($(this), iid)
    })
    $("#theitemc").click(function (e) {
      e.preventDefault()
      var vals = {}
      vals["iid"] = iid
      vals["mr"] = "r"
      vals["version"] = that.vr
      vals["qw"] = that.qw
      wb.vs.mstatesv(vals)
      wb.vs.addHist()
      wb.go()
    })
    $("#theitemc").html(
      "Back to " + $("#theitem").html() + " (version " + that.vr + ")"
    ) // fill in the Back to query/word line in a chart
    this.present(iid)
    this.show(iid)
  }

  this.present = function (iid) {
    $(this.select + "_" + iid).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      close: function () {
        that.loaded[that.qw + "_" + iid] = false
        $(that.select + "_" + iid).html("")
      },
      modal: false,
      title: "chart for " + style[that.qw]["tag"] + " (version " + that.vr + ")",
      width: chartWidth,
      position: { my: "left top", at: "left top", of: window },
    })
  }
  this.show = function (iid) {
    $(this.select + "_" + iid).dialog("open")
  }

  this.genHtml = function (iid) {
    // generate a new chart
    var nbooks = 0
    var booklist = $("#r_chartorder" + this.qw).val()
    var bookdata = $("#r_chart" + this.qw).val()
    if (booklist) {
      booklist = $.parseJSON(booklist)
      bookdata = $.parseJSON(bookdata)
      nbooks = booklist.length
    } else {
      booklist = []
      bookdata = {}
    }
    var ht = ""
    ht +=
      '<p><a id="theitemc" title="back to ' +
      style[this.qw]["tag"] +
      " (version " +
      that.vr +
      ')" href="#">back</a></p>'
    ht += '<table class="chart">'
    var ccl = ccolors.length
    for (const book of booklist) {
      var blocks = bookdata[book]
      ht +=
        '<tr><td class="bnm">' + book + '</td><td class="chp"><table class="chp"><tr>'
      var l = 0
      for (let i = 0; i < blocks.length; i++) {
        if (l == chartCols) {
          ht += "</tr><tr>"
          l = 0
        }
        var blockInfo = blocks[i]
        var chnum = blockInfo[0]
        var chRange = blockInfo[1] + "-" + blockInfo[2]
        var blres = blockInfo[3]
        var blsize = blockInfo[4]
        var blresSelect = blres >= ccl ? ccl - 1 : blres
        var z = ccolors[blresSelect]
        var s = "&nbsp;"
        var sz = ""
        var sc = ""
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
        ht +=
          '<td class="' +
          z +
          '"><a title="' +
          chRange +
          sz +
          ": " +
          blres +
          '" class="cnav ' +
          sc +
          '" href="#" b=' +
          book +
          ' ch="' +
          chnum +
          '">' +
          s +
          "</a></td>"
        l++
      }
      ht += "</tr></table></td></tr>"
    }
    ht += "</table>"
    $(this.select + "_" + iid).html(ht)
    return nbooks
  }
  this.addItem = function (item, iid) {
    item.click(function (e) {
      e.preventDefault()
      var vals = {}
      vals["book"] = $(this).attr("b")
      vals["chapter"] = $(this).attr("ch")
      vals["mr"] = "m"
      vals["version"] = that.vr
      wb.vs.mstatesv(vals)
      wb.vs.hstatesv("q", { selOne: "white", active: "hlcustom" })
      wb.vs.hstatesv("w", { selOne: "black", active: "hlcustom" })
      wb.vs.cstatexx("q")
      wb.vs.cstatexx("w")
      if (that.qw != "n") {
        vals = {}
        vals[iid] = wb.vs.colormap(that.qw)[iid] || defcolor(that.qw == "q", iid)
        wb.vs.cstatesv(that.qw, vals)
      }
      wb.vs.addHist()
      wb.go()
    })
  }
}

// MATERIAL (messages when retrieving, storing the contents)

function MMessage() {
  // diagnostic output
  this.name = "material_message"
  this.hid = "#" + this.name
  this.add = function (response) {
    $(this.hid).html(response.children(this.hid).html())
  }
  this.msg = function (m) {
    $(this.hid).html(m)
  }
}

function MContent() {
  // the actual Hebrew content, either plain text or tabbed data
  this.nameContent = "#material_content"
  this.select = function () {}
  this.add = function (response) {
    $("#material_" + wb.vs.tp()).html(response.children(this.nameContent).html())
  }
  this.show = function () {
    var thisTp = wb.vs.tp()
    for (const tp in nextTp) {
      var thisMaterial = $("#material_" + tp)
      if (thisTp == tp) {
        thisMaterial.show()
      } else {
        thisMaterial.hide()
      }
    }
  }
}

// MATERIAL SETTINGS (for choosing between plain text and tabbed data)

function adaptDocBaseVersion(targetString) {
  //var versionRep = (wb.version == '4' || wb.version == '4b') ? (wb.version+'/features/comments') : wb.version;
  //return targetString+'/'+versionRep
  return targetString
}
function adaptDocName() {
  return "0_home"
}

function MSettings(content) {
  var that = this
  var hltext = $("#mtxt_p")
  var hltabbed = $("#mtxt_tb1")
  var legend = $("#datalegend")
  var legendc = $("#datalegend_control")
  this.name = "material_settings"
  this.hid = "#" + this.name
  this.content = content
  this.hebrewsettings = new HebrewSettings()
  hltext.show()
  hltabbed.show()
  legendc.click(function (e) {
    e.preventDefault()
    $("#datalegend")
      .find("a[fname]")
      .each(function () {
        var thisFeaturehost = adaptDocBaseVersion(featurehost)
        var url = thisFeaturehost + "/" + $(this).attr("fname")
        $(this).attr("href", url)
      })
    legend.dialog({
      autoOpen: true,
      dialogClass: "legend",
      closeOnEscape: true,
      modal: false,
      title: "legend",
      width: "600px",
    })
  })
  this.apply = function () {
    var hlradio = $(".mhradio")
    var plradio = $(".mtradio")
    var newTp = wb.vs.tp()
    var newTr = wb.vs.tr()
    var newc = $("#m" + newTp)
    var newp = $("#m" + newTr)
    hlradio.removeClass("ison")
    plradio.removeClass("ison")
    if (newTp != "txt_p" && newTp != "txt_il") {
      for (let i = 1; i <= tabViews; i++) {
        var mc = $("#mtxt_tb" + i)
        if ("txt_tb" + i == newTp) {
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
    legend.hide()
    closeDialog(legend)
    legendc.hide()
    // I forgot why I thought setting the csv exports here was necessary. It is done after filling the sidebars.
    /*
        for (const v in versions) {
            if (versions[v]) {
                setCsv(v, wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
            }
        }
        */
    wb.material.adapt()
  }
  $(".mhradio").click(function (e) {
    e.preventDefault()
    var oldTp = wb.vs.tp()
    var newTp = $(this).attr("id").substring(1)
    if (oldTp == "txt_p") {
      if (oldTp == newTp) {
        return
      }
    } else if (oldTp == newTp) {
      newTp = nextTp[oldTp]
      if (newTp == "txt_p") {
        newTp = nextTp[newTp]
      }
    }

    wb.vs.mstatesv({ tp: newTp })
    wb.vs.addHist()
    that.apply()
  })
  $(".mtradio").click(function (e) {
    e.preventDefault()
    var oldTr = wb.vs.tr()
    var newTr = $(this).attr("id").substring(1)
    if (oldTr == newTr) {
      newTr = nextTr[oldTr]
    }

    wb.vs.mstatesv({ tr: newTr })
    wb.vs.addHist()
    that.apply()
  })
  for (let i = 1; i <= tabViews; i++) {
    var mc = $("#mtxt_tb" + i)
    mc.attr("title", tabInfo["txt_tb" + i])
    if (i == 1) {
      mc.show()
    } else {
      mc.hide()
    }
  }
  for (const l in trLabels) {
    var t = trInfo[l]
    var mc = $("#m" + t)
    mc.attr("title", trLabels[t])
    if (l == "hb") {
      mc.show()
    } else {
      mc.hide()
    }
  }
}

// HEBREW DATA (which fields to show if interlinear text is displayed)

function HebrewSettings() {
  for (const fld in wb.vs.ddata()) {
    this[fld] = new HebrewSetting(fld)
  }
  this.apply = function () {
    for (const fld in wb.vs.ddata()) {
      this[fld].apply()
    }
    for (const v in versions) {
      setCsv(v, wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
    }
  }
}

function HebrewSetting(fld) {
  var that = this
  this.name = fld
  this.hid = "#" + this.name
  $(this.hid).click(function (e) {
    var vals = {}
    vals[fld] = $(this).prop("checked") ? "v" : "x"
    wb.vs.dstatesv(vals)
    wb.vs.addHist()
    that.applysetting()
    for (const v in versions) {
      setCsv(v, wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
    }
  })
  this.apply = function () {
    var val = wb.vs.ddata()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }
  this.applysetting = function () {
    if (wb.vs.ddata()[this.name] == "v") {
      $("." + this.name).each(function () {
        $(this).show()
      })
    } else {
      $("." + this.name).each(function () {
        $(this).hide()
      })
    }
  }
}

// SIDEBARS

/*

The main material kan be two kinds (mr)

m = material: chapters from books
r = query/word results

There are four kinds of sidebars, indicated by two letters, of which the first indicates the mr

mq = list of queries relevant to main material
mw = list of words relevant to main material
rq = display of query record, the main material are the query results
rw = display of word record, the main material are the word results

The list sidebars (m) have a color picker for selecting a uniform highlight color,
plus controls for deciding whether no, uniform, custom, or many colors will be used.

The record-side bars (r) only have a single color picker, for
choosing the color associated with the item (a query or a word).

When items are displayed in the list sidebars, they each have a color picker that
is identical to the one used for that item in the record sidebar.

The colorpickers for choosing an associated item color, consist of a checkbox and a proper colorpicker.
The checkbox indicates whether the color is customized.
A color gets customized when the user selects an other color than the default one, or by checking the box.

When the user has chosen custom colors, all highlights will be done with the uniform color, except
the customized ones.

Queries are highlighted by background color, words by foreground colors.
Although the names for background and foreground colors are identical, their actual values are not.
Foreground colors are darkened, background colors are lightened.
This is done for better visibility.

All color asscociations are preserved in cookies, one for queries, and one for words.
Nowhere else are they stored, but they can be exported as a (lomg) link.
By using the share link, the user can preserve color settings in a notebook, or mail them to colleagues.

*/

function Sidebars() {
  // TOP LEVEL: all four kinds of sidebars
  const mrs = ["m", "r"]
  const qwns = ["q", "w", "n"]

  this.sidebar = {}
  for (const mr of mrs) {
    for (const qw of qwns) {
      this.sidebar[mr + qw] = new Sidebar(mr, qw)
    }
  }
  sideFetched = {}
  this.apply = function () {
    for (const mr of mrs) {
      for (const qw of qwns) {
        this.sidebar[mr + qw].apply()
      }
    }
  }
  this.afterMaterialFetch = function () {
    for (const qw of qwns) {
      sideFetched["m" + qw] = false
    }
  }
  this.afterItemFetch = function () {
    for (const qw of qwns) {
      sideFetched["r" + qw] = false
    }
  }
}

// SPECIFIC sidebars, the [mr][qw] type is frozen into the object

function Sidebar(mr, qw) {
  // the individual sidebar, parametrized with qr and mw to specify one of the four kinds
  var that = this
  this.mr = mr
  this.qw = qw
  this.name = "side_bar_" + mr + qw
  this.hid = "#" + this.name
  var thebar = $(this.hid)
  var thelist = $("#side_material_" + mr + qw)
  var theset = $("#side_settings_" + mr + qw)
  var hide = $("#side_hide_" + mr + qw)
  var show = $("#side_show_" + mr + qw)
  this.content = new SContent(mr, qw)
  this.addVersion = function (v) {
    this.cselect[v] = new CSelect(v, qw)
  }
  if (mr == "r") {
    this.cselect = {}
    for (const v in versions) {
      if (versions[v]) {
        this.addVersion(v)
      }
    }
  }
  this.apply = function () {
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
  show.click(function (e) {
    e.preventDefault()
    wb.vs.hstatesv(that.qw, { get: "v" })
    wb.vs.addHist()
    that.apply()
  })
  hide.click(function (e) {
    e.preventDefault()
    wb.vs.hstatesv(that.qw, { get: "x" })
    wb.vs.addHist()
    that.apply()
  })
}

// SIDELIST MATERIAL

function SContent(mr, qw) {
  // the contents of an individual sidebar
  var that = this
  this.mr = mr
  this.qw = qw
  this.otherMr = this.mr == "m" ? "r" : "m"
  var thebar = $(this.hid)
  var thelist = $("#side_material_" + mr + qw)
  var hide = $("#side_hide_" + mr + qw)
  var show = $("#side_show_" + mr + qw)
  this.name = "side_material_" + mr + qw
  this.hid = "#" + this.name
  this.msg = function (m) {
    $(this.hid).html(m)
  }
  this.setVselect = function (v) {
    if (versions[v]) {
      $("#version_s_" + v).click(function (e) {
        e.preventDefault()
        wb.vs.mstatesv({ version: v })
        wb.go()
      })
    }
  }
  this.process = function () {
    wb.sidebars.afterItemFetch()
    this.sidelistitems()
    if (this.mr == "m") {
      wb.listsettings[this.qw].apply()
    } else {
      for (const ver of versions) {
        if (ver) {
          wb.sidebars.sidebar["r" + this.qw].cselect[v].init()
        }
      }
      var vr = wb.version
      var iid = wb.vs.iid()
      $(".moredetail").click(function (e) {
        e.preventDefault()
        toggleDetail($(this))
      })
      $(".detail").hide()
      $('div[version="' + vr + '"]')
        .find(".detail")
        .show()
      this.msgo = new Msg("dbmsg_" + qw)
      if (qw == "q") {
        this.info = q
        $("#theqid").html(q.id)
        var ufname = escapeHTML(q.ufname || "")
        var ulname = escapeHTML(q.ulname || "")
        var qname = escapeHTML(q.name || "")
        $("#itemtag").val(ufname + " " + ulname + ": " + qname)
        that.msgov = new Msg("dbmsg_qv")
        $("#is_pub_c").show()
        $("#is_pub_ro").hide()
      } else if (qw == "w") {
        this.info = w
        if ("versions" in w) {
          var wvr = w.versions[vr]
          var wentryh = escapeHTML(wvr.entryHeb)
          var wentryid = escapeHTML(wvr.entryid)
          $("#itemtag").val(wentryh + ": " + wentryid)
          $("#gobackw").attr(
            "href",
            wordsUrl +
              "?lan=" +
              wvr.lan +
              "&letter=" +
              wvr.entryHeb.charCodeAt(0) +
              "&goto=" +
              w.id
          )
        }
      } else if (qw == "n") {
        this.info = n
        if ("versions" in n) {
          var ufname = escapeHTML(n.ufname)
          var ulname = escapeHTML(n.ulname)
          var kw = escapeHTML(n.kw)
          var nvr = n.versions[vr]
          $("#itemtag").val(ufname + " " + ulname + ": " + kw)
          $("#gobackn").attr("href", notesUrl + "?goto=" + n.id)
        }
      }
      if ("versions" in this.info) {
        for (const v of this.info.versions) {
          var extra = qw == "w" ? "" : ufname + "_" + ulname
          this.setVselect(v)
          setCsv(v, mr, qw, iid, extra)
        }
      }
      msgs.forEach(function (m) {
        that.msgo.msg(m)
      })
    }

    var thistitle
    if (this.mr == "m") {
      thistitle =
        "[" +
        wb.vs.version() +
        "] " +
        wb.vs.book() +
        " " +
        wb.vs.chapter() +
        ":" +
        wb.vs.verse()
    } else {
      thistitle = $("#itemtag").val()
      $("#theitem").html(thistitle + " ") // fill in the title of the query/word/note above the verse material and put it in the page title as well
    }
    document.title = thistitle

    if (this.qw == "q") {
      if (this.mr == "m") {
        // in the sidebar list of queries: the mql query body can be popped up as a dialog for viewing it in a larger canvas
        $(".fullc").click(function (e) {
          e.preventDefault()
          var thisiid = $(this).attr("iid")
          var mqlq = $("#area_" + thisiid)
          var dia = $("#bigq_" + thisiid).dialog({
            dialogClass: "mql_dialog",
            closeOnEscape: true,
            close: function () {
              dia.dialog("destroy")
              var mqlq = $("#area_" + thisiid)
              mqlq.css("height", mqlSmallHeight)
              mqlq.css("width", mqlSmallWidth)
            },
            modal: false,
            title: "mql query body",
            position: { my: "left top", at: "left top", of: window },
            width: mqlBigWidthDia,
            height: windowHeight,
          })
          mqlq.css("height", standardHeight)
          mqlq.css("width", mqlBigWidth)
        })
      } else {
        // in the sidebar item view of a single query: the mql query body can be popped up as a dialog for viewing it in a larger canvas
        var vr = wb.version
        var fullc = $(".fullc")
        var editq = $("#editq")
        var execq = $("#execq")
        var saveq = $("#saveq")
        var cancq = $("#cancq")
        var doneq = $("#doneq")
        var nameq = $("#nameq")
        var descm = $("#descm")
        var descq = $("#descq")
        var mqlq = $("#mqlq")
        var pube = $("#is_pub_c")
        var pubr = $("#is_pub_ro")
        var isPub = "versions" in q && vr in q.versions && q.versions[vr].isPublished
        fullc.click(function (e) {
          e.preventDefault()
          fullc.hide()
          var dia = $("#bigger")
            .closest("div")
            .dialog({
              dialogClass: "mql_dialog",
              closeOnEscape: true,
              close: function () {
                dia.dialog("destroy")
                mqlq.css("height", mqlSmallHeight)
                descm.removeClass("desc_dia")
                descm.addClass("desc")
                descm.css("height", mqlSmallHeight)
                fullc.show()
              },
              modal: false,
              title: "description and mql query body",
              position: { my: "left top", at: "left top", of: window },
              width: mqlBigWidthDia,
              height: windowHeight,
            })
          mqlq.css("height", halfStandardHeight)
          descm.removeClass("desc")
          descm.addClass("desc_dia")
          descm.css("height", halfStandardHeight)
        })
        $("#is_pub_c").click(function (e) {
          var val = $(this).prop("checked")
          that.sendval(
            q.versions[vr],
            $(this),
            val,
            vr,
            $(this).attr("qid"),
            "is_published",
            val ? "T" : ""
          )
        })
        $("#is_shared_c").click(function (e) {
          var val = $(this).prop("checked")
          that.sendval(
            q,
            $(this),
            val,
            vr,
            $(this).attr("qid"),
            "is_shared",
            val ? "T" : ""
          )
        })
        nameq.hide()
        descq.hide()
        descm.show()
        editq.show()
        if (isPub) {
          execq.hide()
        } else {
          execq.show()
        }
        saveq.hide()
        cancq.hide()
        doneq.hide()
        pube.show()
        pubr.hide()
        editq.click(function (e) {
          e.preventDefault()
          var isPub = q.versions[vr].isPublished
          that.savedName = nameq.val()
          that.savedDesc = descq.val()
          that.savedMql = mqlq.val()
          setEditWidth()
          if (!isPub) {
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
          mqlq.prop("readonly", isPub)
          mqlq.css("height", "20em")
        })
        cancq.click(function (e) {
          e.preventDefault()
          nameq.val(that.savedName)
          descq.val(that.savedDesc)
          mqlq.val(that.savedMql)
          resetMainWidth()
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
        doneq.click(function (e) {
          e.preventDefault()
          resetMainWidth()
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
          var data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          that.sendvals(data)
        })
        saveq.click(function (e) {
          e.preventDefault()
          var data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          that.sendvals(data)
        })
        execq.click(function (e) {
          e.preventDefault()
          execq.addClass("fa-spin")
          var msg = that.msgov
          msg.clear()
          msg.msg(["special", "executing query ..."])
          var data = {
            version: wb.version,
            qid: $("#qid").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: true,
          }
          that.sendvals(data)
        })
      }
    }
  }
  this.setstatus = function (vr, cls) {
    var statq = cls != null ? cls : $("#statq" + vr).attr("class")
    var statm =
      statq == "good"
        ? "results up to date"
        : statq == "error"
        ? "results outdated"
        : "never executed"
    $("#statm").html(statm)
  }
  this.sendval = function (q, checkbx, newval, vr, iid, fname, val) {
    var good = false
    var senddata = {}
    senddata.version = vr
    senddata.qid = iid
    senddata.fname = fname
    senddata.val = val
    $.post(
      fieldUrl,
      senddata,
      function (json) {
        good = json.good
        var modDates = json.mod_dates
        var modCls = json.mod_cls
        if (good) {
          for (var modDateFld in modDates) {
            $("#" + modDateFld).html(modDates[modDateFld])
          }
          for (var modCl in modCls) {
            var cl = modCls[modCl]
            var dest = $(modCl)
            dest.removeClass("fa-check fa-close published")
            dest.addClass(cl)
          }
          q[fname] = newval
        } else {
          checkbx.prop("checked", !newval)
        }
        var extra = json.extra
        for (var fld in extra) {
          var instr = extra[fld]
          var prop = instr[0]
          var val = instr[1]
          if (prop == "check") {
            var dest = $("#" + fld + "_c")
            dest.prop("checked", val)
          } else if (prop == "show") {
            var dest = $("#" + fld)
            if (val) {
              dest.show()
            } else {
              dest.hide()
            }
          }
        }
        var msg = fname == "is_shared" ? that.msgo : that.msgov
        msg.clear()
        json.msgs.forEach(function (m) {
          msg.msg(m)
        })
      },
      "json"
    )
  }
  this.sendvals = function (senddata) {
    var good = false
    var execute = senddata.execute
    var vr = senddata.version
    $.post(
      fieldsUrl,
      senddata,
      function (json) {
        good = json.good
        var q = json.q
        var msg = that.msgov
        msg.clear()
        json.msgs.forEach(function (m) {
          msg.msg(m)
        })
        if (good) {
          var qx = q.versions[vr]
          $("#nameqm").html(escapeHTML(q.name || ""))
          $("#nameq").val(q.name)
          var dMd = specialLinks(q.description_md)
          var descm = $("#descm")
          descm.html(dMd)
          decorateCrossrefs(descm)
          $("#descq").val(q.description)
          $("#mqlq").val(qx.mql)
          var ev = $("#eversion")
          var evtd = ev.closest("td")
          ev.html(qx.eversion)
          if (qx.eversion in json.oldeversions) {
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
          that.setstatus("", qx.status)
          wb.sidebars.sidebar["rq"].content.info = q
        }
        if (execute) {
          resetMaterialStatus()
          wb.material.adapt()
          var showChart = closeDialog(
            $("#select_contents_chart_" + vr + "_q_" + q.id)
          )
          if (showChart) {
            wb.sidebars.sidebar["rq"].cselect[vr].apply()
          }
          $("#execq").removeClass("fa-spin")
        }
      },
      "json"
    )
  }
  this.apply = function () {
    if (wb.mr == this.mr && (this.mr == "r" || wb.vs.get(this.qw) == "v")) {
      this.fetch()
    }
  }
  this.fetch = function () {
    var vars = "?version=" + wb.version + "&mr=" + this.mr + "&qw=" + this.qw
    var doFetch = false
    var extra = ""
    if (this.mr == "m") {
      vars += "&book=" + wb.vs.book()
      vars += "&chapter=" + wb.vs.chapter()
      if (this.qw == "q" || this.qw == "n") {
        vars += "&" + this.qw + "pub=" + wb.vs.pub(this.qw)
      }
      doFetch = wb.vs.book() != "x" && wb.vs.chapter() > 0
      extra = "m"
    } else {
      vars += "&iid=" + wb.iid
      doFetch = wb.qw == "q" ? wb.iid >= 0 : wb.iid != "-1"
      extra = this.qw + "m"
    }
    if (doFetch && !sideFetched[this.mr + this.qw]) {
      this.msg(
        "fetching " + style[this.qw]["tag" + (this.mr == "m" ? "s" : "")] + " ..."
      )
      if (this.mr == "m") {
        thelist.load(
          sideUrl + extra + vars,
          function () {
            sideFetched[that.mr + that.qw] = true
            that.process()
          },
          "html"
        )
      } else {
        $.get(
          sideUrl + extra + vars,
          function (html) {
            thelist.html(html)
            sideFetched[that.mr + that.qw] = true
            that.process()
          },
          "html"
        )
      }
    }
  }
  this.sidelistitems = function () {
    // the list of items in an m-sidebar
    if (this.mr == "m") {
      if (this.qw != "n") {
        wb.picker1list[this.qw] = {}
      }
      var qwlist = $("#side_list_" + this.qw + " li")
      qwlist.each(function () {
        var iid = $(this).attr("iid")
        that.sidelistitem(iid)
        if (that.qw != "n") {
          wb.picker1list[that.qw][iid] = new Colorpicker1(that.qw, iid, false, false)
        }
      })
    }
  }
  this.sidelistitem = function (iid) {
    // individual item in an m-sidebar
    var itop = $("#" + this.qw + iid)
    var more = $("#m_" + this.qw + iid)
    var desc = $("#d_" + this.qw + iid)
    var item = $("#item_" + this.qw + iid)
    var all = $("#" + this.qw + iid)
    desc.hide()
    more.click(function (e) {
      e.preventDefault()
      toggleDetail($(this), desc, that.qw == "q" ? putMarkdown : undefined)
    })
    item.click(function (e) {
      e.preventDefault()
      var qw = that.qw
      wb.vs.mstatesv({ mr: that.otherMr, qw: qw, iid: $(this).attr("iid"), page: 1 })
      wb.vs.addHist()
      wb.go()
    })
    if (this.qw == "w") {
      if (!wb.vs.iscolor(this.qw, iid)) {
        all.hide()
      }
    } else if (this.qw == "q") {
      if (mutingQ.isSet("q" + iid)) {
        itop.hide()
      } else {
        itop.show()
      }
    } else if (this.qw == "n") {
      if (mutingN.isSet("n" + iid)) {
        itop.hide()
      } else {
        itop.show()
      }
    }
  }
  if (this.mr == "r") {
    if (this.qw != "n") {
      wb.picker1[this.qw] = new Colorpicker1(this.qw, null, true, false)
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
      sideFetched["m" + that.qw] = false
      wb.sidebars.sidebar["m" + that.qw].content.apply()
    })
  }
}

function setCsv(vr, mr, qw, iid, extra) {
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
        csvctrl.attr("href", wb.vs.csvUrl(vr, mr, qw, iid, tp, extra))
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
            tpLabels[tp] +
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

function Colorpicker1(qw, iid, isItem, doHighlight) {
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
  this.code = isItem ? "1a" : "1"
  this.qw = qw
  this.iid = iid
  var isItem = isItem
  var pointer = isItem ? "me" : iid
  var stl = style[this.qw]["prop"]
  var sel = $("#sel_" + this.qw + pointer)
  var selw = $("#sel_" + this.qw + pointer + ">a")
  var selc = $("#selc_" + this.qw + pointer)
  var picker = $("#picker_" + this.qw + pointer)

  this.adapt = function (iid, doHighlight) {
    this.iid = iid
    this.apply(doHighlight)
  }
  this.apply = function (doHighlight) {
    var color = wb.vs.color(this.qw, this.iid) || defcolor(this.qw == "q", this.iid)
    var target = this.qw == "q" ? sel : selw
    target.css(stl, vcolors[color][this.qw]) // apply state to the selected cell
    selc.prop("checked", wb.vs.iscolor(this.qw, this.iid)) // apply state to the checkbox
    if (doHighlight) {
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
    var wasCust = wb.vs.iscolor(that.qw, that.iid)
    closeDialog(picker)
    if (wasCust) {
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
    closeDialog(picker)
    var vals = {}
    vals[that.iid] = $(this).html()
    wb.vs.cstatesv(that.qw, vals)
    wb.vs.hstatesv(that.qw, { active: "hlcustom" })
    wb.vs.addHist()
    that.apply(true)
  })
  picker.hide()
  $(".c" + this.qw + "." + this.qw + pointer + ">a").each(function () {
    //initialize the individual color cells in the picker
    var target = that.qw == "q" ? $(this).closest("td") : $(this)
    target.css(stl, vcolors[$(this).html()][that.qw])
  })
  this.apply(doHighlight)
}

function Colorpicker2(qw, doHighlight) {
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

  this.apply = function (doHighlight) {
    var color = wb.vs.selOne(this.qw) || defcolor(this.qw, null)
    var target = this.qw == "q" ? sel : selw
    target.css(stl, vcolors[color][this.qw]) // apply state to the selected cell
    if (doHighlight) {
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
    closeDialog(picker)
    var currentActive = wb.vs.active(that.qw)
    if (currentActive != "hlone" && currentActive != "hlcustom") {
      wb.vs.hstatesv(that.qw, { active: "hlcustom", selOne: $(this).html() })
    } else {
      wb.vs.hstatesv(that.qw, { selOne: $(this).html() })
    }
    wb.vs.addHist()
    that.apply(true)
  })
  picker.hide()
  $(".c" + this.qw + "." + this.qw + "one>a").each(function () {
    //initialize the individual color cells in the picker
    var target = that.qw == "q" ? $(this).closest("td") : $(this)
    target.css(stl, vcolors[$(this).html()][that.qw])
  })
  this.apply(doHighlight)
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
  this.fromPush = false

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
  this.csvUrl = function (vr, mr, qw, iid, tp, extra) {
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
    return itemUrl + vars
  }
  this.goback = function () {
    var state = History.getState()
    if (!that.fromPush && state && state.data) {
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
    that.fromPush = true
    History.pushState(that.data, title, viewUrl)
    that.fromPush = false
  }
  this.apply = function (state, loadIt) {
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
  this.selOne = function (qw) {
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

function closeDialog(dia) {
  var wasOpen = Boolean(
    dia && dia.length && dia.dialog("instance") && dia.dialog("isOpen")
  )
  if (wasOpen) {
    dia.dialog("close")
  }
  return wasOpen
}

function resetMaterialStatus() {
  materialFetched = { txtP: false }
  materialKind = { txtP: "" }
  for (var i = 1; i <= tabViews; i++) {
    materialFetched["txt_tb" + i] = false
    materialKind["txt_tb" + i] = ""
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

function toggleDetail(wdg, detail, extra) {
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

function decorateCrossrefs(dest) {
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

function specialLinks(dMd) {
  var thisFeaturehost = adaptDocBaseVersion(featurehost)
  dMd = dMd.replace(
    /<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)(<\/a>)/g,
    '<br/><img src="$1"/><br/>$2<br/>'
  )
  dMd = dMd.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="$4" href="#" class="fa fw" $5>&#xf100;$6&#xf101;$7'
  )
  dMd = dMd.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="1" href="#" class="fa fw" $4>&#xf100;$5&#xf101;$6'
  )
  dMd = dMd.replace(
    /(href=['"])shebanq:([^)\n\t '"]+)(['"])/g,
    "$1" + host + '$2$3 class="fa fw fa-bookmark" '
  )
  dMd = dMd.replace(
    /(href=['"])feature:([^)\n\t '"]+)(['"])/g,
    "$1" + thisFeaturehost + '/$2$3 target="_blank" class="fa fw fa-file-text" '
  )
  return specialLinksM(dMd)
}

function specialLinksM(ntxt) {
  var thisFeaturehost = adaptDocBaseVersion(featurehost)
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
    '<a target="_blank" href="' + thisFeaturehost + '/$2" class="fa fw">$1&#xf15c;</a>'
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

function putMarkdown(wdg) {
  var did = wdg.attr("did")
  var src = $("#dv_" + did)
  var mdw = $("#dm_" + did)
  mdw.html(specialLinks(markdown.toHTML(src.val())))
}

function Msg(destination, onClear) {
  var that = this
  this.destination = $("#" + destination)
  this.trashc = $("#trash_" + destination)
  this.clear = function () {
    this.destination.html("")
    if (onClear != undefined) {
      onClear()
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
