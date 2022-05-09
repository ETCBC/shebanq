/* eslint-env jquery */
/* eslint-disable no-new */

/**
 * @module querytree
 */

/* globals Config, LS */

import { LStorage } from "./localstorage.js"
import { escHT, idPrefixQueries } from "./helpers.js"
import { Diagnostics } from "./diagnostics.js"
import { QueryRecent } from "./queryrecent.js"

let treeObj, diagnostics, diagnosticsTree, rootData

/**
 * the canvas holding the material gets a height equal to
 * the window height minus this amount
 */
const subtractForQueriesPage = 80
/**
 * height for messages and controls
 */
const controlHeight = 100

/**
 * Advanced or simple view of the tree of queries.
 * In advanced views there are more sophisticated counts.
 */
class View {
  constructor() {
    const { lsQueries } = LS
    this.statePrev = false
    if (!lsQueries.isSet("simple")) {
      lsQueries.set("simple", true)
    }
    this.simpleOrAdvancedRadio = $(".qvradio")
    this.simpleCtl = $("#c_view_simple")
    this.advancedCtl = $("#c_view_advanced")

    this.simpleCtl.off("click").click(e => {
      e.preventDefault()
      lsQueries.set("simple", true)
      this.adjustView()
    })
    this.advancedCtl.off("click").click(e => {
      e.preventDefault()
      lsQueries.set("simple", false)
      this.adjustView()
    })
    this.adjustView()
  }

  adjustView() {
    const { lsQueries } = LS
    const simple = lsQueries.get("simple")
    this.simpleOrAdvancedRadio.removeClass("ison")
    ;(simple ? this.simpleCtl : this.advancedCtl).addClass("ison")
    if (this.statePrev != simple) {
      if (simple) {
        $(".brq").hide()
      } else {
        $(".brq").show()
      }
      this.statePrev = simple
    }
  }
}

/**
 * The tree can be shown at different levels:
 *
 * *   organization
 * *   project
 * *   user
 * *   query
 */
class Level {
  constructor() {
    const { lsQueries } = LS
    this.levels = { o: 1, p: 2, u: 3, q: 4 }

    $(".qlradio").removeClass("ison")
    if (!lsQueries.isSet("level")) {
      lsQueries.set("level", "o")
    }
    $("#level_o").off("click").click(e => {
      e.preventDefault()
      this.expandLevel("o")
    })
    $("#level_p").off("click").click(e => {
      e.preventDefault()
      this.expandLevel("p")
    })
    $("#level_u").off("click").click(e => {
      e.preventDefault()
      this.expandLevel("u")
    })
    $("#level_q").off("click").click(e => {
      e.preventDefault()
      this.expandLevel("q")
    })
    $("#level_").off("click").click(e => {
      e.preventDefault()
      this.expandLevel("")
    })
  }

  expandAll() {
    treeObj.widget.visit(n => {
      n.setExpanded(true, { noAnimation: true, noEvents: false })
    }, true)
  }

  expandLevel(level) {
    const { lsQueries } = LS
    const { levels } = this

    $(".qlradio").removeClass("ison")
    $(`#level_${level}`).addClass("ison")
    lsQueries.set("level", level)
    if (level in levels) {
      const nLevel = levels[level]
      treeObj.widget.visit(node => {
        const nodelevel = node.getLevel()
        node.setExpanded(nodelevel <= nLevel, { noAnimation: true, noEvents: false })
      }, true)
    }
  }

  initLevel() {
    const { lsQueries } = LS
    this.expandLevel(lsQueries.get("level"))
  }
}

/**
 * The tree can be filtered.
 *
 * This is a full text search on the texts of the nodes.
 */
class Filter {
  constructor() {
    const { lsQueries } = LS
    this.patternCtl = $("#filter_contents")

    const isMyRe = new RegExp('class="[^"]*qmy', "")
    const isPrivateRe = new RegExp('class="[^"]*qpriv', "")

    this.isMy = pattern => node =>
      isMyRe.test(node.title) &&
      (pattern == "" || node.title.toLowerCase().indexOf(pattern.toLowerCase()) >= 0)

    this.isPrivate = pattern => node =>
      isPrivateRe.test(node.title) &&
      (pattern == "" || node.title.toLowerCase().indexOf(pattern.toLowerCase()) >= 0)

    $("#filter_clear").hide()
    $("#filter_contents").val(
      lsQueries.isSet("filter_pat") ? lsQueries.get("filter_pat") : ""
    )
    if (lsQueries.isSet("filter_mode")) {
      this.search(lsQueries.get("filter_mode"))
      $("#filter_clear").show()
    }

    $("#filter_control_a").off("click").click(e => {
      e.preventDefault()
      this.search("a")
    })
    $("#filter_control_c").off("click").click(e => {
      e.preventDefault()
      this.search("c")
    })
    $("#filter_control_q").off("click").click(e => {
      e.preventDefault()
      this.search("q")
    })
    $("#filter_control_m").off("click").click(e => {
      e.preventDefault()
      this.search("m")
    })
    $("#filter_control_r").off("click").click(e => {
      e.preventDefault()
      this.search("r")
    })

    $("#filter_clear").off("click").click(e => {
      e.preventDefault()
      this.clear()
    })
  }

