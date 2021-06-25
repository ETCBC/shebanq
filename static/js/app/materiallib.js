/* eslint-env jquery */
/* globals Config, P */

import { close_dialog } from "./helpers.js"
import { Colorpicker2 } from "./colorpicker.js"


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
    $(`#material_${P.vs.tp()}`).html(response.children(this.name_content).html())
  }

  show() {
    const { next_tp } = Config

    const this_tp = P.vs.tp()
    for (const tp in next_tp) {
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
    const { featurehost } = Config

    const { next_tp, next_tr, tab_info, tab_views, tr_info, tr_labels } = Config

    const hltext = $("#mtxt_p")
    const hltabbed = $("#mtxt_tb1")
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
          const url = `${featurehost}/${elem.attr("fname")}`
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
      const elem = $(e.target)
      const old_tp = P.vs.tp()
      let new_tp = elem.attr("id").substring(1)
      if (old_tp == "txt_p") {
        if (old_tp == new_tp) {
          return
        }
      } else if (old_tp == new_tp) {
        new_tp = next_tp[old_tp]
        if (new_tp == "txt_p") {
          new_tp = next_tp[new_tp]
        }
      }
      P.vs.mstatesv({ tp: new_tp })
      P.vs.addHist()
      this.apply()
    })

    $(".mtradio").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const old_tr = P.vs.tr()
      let new_tr = elem.attr("id").substring(1)
      if (old_tr == new_tr) {
        new_tr = next_tr[old_tr]
      }

      P.vs.mstatesv({ tr: new_tr })
      P.vs.addHist()
      this.apply()
    })

    for (let i = 1; i <= tab_views; i++) {
      const mc = $(`#mtxt_tb${i}`)
      mc.attr("title", tab_info[`txt_tb${i}`])
      if (i == 1) {
        mc.show()
      } else {
        mc.hide()
      }
    }

    for (const l in tr_labels) {
      const t = tr_info[l]
      const mc = $(`#m${t}`)
      mc.attr("title", tr_labels[t])
      if (l == "hb") {
        mc.show()
      } else {
        mc.hide()
      }
    }
  }

  apply() {
    const { tab_views } = Config

    const hlradio = $(".mhradio")
    const plradio = $(".mtradio")
    const new_tp = P.vs.tp()
    const new_tr = P.vs.tr()
    const newc = $(`#m${new_tp}`)
    const newp = $(`#m${new_tr}`)
    hlradio.removeClass("ison")
    plradio.removeClass("ison")
    if (new_tp != "txt_p" && new_tp != "txt_il") {
      for (let i = 1; i <= tab_views; i++) {
        const mc = $(`#mtxt_tb${i}`)
        if (`txt_tb${i}` == new_tp) {
          mc.show()
        } else {
          mc.hide()
        }
      }
    }
    newc.show()
    newp.show()
    newc.addClass("ison")
    newp.addClass("ison")
    this.content.show()
    this.legend.hide()
    close_dialog(this.legend)
    this.legendc.hide()
    P.material.adapt()
  }
}

/* HEBREW DATA (which fields to show if interlinear text is displayed)
 *
 */

class HebrewSettings {
  constructor() {
    for (const fld in P.vs.ddata()) {
      this[fld] = new HebrewSetting(fld)
    }
  }

  apply() {
    const { versions } = Config

    for (const fld in P.vs.ddata()) {
      this[fld].apply()
    }
    for (const v of versions) {
      P.set_csv(v, P.vs.mr(), P.vs.qw(), P.vs.iid())
    }
  }
}

class HebrewSetting {
  constructor(fld) {
    const { versions } = Config

    this.name = fld
    this.hid = `#${this.name}`
    $(this.hid).click(e => {
      const elem = $(e.target)
      const vals = {}
      vals[fld] = elem.prop("checked") ? "v" : "x"
      P.vs.dstatesv(vals)
      P.vs.addHist()
      this.applysetting()
      for (const v of versions) {
        P.set_csv(v, P.vs.mr(), P.vs.qw(), P.vs.iid())
      }
    })
  }

  apply() {
    const val = P.vs.ddata()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }

  applysetting() {
    if (P.vs.ddata()[this.name] == "v") {
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

    const { sidebars: { side_fetched, sidebar } } = P

    if (qw != "n") {
      this.picker2 = new Colorpicker2(this.qw, false)
      const hlradio = $(`.${qw}hradio`)
      hlradio.click(e => {
        e.preventDefault()
        const elem = $(e.target)
        P.vs.hstatesv(this.qw, { active: elem.attr("id").substring(1) })
        P.vs.addHist()
        P.highlight2({ code: "3", qw: this.qw })
      })
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      pradio.click(e => {
        e.preventDefault()
        P.vs.hstatesv(this.qw, { pub: P.vs.pub(this.qw) == "x" ? "v" : "x" })
        side_fetched[`m${this.qw}`] = false
        sidebar[`m${this.qw}`].content.apply()
      })
    }
  }

  apply() {
    const { qw } = this
    if (P.vs.get(qw) == "v") {
      if (qw != "n") {
        for (const iid in P.picker1list[qw]) {
          P.picker1list[qw][iid].apply(false)
        }
        P.picker2[qw].apply(true)
      }
    }
    if (qw == "q" || qw == "n") {
      const pradio = $(`.${qw}pradio`)
      if (P.vs.pub(qw) == "v") {
        pradio.addClass("ison")
      } else {
        pradio.removeClass("ison")
      }
    }
  }
}

