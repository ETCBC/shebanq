/* eslint-env jquery */
/* eslint-disable camelcase */

/**
 * @module share
 *
 * Provides stable urls for citing words, queries, note sets.
 *
 * @see [∈ cite-slider][elem-cite-slider]
 */

/* globals Config, PG, VS */

import { escHT, toggleDetail } from "./helpers.js"

const deselectText = () => {
  if (document.selection) {
    document.selection.empty()
  } else if (window.getSelection) {
    window.getSelection().removeAllRanges()
  }
}
const selectText = containerId => {
  deselectText()
  if (document.selection) {
    const range = document.body.createTextRange()
    range.moveToElementText(document.getElementById(containerId))
    range.select()
  } else if (window.getSelection) {
    const range = document.createRange()
    range.selectNode(document.getElementById(containerId))
    window.getSelection().addRange(range)
  }
}

$(() => {
  const { queryShareUrl, wordShareUrl, noteShareUrl, pageShareUrl } = Config

  const queryMessage = {
    good:
      "The results of this query have been obtained after the query body has been last modified",
    warning: "This query has never been executed in SHEBANQ",
    error:
      "The body of this query has been changed after its current results have been obtained.",
  }

  const drawerHTML = `
<div id="socialdrawer">
    <p id="citeh">Cite</p>
    <table align="center">
        <tr>
            <td class="clip_qx clr">
                <a
                  lnk="" href="#" id="clip_qx_md"
                  title="link to query version (markdown)"
                  class="ctl fa fa-level-down fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_qx_ht"
                  title="link to query version (html)"
                  class="ctl fa fa-external-link fa-lg fa-fw"></a>
            </td>
            <td class="clip_q clr">
                <a
                  lnk="" href="#" id="clip_q_md"
                  title="link to query (markdown)"
                  class="ctl fa fa-level-down fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_q_ht"
                  title="link to query (html)"
                  class="ctl fa fa-external-link fa-lg fa-fw"></a>
            </td>
            <td class="clip_w clr">
                <a
                  lnk="" href="#" id="clip_w_md"
                  title="link to word (markdown)"
                  class="ctl fa fa-level-down fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_w_ht"
                  title="link to word (html)"
                  class="ctl fa fa-external-link fa-lg fa-fw"></a>
            </td>
            <td class="clip_n clr">
                <a
                  lnk="" href="#" id="clip_n_md"
                  title="link to note set (markdown)"
                  class="ctl fa fa-level-down fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_n_ht"
                  title="link to note set (html)"
                  class="ctl fa fa-external-link fa-lg fa-fw"></a>
            </td>
            <td class="clip_pv clr">
                <a
                  lnk="" href="#" id="clip_pv_md"
                  title="link to page content and appearance (markdown)"
                  class="ctl fa fa-level-down fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_pv_ht"
                  title="link to page content and appearance (html)"
                  class="ctl fa fa-external-link-square fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_pv_htc"
                  title="link to page content (html)"
                  class="ctl fa fa-external-link fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_pv_nl"
                  title="internal link to page content"
                  class="ctl fa fa-bookmark fa-lg fa-fw"></a>
                <a
                  lnk="" href="#" id="clip_pv_cn"
                  title="copy page content"
                  class="ctl fa fa-file-text-o fa-lg fa-fw"></a>
            </td>
        </tr>
        <tr>
            <th class="clip_qx" width="120px">query v</th>
            <th class="clip_q" width="120px">query</th>
            <th class="clip_w" width="120px">word</th>
            <th class="clip_n" width="120px">note</th>
            <th class="clip_pv" width="120px">page view</th>
        </tr>
        <tr class="citexpl">
            <td class="clip_qx">
              <span id="xc_qx" class="ctl fa fa-chevron-right fa-fw"></span>
              <span id="x_qx" class="detail">cite query with its results on
                <i>this</i> data version</span>
              </td>
            <td class="clip_q">
              <span id="xc_q" class="ctl fa fa-chevron-right fa-fw"></span>
              <span id="x_q" class="detail">share link to query page</span>
            </td>
            <td class="clip_w">
              <span id="xc_w" class="ctl fa fa-chevron-right fa-fw"></span>
              <span id="x_w" class="detail">cite word with its occs on
                <i>this</i> data version</span>
              </td>
            <td class="clip_n">
              <span id="xc_n" class="ctl fa fa-chevron-right fa-fw"></span>
              <span id="x_n" class="detail">cite note set with its members</span>
            </td>
            <td class="clip_pv">
              <span id="xc_pv" class="ctl fa fa-chevron-right fa-fw"></span>
              <span id="x_pv" class="detail">share link to this page
                with or without view settings, or as internal note link,
                or copy page contents to paste in mail, Evernote, etc.</span>
            </td>
        </tr>
    </table>
    <p id="diagpub"></p>
    <p id="diagstatus"></p>
</div>
`
  /* Add the share tool bar.
   */
  $("body").append(drawerHTML)
  const st = $("#socialdrawer")
  st.css({
    opacity: ".7",
    "z-index": "3000",
    background: "#FFF",
    border: "solid 1px #666",
    "border-width": " 1px 0 0 1px",
    height: "20px",
    width: "40px",
    position: "fixed",
    bottom: "0",
    right: "0",
    padding: "2px 5px",
    overflow: "hidden",
    "-webkit-border-top-left-radius": " 12px",
    "-moz-border-radius-topleft": " 12px",
    "border-top-left-radius": " 12px",
    "-moz-box-shadow": " -3px -3px 3px rgba(0,0,0,0.5)",
    "-webkit-box-shadow": " -3px -3px 3px rgba(0,0,0,0.5)",
    "box-shadow": " -3px -3px 3px rgba(0,0,0,0.5)",
  })
  $("#citeh").css({
    margin: "2px 3px",
    "text-shadow": " 1px 1px 1px #FFF",
    color: "#444",
    "font-size": "12px",
    "line-height": "1em",
  })
  $("#socialdrawer td,#socialdrawer th").css({
    width: "120px",
    "text-align": "center",
    "border-left": "2px solid #888888",
    "border-right": "2px solid #888888",
  })
  $("#socialdrawer .detail").hide()
  // hover
  $(
    "#clip_qx_md,#clip_qx_ht,#clip_q_md,#clip_q_ht,#clip_w_md,#clip_w_ht,#clip_n_md,#clip_n_ht,#clip_pv_md,#clip_pv_ht,#clip_pv_htc,#clip_pv_nl"
  ).off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    window.prompt(
      "Press <Cmd-C> and then <Enter> to copy link on clipboard",
      elem.attr("lnk")
    )
  })
  $("#clip_pv_cn").off("click").click(e => {
    e.preventDefault()
    const pageUrlRaw = `${pageShareUrl}${VS.getVars()}&pref=alt`
    const selfLink = $("#self_link")
    selfLink.show()
    selfLink.attr("href", pageUrlRaw)
    selectText("material")
  })
  $("#xc_qx").off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggleDetail(elem, $("#x_qx"))
  })
  $("#xc_q").off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggleDetail(elem, $("#x_q"))
  })
  $("#xc_w").off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggleDetail(elem, $("#x_w"))
  })
  $("#xc_n").off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggleDetail(elem, $("#x_n"))
  })
  $("#xc_pv").off("click").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggleDetail(elem, $("#x_pv"))
  })
  st.off("click").click(e => {
    e.preventDefault()
    const pageUrlRaw = `${pageShareUrl}${VS.getVars()}&pref=alt`
    let noteUrl
    let chapterUrlRaw
    const notePrefix = "shebanq:"

    const { version: vr, mr, qw, iid } = PG
    const tp = VS.tp()
    const tr = VS.tr()
    const w = VS.get("w")
    const q = VS.get("q")
    const n = VS.get("n")
    const theBook = $("#thebook").html()
    const theChapter = $("#thechapter").html()
    const book = VS.book()
    const chapter = VS.chapter()
    const verse = VS.verse()
    const page = VS.page()
    const pageUrlVars = `"&version=${vr}&mr=${mr}&qw=${qw}&tp=${tp}&tr=${tr}`
    const sidebarUrlVars = `&wget=${w}&qget=${q}&nget=${n}`
    const vars = `${pageUrlVars}${sidebarUrlVars}`

    $("#citeh").hide()
    $("#diagpub").html("")
    $("#diagstatus").html("")
    $(
      ".clip_qx.clr,.clip_q.clr,.clip_w.clr,.clip_n.clr,.clip_pv.clr,#diagpub,#diagstatus"
    ).removeClass("error warning good special")

    let itemTitle

    if (mr == "m") {
      itemTitle = `bhsa${vr} ${theBook} ${theChapter}:${verse}`
      noteUrl = `${notePrefix}?book=${book}&chapter=${chapter}&verse=${verse}${vars}`
      chapterUrlRaw = `${pageShareUrl}?book=${book}&chapter=${chapter}&verse=${verse}${vars}`

      $(".clip_qx").hide()
      $(".clip_q").hide()
      $(".clip_w").hide()
      $(".clip_n").hide()
    } else if (PG.mr == "r") {
      noteUrl = `${notePrefix}?id=${iid}&page=${page}${pageUrlVars}`
      chapterUrlRaw = `${pageShareUrl}?id=${iid}&page=${page}${pageUrlVars}`

      const iinfo = PG.sidebars.sidebar[`r${qw}`].content.info
      if (qw == "q") {
        const {
          first_name,
          last_name,
          name,
          is_shared,
          is_published,
          versions,
        } = iinfo
        itemTitle = `${first_name} ${last_name}: ${name}`
        const queryStatus = versions[vr].status
        if (is_shared) {
          if (!is_published) {
            $(".clip_qx.clr").addClass("warning")
            $("#diagpub").addClass("warning")
            $("#diagpub").html(
              "Beware of citing this query. It has not been published. It may be changed later."
            )
          } else {
            $(".clip_qx.clr").addClass("special")
            $("#diagpub").addClass("special")
            $("#diagpub").html(
              "This query has been published. If that happened more than a week ago, it can be safely cited. It will not be changed anymore."
            )
          }
          $(".clip_q.clr").addClass(queryStatus)
          $("#diagstatus").addClass(queryStatus)
          $("#diagstatus").html(queryMessage[queryStatus])
        } else {
          $(".clip_qx.clr").addClass("error")
          $(".clip_q.clr").addClass("error")
          $(".clip_pv.clr").addClass("error")
          $("#diagpub").addClass("error")
          $("#diagpub").html(
            "This query is not accessible to others because it is not shared."
          )
        }
        const quoteUrl = `${queryShareUrl}?id=${iid}`
        const versionUrl = `${queryShareUrl}?version=${vr}&id=${iid}`
        $("#clip_qx_md").attr("lnk", `[${itemTitle}](${versionUrl})`)
        $("#clip_qx_ht").attr("lnk", versionUrl)
        $("#clip_q_md").attr("lnk", `[${itemTitle}](${quoteUrl})`)
        $("#clip_q_ht").attr("lnk", quoteUrl)
        $(".clip_qx").show()
        $(".clip_q").show()
        $(".clip_w").hide()
        $(".clip_n").hide()
      } else if (qw == "w") {
        const versionInfo = iinfo.versions[vr]
        const { entryid, entryid_heb } = versionInfo
        itemTitle = `${entryid_heb} (${entryid})`
        const versionUrl = `${wordShareUrl}?version=${vr}&id=${iid}`
        $("#clip_w_md").attr("lnk", `[${itemTitle}](${versionUrl})`)
        $("#clip_w_ht").attr("lnk", versionUrl)
        $(".clip_w.clr").addClass("special")
        $(".clip_qx").hide()
        $(".clip_q").hide()
        $(".clip_w").show()
        $(".clip_n").hide()
      } else if (qw == "n") {
        const { first_name, last_name, keywords } = iinfo
        const first_nameX = escHT(first_name)
        const last_nameX = escHT(last_name)
        const keywordsX = escHT(keywords)
        itemTitle = `${first_nameX} ${last_nameX} - ${keywordsX}`
        const versionUrl = `${noteShareUrl}?version=${vr}&id=${iid}&tp=txt1&nget=v`
        $("#clip_n_md").attr("lnk", `[${itemTitle}](${versionUrl})`)
        $("#clip_n_ht").attr("lnk", versionUrl)
        $(".clip_n.clr").addClass("special")
        $(".clip_qx").hide()
        $(".clip_q").hide()
        $(".clip_w").hide()
        $(".clip_n").show()
      }
    }
    $("#clip_pv_md").attr("lnk", `[${itemTitle}](${pageUrlRaw})`)
    $("#clip_pv_ht").attr("lnk", pageUrlRaw)
    $("#clip_pv_htc").attr("lnk", chapterUrlRaw)
    $("#clip_pv_nl").attr("lnk", noteUrl)
    $("#clip_pv_cn").attr("lnk", pageUrlRaw)
    $("#clip_pv_cn").attr("tit", itemTitle)
    st.animate({ height: "260px", width: "570px", opacity: 0.95 }, 300)
  })

  st.mouseleave(() => {
    $("#self_link").hide()
    deselectText()
    $("#citeh").show()
    st.animate({ height: "20px", width: "40px", opacity: 0.7 }, 300)
    return false
  })
})