  clear() {
    const { lsQueries } = LS
    treeObj.widget.clearFilter()
    diagnostics.clear()
    diagnostics.msg(["good", "no filter applied"])
    $(".qfradio").removeClass("ison")
    lsQueries.remove("filter_mode")
    $("#filter_clear").hide()
    $("#allmatches").html("")
    $("#branchmatches").html("")
    $("#querymatches").html("")
    $("#mymatches").html("")
    $("#privatematches").html("")
    $("#count_o").html(rootData.o)
    $("#count_p").html(rootData.p)
    $("#count_u").html(rootData.u)
    $("#count_q").html(rootData.q)
  }

  search(kind) {
    const { lsQueries } = LS
    const { isMy, isPrivate, patternCtl } = this
    const pattern = patternCtl.val()
    lsQueries.set("filter_pat", pattern)
    let allMatches = 0
    let branchMatches = 0
    let queryMatches = 0
    let myMatches = 0
    let privateMatches = 0
    if (pattern == "") {
      allMatches = -1
      branchMatches = -1
      queryMatches = -1
      myMatches = -1
      privateMatches = -1
    }
    $(".qfradio").removeClass("ison")
    if (kind == "m") {
      diagnostics.clear()
      diagnostics.msg(["warning", "my queries"])
    } else if (kind == "r") {
      diagnostics.clear()
      diagnostics.msg(["warning", "private queries"])
    } else if (pattern == "") {
      this.clear()
      return
    } else {
      diagnostics.clear()
      diagnostics.msg(["special", "filter applied"])
    }
    $(`#filter_control_${kind}`).addClass("ison")
    lsQueries.set("filter_mode", kind)

    treeObj.level.expandAll()
    if (kind == "a") {
      allMatches = treeObj.widget.filterNodes(pattern, false)
      $("#allmatches").html(allMatches >= 0 ? `(${allMatches})` : "")
    } else if (kind == "c") {
      branchMatches = treeObj.widget.filterBranches(pattern)
      $("#branchmatches").html(branchMatches >= 0 ? `(${branchMatches})` : "")
    } else if (kind == "q") {
      queryMatches = treeObj.widget.filterNodes(pattern, true)
      $("#querymatches").html(queryMatches >= 0 ? `(${queryMatches})` : "")
    } else if (kind == "m") {
      myMatches = treeObj.widget.filterNodes(isMy(pattern), true)
      $("#mymatches").html(myMatches >= 0 ? `(${myMatches})` : "")
    } else if (kind == "r") {
      privateMatches = treeObj.widget.filterNodes(isPrivate(pattern), true)
      $("#privatematches").html(privateMatches >= 0 ? `(${privateMatches})` : "")
    }
    $("#filter_clear").show()
    const submatch = "span.fancytree-submatch"
    const match = "span.fancytree-match"
    const baseOrg = "#queries>ul>li>ul>li>"
    const matchOrg = $(`${baseOrg}${match}`).length
    const submatchOrg = $(`${baseOrg}${submatch}`).length
    const baseProject = `${baseOrg}ul>li>`
    const matchProject = $(`${baseProject}${match}`).length
    const submatchProject = $(`${baseProject}${submatch}`).length
    const baseUser = `${baseProject}ul>li>`
    const matchUser = $(`${baseUser}${match}`).length
    const submatchUser = $(`${baseUser}${submatch}`).length
    const base_q = `${baseUser}ul>li>`
    const match_q = $(`${base_q}${match}`).length
    $("#count_o").html(`
      <span class="match">${matchOrg}</span>
      <span class="brq submatch">${submatchOrg}</span>`)
    $("#count_p").html(`
      <span class="match">${matchProject}</span>
      <span class="brq submatch">${submatchProject}</span>`)
    $("#count_u").html(`
      '<span class="match">${matchUser}</span>
      <span class="brq submatch">${submatchUser}</span>`)
    $("#count_q").html(`<span class="match">${match_q}</span>`)
    if (treeObj.view.simple) {
      $(".brq").hide()
    }
  }
}

