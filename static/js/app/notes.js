/* eslint-env jquery */
/* eslint-disable no-new */

/* globals L, Config */

import { LStorage } from "./page.js"
import { Msg } from "./msg.js"

let ftree, msgflt, rdata
const subtractn = 80
/* the canvas holding the material gets a height equal to
 * the window height minus this amount
 */
const control_height = 100
/* height for messages and controls
 */

class View {
  constructor() {
    const { nsview } = L
    this.prevstate = false
    if (!nsview.isSet("simple")) {
      nsview.set("simple", true)
    }
    this.nvradio = $(".nvradio")
    this.csimple = $("#c_view_simple")
    this.cadvanced = $("#c_view_advanced")

    this.csimple.click(e => {
      e.preventDefault()
      nsview.set("simple", true)
      this.adjust_view()
    })

    this.cadvanced.click(e => {
      e.preventDefault()
      nsview.set("simple", false)
      this.adjust_view()
    })
    this.adjust_view()
  }

  adjust_view() {
    const { nsview } = L
    const simple = nsview.get("simple")
    this.nvradio.removeClass("ison")
    ;(simple ? this.csimple : this.cadvanced).addClass("ison")
    if (this.prevstate != simple) {
      if (simple) {
        $(".brn").hide()
      } else {
        $(".brn").show()
      }
      this.prevstate = simple
    }
  }
}

class Level {
  constructor() {
    const { nsview } = L
    this.levels = { u: 1, n: 2 }

    $(".nlradio").removeClass("ison")
    if (!nsview.isSet("level")) {
      nsview.set("level", "u")
    }
    $("#level_u").click(e => {
      e.preventDefault()
      this.expand_level("u")
    })
    $("#level_n").click(e => {
      e.preventDefault()
      this.expand_level("n")
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
    const { nsview } = L
    const { levels } = this

    $(".nlradio").removeClass("ison")
    $(`#level_${level}`).addClass("ison")
    nsview.set("level", level)
    if (level in levels) {
      const numlevel = levels[level]
      ftree.ftw.visit(n => {
        const nlevel = n.getLevel()
        n.setExpanded(nlevel <= numlevel, { noAnimation: true, noEvents: false })
      }, true)
    }
  }

  initlevel() {
    const { nsview } = L
    this.expand_level(nsview.get("level"))
  }
}

class Filter {
  constructor() {
    const { nsview } = L
    this.patc = $("#filter_contents")

    $("#filter_clear").hide()
    $("#filter_contents").val(
      nsview.isSet("filter_pat") ? nsview.get("filter_pat") : ""
    )
    if (nsview.isSet("filter_mode")) {
      this.pnsearch(nsview.get("filter_mode"))
      $("#filter_clear").show()
    }

    $("#filter_control_a").click(e => {
      e.preventDefault()
      this.pnsearch("a")
    })
    $("#filter_control_c").click(e => {
      e.preventDefault()
      this.pnsearch("c")
    })
    $("#filter_control_n").click(e => {
      e.preventDefault()
      this.pnsearch("q")
    })
    $("#filter_clear").click(e => {
      e.preventDefault()
      this.clear()
    })
  }

  clear() {
    const { nsview } = L
    ftree.ftw.clearFilter()
    msgflt.clear()
    msgflt.msg(["good", "no filter applied"])
    $(".nfradio").removeClass("ison")
    nsview.remove("filter_mode")
    $("#filter_clear").hide()
    $("#amatches").html("")
    $("#cmatches").html("")
    $("#nmatches").html("")
    $("#count_u").html(rdata.u)
    $("#count_n").html(rdata.n)
  }

  pnsearch(kind) {
    const { nsview } = L
    const pat = this.patc.val()
    nsview.set("filter_pat", pat)
    let amatches = 0
    let cmatches = 0
    let nmatches = 0
    if (pat == "") {
      amatches = -1
      cmatches = -1
      nmatches = -1
    }
    $(".nfradio").removeClass("ison")
    if (pat == "") {
      this.clear()
      return
    } else {
      msgflt.clear()
      msgflt.msg(["special", "filter applied"])
    }
    $(`#filter_control_${kind}`).addClass("ison")
    nsview.set("filter_mode", kind)

    ftree.level.expand_all()
    if (kind == "a") {
      amatches = ftree.ftw.filterNodes(pat, false)
      $("#amatches").html(amatches >= 0 ? `(${amatches})` : "")
    } else if (kind == "c") {
      cmatches = ftree.ftw.filterBranches(pat)
      $("#cmatches").html(cmatches >= 0 ? `(${cmatches})` : "")
    } else if (kind == "n") {
      nmatches = ftree.ftw.filterNodes(pat, true)
      $("#nmatches").html(nmatches >= 0 ? `(${nmatches})` : "")
    }
    $("#filter_clear").show()
    const submatch = "span.fancytree-submatch"
    const match = "span.fancytree-match"
    const base_u = "#queries>ul>li>ul>li>"
    const match_u = $(`${base_u}${match}`).length
    const submatch_u = $(`${base_u}${submatch}`).length
    const base_n = `${base_n}ul>li>`
    const match_n = $(`${base_n}${match}`).length
    $("#count_u").html(`
      <span class="match">${match_u}</span>
      <span class="brn submatch">${submatch_u}</span>`)
    $("#count_n").html(`<span class="match">${match_n}</span>`)
    if (ftree.view.simple) {
      $(".brn").hide()
    }
  }
}

class Tree {
  constructor() {
    const { pn_url } = Config
    const { muting_n: muting } = L

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
        url: pn_url,
        dataType: "json",
      },
      filter: {
        mode: "hide",
      },
      init: () => {
        muting.removeAll()
        tree.ftw = $("#notes").fancytree("getTree")
        const s = tree.ftw.getSelectedNodes(true)
        for (const i in s) {
          tree.store_select_deep(s[i])
        }
        tree.ftw.render(true, true)
        tree.dress_notes()
        rdata = tree.ftw.rootNode.children[0].data
        $("#count_u").html(rdata.u)
        $("#count_n").html(rdata.n)
        msgflt = new Msg("filter_msg")
        tree.view = new View()
        tree.level = new Level()
        tree.filter = new Filter()
        tree.level.initlevel()
        tree.gotonote($("#nkid").val())
      },
      expand: () => {
        const { level } = tree
        if (level != undefined) {
          level.expand_level("")
        }
      },
      collapse: () => {
        const { level } = tree
        if (level != undefined) {
          level.expand_level("")
        }
      },
      select: (e, data) => {
        tree.store_select_deep(data.node)
      },
    })

