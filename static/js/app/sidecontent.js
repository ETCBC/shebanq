/* eslint-env jquery */
/* globals Config, PG, VS, LS, State */

/**
 * @module sidecontent
 */

/* SIDELIST MATERIAL
 *
 */

import {
  toggleDetail,
  escHT,
  specialLinks,
  closeDialog,
  putMarkdown,
  idPrefixQueries,
  idPrefixNotes,
} from "./helpers.js"

import { Diagnostics } from "./diagnostics.js"
import { ColorPicker1 } from "./colorpicker.js"

/**
 * Controls the content of a side bar
 */
export class SideContent {
  constructor(mr, qw) {
    this.mr = mr
    this.qw = qw
    this.other_mr = this.mr == "m" ? "r" : "m"
    this.name = `side_material_${mr}${qw}`
    this.hid = `#${this.name}`

    if (mr == "r") {
      if (qw != "n") {
        PG.picker1[qw] = new ColorPicker1(qw, null, true, false)
      }
    }
  }

  msg(mg) {
    $(this.hid).html(mg)
  }

  selectVersion(v) {
    $(`#version_s_${v}`)
      .off("click")
      .click(e => {
        e.preventDefault()
        VS.setMaterial({ version: v })
        PG.go()
      })
  }

  process() {
    const { versions, wordsPageUrl, queriesPageUrl, notesPageUrl } = Config

    const { mr, qw } = this

    PG.sidebars.afterItemFetch()
    this.sideListItems()

    let thisTitle

    if (this.mr == "m") {
      PG.sideSettings[this.qw].apply()
      thisTitle = `[${VS.version()}] ${VS.book()} ${VS.chapter()}:${VS.verse()}`
    } else {
      for (const v of versions) {
        PG.sidebars.sidebar[`r${this.qw}`].chart[v].init()
      }

      const vr = PG.version
      const iid = VS.iid()

      $(".moredetail")
        .off("click")
        .click(e => {
          e.preventDefault()
          const elem = $(e.delegateTarget)
          toggleDetail(elem)
        })
      $(".detail").hide()
      $(`div[version="${vr}"]`).find(".detail").show()

      this.diagnostics = new Diagnostics(`dbmsg_${qw}`)

      let first_name, last_name, itemTag

      if (qw == "q") {
        const { query } = State
        this.info = query
        itemTag = "querytag"
        $("#thequeryid").html(query.id)
        first_name = escHT(query.first_name || "")
        last_name = escHT(query.last_name || "")
        const query_name = escHT(query.name || "")
        $(`#${itemTag}`).val(`${first_name} ${last_name}: ${query_name}`)
        $("#gobackq").attr("href", `${queriesPageUrl}?goto=${query.id}`)
        this.diagnosticsVersion = new Diagnostics("dbmsg_qv")
        $("#is_pub_c").show()
        $("#is_pub_ro").hide()
      } else if (qw == "w") {
        const { word } = State
        this.info = word
        itemTag = "wordtag"
        if ("versions" in word) {
          const wordVersion = word.versions[vr]
          const entry_heb = escHT(wordVersion.entry_heb)
          const entryid = escHT(wordVersion.entryid)
          $(`#${itemTag}`).val(`${entry_heb}: ${entryid}`)
          $("#gobackw").attr(
            "href",
            `${wordsPageUrl}?lan=${wordVersion.lan}&` +
              `letter=${wordVersion.entry_heb.charCodeAt(0)}&goto=${word.id}`
          )
        }
      } else if (qw == "n") {
        const { note } = State
        this.info = note
        itemTag = "notetag"
        if ("versions" in note) {
          first_name = escHT(note.first_name)
          last_name = escHT(note.last_name)
          const keywords = escHT(note.keywords)
          $(`#${itemTag}`).val(`${first_name} ${last_name}: ${keywords}`)
          $("#gobackn").attr("href", `${notesPageUrl}?goto=${note.id}`)
        }
      }
      if ("versions" in this.info) {
        for (const v in this.info.versions) {
          const extra = qw == "w" ? "" : `${first_name}_${last_name}`
          this.selectVersion(v)
          PG.setCsv(v, mr, qw, iid, extra)
        }
      }
      if (qw) {
        const { msgs } = State
        for (const mg of msgs) {
          this.diagnostics.msg(mg)
        }
      }
      thisTitle = $(`#${itemTag}`).val()
      $("#theitem").html(`${thisTitle} `)
      /* fill in the title of the query/word/note above the verse material
       * and put it in the page title as well
       */
    }

    document.title = thisTitle

    if (this.qw == "q") {
      const { mqlSmallHeight, mqlSmallWidth, mqlBigWidth, mqlBigWidthDia } = PG
      if (this.mr == "m") {
        /* in the sidebar list of queries:
         * the mql query body can be popped up as a dialog for viewing it
         * in a larger canvas
         */
        $(".fullc")
          .off("click")
          .click(e => {
            e.preventDefault()
            const elem = $(e.delegateTarget)
            const { windowHeight } = PG
            const thisIid = elem.attr("iid")
            const mqlArea = $(`#area_${thisIid}`)
            const dia = $(`#bigq_${thisIid}`).dialog({
              dialogClass: "mql_dialog",
              closeOnEscape: true,
              close: () => {
                dia.dialog("destroy")
                const mqlArea = $(`#area_${thisIid}`)
                mqlArea.css("height", mqlSmallHeight)
                mqlArea.css("width", mqlSmallWidth)
              },
              modal: false,
              title: "mql query body",
              position: { my: "left top", at: "left top", of: window },
              width: mqlBigWidthDia,
              height: windowHeight,
            })
            mqlArea.css("height", PG.standardHeight)
            mqlArea.css("width", mqlBigWidth)
          })
      } else {
        /* in the sidebar item view of a single query:
         * the mql query body can be popped up as a dialog for viewing it
         * in a larger canvas
         */
        const { query } = State
        const vr = PG.version
        const fullCtl = $(".fullc")
        const editQueryCtl = $("#editq")
        const execQueryCtl = $("#execq")
        const saveQueryCtl = $("#saveq")
        const cancelQueryCtl = $("#cancq")
        const doneQueryCtl = $("#doneq")
        const nameQueryBox = $("#nameq")
        const descriptionMarkdown = $("#descm")
        const descriptionQueryBox = $("#descq")
        const mqlArea = $("#mqlq")
        const publishCtl = $("#is_pub_c")
        const publishInfo = $("#is_pub_ro")
        const is_published =
          "versions" in query && vr in query.versions && query.versions[vr].is_published

        const markdown = specialLinks(descriptionMarkdown.html())
        descriptionMarkdown.html(markdown)
        PG.decorateCrossrefs(descriptionMarkdown)

        fullCtl.off("click").click(e => {
          e.preventDefault()
          const { windowHeight, halfStandardHeight } = PG
          fullCtl.hide()
          const dia = $("#bigger")
            .closest("div")
            .dialog({
              dialogClass: "mql_dialog",
              closeOnEscape: true,
              close: () => {
                dia.dialog("destroy")
                mqlArea.css("height", mqlSmallHeight)
                descriptionMarkdown.removeClass("desc_dia")
                descriptionMarkdown.addClass("description")
                descriptionMarkdown.css("height", mqlSmallHeight)
                fullCtl.show()
              },
              modal: false,
              title: "description and mql query body",
              position: { my: "left top", at: "left top", of: window },
              width: mqlBigWidthDia,
              height: windowHeight,
            })
          mqlArea.css("height", halfStandardHeight)
          descriptionMarkdown.removeClass("description")
          descriptionMarkdown.addClass("desc_dia")
          descriptionMarkdown.css("height", halfStandardHeight)
        })

        $("#is_pub_c")
          .off("click")
          .click(e => {
            const elem = $(e.delegateTarget)
            const val = elem.prop("checked")
            this.sendVal(
              query.versions[vr],
              elem,
              val,
              vr,
              elem.attr("query_id"),
              "is_published",
              val ? "T" : ""
            )
          })

        $("#is_shared_c")
          .off("click")
          .click(e => {
            const elem = $(e.delegateTarget)
            const val = elem.prop("checked")
            this.sendVal(
              query,
              elem,
              val,
              vr,
              elem.attr("query_id"),
              "is_shared",
              val ? "T" : ""
            )
          })

        nameQueryBox.hide()
        descriptionQueryBox.hide()
        descriptionMarkdown.show()
        editQueryCtl.show()
        if (is_published) {
          execQueryCtl.hide()
        } else {
          execQueryCtl.show()
        }
        saveQueryCtl.hide()
        cancelQueryCtl.hide()
        doneQueryCtl.hide()
        publishCtl.show()
        publishInfo.hide()

        editQueryCtl.off("click").click(e => {
          e.preventDefault()
          const { halfStandardHeight } = PG
          const { is_published } = query.versions[vr]
          this.nameSaved = nameQueryBox.val()
          this.descriptionSaved = descriptionQueryBox.val()
          this.mqlSaved = mqlArea.val()
          PG.setEditWidth()
          if (!is_published) {
            nameQueryBox.show()
          }
          descriptionQueryBox.show()
          descriptionQueryBox.css("height", halfStandardHeight)
          descriptionMarkdown.hide()
          editQueryCtl.hide()
          saveQueryCtl.show()
          cancelQueryCtl.show()
          doneQueryCtl.show()
          publishInfo.show()
          publishCtl.hide()
          mqlArea.prop("readonly", !!is_published)
          mqlArea.css("height", "20em")
        })

        cancelQueryCtl.off("click").click(e => {
          e.preventDefault()
          nameQueryBox.val(this.nameSaved)
          descriptionQueryBox.val(this.descriptionSaved)
          mqlArea.val(this.mqlSaved)
          PG.resetMainWidth()
          nameQueryBox.hide()
          descriptionQueryBox.hide()
          descriptionMarkdown.show()
          editQueryCtl.show()
          saveQueryCtl.hide()
          cancelQueryCtl.hide()
          doneQueryCtl.hide()
          publishCtl.show()
          publishInfo.hide()
          mqlArea.prop("readonly", true)
          mqlArea.css("height", "10em")
        })

        doneQueryCtl.off("click").click(e => {
          e.preventDefault()
          PG.resetMainWidth()
          nameQueryBox.hide()
          descriptionQueryBox.hide()
          descriptionMarkdown.show()
          editQueryCtl.show()
          saveQueryCtl.hide()
          cancelQueryCtl.hide()
          doneQueryCtl.hide()
          publishCtl.show()
          publishInfo.hide()
          mqlArea.prop("readonly", true)
          mqlArea.css("height", "10em")
          const data = {
            version: PG.version,
            query_id: $("#query_id").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          this.sendVals(data)
        })

        saveQueryCtl.off("click").click(e => {
          e.preventDefault()
          const data = {
            version: PG.version,
            query_id: $("#query_id").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: false,
          }
          this.sendVals(data)
        })
        execQueryCtl.off("click").click(e => {
          e.preventDefault()
          execQueryCtl.addClass("fa-spin")
          const msg = this.diagnosticsVersion
          msg.clear()
          msg.msg(["special", "executing query ..."])
          const data = {
            version: PG.version,
            query_id: $("#query_id").val(),
            name: $("#nameq").val(),
            description: $("#descq").val(),
            mql: $("#mqlq").val(),
            execute: true,
          }
          this.sendVals(data)
        })
      }
    }
  }

  setStatus(vr, cls) {
    const statusQuery = cls != null ? cls : $(`#statq${vr}`).attr("class")
    const statusElem =
      statusQuery == "good"
        ? "results up to date"
        : statusQuery == "error"
        ? "results outdated"
        : "never executed"
    $("#statm").html(statusElem)
  }

  /**
   * Updates a single field of a query.
   *
   * Meant for `is_shared` and `is_published`.
   *
   * !!! note
   *     `is_shared` is a field of a query record.
   *
   *     `is_published` is a field of a query_exe record.
   *
   * @see Triggers [C:hebrew.querysharing][controllers.hebrew.querysharing].
   */
  sendVal(query, box, valNew, vr, iid, fieldName, val) {
    const { querySharingJsonUrl } = Config

    const sendData = {}
    sendData.version = vr
    sendData.query_id = iid
    sendData.fname = fieldName
    sendData.val = val

    $.post(
      querySharingJsonUrl,
      sendData,
      data => {
        const { good, modDates, modCls, extra, msgs } = data

        if (good) {
          for (const [modDateField, modDate] of Object.entries(modDates)) {
            $(`#${modDateField}`).html(modDate)
          }
          for (const [modJquery, modCl] in Object.entries(modCls)) {
            const dest = $(modJquery)
            dest.removeClass("fa-check fa-close published")
            dest.addClass(modCl)
          }
          query[fieldName] = valNew
        } else {
          box.prop("checked", !valNew)
        }

        for (const [field, instruction] of Object.entries(extra)) {
          const prop = instruction[0]
          const val = instruction[1]

          if (prop == "check") {
            const dest = $(`#${field}_c`)
            dest.prop("checked", val)
          } else if (prop == "show") {
            const dest = $(`#${field}`)
            if (val) {
              dest.show()
            } else {
              dest.hide()
            }
          }
        }
        const theseDiagnostics =
          fieldName == "is_shared" ? this.diagnostics : this.diagnosticsVersion
        theseDiagnostics.clear()
        for (const mg of msgs) {
          theseDiagnostics.msg(mg)
        }
      },
      "json"
    )
  }

  /**
   * Sends un updated record to the database.
   *
   * @see Triggers [C:hebrew.queryupdate][controllers.hebrew.queryupdate].
   */
  sendVals(sendData) {
    const { queryUpdateJsonUrl } = Config

    const { execute, version: vr } = sendData

    $.post(
      queryUpdateJsonUrl,
      sendData,
      data => {
        const { good, query, msgs } = data

        const msg = this.diagnosticsVersion
        msg.clear()

        for (const mg of msgs) {
          msg.msg(mg)
        }

        if (good) {
          const { emdrosVersionsOld } = data
          const qx = query.versions[vr]
          $("#nameqm").html(escHT(query.name || ""))
          $("#nameq").val(query.name)
          const markdown = specialLinks(query.description_md)
          const descriptionMarkdown = $("#descm")
          descriptionMarkdown.html(markdown)
          PG.decorateCrossrefs(descriptionMarkdown)
          $("#descq").val(query.description)
          $("#mqlq").val(qx.mql)
          const emdrosVersionElem = $("#eversion")
          const emdrosVersionCell = emdrosVersionElem.closest("td")
          emdrosVersionElem.html(qx.eversion)
          if (qx.eversion in emdrosVersionsOld) {
            emdrosVersionCell.addClass("exeversionold")
            emdrosVersionCell.attr("title", "this is not the newest version")
          } else {
            emdrosVersionCell.removeClass("exeversionold")
            emdrosVersionCell.attr("title", "this is the newest version")
          }
          $("#executed_on").html(qx.executed_on)
          $("#xmodified_on").html(qx.xmodified_on)
          $("#qresults").html(qx.results)
          $("#qresultslots").html(qx.resultmonads)
          $("#statq").removeClass("error warning good").addClass(qx.status)
          this.setStatus("", qx.status)
          PG.sidebars.sidebar["rq"].content.info = query
        }
        if (execute) {
          PG.materialStatusReset()
          PG.material.adapt()
          const showChart = closeDialog($(`#select_contents_chart_${vr}_q_${query.id}`))
          if (showChart) {
            PG.sidebars.sidebar["rq"].chart[vr].apply()
          }
          $("#execq").removeClass("fa-spin")
        }
      },
      "json"
    )
  }

  apply() {
    if (PG.mr == this.mr && (this.mr == "r" || VS.get(this.qw) == "v")) {
      this.fetch()
    }
  }

  /**
   * get the material by AJAX if needed, and process the material afterward
   *
   * This method takes into account what kind of sidebar this is:
   *
   * @see Triggers [C:hebrew.sidematerial][controllers.hebrew.sidematerial]
   * @see Triggers [C:hebrew.sideword][controllers.hebrew.sideword]
   * @see Triggers [C:hebrew.sidequery][controllers.hebrew.sidequery]
   * @see Triggers [C:hebrew.sidenote][controllers.hebrew.sidenote]
   */
  fetch() {
    const { itemStyle, pageSidebarUrl } = Config
    const {
      version,
      iid,
      sidebars: { sideFetched },
    } = PG

    const { mr, qw } = this
    const theList = $(`#side_material_${mr}${qw}`)

    let vars = `?version=${version}&mr=${mr}&qw=${qw}`

    let doFetch = false
    let kind = ""

    if (mr == "m") {
      vars += `&book=${VS.book()}&chapter=${VS.chapter()}`
      if (qw == "q" || qw == "n") {
        vars += `&${qw}pub=${VS.is_published(qw)}`
      }
      doFetch = VS.book() != "x" && VS.chapter() > 0
      kind = "material"
    } else {
      vars += `&iid=${iid}`
      doFetch = PG.qw == "q" ? iid >= 0 : iid != "-1"
      kind = qw == "w" ? "word" : qw == "q" ? "query" : "note"
    }
    if (doFetch && !sideFetched[`${mr}${qw}`]) {
      const tag = `tag${mr == "m" ? "s" : ""}`
      this.msg(`fetching ${itemStyle[qw][tag]} ...`)
      if (mr == "m") {
        theList.load(
          `${pageSidebarUrl}${kind}${vars}`,
          () => {
            sideFetched[`${mr}${qw}`] = true
            this.process()
          },
          "html"
        )
      } else {
        $.get(
          `${pageSidebarUrl}${kind}${vars}`,
          html => {
            theList.html(html)
            sideFetched[`${mr}${qw}`] = true
            this.process()
          },
          "html"
        )
      }
    }
  }

  sideListItems() {
    /* the list of items in an m-sidebar
     */
    const { mr, qw } = this

    if (mr == "m") {
      if (qw != "n") {
        PG.picker1List[qw] = {}
      }
      const itemList = $(`#side_list_${qw} li`)
      itemList.each((i, el) => {
        const elem = $(el)
        const iid = elem.attr("iid")
        this.sideListItem(iid)
        if (qw != "n") {
          PG.picker1List[qw][iid] = new ColorPicker1(qw, iid, false, false)
        }
      })
    }
  }

  sideListItem(iid) {
    /* individual item in an m-sidebar
     */
    const { lsNotesMuted, lsQueriesMuted } = LS
    const { qw } = this

    const topElem = $(`#${qw}${iid}`)
    const moreCtl = $(`#m_${qw}${iid}`)
    const descriptionElem = $(`#d_${qw}${iid}`)
    const itemElem = $(`#item_${qw}${iid}`)

    descriptionElem.hide()

    moreCtl.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      toggleDetail(elem, descriptionElem, qw == "q" ? putMarkdown : undefined)
    })

    itemElem.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { qw } = this
      VS.setMaterial({ mr: this.other_mr, qw, iid: elem.attr("iid"), page: 1 })
      VS.addHist()
      PG.go()
    })

    if (qw == "w") {
      if (!VS.isColor(qw, iid)) {
        topElem.hide()
      }
    } else if (qw == "q") {
      if (lsQueriesMuted.isSet(`${idPrefixQueries}${iid}`)) {
        topElem.hide()
      } else {
        topElem.show()
      }
    } else if (qw == "n") {
      if (lsNotesMuted.isSet(`${idPrefixNotes}${iid}`)) {
        topElem.hide()
      } else {
        topElem.show()
      }
    }
  }
}
