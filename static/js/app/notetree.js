/* eslint-env jquery */
/* eslint-disable no-new */

/* globals Config, LS */

import { LStorage } from "./localstorage.js"
import { Diagnostics } from "./diagnostics.js"

let treeObj, diagnostics, rootData
const subtractForNotesPage = 80
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */

class View {
  constructor() {
    const { lsNotes } = LS
    this.statePrev = false
    if (!lsNotes.isSet("simple")) {
      lsNotes.set("simple", true)
    }
    this.simpleOrAdvancedRadio = $(".nvradio")
    this.simpleCtl = $("#c_view_simple")
    this.advancedCtl = $("#c_view_advanced")

    this.simpleCtl.click(e => {
      e.preventDefault()
      lsNotes.set("simple", true)
      this.adjustView()
    })

    this.advancedCtl.click(e => {
      e.preventDefault()
      lsNotes.set("simple", false)
      this.adjustView()
    })
    this.adjustView()
  }

  adjustView() {
    const { lsNotes } = LS
    const simple = lsNotes.get("simple")
    this.simpleOrAdvancedRadio.removeClass("ison")
    ;(simple ? this.simpleCtl : this.advancedCtl).addClass("ison")
    if (this.statePrev != simple) {
      if (simple) {
        $(".brn").hide()
      } else {
        $(".brn").show()
      }
      this.statePrev = simple
    }
  }
}