    const standard_height = window.innerHeight - subtractn
    const form_height = standard_height - control_height
    const canvas_left = $(".left-sidebar")
    const canvas_right = $(".right-sidebar")
    canvas_left.css("height", `${standard_height}px`)
    $("#notes").css("height", `${standard_height}px`)
    $("#opqforms").css("height", `${form_height}px`)
    $("#opqctrl").css("height", `${control_height}px`)
    canvas_right.css("height", `${standard_height}px`)

    const detailcontrols = `<a
        class="showc fa fa-chevron-right"
        href="#"
        title="Show details"
      ></a><a
        class="hidec fa fa-chevron-down"
        href="#"
        title="Hide details"></a>`

    $('dt.cps').each((i, e) => {
        const elem = $(e.target)
        const orig = elem.html()
        elem.html(`${detailcontrols}&nbsp;${orig}`)
    })
    $('dd.cps').hide()
    $('.hidec').hide()
    $('.showc').show()
    $('.hidec').click(e => {
        e.preventDefault()
        const elem = $(e.target)
        const refo = elem.closest('dt')
        refo.next().hide()
        refo.find('.hidec').hide()
        refo.find('.showc').show()
    })
    $('.showc').click(e => {
        e.preventDefault()
        const elem = $(e.target)
        const refo = elem.closest('dt')
        refo.next().show()
        refo.find('.hidec').show()
        refo.find('.showc').hide()
    })
  }

  store_select(node) {
    const { muting_n: muting } = L
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

  dress_notes() {
    const { n_url } = Config
    $("#notes a.md").addClass("fa fa-level-down")
    $("#notes a[nkid]").each((i, el) => {
      const elem = $(el)
      const vr = elem.attr("v")
      const extra = vr == undefined ? "" : `&version=${vr}`
      elem.attr(
        "href",
        `${n_url}?iid=${elem.attr("nkid")}${extra}&page=1&mr=r&qw=n&tp=txt_tb1&nget=v`
      )
    })
    $("#notes a.md").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const uname = elem.closest("ul").closest("li").find("span[n]").html()
      const tit = elem.prev()
      const lnk = tit.attr("href")
      const nname = tit.html()
      window.prompt(
        "Press <Cmd-C> and then <Enter> to copy link on clipboard",
        `[${uname}: ${nname}](${lnk})`
      )
    })
  }

  gotonote(nkid) {
    if (nkid != undefined && nkid != "0") {
      const nnode = this.ftw.getNodeByKey(`n${nkid}`)
      if (nnode != null) {
        nnode.makeVisible({ noAnimation: true })
        $(".treehl").removeClass("treehl")
        $(`a[nkid="${nkid}"]`).closest("span").addClass("treehl")
        $(nnode.li)[0].scrollIntoView()
      }
    }
  }
}

class Upload {
  constructor() {
    this.inpt = $("#ncsv")
    this.ctrl = $("#ncsv_upload")
    this.limit = 20 * 1024 * 1024
    this.ftype = "text/csv"
    if (this.inpt) {
      this.init()
    }
  }

  init() {
    this.msgs = new Msg("upl_msgs")
    this.ctrl.hide()
    const { msgs, ctrl, limit, ftype, inpt } = this
    inpt.change(() => {
      this.file = this.files[0]
      const { file } = this
      if (file.name.length > 0) {
        const msize = (file.size / 1024).toFixed(1)
        if (file.type != this.ftype) {
          msgs.msg(["error", `File has type ${file.type}; should be ${ftype}`])
        } else if (file.size >= limit) {
          msgs.msg([
            "error",
            `File has size ${msize}Kb; should be less than ${limit / 1024}Kb`,
          ])
        } else {
          msgs.msg(["good", `File has type ${file.type} and size ${msize}Kb`])
          ctrl.show()
        }
      }
    })
    ctrl.click(e => {
      e.preventDefault()
      this.fsubmit()
      ctrl.hide()
      inpt.val("")
    })
  }
  fsubmit() {
    const { upload_url } = Config
    const { msgs } = this
    const fd = new FormData(document.getElementById("fileinfo"))
    msgs.msg(["special", "uploading ..."])
    $.ajax({
      url: upload_url,
      type: "POST",
      data: fd,
      enctype: "multipart/form-data",
      processData: false, // tell jQuery not to process the data
      contentType: false, // tell jQuery not to set contentType
    }).done(data => {
      for (const m of data.msgs) {
        msgs.msg(m)
      }
    }, "json")
    return false
  }
}

$(() => {
  window.L = new LStorage()
  ftree = new Tree()
  new Upload()
})
