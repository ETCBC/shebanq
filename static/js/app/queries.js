/* eslint-env jquery */
/* eslint-disable no-new */

/* globals Config, L */

import { escHT } from "./helpers.js"
import { Msg } from "./msg.js"
import { LStorage } from "./page.js"

const vs = $.initNamespaceStorage("qsview")
const qsview = vs.localStorage
let ftree, msgflt, msgopq, rdata
const subtractq = 80
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */
const control_height = 100
/* height for messages and controls
 */

class Recent {
  constructor() {
    this.loaded = false
    this.queries = []
    this.msgqr = new Msg("msg_qr")
    this.refreshctl = $("#reload_recentq")

    this.msgqr.clear()
    this.refreshctl.click(e => {
      e.preventDefault()
      this.fetch()
    })
    this.apply()
  }

  apply() {
    this.fetch()
  }

  fetch() {
    const { queriesrUrl } = Config

    this.msgqr.msg(["info", "fetching recent queries ..."])
    $.post(queriesrUrl, {}, json => {
      this.loaded = true
      this.msgqr.clear()
      const { msgs, good, queries } = json
      for (const m of msgs) {
        this.msgqr.msg(m)
      }
      if (good) {
        this.queries = queries
        this.process()
      }
    })
  }
  process() {
    this.gen_html()
    this.dress_queriesr()
  }
  gen_html() {
    const target = $("#recentqi")
    const { queries } = this
    let html = ""
    for (let n = 0; n < queries.length; n++) {
      const { id, text, title, version } = queries[n]
      html += `<a class="q" qid="${id}"
          v="${version}" href="#"
          title="${title}">${text}</a><br/>
      `
    }
    target.html(html)
  }

  dress_queriesr() {
    $("#recentqi a[qid]").each((i, el) => {
      const elem = $(el)
      elem.click(e => {
        e.preventDefault()
        ftree.filter.clear()
        ftree.gotoquery(elem.attr("qid"))
      })
    })
  }
}

class View {
  constructor() {
    this.prevstate = false
    if (!qsview.isSet("simple")) {
      qsview.set("simple", true)
    }
    this.qvradio = $(".qvradio")
    this.csimple = $("#c_view_simple")
    this.cadvanced = $("#c_view_advanced")

    this.csimple.click(e => {
      e.preventDefault()
      qsview.set("simple", true)
      this.adjust_view()
    })
    this.cadvanced.click(e => {
      e.preventDefault()
      qsview.set("simple", false)
      this.adjust_view()
    })
    this.adjust_view()
  }

  adjust_view() {
    const simple = qsview.get("simple")
    this.qvradio.removeClass("ison")
    ;(simple ? this.csimple : this.cadvanced).addClass("ison")
    if (this.prevstate != simple) {
      if (simple) {
        $(".brq").hide()
      } else {
        $(".brq").show()
      }
      this.prevstate = simple
    }
  }
}

class Level {
  constructor() {
    this.levels = { o: 1, p: 2, u: 3, q: 4 }

    $(".qlradio").removeClass("ison")
    if (!qsview.isSet("level")) {
      qsview.set("level", "o")
    }
    $("#level_o").click(e => {
      e.preventDefault()
      this.expand_level("o")
    })
    $("#level_p").click(e => {
      e.preventDefault()
      this.expand_level("p")
    })
    $("#level_u").click(e => {
      e.preventDefault()
      this.expand_level("u")
    })
    $("#level_q").click(e => {
      e.preventDefault()
      this.expand_level("q")
    })
    $("#level_").click(e => {
      e.preventDefault()
      this.expand_level("")
    })
  }

  expand_all() {
    ftree.ftw.visit(n => {
      n.setExpanded(true, { noAnimation: true, noEvents: false })
    }, true)
  }

  expand_level(level) {
    const { levels } = this

    $(".qlradio").removeClass("ison")
    $(`#level_${level}`).addClass("ison")
    qsview.set("level", level)
    if (level in levels) {
      const numlevel = levels[level]
      ftree.ftw.visit(n => {
        const nlevel = n.getLevel()
        n.setExpanded(nlevel <= numlevel, { noAnimation: true, noEvents: false })
      }, true)
    }
  }

