/* eslint-env jquery */
/* eslint-disable no-new */

/* globals Config, L */

import { escHT } from "./helpers.js"
import { Msg } from "./msg.js"
import { LStorage } from "./page.js"

const vs = $.initNamespaceStorage("viewStoredQueries")
const viewStoredQueries = vs.localStorage
let ftree, msgflt, msgopq, rdata
const subtractForQueriesPage = 80
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */
const controlHeight = 100
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
      html += `<a class="q" query_id="${id}"
          v="${version}" href="#"
          title="${title}">${text}</a><br/>
      `
    }
    target.html(html)
  }

  dress_queriesr() {
    $("#recentqi a[query_id]").each((i, el) => {
      const elem = $(el)
      elem.click(e => {
        e.preventDefault()
        ftree.filter.clear()
        ftree.gotoQuery(elem.attr("query_id"))
      })
    })
  }
}

class View {
  constructor() {
    this.prevstate = false
    if (!viewStoredQueries.isSet("simple")) {
      viewStoredQueries.set("simple", true)
    }
    this.qvradio = $(".qvradio")
    this.csimple = $("#c_view_simple")
    this.cadvanced = $("#c_view_advanced")

    this.csimple.click(e => {
      e.preventDefault()
      viewStoredQueries.set("simple", true)
      this.adjust_view()
    })
    this.cadvanced.click(e => {
      e.preventDefault()
      viewStoredQueries.set("simple", false)
      this.adjust_view()
    })
    this.adjust_view()
  }

