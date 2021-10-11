/* eslint-env jquery */
/* globals Config, PG, VS, State */

/**
 * @module materialsettings
 */

import { closeDialog, escHT } from "./helpers.js"

/**
 * MATERIAL SETTINGS (for choosing between plain text and tabbed data, etc)
 *
 * [∈ text-presentation][elem-text-presentation]
 * [∈ text-representation][elem-text-representation]
 * [∈ feature-legend][elem-feature-legend]
 */
export class MaterialSettings {
  constructor(content) {
    const {
      featureHost,
      nextTp,
      nextTr,
      tabInfo,
      nTabViews,
      trInfo,
      trLabels,
      versions,
    } = Config

    const highlightedText = $("#mtxtp")
    const highlightedTextTab1 = $("#mtxt1")
    this.legend = $("#datalegend")
    this.legendc = $("#datalegend_control")
    this.name = "material_settings"
    this.hid = `#${this.name}`
    this.content = content

    highlightedText.show()
    highlightedTextTab1.show()

    this.legendc.off("click").click(e => {
      e.preventDefault()
      $("#datalegend")
        .find("a[fname]")
        .each((i, el) => {
          const elem = $(el)
          const url = `${featureHost}/${elem.attr("fname")}`
          elem.attr("href", url)
        })
      this.legend.dialog({
        autoOpen: true,
        dialogClass: "legend",
        closeOnEscape: true,
        modal: false,
        title: "legend",
        width: "600px",
      })
    })

    $(".mhradio").off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const tpOld = VS.tp()
      let tpNew = elem.attr("id").substring(1)
      if (tpOld == "txtp") {
        if (tpOld == tpNew) {
          return
        }
      } else if (tpOld == tpNew) {
        tpNew = nextTp[tpOld]
        if (tpNew == "txtp") {
          tpNew = nextTp[tpNew]
        }
      }
      VS.setMaterial({ tp: tpNew })
      VS.addHist()
      this.apply()
      const mr = VS.mr()
      const qw = VS.qw()
      if (mr == "r") {
        let extra = undefined
        if (qw == "q") {
          const { query } = State
          const first_name = escHT(query.first_name || "")
          const last_name = escHT(query.last_name || "")
          extra = `${first_name}_${last_name}`
        }
        for (const v of versions) {
          PG.setCsv(v, mr, qw, VS.iid(), extra)
        }
      }
    })

    $(".mtradio").off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const trOld = VS.tr()
      let trNew = elem.attr("id").substring(1)
      if (trOld == trNew) {
        trNew = nextTr[trOld]
      }

      VS.setMaterial({ tr: trNew })
      VS.addHist()
      this.apply()
    })

    for (let i = 1; i <= nTabViews; i++) {
      const mc = $(`#mtxt${i}`)
      mc.attr("title", tabInfo[`txt${i}`])
      if (i == 1) {
        mc.show()
      } else {
        mc.hide()
      }
    }

    for (const l in trLabels) {
      const t = trInfo[l]
      const mc = $(`#m${t}`)
      mc.attr("title", trLabels[t])
      if (l == "hb") {
        mc.show()
      } else {
        mc.hide()
      }
    }
  }

  apply() {
    const { nTabViews } = Config

    const textOrPhonoRadio = $(".mhradio")
    const textOrTabbedRadio = $(".mtradio")
    const tpNew = VS.tp()
    const trNew = VS.tr()
    const tpNewCtl = $(`#m${tpNew}`)
    const trNewCtl = $(`#m${trNew}`)
    textOrPhonoRadio.removeClass("ison")
    textOrTabbedRadio.removeClass("ison")
    if (tpNew != "txtp" && tpNew != "txtd") {
      for (let i = 1; i <= nTabViews; i++) {
        const mc = $(`#mtxt${i}`)
        if (`txt${i}` == tpNew) {
          mc.show()
        } else {
          mc.hide()
        }
      }
    }
    tpNewCtl.show()
    trNewCtl.show()
    tpNewCtl.addClass("ison")
    trNewCtl.addClass("ison")
    this.content.show()
    this.legend.hide()
    closeDialog(this.legend)
    this.legendc.hide()
    PG.material.adapt()
  }
}