  initlevel() {
    this.expand_level(qsview.get("level"))
  }
}

class Filter {
  constructor() {
    this.patc = $("#filter_contents")

    const re_is_my = new RegExp('class="[^"]*qmy', "")
    const re_is_private = new RegExp('class="[^"]*qpriv', "")

    this.in_my = pat => node =>
      re_is_my.test(node.title) &&
      (pat == "" || node.title.toLowerCase().indexOf(pat.toLowerCase()) >= 0)

    this.in_private = pat => node =>
      re_is_private.test(node.title) &&
      (pat == "" || node.title.toLowerCase().indexOf(pat.toLowerCase()) >= 0)

    $("#filter_clear").hide()
    $("#filter_contents").val(
      qsview.isSet("filter_pat") ? qsview.get("filter_pat") : ""
    )
    if (qsview.isSet("filter_mode")) {
      this.pqsearch(qsview.get("filter_mode"))
      $("#filter_clear").show()
    }

    $("#filter_control_a").click(e => {
      e.preventDefault()
      this.pqsearch("a")
    })
    $("#filter_control_c").click(e => {
      e.preventDefault()
      this.pqsearch("c")
    })
    $("#filter_control_q").click(e => {
      e.preventDefault()
      this.pqsearch("q")
    })
    $("#filter_control_m").click(e => {
      e.preventDefault()
      this.pqsearch("m")
    })
    $("#filter_control_r").click(e => {
      e.preventDefault()
      this.pqsearch("r")
    })

    $("#filter_clear").click(e => {
      e.preventDefault()
      this.clear()
    })
  }

  clear() {
    ftree.ftw.clearFilter()
    msgflt.clear()
    msgflt.msg(["good", "no filter applied"])
    $(".qfradio").removeClass("ison")
    qsview.remove("filter_mode")
    $("#filter_clear").hide()
    $("#allmatches").html("")
    $("#branchmatches").html("")
    $("#querymatches").html("")
    $("#mymatches").html("")
    $("#privatematches").html("")
    $("#count_o").html(rdata.o)
    $("#count_p").html(rdata.p)
    $("#count_u").html(rdata.u)
    $("#count_q").html(rdata.q)
  }

  pqsearch(kind) {
    const { in_my, in_private, patc } = this
    const pat = patc.val()
    qsview.set("filter_pat", pat)
    let allMatches = 0
    let branchMatches = 0
    let queryMatches = 0
    let myMatches = 0
    let privateMatches = 0
    if (pat == "") {
      allMatches = -1
      branchMatches = -1
      queryMatches = -1
      myMatches = -1
      privateMatches = -1
    }
    $(".qfradio").removeClass("ison")
    if (kind == "m") {
      msgflt.clear()
      msgflt.msg(["warning", "my queries"])
    } else if (kind == "r") {
      msgflt.clear()
      msgflt.msg(["warning", "private queries"])
    } else if (pat == "") {
      this.clear()
      return
    } else {
      msgflt.clear()
      msgflt.msg(["special", "filter applied"])
    }
    $(`#filter_control_${kind}`).addClass("ison")
    qsview.set("filter_mode", kind)

    ftree.level.expand_all()
    if (kind == "a") {
      allMatches = ftree.ftw.filterNodes(pat, false)
      $("#allmatches").html(allMatches >= 0 ? `(${allMatches})` : "")
    } else if (kind == "c") {
      branchMatches = ftree.ftw.filterBranches(pat)
      $("#branchmatches").html(branchMatches >= 0 ? `(${branchMatches})` : "")
    } else if (kind == "q") {
      queryMatches = ftree.ftw.filterNodes(pat, true)
      $("#querymatches").html(queryMatches >= 0 ? `(${queryMatches})` : "")
    } else if (kind == "m") {
      myMatches = ftree.ftw.filterNodes(in_my(pat), true)
      $("#mymatches").html(myMatches >= 0 ? `(${myMatches})` : "")
    } else if (kind == "r") {
      privateMatches = ftree.ftw.filterNodes(in_private(pat), true)
      $("#privatematches").html(privateMatches >= 0 ? `(${privateMatches})` : "")
    }
    $("#filter_clear").show()
    const submatch = "span.fancytree-submatch"
    const match = "span.fancytree-match"
    const base_o = "#queries>ul>li>ul>li>"
    const match_o = $(`${base_o}${match}`).length
    const submatch_o = $(`${base_o}${submatch}`).length
    const base_p = `${base_o}ul>li>`
    const match_p = $(`${base_p}${match}`).length
    const submatch_p = $(`${base_p}${submatch}`).length
    const base_u = `${base_p}ul>li>`
    const match_u = $(`${base_u}${match}`).length
    const submatch_u = $(`${base_u}${submatch}`).length
    const base_q = `${base_u}ul>li>`
    const match_q = $(`${base_q}${match}`).length
    $("#count_o").html(`
      <span class="match">${match_o}</span>
      <span class="brq submatch">${submatch_o}</span>`)
    $("#count_p").html(`
      <span class="match">${match_p}</span>
      <span class="brq submatch">${submatch_p}</span>`)
    $("#count_u").html(`
      '<span class="match">${match_u}</span>
      <span class="brq submatch">${submatch_u}</span>`)
    $("#count_q").html(`<span class="match">${match_q}</span>`)
    if (ftree.view.simple) {
      $(".brq").hide()
    }
  }
}