  adjust_view() {
    const simple = viewStoredQueries.get("simple")
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
    if (!viewStoredQueries.isSet("level")) {
      viewStoredQueries.set("level", "o")
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
    viewStoredQueries.set("level", level)
    if (level in levels) {
      const numlevel = levels[level]
      ftree.ftw.visit(n => {
        const nlevel = n.getLevel()
        n.setExpanded(nlevel <= numlevel, { noAnimation: true, noEvents: false })
      }, true)
    }
  }

  initlevel() {
    this.expand_level(viewStoredQueries.get("level"))
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
      viewStoredQueries.isSet("filter_pat") ? viewStoredQueries.get("filter_pat") : ""
    )
    if (viewStoredQueries.isSet("filter_mode")) {
      this.pqsearch(viewStoredQueries.get("filter_mode"))
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
    viewStoredQueries.remove("filter_mode")
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
    viewStoredQueries.set("filter_pat", pat)
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
    viewStoredQueries.set("filter_mode", kind)

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
        if (rdata.user_id) {
          tree.editInit()
        } else {
          tree.viewInit()
        }
        tree.bothInit()
        tree.gotoQuery($("#query_id").val())
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

    const standardHeight = window.innerHeight - subtractForQueriesPage
    const canvas_left = $(".left-sidebar")
    const canvas_right = $(".right-sidebar")
    canvas_left.css("height", `${standardHeight}px`)
    $("#queries").css("height", `${standardHeight}px`)
    $("#opqctl").css("height", `${controlHeight}px`)
    canvas_right.css("height", `${standardHeight}px`)
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
    $("#queries a[query_id]").each((i, el) => {
      const elem = $(el)
      const vr = elem.attr("v")
      const extra = vr == undefined ? "" : `&version=${vr}`
      elem.attr("href", `${qUrl}?iid=${elem.attr("query_id")}${extra}&page=1&mr=r&qw=q`)
    })
    $("#queries a.md").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const uname = elem.closest("ul").closest("li").find("span[n]").html()
      const tit = elem.prev()
      const lnk = tit.attr("href")
      const query_name = tit.html()
      window.prompt(
        "Press <Cmd-C> and then <Enter> to copy link on clipboard",
        `[${uname}: ${query_name}](${lnk})`
      )
    })
  }

  record(tp, o, update, view) {
    const { queryMetaUrl, qUrl } = Config

    const obj_id = $(`#id_${tp}`).val()
    if (!update && obj_id == "0" && tp != "q") {
      return
    }
    const senddata = {
      tp,
      upd: update,
      obj_id,
      name: $(`#name_${tp}`).val(),
    }
    if (tp == "q") {
      senddata["org_id"] = $("#org_of_query").attr("org_id")
      senddata["org_name"] = $("#nameq_o").val()
      senddata["org_website"] = $("#websiteq_o").val()
      senddata["project_id"] = $("#project_of_query").attr("project_id")
      senddata["project_name"] = $("#nameq_p").val()
      senddata["project_website"] = $("#websiteq_p").val()
      senddata["do_new_o"] = this.do_new["o"]
      senddata["do_new_p"] = this.do_new["p"]
    } else {
      senddata["website"] = $(`#website_${tp}`).val()
    }

    $.post(
      queryMetaUrl,
      senddata,
      json => {
        const {
          msgs,
          good,
          orgGood,
          projectGood,
          record: rec,
          orgRecord,
          projectRecord,
        } = json
        msgopq.clear()
        for (const m of msgs) {
          msgopq.msg(m)
        }
        if (update && tp == "q") {
          if (good) {
            this.selectId("o", rec.org_id, null)
            this.selectId("p", rec.project_id, o)
          } else {
            if (orgGood) {
              this.selectId("o", orgRecord.id, null)
            }
            if (projectGood) {
              this.selectId("p", projectRecord.id, o)
            }
          }
        }
        if (!update) {
          const name = $(`#name_${tp}`)
          name.prop("readonly", view)
          name.val(rec.name)
          if (tp == "q") {
            const org_name = rec.org_name == undefined ? "" : escHT(rec.org_name)
            const project_name =
              rec.project_name == undefined ? "" : escHT(rec.project_name)
            $("org_of_query").attr("href", rec.org_website)
            $("org_of_query").html(escHT(org_name))
            $("project_of_query").attr("href", rec.project_website)
            $("project_of_query").html(escHT(project_name))
            $("org_of_query").attr("org_id", rec.org_id)
            $("project_of_query").attr("project_id", rec.project_id)
          } else {
            const kind = tp == "o" ? "org" : "project"
            $(`#website_${kind}`).val(rec.website)
            $(`#${kind}_of_query_view`).attr("href", rec.website)
            $(`#${kind}_of_query_view`).html(escHT(rec.name))
          }
        } else if (update && senddata.obj_id != "0") {
          if (tp == "q") {
            if (good) {
              const org_name = rec.org_name == undefined ? "" : escHT(rec.org_name)
              const project_name =
                rec.project_name == undefined ? "" : escHT(rec.project_name)
              this.hideQueryNew(rec.id, "o")
              this.hideQueryNew(rec.id, "p")
              $("org_of_query").attr("href", rec.org_website)
              $("org_of_query").html(escHT(org_name))
              $("project_of_query").attr("href", rec.project_website)
              $("project_of_query").html(escHT(project_name))
              $("org_of_query").attr("org_id", rec.org_id)
              $("project_of_query").attr("project_id", rec.project_id)
              $("#title_q").html("Modify")
            } else {
              if (orgGood) {
                const org_name =
                  orgRecord.name == undefined ? "" : escHT(orgRecord.name)
                this.hideQueryNew(orgRecord.id, "o")
                $("org_of_query").attr("href", orgRecord.website)
                $("org_of_query").html(escHT(org_name))
                $("org_of_query").attr("org_id", orgRecord.id)
              }
              if (projectGood) {
                const project_name =
                  projectRecord.name == undefined ? "" : escHT(projectRecord.name)
                this.hideQueryNew(projectRecord.id, "p")
                $("project_of_query").attr("href", projectRecord.website)
                $("project_of_query").html(escHT(project_name))
                $("project_of_query").attr("project_id", projectRecord.id)
              }
            }
          } else {
            const kind = tp == "o" ? "org" : "project"
            $(`#website_${kind}`).val(rec.website)
            $(`#${kind}_of_query_view`).attr("href", rec.website)
            $(`#${kind}_of_query_view`).html(escHT(rec.name))
          }
          const elm = tp == "q" ? "a" : "span"
          const moditem = this.moditem.find(`${elm}[n=1]`)
          if (moditem != undefined) {
            moditem.html(escHT(rec.name))
          }
        } else if (update && senddata.obj_id == "0") {
          if (good) {
            $(`#id_${tp}`).val(rec.id)
          }
          if (tp == "q") {
            if (good) {
              const org_name = rec.org_name == undefined ? "" : escHT(rec.org_name)
              const project_name =
                rec.project_name == undefined ? "" : escHT(rec.project_name)
              this.hideQueryNew(rec.id, "o")
              this.hideQueryNew(rec.id, "p")
              $("org_of_query").attr("href", rec.org_website)
              $("org_of_query").html(escHT(org_name))
              $("project_of_query").attr("href", rec.project_website)
              $("project_of_query").html(escHT(project_name))
              $("org_of_query").attr("org_id", rec.org_id)
              $("project_of_query").attr("project_id", rec.project_id)
              $("#title_q").html("Modify")
            } else {
              if (orgGood) {
                const org_name =
                  orgRecord.name == undefined ? "" : escHT(orgRecord.name)
                this.hideQueryNew(orgRecord.id, "o")
                $("org_of_query").attr("href", orgRecord.website)
                $("org_of_query").html(escHT(org_name))
                $("org_of_query").attr("org_id", orgRecord.id)
              }
              if (projectGood) {
                const project_name =
                  projectRecord.name == undefined ? "" : escHT(projectRecord.name)
                this.hideQueryNew(projectRecord.id, "p")
                $("project_of_query").attr("href", projectRecord.website)
                $("project_of_query").html(escHT(project_name))
                $("project_of_query").attr("project_id", projectRecord.id)
              }
            }
          }
        }
        const orig = $(".treehl")
        const origp = orig.closest("ul").closest("li").closest("ul").closest("li")
        const origo = origp.closest("ul").closest("li")
        const origoid = origo.find("a[obj_id]").attr("obj_id")
        const origpid = origp.find("a[obj_id]").attr("obj_id")
        if (
          update &&
          good &&
          (senddata.obj_id == "0" || origoid != rec.org_id || origpid != rec.project_id)
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

  doEditControlsQuery() {
    const orgNewCtl = $("#org_new_ctl")
    const projectNewCtl = $("#project_new_ctl")
    const orgExistCtl = $("#org_exist_ctl")
    const projectExistCtl = $("#project_exist_ctl")
    const orgDetail = $(".org_detail")
    const projectDetail = $(".project_detail")
    const orgOfQuery = $("#org_of_query")
    const projectOfQuery = $("#project_of_query")
    orgDetail.hide()
    projectDetail.hide()
    orgExistCtl.hide()
    projectExistCtl.hide()
    orgNewCtl.click(e => {
      e.preventDefault()
      orgDetail.show()
      orgExistCtl.show()
      orgNewCtl.hide()
      orgOfQuery.hide()
      this.do_new["o"] = true
    })
    orgExistCtl.click(e => {
      e.preventDefault()
      orgDetail.hide()
      orgExistCtl.hide()
      orgNewCtl.show()
      orgOfQuery.show()
      this.do_new["o"] = false
    })
    projectNewCtl.click(e => {
      e.preventDefault()
      projectDetail.show()
      projectExistCtl.show()
      projectNewCtl.hide()
      projectOfQuery.hide()
      this.do_new["p"] = true
      this.select_clear("p", true)
    })
    projectExistCtl.click(e => {
      e.preventDefault()
      projectDetail.hide()
      projectExistCtl.hide()
      projectNewCtl.show()
      projectOfQuery.show()
    })
  }

  hideQueryNew(obj_id, tp) {
    const kind = tp == "o" ? "org" : "project"
    $(`#${kind}_new_ctl`).show()
    $(`#${kind}_exist_ctl`).hide()
    $(`.${kind}_detail`).hide()
    $(`#${kind}_of_query`).show()
    this.do_new[tp] = false
  }

  doViewControlsQuery() {
    const orgNewCtl = $("#org_new_ctl")
    const projectNewCtl = $("#project_new_ctl")
    const orgExistCtl = $("#org_exist_ctl")
    const projectExistCtl = $("#project_exist_ctl")
    const orgDetail = $(".org_detail")
    const projectDetail = $(".project_detail")
    orgDetail.hide()
    projectDetail.hide()
    orgNewCtl.hide()
    orgExistCtl.hide()
    projectNewCtl.hide()
    projectExistCtl.hide()
  }

  doCreate(tp, obj) {
    msgopq.clear()
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("New")
    $(`#name_${tp}`).val("")
    let o = null
    if (tp == "q") {
      this.do_new["o"] = false
      this.do_new["p"] = false
      $("#org_of_query").attr("org_id", 0)
      $("#project_of_query").attr("project_id", 0)
      this.doEditControlsQuery()
    } else {
      const kind = tp == "o" ? "org" : "project"
      $(`#website_${kind}`).val("")
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

  do_update(tp, obj, obj_id) {
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
      this.doEditControlsQuery()
    } else if (tp == "p") {
      o = obj.closest("ul").closest("li")
    }
    this.moditem = obj.closest("span")
    msgopq.clear()
    msgopq.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("Modify")
    $(`#id_${tp}`).val(obj_id)
    this.record(tp, o, false, false)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    $(`#ctl_${tp}`).show()
    $(".old").show()
  }

  do_view(tp, obj, obj_id) {
    let o = null
    if (tp == "q") {
      o = obj
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
      this.doViewControlsQuery()
    } else if (tp == "p") {
      o = obj.closest("ul").closest("li")
    }
    msgopq.clear()
    msgopq.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("View")
    $(`#id_${tp}`).val(obj_id)
    this.record(tp, o, false, true)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    if (tp == "o" || tp == "p") {
      const kind = tp == "o" ? "org" : "project"
      $(`#nameline_${kind}`).hide()
      $(`#website_${kind}`).hide()
      $(`#${kind}_of_query_view`).show()
    }
    this.selectHide()
  }

  op_selection(tp) {
    if (tp == "q") {
      this.select_clear("o", true)
      this.select_clear("p", true)
    } else {
      this.selectHide()
    }
  }

  selectHide() {
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

  selectId(tp, obj_id, pr) {
    const jpr = `.s_${tp}[obj_id=${obj_id}]`
    const icon = pr == null ? $(jpr) : pr.find(jpr)
    const i = icon.closest("li")
    const is = i.children("span")
    this.selectOne(tp, icon, is)
  }

  selectOne(tp, icon, obj) {
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

  viewInit() {
    $("#lmsg").show()
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(".treehl").removeClass("treehl")
    this.selectHide()
  }

  bothInit() {
    const canvas_left = $(".left-sidebar")
    const canvasMiddle = $(".span6")
    const canvas_right = $(".right-sidebar")
    canvas_left.css("width", "23%")
    canvasMiddle.css("width", "40%")
    canvas_right.css("width", "30%")
    const view = $(".v_o, .v_p, .v_q")
    view.addClass("fa fa-info")

    const viewTp = tp => {
      const objs = $(`.v_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.op_selection(tp)
        elem.closest("span").addClass("treehl")
        const obj_id = $(this).attr("obj_id")
        this.do_view(tp, $(this), obj_id)
        return false
      })
    }

    const selectInit = tp => {
      const objs = $(`.s_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        if (tp == "o") {
          const o = elem.closest("li")
          const org_id = o.find("a[obj_id]").attr("obj_id")
          const org_name = o.find("span[n=1]").html()
          $("#org_of_query").html(org_name)
          $("#org_of_query").attr("org_id", org_id)
          this.selectId("o", org_id, null)
        } else if (tp == "p") {
          const o = elem.closest("ul").closest("li")
          const org_id = o.find("a[obj_id]").attr("obj_id")
          const org_name = o.find("span[n=1]").html()
          const p = elem.closest("li")
          const project_id = p.find("a[obj_id]").attr("obj_id")
          const project_name = p.find("span[n=1]").html()
          $("#org_of_query").html(org_name)
          $("#project_of_query").html(project_name)
          $("#org_of_query").attr("org_id", org_id)
          $("#project_of_query").attr("project_id", project_id)
          this.selectId("o", org_id, null)
          this.selectId("p", project_id, o)
        }
        return false
      })
    }
    for (const t in this.tps) {
      $(`#form_${t}`).hide()
      $(`#ctl_${t}`).hide()
      viewTp(t)
      if (t == "q") {
        selectInit("o")
        selectInit("p")
      }
    }
  }

  editInit() {
    $(".treehl").removeClass("treehl")
    $("#lmsg").hide()
    const select = $(".s_o,.s_p")
    select.addClass("fa-circle-o")
    select.hide()
    const create = $(".n_q")
    create.addClass("fa fa-plus")

    const createTp = tp => {
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
        this.doCreate(tp, elem)
        return false
      })
    }
    const update = $(".r_o, .r_p, .r_q")
    update.addClass("fa fa-pencil")

    const updateTp = tp => {
      const objs = $(`.r_${tp}`)
      objs.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.op_selection(tp)
        elem.closest("span").addClass("treehl")
        const obj_id = elem.attr("obj_id")
        if (tp == "q") {
          $("#id_q").val(obj_id)
        }
        this.do_update(tp, elem, obj_id)
        return false
      })
    }
    const formTp = tp => {
      $(`#save_${tp}`).click(e => {
        e.preventDefault()
        this.op_selection(tp)
        this.record(tp, null, true, false)
      })
      $(`#cancel_${tp}`).click(e => {
        e.preventDefault()
        $(".treehl").removeClass("treehl")
        this.selectHide()
        $(`#form_${tp}`).hide()
        $(`#ctl_${tp}`).hide()
      })
      $(`#done_${tp}`).click(e => {
        e.preventDefault()
        this.op_selection(tp)
        this.record(tp, null, true, false)
        this.selectHide()
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
      createTp(t)
      updateTp(t)
      formTp(t)
    }
  }

  gotoQuery(query_id) {
    if (query_id != undefined && query_id != "0") {
      const qnode = this.ftw.getNodeByKey(`${query_id}`)
      if (qnode != undefined) {
        qnode.makeVisible({ noAnimation: true })
        $(".treehl").removeClass("treehl")
        $(`a[query_id=${query_id}]`).closest("span").addClass("treehl")
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
