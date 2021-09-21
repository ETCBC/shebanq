/* eslint-env jquery */
/* globals Config, P, State */

import { closeDialog, escHT } from "./helpers.js"
import { ColorPicker2 } from "./colorpicker.js"

export class MMessage {
  /* diagnostic output
   */
  constructor() {
    this.name = "material_message"
    this.hid = `#${this.name}`
  }

  add(response) {
    $(this.hid).html(response.children(this.hid).html())
  }

  msg(m) {
    $(this.hid).html(m)
  }
}

export class MContent {
  /* the actual Hebrew content, either plain text or tabbed data
   */
  constructor() {
    this.name_content = "#material_content"
    this.select = () => {}
  }

  add(response) {
    $(`#material_${P.viewState.tp()}`).html(response.children(this.name_content).html())
  }

  show() {
    const { nextTp } = Config

    const this_tp = P.viewState.tp()
    for (const tp in nextTp) {
      const this_material = $(`#material_${tp}`)
      if (this_tp == tp) {
        this_material.show()
      } else {
        this_material.hide()
      }
    }
  }
}

/* MATERIAL SETTINGS (for choosing between plain text and tabbed data)
 *
 */

export class MSettings {
  constructor(content) {
    const {
      featureHost,
      nextTp,
      nextTr,
      tabInfo,
      tabViews,
      trInfo,
      trLabels,
      versions,
    } = Config

    const hltext = $("#mtxtp")
    const hltabbed = $("#mtxt1")
    this.legend = $("#datalegend")
    this.legendc = $("#datalegend_control")
    this.name = "material_settings"
    this.hid = `#${this.name}`
    this.content = content
    this.hebrewsettings = new HebrewSettings()

    hltext.show()
    hltabbed.show()

    this.legendc.click(e => {
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

    $(".mhradio").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const tpOld = P.viewState.tp()
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
      P.viewState.mstatesv({ tp: tpNew })
      P.viewState.addHist()
      this.apply()
      const mr = P.viewState.mr()
      const qw = P.viewState.qw()
      if (mr == "r") {
        let extra = undefined
        if (qw == "q") {
          const { q } = State
          const first_name = escHT(q.first_name || "")
          const last_name = escHT(q.last_name || "")
          extra = `${first_name}_${last_name}`
        }
        for (const v of versions) {
          P.set_csv(v, mr, qw, P.viewState.iid(), extra)
        }
      }
    })

    $(".mtradio").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const trOld = P.viewState.tr()
      let trNew = elem.attr("id").substring(1)
      if (trOld == trNew) {
        trNew = nextTr[trOld]
      }

      P.viewState.mstatesv({ tr: trNew })
      P.viewState.addHist()
      this.apply()
    })

    for (let i = 1; i <= tabViews; i++) {
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
    const { tabViews } = Config

    const hlradio = $(".mhradio")
    const plradio = $(".mtradio")
    const tpNew = P.viewState.tp()
    const trNew = P.viewState.tr()
    const tpNewCtl = $(`#m${tpNew}`)
    const trNewCtl = $(`#m${trNew}`)
    hlradio.removeClass("ison")
    plradio.removeClass("ison")
    if (tpNew != "txtp" && tpNew != "txtd") {
      for (let i = 1; i <= tabViews; i++) {
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
    P.material.adapt()
  }
}

/* HEBREW DATA (which fields to show if interlinear text is displayed)
 *
 */

class HebrewSettings {
  constructor() {
    for (const fld in P.viewState.ddata()) {
      this[fld] = new HebrewSetting(fld)
    }
  }

  apply() {
    const { versions } = Config

    for (const fld in P.viewState.ddata()) {
      this[fld].apply()
    }
    for (const v of versions) {
      P.set_csv(v, P.viewState.mr(), P.viewState.qw(), P.viewState.iid())
    }
  }
}

class HebrewSetting {
  constructor(fld) {
    const { versions } = Config

    this.name = fld
    this.hid = `#${this.name}`
    $(this.hid).click(e => {
      const elem = $(e.delegateTarget)
      const vals = {}
      vals[fld] = elem.prop("checked") ? "v" : "x"
      P.viewState.dstatesv(vals)
      P.viewState.addHist()
      this.applysetting()
      for (const v of versions) {
        P.set_csv(v, P.viewState.mr(), P.viewState.qw(), P.viewState.iid())
      }
    })
  }

  apply() {
    const val = P.viewState.ddata()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }

  applysetting() {
    if (P.viewState.ddata()[this.name] == "v") {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.show()
      })
    } else {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.hide()
      })
    }
  }
}

export class LSettings {
  /* the view controls belonging to a side bar with a list of items
   */
  constructor(qw) {
    this.qw = qw

    const {
      sidebars: { side_fetched, sidebar },
    } = P

    if (qw != "n") {
      this.picker2 = new ColorPicker2(this.qw, false)
      const hlradio = $(`.${qw}hradio`)
      hlradio.click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        P.viewState.hstatesv(this.qw, { active: elem.attr("id").substring(1) })
        P.viewState.addHist()
        P.highlight2({ code: "3", qw: this.qw })
      })
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      pradio.click(e => {
        e.preventDefault()
        P.viewState.hstatesv(this.qw, { is_published: P.viewState.is_published(this.qw) == "x" ? "v" : "x" })
        side_fetched[`m${this.qw}`] = false
        sidebar[`m${this.qw}`].content.apply()
      })
    }
  }

  apply() {
    const { qw } = this
    if (P.viewState.get(qw) == "v") {
      if (qw != "n") {
        for (const iid in P.picker1list[qw]) {
          P.picker1list[qw][iid].apply(false)
        }
        P.picker2[qw].apply(true)
      }
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      if (P.viewState.is_published(qw) == "v") {
        pradio.addClass("ison")
      } else {
        pradio.removeClass("ison")
      }
    }
  }
}