class Level {
  constructor() {
    const { lsNotes } = LS
    this.levels = { u: 1, n: 2 }

    $(".nlradio").removeClass("ison")
    if (!lsNotes.isSet("level")) {
      lsNotes.set("level", "u")
    }
    $("#level_u").click(e => {
      e.preventDefault()
      this.expandLevel("u")
    })
    $("#level_n").click(e => {
      e.preventDefault()
      this.expandLevel("n")
    })
    $("#level_").click(e => {
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
    const { lsNotes } = LS
    const { levels } = this

    $(".nlradio").removeClass("ison")
    $(`#level_${level}`).addClass("ison")
    lsNotes.set("level", level)
    if (level in levels) {
      const nLevel = levels[level]
      treeObj.widget.visit(node => {
        const nodelevel = node.getLevel()
        node.setExpanded(nodelevel <= nLevel, { noAnimation: true, noEvents: false })
      }, true)
    }
  }

  initLevel() {
    const { lsNotes } = LS
    this.expandLevel(lsNotes.get("level"))
  }
}

class Filter {
  constructor() {
    const { lsNotes } = LS
    this.patternCtl = $("#filter_contents")

    $("#filter_clear").hide()
    $("#filter_contents").val(
      lsNotes.isSet("filter_pat") ? lsNotes.get("filter_pat") : ""
    )
    if (lsNotes.isSet("filter_mode")) {
      this.search(lsNotes.get("filter_mode"))
      $("#filter_clear").show()
    }

    $("#filter_control_a").click(e => {
      e.preventDefault()
      this.search("a")
    })
    $("#filter_control_c").click(e => {
      e.preventDefault()
      this.search("c")
    })
    $("#filter_control_n").click(e => {
      e.preventDefault()
      this.search("q")
    })
    $("#filter_clear").click(e => {
      e.preventDefault()
      this.clear()
    })
  }

  clear() {
    const { lsNotes } = LS
    treeObj.widget.clearFilter()
    diagnostics.clear()
    diagnostics.msg(["good", "no filter applied"])
    $(".nfradio").removeClass("ison")
    lsNotes.remove("filter_mode")
    $("#filter_clear").hide()
    $("#allmatches").html("")
    $("#branchmatches").html("")
    $("#notematches").html("")
    $("#count_u").html(rootData.u)
    $("#count_n").html(rootData.n)
  }

  search(kind) {
    const { lsNotes } = LS
    const pattern = this.patternCtl.val()
    lsNotes.set("filter_pat", pattern)
    let allMatches = 0
    let branchMatches = 0
    let noteMatches = 0
    if (pattern == "") {
      allMatches = -1
      branchMatches = -1
      noteMatches = -1
    }
    $(".nfradio").removeClass("ison")
    if (pattern == "") {
      this.clear()
      return
    } else {
      diagnostics.clear()
      diagnostics.msg(["special", "filter applied"])
    }
    $(`#filter_control_${kind}`).addClass("ison")
    lsNotes.set("filter_mode", kind)

    treeObj.level.expandAll()
    if (kind == "a") {
      allMatches = treeObj.widget.filterNodes(pattern, false)
      $("#allmatches").html(allMatches >= 0 ? `(${allMatches})` : "")
    } else if (kind == "c") {
      branchMatches = treeObj.widget.filterBranches(pattern)
      $("#branchmatches").html(branchMatches >= 0 ? `(${branchMatches})` : "")
    } else if (kind == "n") {
      noteMatches = treeObj.widget.filterNodes(pattern, true)
      $("#notematches").html(noteMatches >= 0 ? `(${noteMatches})` : "")
    }
    $("#filter_clear").show()
    const submatch = "span.fancytree-submatch"
    const match = "span.fancytree-match"
    const baseUser = "#notes>ul>li>ul>li>"
    const matchUser = $(`${baseUser}${match}`).length
    const submatchUser = $(`${baseUser}${submatch}`).length
    const baseNote = `${baseUser}ul>li>`
    const matchNote = $(`${baseNote}${match}`).length
    $("#count_u").html(`
      <span class="match">${matchUser}</span>
      <span class="brn submatch">${submatchUser}</span>`)
    $("#count_n").html(`<span class="match">${matchNote}</span>`)
    if (treeObj.view.simple) {
      $(".brn").hide()
    }
  }
}

class Tree {
  constructor() {
    const { noteTreeJsonUrl } = Config
    const { lsNotesMuted: lsMuted } = LS

    this.tps = { u: "user", n: "note" }

    const tree = this

    $("#notes").fancytree({
      extensions: ["persist", "filter"],
      checkbox: true,
      selectMode: 3,
      activeVisible: true,
      toggleEffect: false,
      clickFolderMode: 2,
      focusOnSelect: false,
      quicksearch: true,
      icons: false,
      persist: {
        cookiePrefix: "ft-n-",
        store: "local",
        types: "expanded selected",
      },
      source: {
        url: noteTreeJsonUrl,
        dataType: "json",
      },
      filter: {
        mode: "hide",
      },
      init: () => {
        lsMuted.removeAll()
        tree.widget = $("#notes").fancytree("getTree")
        const s = tree.widget.getSelectedNodes(true)
        for (const node of s) {
          tree.storeSelectDeep(node)
        }
        tree.widget.render(true, true)
        tree.dressNotes()
        rootData = tree.widget.rootNode.children[0].data
        $("#count_u").html(rootData.u)
        $("#count_n").html(rootData.n)
        diagnostics = new Diagnostics("filter_msg")
        tree.view = new View()
        tree.level = new Level()
        tree.filter = new Filter()
        tree.level.initLevel()
        tree.gotoNote($("#key_id").val())
      },
      expand: () => {
        const { level } = tree
        if (level != undefined) {
          level.expandLevel("")
        }
      },
      collapse: () => {
        const { level } = tree
        if (level != undefined) {
          level.expandLevel("")
        }
      },
      select: (e, data) => {
        tree.storeSelectDeep(data.node)
      },
    })

    const standardHeight = window.innerHeight - subtractForNotesPage
    const canvasLeft = $(".left-sidebar")
    const canvasRight = $(".right-sidebar")
    canvasLeft.css("height", `${standardHeight}px`)
    $("#notes").css("height", `${standardHeight}px`)
    canvasRight.css("height", `${standardHeight}px`)

    const detailControls = `<a
        class="showc fa fa-chevron-right"
        href="#"
        title="Show details"
      ></a><a
        class="hidec fa fa-chevron-down"
        href="#"
        title="Hide details"></a>`

    $("dt.cps").each((i, e) => {
      const elem = $(e.delegateTarget)
      const orig = elem.html()
      elem.html(`${detailControls}&nbsp;${orig}`)
    })
    $("dd.cps").hide()
    $(".hidec").hide()
    $(".showc").show()
    $(".hidec").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const refElem = elem.closest("dt")
      refElem.next().hide()
      refElem.find(".hidec").hide()
      refElem.find(".showc").show()
    })
    $(".showc").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const refElem = elem.closest("dt")
      refElem.next().show()
      refElem.find(".hidec").show()
      refElem.find(".showc").hide()
    })
  }

  storeSelect(node) {
    const { lsNotesMuted: lsMuted } = LS
    const { folder, key: iid, selected } = node
    if (!folder) {
      if (selected) {
        lsMuted.set(iid, 1)
      } else {
        if (lsMuted.isSet(iid)) {
          lsMuted.remove(iid)
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

  dressNotes() {
    const { pageUrl } = Config
    $("#notes a.md").addClass("fa fa-level-down")
    $("#notes a[key_id]").each((i, el) => {
      const elem = $(el)
      const vr = elem.attr("v")
      const extra = vr == undefined ? "" : `&version=${vr}`
      elem.attr(
        "href",
        `${pageUrl}?iid=${elem.attr("key_id")}${extra}&page=1&mr=r&qw=n&tp=txt1&nget=v`
      )
    })
    $("#notes a.md").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const userName = elem.closest("ul").closest("li").find("span[n]").html()
      const tit = elem.prev()
      const lnk = tit.attr("href")
      const note_name = tit.html()
      window.prompt(
        "Press <Cmd-C> and then <Enter> to copy link on clipboard",
        `[${userName}: ${note_name}](${lnk})`
      )
    })
  }

  gotoNote(key_id) {
    if (key_id != undefined && key_id != "0") {
      const nnode = this.widget.getNodeByKey(`n${key_id}`)
      if (nnode != null) {
        nnode.makeVisible({ noAnimation: true })
        $(".treehl").removeClass("treehl")
        $(`a[key_id="${key_id}"]`).closest("span").addClass("treehl")
        $(nnode.li)[0].scrollIntoView()
      }
    }
  }
}

class Upload {
  constructor() {
    this.inpt = $("#ncsv")
    this.ctl = $("#ncsv_upload")
    this.limit = 20 * 1024 * 1024
    this.fileType = "text/csv"
    if (this.inpt) {
      this.init()
    }
  }

  init() {
    this.msgs = new Diagnostics("upl_msgs")
    this.ctl.hide()
    const { msgs, ctl, limit, fileType, inpt } = this
    inpt.change(e => {
      const elem = e.delegateTarget
      const file = elem.files[0]
      this.file = file
      const { name, size, type } = file
      if (name.length > 0) {
        const msize = (size / 1024).toFixed(1)
        if (type != this.fileType) {
          msgs.msg(["error", `File has type ${type}; should be ${fileType}`])
        } else if (file.size >= limit) {
          msgs.msg([
            "error",
            `File has size ${msize}Kb; should be less than ${limit / 1024}Kb`,
          ])
        } else {
          msgs.msg(["good", `File has type ${type} and size ${msize}Kb`])
          ctl.show()
        }
      }
    })
    ctl.click(e => {
      e.preventDefault()
      this.submit()
      ctl.hide()
      inpt.val("")
    })
  }
  submit() {
    const { noteUploadJsonUrl } = Config
    const { msgs } = this
    const fd = new FormData(document.getElementById("fileinfo"))
    msgs.msg(["special", "uploading ..."])
    $.ajax({
      url: noteUploadJsonUrl,
      type: "POST",
      data: fd,
      enctype: "multipart/form-data",
      processData: false, // tell jQuery not to process the data
      contentType: false, // tell jQuery not to set contentType
    }).done(data => {
      for (const mg of data.msgs) {
        msgs.msg(mg)
      }
    }, "json")
    return false
  }
}

$(() => {
  window.LS = new LStorage()
  treeObj = new Tree()
  new Upload()
})
