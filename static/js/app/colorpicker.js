/* eslint-env jquery */
/* globals Config, PG, VS */

/**
 * @module colorpicker
 */

import { closeDialog, colorDefault } from "./helpers.js"

/**
 * The ColorPicker associated with individual items
 *
 * These pickers show up in lists of items (in mq and mw sidebars) and
 * near individual items (in rq and rw sidebars).
 * They also have a checkbox, stating whether the color counts as customized.
 * Customized colors are held in a global colorMap,
 * which is saved in a cookie upon every picking action.
 *
 * All actions are processed by the highlight2 (!) method
 * of the associated Settings object.
 *
 * @see [∈ highlight-select-single-color][elem-highlight-select-single-color]
 * @see [∈ highlight-select-color][elem-highlight-select-color]
 */
export class ColorPicker1 {
  constructor(qw, iid, isItem, doHighlight) {
    const { itemStyle, colors } = Config

    const pointer = isItem ? "me" : iid
    this.code = isItem ? "1a" : "1"
    this.qw = qw
    this.iid = iid
    this.picker = $(`#picker_${qw}${pointer}`)
    this.stl = itemStyle[qw]["prop"]
    this.sel = $(`#sel_${qw}${pointer}`)
    this.selw = $(`#sel_${qw}${pointer}>a`)
    this.select = $(`#select_${qw}${pointer}`)

    this.sel.off("click").click(e => {
      e.preventDefault()
      this.picker.dialog({
        dialogClass: "picker_dialog",
        closeOnEscape: true,
        modal: true,
        title: "choose a color",
        position: { my: "right top", at: "left top", of: this.select },
        width: "200px",
      })
    })

    this.select.off("click").click(() => {
      /* process a click on the selectbox of the picker
       */
      const { qw, iid, picker } = this
      const wasCustom = VS.isColor(qw, iid)
      closeDialog(picker)
      if (wasCustom) {
        VS.delColor(qw, iid)
      } else {
        const vals = {}
        vals[iid] = colorDefault(qw == "q", iid)
        VS.setColor(qw, vals)
        const active = VS.active(qw)
        if (active != "hlcustom" && active != "hlmany") {
          VS.setHighlight(qw, { active: "hlcustom" })
        }
      }
      VS.addHist()
      this.apply(true)
    })

    $(`.c${qw}.${qw}${pointer}>a`).off("click").click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { picker } = this
      closeDialog(picker)

      const { qw, iid } = this
      const vals = {}
      vals[iid] = elem.html()
      VS.setColor(qw, vals)
      VS.setHighlight(qw, { active: "hlcustom" })
      VS.addHist()
      this.apply(true)
    })

    this.picker.hide()
    $(`.c${qw}.${qw}${pointer}>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(this.stl, colors[elem.html()][qw])
    })
    this.apply(doHighlight)
  }

  adapt(iid, doHighlight) {
    this.iid = iid
    this.apply(doHighlight)
  }

  apply(doHighlight) {
    const { colors } = Config

    const { qw, iid, stl, sel, select, selw } = this
    const color = VS.color(qw, iid) || colorDefault(qw == "q", iid)
    const target = qw == "q" ? sel : selw
    if (color) {
      target.css(stl, colors[color][qw])
      /* apply state to the selected cell
       */
    }
    select.prop("checked", VS.isColor(qw, iid))
    /* apply state to the checkbox
     */
    if (doHighlight) {
      PG.highlight2(this)
    }
  }
}

/**
 * The ColorPicker associated with the view settings in a sidebar
 *
 * These pickers show up at the top of the individual sidebars,
 * only on mq and mw sidebars.
 * They are used to control the uniform color with which
 * the results are to be painted.
 * They can be configured for dealing with background or foreground painting.
 * The paint actions depend on the mode of coloring
 * that the user has selected in settings.
 * So the paint logic is more involved.
 * But there is no associated checkbox.
 * The selected color is stored in the highlight settings,
 * which are synchronized in a cookie.
 * All actions are processed by the highlight2 method
 * of the associated Settings object.
 *
 * @see [∈ highlight-select-single-color][elem-highlight-select-single-color]
 */
export class ColorPicker2 {
  constructor(qw, doHighlight) {
    const { itemStyle, colors } = Config

    this.code = "2"
    this.qw = qw
    this.picker = $(`#picker_${qw}one`)
    this.stl = itemStyle[this.qw]["prop"]
    this.sel = $(`#sel_${qw}one`)
    this.selw = $(`#sel_${qw}one>a`)

    this.sel.off("click").click(e => {
      e.preventDefault()
      this.picker.dialog({
        dialogClass: "picker_dialog",
        closeOnEscape: true,
        modal: true,
        title: "choose a color",
        position: { my: "right top", at: "left top", of: this.sel },
        width: "200px",
      })
    })

    $(`.c${qw}.${qw}one>a`).off("click").click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { picker } = this
      closeDialog(picker)
      const { qw } = this
      const curActive = VS.active(qw)
      if (curActive != "hlone" && curActive != "hlcustom") {
        VS.setHighlight(qw, { active: "hlcustom", sel_one: elem.html() })
      } else {
        VS.setHighlight(qw, { sel_one: elem.html() })
      }
      VS.addHist()
      this.apply(true)
    })

    this.picker.hide()

    $(`.c${qw}.${qw}one>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw, stl } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(stl, colors[elem.html()][qw])
    })
    this.apply(doHighlight)
  }

  apply(doHighlight) {
    const { colors } = Config

    const { qw, stl, sel, selw } = this
    const color = VS.sel_one(qw) || colorDefault(qw, null)
    const target = qw == "q" ? sel : selw
    target.css(stl, colors[color][qw])
    /* apply state to the selected cell
     */
    if (doHighlight) {
      PG.highlight2(this)
    }
  }
}
