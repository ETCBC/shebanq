/* eslint-env jquery */
/* eslint-disable camelcase */

/* globals Config, P */

import { escHT, toggle_detail } from "./helpers.js"

const deselectText = () => {
  if (document.selection) {
    document.selection.empty()
  } else if (window.getSelection) {
    window.getSelection().removeAllRanges()
  }
}
const selectText = containerid => {
  deselectText()
  if (document.selection) {
    const range = document.body.createTextRange()
    range.moveToElementText(document.getElementById(containerid))
    range.select()
  } else if (window.getSelection) {
    const range = document.createRange()
    range.selectNode(document.getElementById(containerid))
    window.getSelection().addRange(range)
  }
}

$(() => {
  const { queryUrl, wordUrl, noteUrl, pageViewUrl } = Config

  const qmsg = {
    good:
      "The results of this query have been obtained after the query body has been last modified",
    warning: "This query has never been executed in SHEBANQ",
    error:
      "The body of this query has been changed after its current results have been obtained.",
  }

  const tbar = `
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
  $("body").append(tbar)
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
  ).click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    window.prompt(
      "Press <Cmd-C> and then <Enter> to copy link on clipboard",
      elem.attr("lnk")
    )
  })
  $("#clip_pv_cn").click(e => {
    e.preventDefault()
    const shebanqUrl_raw = `${pageViewUrl}${P.viewState.getvars()}&pref=alt`
    const slink = $("#self_link")
    slink.show()
    slink.attr("href", shebanqUrl_raw)
    selectText("material")
  })
  $("#xc_qx").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggle_detail(elem, $("#x_qx"))
  })
  $("#xc_q").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggle_detail(elem, $("#x_q"))
  })
  $("#xc_w").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggle_detail(elem, $("#x_w"))
  })
  $("#xc_n").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggle_detail(elem, $("#x_n"))
  })
  $("#xc_pv").click(e => {
    e.preventDefault()
    const elem = $(e.delegateTarget)
    toggle_detail(elem, $("#x_pv"))
  })
  st.click(e => {
    e.preventDefault()
    const shebanqUrl_raw = `${pageViewUrl}${P.viewState.getvars()}&pref=alt`
    let shebanqUrl_note
    let shebanqUrl_rawc
    const shebanqUrl_note_pref = "shebanq:"

    const { version: vr, mr, qw, viewState, iid } = P
    const tp = viewState.tp()
    const tr = viewState.tr()
    const w = viewState.get("w")
    const q = viewState.get("q")
    const n = viewState.get("n")
    const thebook = $("#thebook").html()
    const thechapter = $("#thechapter").html()
    const book = viewState.book()
    const chapter = viewState.chapter()
    const verse = viewState.verse()
    const page = viewState.page()
    const shebanqUrl_show_vars = `"&version=${vr}&mr=${mr}&qw=${qw}&tp=${tp}&tr=${tr}`
    const shebanqUrl_side_vars = `&wget=${w}&qget=${q}&nget=${n}`
    const sv = `${shebanqUrl_show_vars}${shebanqUrl_side_vars}`

    $("#citeh").hide()
    $("#diagpub").html("")
    $("#diagstatus").html("")
    $(
      ".clip_qx.clr,.clip_q.clr,.clip_w.clr,.clip_n.clr,.clip_pv.clr,#diagpub,#diagstatus"
    ).removeClass("error warning good special")

    let pvtitle

    if (mr == "m") {
      pvtitle = `bhsa${vr} ${thebook} ${thechapter}:${verse}`
      shebanqUrl_note = `${shebanqUrl_note_pref}?book=${book}&chapter=${chapter}&verse=${verse}${sv}`
      shebanqUrl_rawc = `${pageViewUrl}?book=${book}&chapter=${chapter}&verse=${verse}${sv}`

      $(".clip_qx").hide()
      $(".clip_q").hide()
      $(".clip_w").hide()
      $(".clip_n").hide()
    } else if (P.mr == "r") {
      shebanqUrl_note = `${shebanqUrl_note_pref}?id=${iid}&page=${page}${shebanqUrl_show_vars}`
      shebanqUrl_rawc = `${pageViewUrl}?id=${iid}&page=${page}${shebanqUrl_show_vars}`

      const iinfo = P.sidebars.sidebar[`r${qw}`].content.info
      if (qw == "q") {
        const {
          first_name,
          last_name,
          name,
          is_shared,
          is_published,
          versions,
        } = iinfo
        pvtitle = `${first_name} ${last_name}: ${name}`
        const qstatus = versions[vr].status
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
          $(".clip_q.clr").addClass(qstatus)
          $("#diagstatus").addClass(qstatus)
          $("#diagstatus").html(qmsg[qstatus])
        } else {
          $(".clip_qx.clr").addClass("error")
          $(".clip_q.clr").addClass("error")
          $(".clip_pv.clr").addClass("error")
          $("#diagpub").addClass("error")
          $("#diagpub").html(
            "This query is not accessible to others because it is not shared."
          )
        }
        const quoteUrl = `${queryUrl}?id=${iid}`
        const quotevUrl = `${queryUrl}?version=${vr}&id=${iid}`
        $("#clip_qx_md").attr("lnk", `[${pvtitle}](${quotevUrl})`)
        $("#clip_qx_ht").attr("lnk", quotevUrl)
        $("#clip_q_md").attr("lnk", `[${pvtitle}](${quoteUrl})`)
        $("#clip_q_ht").attr("lnk", quoteUrl)
        $(".clip_qx").show()
        $(".clip_q").show()
        $(".clip_w").hide()
        $(".clip_n").hide()
      } else if (qw == "w") {
        const versionInfo = iinfo.versions[vr]
        const { entryid, entryid_heb } = versionInfo
        pvtitle = `${entryid_heb} (${entryid})`
        const quotevUrl = `${wordUrl}?version=${vr}&id=${iid}`
        $("#clip_w_md").attr("lnk", `[${pvtitle}](${quotevUrl})`)
        $("#clip_w_ht").attr("lnk", quotevUrl)
        $(".clip_w.clr").addClass("special")
        $(".clip_qx").hide()
        $(".clip_q").hide()
        $(".clip_w").show()
        $(".clip_n").hide()
      } else if (qw == "n") {
        const { first_name, last_name, keywords } = iinfo
        const first_nameX = escHT(first_name)
        const last_nameX = escHT(last_name)
        const kwx = escHT(keywords)
        pvtitle = `${first_nameX} ${last_nameX} - ${kwx}`
        const quotevUrl = `${noteUrl}?version=${vr}&id=${iid}&tp=txt1&nget=v`
        $("#clip_n_md").attr("lnk", `[${pvtitle}](${quotevUrl})`)
        $("#clip_n_ht").attr("lnk", quotevUrl)
        $(".clip_n.clr").addClass("special")
        $(".clip_qx").hide()
        $(".clip_q").hide()
        $(".clip_w").hide()
        $(".clip_n").show()
      }
    }
    $("#clip_pv_md").attr("lnk", `[${pvtitle}](${shebanqUrl_raw})`)
    $("#clip_pv_ht").attr("lnk", shebanqUrl_raw)
    $("#clip_pv_htc").attr("lnk", shebanqUrl_rawc)
    $("#clip_pv_nl").attr("lnk", shebanqUrl_note)
    $("#clip_pv_cn").attr("lnk", shebanqUrl_raw)
    $("#clip_pv_cn").attr("tit", pvtitle)
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