class Tree {
  constructor() {
    const { pqUrl } = Config
    const { muting_q: muting } = L

    this.tps = { o: "organization", p: "project", q: "query" }

    const tree = this

    this.do_new = {}

    $("#queries").fancytree({
      extensions: ["persist", "filter"],
      checkbox: true,
      selectMode: 3,
      activeVisible: true,
      toggleEffect: false,
      clickFolderMode: 2,
      focusOnSelect: false,
      quicksearch: true,
      icons: false,
      idPrefix: "q_",
      persist: {
        cookiePrefix: "ft-q-",
        store: "local",
        types: "expanded selected",
      },
      source: {
        url: pqUrl,
        dataType: "json",
      },
      filter: {
        mode: "hide",
      },
      init: () => {
        muting.removeAll()
        tree.ftw = $("#queries").fancytree("getTree")
        const s = tree.ftw.getSelectedNodes(true)
        for (const i in s) {
          tree.store_select_deep(s[i])
        }
        tree.ftw.render(true, true)
        tree.dress_queries()
        rdata = tree.ftw.rootNode.children[0].data
        $("#count_o").html(rdata.o)
        $("#count_p").html(rdata.p)
        $("#count_u").html(rdata.u)
        $("#count_q").html(rdata.q)
        msgopq = new Msg("opqmsgs")
        msgflt = new Msg("filter_msg")
        tree.view = new View()
        tree.level = new Level()
        tree.filter = new Filter()
        tree.level.initlevel()
        if (rdata.uid) {
          tree.editinit()
        } else {
          tree.viewinit()
        }
        tree.bothinit()
        tree.gotoquery($("#qid").val())
        $("#reload_tree").hide()
      },
      expand: () => {
        if (tree.level != undefined) {
          tree.level.expand_level("")
        }
      },
      collapse: () => {
        if (tree.level != undefined) {
          tree.level.expand_level("")
        }
      },
      select: (e, data) => {
        tree.store_select_deep(data.node)
      },
    })

    const standard_height = window.innerHeight - subtractq
    const canvas_left = $(".left-sidebar")
    const canvas_right = $(".right-sidebar")
    canvas_left.css("height", `${standard_height}px`)
    $("#queries").css("height", `${standard_height}px`)
    $("#opqctl").css("height", `${control_height}px`)
    canvas_right.css("height", `${standard_height}px`)
  }

  store_select(node) {
    const { muting_q: muting } = L
    const { folder, key: iid, selected } = node
    if (!folder) {
      if (selected) {
        muting.set(iid, 1)
      } else {
        if (muting.isSet(iid)) {
          muting.remove(iid)
        }
      }
    }
  }

  store_select_deep(node) {
    const { children } = node
    this.store_select(node)
    if (children != null) {
      for (const n in children) {
        this.store_select_deep(children[n])
      }
    }
  }