/**
 * Handles the tree of queries
 */
class Tree {
  /**
   * Initializes the query tree
   *
   * Stores a url to fetch content from the server.
   *
   * @see Triggers [C:hebrew.querytree][controllers.hebrew.querytree]
   */
  constructor() {
    const { queryTreeJsonUrl } = Config
    const { lsQueriesMuted: lsMuted } = LS

    this.tps = { o: "organization", p: "project", q: "query" }

    const tree = this

    this.doNew = {}

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
      idPrefix: idPrefixQueries,
      persist: {
        cookiePrefix: "ft-q-",
        store: "local",
        types: "expanded selected",
      },
      source: {
        url: queryTreeJsonUrl,
        dataType: "json",
      },
      filter: {
        mode: "hide",
      },
      init: () => {
        lsMuted.removeAll()
        tree.widget = $("#queries").fancytree("getTree")
        const s = tree.widget.getSelectedNodes(true)
        for (const node of s) {
          tree.storeSelectDeep(node)
        }
        tree.widget.render(true, true)
        tree.dressQueries()
        rootData = tree.widget.rootNode.children[0].data
        $("#count_o").html(rootData.o)
        $("#count_p").html(rootData.p)
        $("#count_u").html(rootData.u)
        $("#count_q").html(rootData.q)
        diagnosticsTree = new Diagnostics("opqmsgs")
        diagnostics = new Diagnostics("filter_msg")
        tree.view = new View()
        tree.level = new Level()
        tree.filter = new Filter()
        tree.level.initLevel()
        if (rootData.user_id) {
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
          tree.level.expandLevel("")
        }
      },
      collapse: () => {
        if (tree.level != undefined) {
          tree.level.expandLevel("")
        }
      },
      select: (e, data) => {
        tree.storeSelectDeep(data.node)
      },
    })

    const standardHeight = window.innerHeight - subtractForQueriesPage
    const canvasLeft = $(".left-sidebar")
    const canvasRight = $(".right-sidebar")
    canvasLeft.css("height", `${standardHeight}px`)
    $("#queries").css("height", `${standardHeight}px`)
    $("#opqctl").css("height", `${controlHeight}px`)
    canvasRight.css("height", `${standardHeight}px`)
  }

  storeSelect(node) {
    const { lsQueriesMuted: lsMuted } = LS
    const { folder, key, selected } = node
    if (!folder) {
      if (selected) {
        lsMuted.set(key, 1)
      } else {
        if (lsMuted.isSet(key)) {
          lsMuted.remove(key)
        }
      }
    }
  }

  storeSelectDeep(node) {
    const { children } = node
    this.storeSelect(node)
    if (children != null) {
      for (const child of children) {
        this.storeSelectDeep(child)
      }
    }
  }

  dressQueries() {
    const { pageUrl } = Config
    $("#queries a.md").addClass("fa fa-level-down")
    $("#queries a[query_id]").each((i, el) => {
      const elem = $(el)
      const vr = elem.attr("v")
      const extra = vr == undefined ? "" : `&version=${vr}`
      elem.attr(
        "href",
        `${pageUrl}?iid=${elem.attr("query_id")}${extra}&page=1&mr=r&qw=q`
      )
    })
    $("#queries a.md").off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const userName = elem.closest("ul").closest("li").find("span[n]").html()
      const tit = elem.prev()
      const lnk = tit.attr("href")
      const query_name = tit.html()
      window.prompt(
        "Press <Cmd-C> and then <Enter> to copy link on clipboard",
        `[${userName}: ${query_name}](${lnk})`
      )
    })
  }

  /**
   * Sends a record to the database to be saved
   *
   * @see Triggers [C:hebrew.itemrecord][controllers.hebrew.itemrecord]
   */
  record(tp, o, update, view) {
    const { itemRecordJsonUrl, pageUrl } = Config

    const obj_id = $(`#id_${tp}`).val()
    if (!update && obj_id == "0" && tp != "q") {
      return
    }
    const sendData = {
      tp,
      upd: update,
      obj_id,
      name: $(`#name_${tp}`).val(),
    }
    if (tp == "q") {
      sendData["org_id"] = $("#org_of_query").attr("org_id")
      sendData["org_name"] = $("#nameq_o").val()
      sendData["org_website"] = $("#websiteq_o").val()
      sendData["project_id"] = $("#project_of_query").attr("project_id")
      sendData["project_name"] = $("#nameq_p").val()
      sendData["project_website"] = $("#websiteq_p").val()
      sendData["doNewOrg"] = this.doNew["o"]
      sendData["doNewProject"] = this.doNew["p"]
    } else {
      sendData["website"] = $(`#website_${tp}`).val()
    }

    $.post(
      itemRecordJsonUrl,
      sendData,
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
        diagnosticsTree.clear()
        for (const mg of msgs) {
          diagnosticsTree.msg(mg)
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
        } else if (update && sendData.obj_id != "0") {
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
          const itemMod = this.itemMod.find(`${elm}[n=1]`)
          if (itemMod != undefined) {
            itemMod.html(escHT(rec.name))
          }
        } else if (update && sendData.obj_id == "0") {
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
        const projectOrig = orig.closest("ul").closest("li").closest("ul").closest("li")
        const orgOrig = projectOrig.closest("ul").closest("li")
        const orgOrigId = orgOrig.find("a[obj_id]").attr("obj_id")
        const projectOrigId = projectOrig.find("a[obj_id]").attr("obj_id")
        if (
          update &&
          good &&
          (sendData.obj_id == "0" ||
            orgOrigId != rec.org_id ||
            projectOrigId != rec.project_id)
        ) {
          $("#reload_tree").show()
        } else {
          $("#reload_tree").hide()
        }
        if (update && good && tp == "q") {
          $("#continue_q").attr(
            "href",
            `${pageUrl}?iid=${$("#id_q").val()}&page=1&mr=r&qw=q`
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
    orgNewCtl.off("click").click(e => {
      e.preventDefault()
      orgDetail.show()
      orgExistCtl.show()
      orgNewCtl.hide()
      orgOfQuery.hide()
      this.doNew["o"] = true
    })
    orgExistCtl.off("click").click(e => {
      e.preventDefault()
      orgDetail.hide()
      orgExistCtl.hide()
      orgNewCtl.show()
      orgOfQuery.show()
      this.doNew["o"] = false
    })
    projectNewCtl.off("click").click(e => {
      e.preventDefault()
      projectDetail.show()
      projectExistCtl.show()
      projectNewCtl.hide()
      projectOfQuery.hide()
      this.doNew["p"] = true
      this.selectClear("p", true)
    })
    projectExistCtl.off("click").click(e => {
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
    this.doNew[tp] = false
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
    diagnosticsTree.clear()
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("New")
    $(`#name_${tp}`).val("")
    let elem = null
    if (tp == "q") {
      this.doNew["o"] = false
      this.doNew["p"] = false
      $("#org_of_query").attr("org_id", 0)
      $("#project_of_query").attr("project_id", 0)
      this.doEditControlsQuery()
    } else {
      const kind = tp == "o" ? "org" : "project"
      $(`#website_${kind}`).val("")
      if (tp == "p") {
        elem = obj.closest("li")
      }
    }
    $(`#id_${tp}`).val(0)
    this.record(tp, elem, false, false)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    $(`#ctl_${tp}`).show()
    $(".old").hide()
  }

  doUpdate(tp, obj, obj_id) {
    let elem = null
    if (tp == "q") {
      this.doNew["o"] = false
      this.doNew["p"] = false
      elem = obj
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
      this.doEditControlsQuery()
    } else if (tp == "p") {
      elem = obj.closest("ul").closest("li")
    }
    this.itemMod = obj.closest("span")
    diagnosticsTree.clear()
    diagnosticsTree.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("Modify")
    $(`#id_${tp}`).val(obj_id)
    this.record(tp, elem, false, false)
    $("#opqforms").show()
    $("#opqctl").show()
    $(`#form_${tp}`).show()
    $(`#ctl_${tp}`).show()
    $(".old").show()
  }

  doView(tp, obj, obj_id) {
    let elem = null
    if (tp == "q") {
      elem = obj
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
        .closest("ul")
        .closest("li")
      this.doViewControlsQuery()
    } else if (tp == "p") {
      elem = obj.closest("ul").closest("li")
    }
    diagnosticsTree.clear()
    diagnosticsTree.msg(["info", "loading ..."])
    $(".formquery").hide()
    $(".ctlquery").hide()
    $(`#title_${tp}`).html("View")
    $(`#id_${tp}`).val(obj_id)
    this.record(tp, elem, false, true)
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

  orgProjectSelect(tp) {
    if (tp == "q") {
      this.selectClear("o", true)
      this.selectClear("p", true)
    } else {
      this.selectHide()
    }
  }

  selectHide() {
    for (const tp of ["o", "p"]) {
      this.selectClear(tp, false)
    }
  }

  selectClear(tp, show) {
    const objects = $(`.selecthl${tp}`)
    const icons = $(`.s_${tp}`)
    objects.removeClass(`selecthl${tp}`)
    icons.removeClass("fa-check-circle")
    icons.addClass("fa-circle-o")
    if (show) {
      icons.show()
    } else {
      icons.hide()
    }
  }

  selectId(tp, obj_id, above) {
    const parentJquery = `.s_${tp}[obj_id=${obj_id}]`
    const icon = above == null ? $(parentJquery) : above.find(parentJquery)
    const i = icon.closest("li")
    const is = i.children("span")
    this.selectOne(tp, icon, is)
  }

  selectOne(tp, icon, obj) {
    const selectCls = `selecthl${tp}`
    const selectedObjects = $(`.${selectCls}`)
    const iconsr = $(`.s_${tp}`)
    selectedObjects.removeClass(selectCls)
    obj.addClass(selectCls)
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
    const canvasLeft = $(".left-sidebar")
    const canvasMiddle = $(".span6")
    const canvasRight = $(".right-sidebar")
    canvasLeft.css("width", "23%")
    canvasMiddle.css("width", "40%")
    canvasRight.css("width", "30%")
    const view = $(".v_o, .v_p, .v_q")
    view.addClass("fa fa-info")

    const viewTp = tp => {
      const objects = $(`.v_${tp}`)
      objects.off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.orgProjectSelect(tp)
        elem.closest("span").addClass("treehl")
        const obj_id = $(elem).attr("obj_id")
        this.doView(tp, $(elem), obj_id)
        return false
      })
    }

    const selectInit = tp => {
      const objects = $(`.s_${tp}`)
      objects.off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        if (tp == "o") {
          const org = elem.closest("li")
          const org_id = org.find("a[obj_id]").attr("obj_id")
          const org_name = org.find("span[n=1]").html()
          $("#org_of_query").html(org_name)
          $("#org_of_query").attr("org_id", org_id)
          this.selectId("o", org_id, null)
        } else if (tp == "p") {
          const org = elem.closest("ul").closest("li")
          const org_id = org.find("a[obj_id]").attr("obj_id")
          const org_name = org.find("span[n=1]").html()
          const project = elem.closest("li")
          const project_id = project.find("a[obj_id]").attr("obj_id")
          const project_name = project.find("span[n=1]").html()
          $("#org_of_query").html(org_name)
          $("#project_of_query").html(project_name)
          $("#org_of_query").attr("org_id", org_id)
          $("#project_of_query").attr("project_id", project_id)
          this.selectId("o", org_id, null)
          this.selectId("p", project_id, org)
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
      const objects = $(`.n_${tp}`)
      objects.off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.orgProjectSelect(tp)
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
      const objects = $(`.r_${tp}`)
      objects.off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        $(".treehl").removeClass("treehl")
        this.orgProjectSelect(tp)
        elem.closest("span").addClass("treehl")
        const obj_id = elem.attr("obj_id")
        if (tp == "q") {
          $("#id_q").val(obj_id)
        }
        this.doUpdate(tp, elem, obj_id)
        return false
      })
    }
    const formTp = tp => {
      $(`#save_${tp}`).off("click").click(e => {
        e.preventDefault()
        this.orgProjectSelect(tp)
        this.record(tp, null, true, false)
      })
      $(`#cancel_${tp}`).off("click").click(e => {
        e.preventDefault()
        $(".treehl").removeClass("treehl")
        this.selectHide()
        $(`#form_${tp}`).hide()
        $(`#ctl_${tp}`).hide()
      })
      $(`#done_${tp}`).off("click").click(e => {
        e.preventDefault()
        this.orgProjectSelect(tp)
        this.record(tp, null, true, false)
        this.selectHide()
        $(`#form_${tp}`).hide()
        $(`#ctl_${tp}`).hide()
      })
      $("#reload_tree").off("click").click(e => {
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
    if (query_id != null && query_id != "0") {
      const queryNode = this.widget.getNodeByKey(`${idPrefixQueries}${query_id}`)
      if (queryNode != undefined) {
        queryNode.makeVisible({ noAnimation: true })
        $(".treehl").removeClass("treehl")
        $(`a[query_id=${query_id}]`).closest("span").addClass("treehl")
        $(queryNode.li)[0].scrollIntoView({
          behavior: "smooth",
        })
        $("#queries").scrollTop -= 20
      }
    }
  }
}

$(() => {
  window.LS = new LStorage()
  treeObj = new Tree()
  new QueryRecent(treeObj)
})
