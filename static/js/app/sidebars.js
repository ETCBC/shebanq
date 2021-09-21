/* eslint-env jquery */
/* globals Config, P, L, State */

import {
  toggle_detail,
  escHT,
  specialLinks,
  closeDialog,
  put_markdown,
} from "./helpers.js"
import { Msg } from "./msg.js"
import { CSelect } from "./select.js"
import { ColorPicker1 } from "./colorpicker.js"

export class Sidebars {
  /* TOP LEVEL: all four kinds of sidebars
   */
  constructor() {
    this.sidebar = {}
    for (const mr of ["m", "r"]) {
      for (const qw of ["q", "w", "n"]) {
        this.sidebar[`${mr}${qw}`] = new Sidebar(mr, qw)
      }
    }
    this.side_fetched = {}
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
      this.side_fetched[`m${qw}`] = false
    }
  }

  after_item_fetch() {
    for (const qw of ["q", "w", "n"]) {
      this.side_fetched[`r${qw}`] = false
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
      for (const v of versions) {
        this.add_version(v)
      }
    }
    this.show.click(e => {
      e.preventDefault()
      P.viewState.hstatesv(this.qw, { get: "v" })
      P.viewState.addHist()
      this.apply()
    })

    this.hide.click(e => {
      e.preventDefault()
      P.viewState.hstatesv(this.qw, { get: "x" })
      P.viewState.addHist()
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
        if (P.viewState.get(this.qw) == "x") {
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
    this.name = `side_material_${mr}${qw}`
    this.hid = `#${this.name}`

    if (mr == "r") {
      if (qw != "n") {
        P.picker1[qw] = new ColorPicker1(qw, null, true, false)
      }
    }
  }

  msg(m) {
    $(this.hid).html(m)
  }

  set_vselect(v) {
    $(`#version_s_${v}`).click(e => {
      e.preventDefault()
      P.viewState.mstatesv({ version: v })
      P.go()
    })
  }

  process() {
    const { versions, wordsUrl, notesUrl } = Config

    const { mr, qw } = this

    P.sidebars.after_item_fetch()
    this.sidelistitems()
    if (this.mr == "m") {
      P.listsettings[this.qw].apply()
    } else {
      for (const v of versions) {
        P.sidebars.sidebar[`r${this.qw}`].cselect[v].init()
      }

      const vr = P.version
      const iid = P.viewState.iid()

      $(".moredetail").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        toggle_detail(elem)
      })
      $(".detail").hide()
      $(`div[version="${vr}"]`).find(".detail").show()

      this.msgo = new Msg(`dbmsg_${qw}`)

      let first_name, last_name

      if (qw == "q") {
        const { q } = State
        this.info = q
        $("#thequeryid").html(q.id)
        first_name = escHT(q.first_name || "")
        last_name = escHT(q.last_name || "")
        const query_name = escHT(q.name || "")
        $("#itemtag").val(`${first_name} ${last_name}: ${query_name}`)
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
            `${wordsUrl}?lan=${wvr.lan}&` +
              `letter=${wvr.entry_heb.charCodeAt(0)}&goto=${w.id}`
          )
        }
      } else if (qw == "n") {
        const { n } = State
        this.info = n
        if ("versions" in n) {
          first_name = escHT(n.first_name)
          last_name = escHT(n.last_name)
          const keywords = escHT(n.keywords)
          $("#itemtag").val(`${first_name} ${last_name}: ${keywords}`)
          $("#gobackn").attr("href", `${notesUrl}?goto=${n.id}`)
        }
      }
      if ("versions" in this.info) {
        for (const v in this.info.versions) {
          const extra = qw == "w" ? "" : `${first_name}_${last_name}`
          this.set_vselect(v)
          P.set_csv(v, mr, qw, iid, extra)
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
      thistitle = `[${P.viewState.version()}] ${P.viewState.book()} ${P.viewState.chapter()}:${P.viewState.verse()}`
    } else {
      thistitle = $("#itemtag").val()
      $("#theitem").html(`${thistitle} `)
      /* fill in the title of the query/word/note above the verse material
       * and put it in the page title as well
       */
    }
    document.title = thistitle

    if (this.qw == "q") {
      const { mqlSmallHeight, mqlSmallWidth, mqlBigWidth, mqlBigWidthDia } = P
      if (this.mr == "m") {
        /* in the sidebar list of queries:
         * the mql query body can be popped up as a dialog for viewing it
         * in a larger canvas
         */
        $(".fullc").click(e => {
          e.preventDefault()
          const elem = $(e.delegateTarget)
          const { windowHeight } = P
          const thisiid = elem.attr("iid")
          const mqlq = $(`#area_${thisiid}`)
          const dia = $(`#bigq_${thisiid}`).dialog({
            dialogClass: "mql_dialog",
            closeOnEscape: true,
            close: () => {
              dia.dialog("destroy")
              const mqlq = $(`#area_${thisiid}`)
              mqlq.css("height", mqlSmallHeight)
              mqlq.css("width", mqlSmallWidth)
            },
            modal: false,
            title: "mql query body",
            position: { my: "left top", at: "left top", of: window },
            width: mqlBigWidthDia,
            height: windowHeight,
          })
          mqlq.css("height", P.standardHeight)
          mqlq.css("width", mqlBigWidth)
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
        const is_published =
          "versions" in q && vr in q.versions && q.versions[vr].is_published

        const d_md = specialLinks(descm.html())
        descm.html(d_md)
        P.decorate_crossrefs(descm)

        fullc.click(e => {
          e.preventDefault()
          const { windowHeight, half_standard_height } = P
          fullc.hide()
          const dia = $("#bigger")
            .closest("div")
            .dialog({
              dialogClass: "mql_dialog",
              closeOnEscape: true,
              close: () => {
                dia.dialog("destroy")
                mqlq.css("height", mqlSmallHeight)
                descm.removeClass("desc_dia")
                descm.addClass("description")
                descm.css("height", mqlSmallHeight)
                fullc.show()
              },
              modal: false,
              title: "description and mql query body",
              position: { my: "left top", at: "left top", of: window },
              width: mqlBigWidthDia,
              height: windowHeight,
            })
          mqlq.css("height", half_standard_height)
          descm.removeClass("description")
          descm.addClass("desc_dia")
          descm.css("height", half_standard_height)
        })

        $("#is_pub_c").click(e => {
          const elem = $(e.delegateTarget)
          const val = elem.prop("checked")
          this.sendval(
            q.versions[vr],
            elem,
            val,
            vr,
            elem.attr("query_id"),
            "is_published",
            val ? "T" : ""
          )
        })

        $("#is_shared_c").click(e => {
          const elem = $(e.delegateTarget)
          const val = elem.prop("checked")
          this.sendval(
            q,
            elem,
            val,
            vr,
            elem.attr("query_id"),
            "is_shared",
            val ? "T" : ""
          )
        })

        nameq.hide()
        descq.hide()
        descm.show()
        editq.show()
        if (is_published) {
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
          const { is_published } = q.versions[vr]
          this.saved_name = nameq.val()
          this.saved_desc = descq.val()
          this.saved_mql = mqlq.val()
          P.set_edit_width()
          if (!is_published) {
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
          mqlq.prop("readonly", is_published)
          mqlq.css("height", "20em")
        })

        cancq.click(e => {
          e.preventDefault()
          nameq.val(this.saved_name)
          descq.val(this.saved_desc)
          mqlq.val(this.saved_mql)
          P.reset_main_width()
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
          P.reset_main_width()
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
            query_id: $("#query_id").val(),
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
            query_id: $("#query_id").val(),
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
            query_id: $("#query_id").val(),
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
    const { queryMetaFieldUrl } = Config

    const senddata = {}
    senddata.version = vr
    senddata.query_id = iid
    senddata.fname = fname
    senddata.val = val

    $.post(
      queryMetaFieldUrl,
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
    const { queryMetaFieldsUrl } = Config

    const { execute, version: vr } = senddata

    $.post(
      queryMetaFieldsUrl,
      senddata,
      data => {
        const { good, q, msgs } = data

        const msg = this.msgov
        msg.clear()

        for (const m of msgs) {
          msg.msg(m)
        }

        if (good) {
          const { emdrosVersionsOld } = data
          const qx = q.versions[vr]
          $("#nameqm").html(escHT(q.name || ""))
          $("#nameq").val(q.name)
          const d_md = specialLinks(q.description_md)
          const descm = $("#descm")
          descm.html(d_md)
          P.decorate_crossrefs(descm)
          $("#descq").val(q.description)
          $("#mqlq").val(qx.mql)
          const ev = $("#eversion")
          const evtd = ev.closest("td")
          ev.html(qx.eversion)
          if (qx.eversion in emdrosVersionsOld) {
            evtd.addClass("exeversionold")
            evtd.attr("title", "this is not the newest version")
          } else {
            evtd.removeClass("exeversionold")
            evtd.attr("title", "this is the newest version")
          }
          $("#executed_on").html(qx.executed_on)
          $("#xmodified_on").html(qx.xmodified_on)
          $("#qresults").html(qx.results)
          $("#qresultslots").html(qx.resultmonads)
          $("#statq").removeClass("error warning good").addClass(qx.status)
          this.setstatus("", qx.status)
          P.sidebars.sidebar["rq"].content.info = q
        }
        if (execute) {
          P.reset_material_status()
          P.material.adapt()
          const show_chart = closeDialog($(`#select_contents_chart_${vr}_q_${q.id}`))
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
    if (P.mr == this.mr && (this.mr == "r" || P.viewState.get(this.qw) == "v")) {
      this.fetch()
    }
  }

  fetch() {
    const { shbStyle, sideUrl } = Config
    const {
      version,
      iid,
      sidebars: { side_fetched },
    } = P

    const { mr, qw } = this
    const thelist = $(`#side_material_${mr}${qw}`)

    let vars = `?version=${version}&mr={mr}&qw=${qw}`

    let do_fetch = false
    let extra = ""

    if (mr == "m") {
      vars += `&book=${P.viewState.book()}&chapter=${P.viewState.chapter()}`
      if (qw == "q" || qw == "n") {
        vars += `&${qw}pub=${P.viewState.is_published(qw)}`
      }
      do_fetch = P.viewState.book() != "x" && P.viewState.chapter() > 0
      extra = "m"
    } else {
      vars += `&iid=${iid}`
      do_fetch = P.qw == "q" ? iid >= 0 : iid != "-1"
      extra = `${qw}m`
    }
    if (do_fetch && !side_fetched[`${mr}${qw}`]) {
      const tag = `tag${mr == "m" ? "s" : ""}`
      this.msg(`fetching ${shbStyle[qw][tag]} ...`)
      if (mr == "m") {
        thelist.load(
          `${sideUrl}${extra}${vars}`,
          () => {
            side_fetched[`${mr}${qw}`] = true
            this.process()
          },
          "html"
        )
      } else {
        $.get(
          `${sideUrl}${extra}${vars}`,
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
          P.picker1list[qw][iid] = new ColorPicker1(qw, iid, false, false)
        }
      })
    }
  }

  sidelistitem(iid) {
    /* individual item in an m-sidebar
     */
    const { muting_n, muting_q } = L
    const { qw } = this

    const itop = $(`#${qw}${iid}`)
    const more = $(`#m_${qw}${iid}`)
    const desc = $(`#d_${qw}${iid}`)
    const item = $(`#item_${qw}${iid}`)
    const all = $(`#${qw}${iid}`)

    desc.hide()

    more.click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      toggle_detail(elem, desc, qw == "q" ? put_markdown : undefined)
    })

    item.click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { qw } = this
      P.viewState.mstatesv({ mr: this.other_mr, qw, iid: elem.attr("iid"), page: 1 })
      P.viewState.addHist()
      P.go()
    })

    if (qw == "w") {
      if (!P.viewState.iscolor(qw, iid)) {
        all.hide()
      }
    } else if (qw == "q") {
      if (muting_q.isSet(`${iid}`)) {
        itop.hide()
      } else {
        itop.show()
      }
    } else if (qw == "n") {
      if (muting_n.isSet(`${iid}`)) {
        itop.hide()
      } else {
        itop.show()
      }
    }
  }
}