  dress_queries() {
    const { qUrl } = Config
    $("#queries a.md").addClass("fa fa-level-down")
    $("#queries a[qid]").each((i, el) => {
      const elem = $(el)
      const vr = elem.attr("v")
      const extra = vr == undefined ? "" : `&version=${vr}`
      elem.attr("href", `${qUrl}?iid=${elem.attr("qid")}${extra}&page=1&mr=r&qw=q`)
    })
    $("#queries a.md").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const uname = elem.closest("ul").closest("li").find("span[n]").html()
      const tit = elem.prev()
      const lnk = tit.attr("href")
      const qname = tit.html()
      window.prompt(
        "Press <Cmd-C> and then <Enter> to copy link on clipboard",
        `[${uname}: ${qname}](${lnk})`
      )
    })
  }

  record(tp, o, update, view) {
    const { recordUrl, qUrl } = Config

    const lid = $(`#id_${tp}`).val()
    if (!update && lid == "0" && tp != "q") {
      return
    }
    const senddata = {
      tp,
      upd: update,
      lid,
      name: $(`#name_${tp}`).val(),
    }
    if (tp == "q") {
      senddata["oid"] = $("#fo_q").attr("oid")
      senddata["oname"] = $("#nameq_o").val()
      senddata["owebsite"] = $("#websiteq_o").val()
      senddata["pid"] = $("#fp_q").attr("pid")
      senddata["pname"] = $("#nameq_p").val()
      senddata["pwebsite"] = $("#websiteq_p").val()
      senddata["do_new_o"] = this.do_new["o"]
      senddata["do_new_p"] = this.do_new["p"]
    } else {
      senddata["website"] = $(`#website_${tp}`).val()
    }

    $.post(
      recordUrl,
      senddata,
      json => {
        const {
          msgs,
          good,
          ogood,
          pgood,
          record: rec,
          orecord: orec,
          precord: prec,
        } = json
        msgopq.clear()
        for (const m of msgs) {
          msgopq.msg(m)
        }
        if (update && tp == "q") {
          if (good) {
            this.selectid("o", rec.oid, null)
            this.selectid("p", rec.pid, o)
          } else {
            if (ogood) {
              this.selectid("o", orec.id, null)
            }
            if (pgood) {
              this.selectid("p", prec.id, o)
            }
          }
        }
        if (!update) {
          const name = $(`#name_${tp}`)
          name.prop("readonly", view)
          name.val(rec.name)
          if (tp == "q") {
            const oname = rec.oname == undefined ? "" : escHT(rec.oname)
            const pname = rec.pname == undefined ? "" : escHT(rec.pname)
            $(`#fo_${tp}`).attr("href", rec.owebsite)
            $(`#fo_${tp}`).html(escHT(oname))
            $(`#fp_${tp}`).attr("href", rec.pwebsite)
            $(`#fp_${tp}`).html(escHT(pname))
            $(`#fo_${tp}`).attr("oid", rec.oid)
            $(`#fp_${tp}`).attr("pid", rec.pid)
          } else {
            $(`#website_${tp}`).val(rec.website)
            $(`#f${tp}_v`).attr("href", rec.owebsite)
            $(`#f${tp}_v`).html(escHT(rec.name))
          }
        } else if (update && senddata.lid != "0") {
          if (tp == "q") {
            if (good) {
              const oname = rec.oname == undefined ? "" : escHT(rec.oname)
              const pname = rec.pname == undefined ? "" : escHT(rec.pname)
              this.hide_new_q(rec.id, "o")
              this.hide_new_q(rec.id, "p")
              $(`#fo_${tp}`).attr("href", rec.owebsite)
              $(`#fo_${tp}`).html(escHT(oname))
              $(`#fp_${tp}`).attr("href", rec.pwebsite)
              $(`#fp_${tp}`).html(escHT(pname))
              $(`#fo_${tp}`).attr("oid", rec.oid)
              $(`#fp_${tp}`).attr("pid", rec.pid)
              $("#title_q").html("Modify")
            } else {
              if (ogood) {
                const oname = orec.name == undefined ? "" : escHT(orec.name)
                this.hide_new_q(orec.id, "o")
                $(`#fo_${tp}`).attr("href", orec.website)
                $(`#fo_${tp}`).html(escHT(oname))
                $(`#fo_${tp}`).attr("oid", orec.id)
              }
              if (pgood) {
                const pname = prec.name == undefined ? "" : escHT(prec.name)
                this.hide_new_q(prec.id, "p")
                $(`#fp_${tp}`).attr("href", prec.website)
                $(`#fp_${tp}`).html(escHT(pname))
                $(`#fp_${tp}`).attr("pid", prec.id)
              }
            }
          } else {
            $(`#website_${tp}`).val(rec.website)
            $(`#f${tp}_v`).attr("href", rec.owebsite)
            $(`#f${tp}_v`).html(escHT(rec.name))
          }
          const elm = tp == "q" ? "a" : "span"
          const moditem = this.moditem.find(`${elm}[n=1]`)
          if (moditem != undefined) {
            moditem.html(escHT(rec.name))
          }
        } else if (update && senddata.lid == "0") {
          if (good) {
            $(`#id_${tp}`).val(rec.id)
          }
          if (tp == "q") {
            if (good) {
              const oname = rec.oname == undefined ? "" : escHT(rec.oname)
              const pname = rec.pname == undefined ? "" : escHT(rec.pname)
              this.hide_new_q(rec.id, "o")
              this.hide_new_q(rec.id, "p")
              $(`#fo_${tp}`).attr("href", rec.owebsite)
              $(`#fo_${tp}`).html(escHT(oname))
              $(`#fp_${tp}`).attr("href", rec.pwebsite)
              $(`#fp_${tp}`).html(escHT(pname))
              $(`#fo_${tp}`).attr("oid", rec.oid)
              $(`#fp_${tp}`).attr("pid", rec.pid)
              $("#title_q").html("Modify")
            } else {
              if (ogood) {
                const oname = orec.name == undefined ? "" : escHT(orec.name)
                this.hide_new_q(orec.id, "o")
                $(`#fo_${tp}`).attr("href", orec.website)
                $(`#fo_${tp}`).html(escHT(oname))
                $(`#fo_${tp}`).attr("oid", orec.id)
              }
              if (pgood) {
                const pname = prec.name == undefined ? "" : escHT(prec.name)
                this.hide_new_q(prec.id, "p")
                $(`#fp_${tp}`).attr("href", prec.website)
                $(`#fp_${tp}`).html(escHT(pname))
                $(`#fp_${tp}`).attr("pid", prec.id)
              }
            }
          }
        }
        const orig = $(".treehl")
        const origp = orig.closest("ul").closest("li").closest("ul").closest("li")
        const origo = origp.closest("ul").closest("li")
        const origoid = origo.find("a[lid]").attr("lid")
        const origpid = origp.find("a[lid]").attr("lid")
        if (
          update &&
          good &&
          (senddata.lid == "0" || origoid != rec.oid || origpid != rec.pid)
        ) {
          $("#reload_tree").show()
        } else {
          $("#reload_tree").hide()
        }
        if (update && good && tp == "q") {
          $("#continue_q").attr(
            "href",
            `${qUrl}?iid=${$("#id_q").val()}&page=1&mr=r&qw=q`
          )
          $("#continue_q").show()
        } else {
          $("#continue_q").hide()
        }
      },
      "json"
    )
  }

  do_edit_controls_q() {
    const ctlo = $("#new_ctl_o")
    const ctlp = $("#new_ctl_p")
    const ctlxo = $("#newx_ctl_o")
    const ctlxp = $("#newx_ctl_p")
    const detailo = $(".detail_o")
    const detailp = $(".detail_p")
    const existo = $("#fo_q")
    const existp = $("#fp_q")
    detailo.hide()
    detailp.hide()
    ctlxo.hide()
    ctlxp.hide()
    ctlo.click(e => {
      e.preventDefault()
      detailo.show()
      ctlxo.show()
      ctlo.hide()
      existo.hide()
      this.do_new["o"] = true
    })
    ctlxo.click(e => {
      e.preventDefault()
      detailo.hide()
      ctlxo.hide()
      ctlo.show()
      existo.show()
      this.do_new["o"] = false
    })
    ctlp.click(e => {
      e.preventDefault()
      detailp.show()
      ctlxp.show()
      ctlp.hide()
      existp.hide()
      this.do_new["p"] = true
      this.select_clear("p", true)
    })
    ctlxp.click(e => {
      e.preventDefault()
      detailp.hide()
      ctlxp.hide()
      ctlp.show()
      existp.show()
    })
  }

  hide_new_q(lid, tp) {
    $(`#new_ctl_${tp}`).show()
    $(`#newx_ctl_${tp}`).hide()
    $(`.detail_${tp}`).hide()
    $(`#f${tp}_q`).show()
    this.do_new[tp] = false
  }

  do_view_controls_q() {
    const ctlo = $("#new_ctl_o")
    const ctlp = $("#new_ctl_p")
    const ctlxo = $("#newx_ctl_o")
    const ctlxp = $("#newx_ctl_p")
    const detailo = $(".detail_o")
    const detailp = $(".detail_p")
    detailo.hide()
    detailp.hide()
    ctlo.hide()
    ctlxo.hide()
    ctlp.hide()
    ctlxp.hide()
  }

  do_create(tp, obj) {
    msgopq.clear()
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("New")
    $(`#name_${tp}`).val("")
    let o = null
    if (tp == "q") {
      this.do_new["o"] = false
      this.do_new["p"] = false
      $("#fo_q").attr("oid", 0)
      $("#fp_q").attr("pid", 0)
      this.do_edit_controls_q()
    } else {
      $(`#website_${tp}`).val("")
      if (tp == "p") {
        o = obj.closest("li")
      }
    }
    $(`#id_${tp}`).val(0)
    this.record(tp, o, false, false)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    $(`#ctl_${tp}`).show()
    $(".old").hide()
  }

  do_update(tp, obj, lid) {
    let o = null
    if (tp == "q") {
      this.do_new["o"] = false
      this.do_new["p"] = false
      o = obj
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
      this.do_edit_controls_q()
    } else if (tp == "p") {
      o = obj.closest("ul").closest("li")
    }
    this.moditem = obj.closest("span")
    msgopq.clear()
    msgopq.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("Modify")
    $(`#id_${tp}`).val(lid)
    this.record(tp, o, false, false)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    $(`#ctl_${tp}`).show()
    $(".old").show()
  }

  do_view(tp, obj, lid) {
    let o = null
    if (tp == "q") {
      o = obj
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
      this.do_view_controls_q()
    } else if (tp == "p") {
      o = obj.closest("ul").closest("li")
    }
    msgopq.clear()
    msgopq.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("View")
    $(`#id_${tp}`).val(lid)
    this.record(tp, o, false, true)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    if (tp == "o" || tp == "p") {
      $(`#nameline_${tp}`).hide()
      $(`#website_${tp}`).hide()
      $(`#f${tp}_v`).show()
    }
    this.select_hide()
  }

  op_selection(tp) {
    if (tp == "q") {
      this.select_clear("o", true)
      this.select_clear("p", true)
    } else {
      this.select_hide()
    }
  }

  select_hide() {
    for (const tp of ["o", "p"]) {
      this.select_clear(tp, false)
    }
  }

  select_clear(tp, show) {
    const objs = $(`.selecthl${tp}`)
    const icons = $(`.s_${tp}`)
    objs.removeClass(`selecthl${tp}`)
    icons.removeClass("fa-check-circle")
    icons.addClass("fa-circle-o")
    if (show) {
      icons.show()
    } else {
      icons.hide()
    }
  }

  selectid(tp, lid, pr) {
    const jpr = `.s_${tp}[lid=${lid}]`
    const icon = pr == null ? $(jpr) : pr.find(jpr)
    const i = icon.closest("li")
    const is = i.children("span")
    this.selectone(tp, icon, is)
  }

  selectone(tp, icon, obj) {
    const sclass = `selecthl${tp}`
    const objs = $(`.${sclass}`)
    const iconsr = $(`.s_${tp}`)
    objs.removeClass(sclass)
    obj.addClass(sclass)
    iconsr.removeClass("fa-check-circle")
    iconsr.addClass("fa-circle-o")
    icon.removeClass("fa-circle-o")
    icon.addClass("fa-check-circle")
  }

  viewinit() {
    $("#lmsg").show()
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(".treehl").removeClass("treehl")
    this.select_hide()
  }

  bothinit() {
    const canvas_left = $(".left-sidebar")
    const canvas_middle = $(".span6")
    const canvas_right = $(".right-sidebar")
    canvas_left.css("width", "23%")
    canvas_middle.css("width", "40%")
    canvas_right.css("width", "30%")
    const view = $(".v_o, .v_p, .v_q")
    view.addClass("fa fa-info")

    const viewtp = tp => {
      const objs = $(`.v_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.op_selection(tp)
        elem.closest("span").addClass("treehl")
        const lid = $(this).attr("lid")
        this.do_view(tp, $(this), lid)
        return false
      })
    }

    const select_init = tp => {
      const objs = $(`.s_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        if (tp == "o") {
          const o = elem.closest("li")
          const oid = o.find("a[lid]").attr("lid")
          const oname = o.find("span[n=1]").html()
          $("#fo_q").html(oname)
          $("#fo_q").attr("oid", oid)
          this.selectid("o", oid, null)
        } else if (tp == "p") {
          const o = elem.closest("ul").closest("li")
          const oid = o.find("a[lid]").attr("lid")
          const oname = o.find("span[n=1]").html()
          const p = elem.closest("li")
          const pid = p.find("a[lid]").attr("lid")
          const pname = p.find("span[n=1]").html()
          $("#fo_q").html(oname)
          $("#fp_q").html(pname)
          $("#fo_q").attr("oid", oid)
          $("#fp_q").attr("pid", pid)
          this.selectid("o", oid, null)
          this.selectid("p", pid, o)
        }
        return false
      })
    }
    for (const t in this.tps) {
      $(`#form_${t}`).hide()
      $(`#ctl_${t}`).hide()
      viewtp(t)
      if (t == "q") {
        select_init("o")
        select_init("p")
      }
    }
  }

  editinit() {
    $(".treehl").removeClass("treehl")
    $("#lmsg").hide()
    const select = $(".s_o,.s_p")
    select.addClass("fa-circle-o")
    select.hide()
    const create = $(".n_q")
    create.addClass("fa fa-plus")

    const createtp = tp => {
      const objs = $(`.n_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.op_selection(tp)
        if (tp == "q") {
          $("#id_q").val(0)
        }
        elem.closest("span").addClass("treehl")
        this.do_create(tp, elem)
        return false
      })
    }
    const update = $(".r_o, .r_p, .r_q")
    update.addClass("fa fa-pencil")

    const updatetp = tp => {
      const objs = $(`.r_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.op_selection(tp)
        elem.closest("span").addClass("treehl")
        const lid = elem.attr("lid")
        if (tp == "q") {
          $("#id_q").val(lid)
        }
        this.do_update(tp, elem, lid)
        return false
      })
    }
    const formtp = tp => {
      $(`#save_${tp}`).click(e => {
        e.preventDefault()
        this.op_selection(tp)
        this.record(tp, null, true, false)
      })
      $(`#cancel_${tp}`).click(e => {
        e.preventDefault()
        $(".treehl").removeClass("treehl")
        this.select_hide()
        $(`#form_${tp}`).hide()
        $(`#ctl_${tp}`).hide()
      })
      $(`#done_${tp}`).click(e => {
        e.preventDefault()
        this.op_selection(tp)
        this.record(tp, null, true, false)
        this.select_hide()
        $(`#form_${tp}`).hide()
        $(`#ctl_${tp}`).hide()
      })
      $("#reload_tree").click(e => {
        e.preventDefault()
        window.location.reload(true)
      })
    }
    for (const t in this.tps) {
      $(`#form_${t}`).hide()
      $(`#ctl_${t}`).hide()
      createtp(t)
      updatetp(t)
      formtp(t)
    }
  }

  gotoquery(queryId) {
    if (queryId != undefined && queryId != "0") {
      const qnode = this.ftw.getNodeByKey(`q${queryId}`)
      if (qnode != undefined) {
        qnode.makeVisible({ noAnimation: true })
        $(".treehl").removeClass("treehl")
        $(`a[qid=${queryId}]`).closest("span").addClass("treehl")
        $(qnode.li)[0].scrollIntoView({
          behavior: "smooth",
        })
        $("#queries").scrollTop -= 20
      }
    }
  }
}

$(() => {
  window.L = new LStorage()
  new Recent()
  ftree = new Tree()
})
