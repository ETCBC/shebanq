/* eslint-env jquery */
/* globals Config, P */

import { closeDialog, colorDefault } from "./helpers.js"

export class ColorPicker1 {
  /* the ColorPicker associated with individual items
   *
   * These pickers show up in lists of items (in mq and mw sidebars) and
   * near individual items (in rq and rw sidebars).
   * They also have a checkbox, stating whether the color counts as customized.
   * Customized colors are held in a global colormap,
   * which is saved in a cookie upon every picking action.
   *
   * All actions are processed by the highlight2 (!) method
   * of the associated Settings object.
   */
  constructor(qw, iid, isItem, doHighlight) {
    const { shbStyle, colors } = Config

    const pointer = isItem ? "me" : iid
    this.code = isItem ? "1a" : "1"
    this.qw = qw
    this.iid = iid
    this.picker = $(`#picker_${qw}${pointer}`)
    this.stl = shbStyle[qw]["prop"]
    this.sel = $(`#sel_${qw}${pointer}`)
    this.selw = $(`#sel_${qw}${pointer}>a`)
    this.select = $(`#select_${qw}${pointer}`)

    this.sel.click(e => {
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

    this.select.click(() => {
      /* process a click on the selectbox of the picker
       */
      const { qw, iid, picker } = this
      const wasCustom = P.viewState.iscolor(qw, iid)
      closeDialog(picker)
      if (wasCustom) {
        P.viewState.cstatex(qw, iid)
      } else {
        const vals = {}
        vals[iid] = colorDefault(qw == "q", iid)
        P.viewState.cstatesv(qw, vals)
        const active = P.viewState.active(qw)
        if (active != "hlcustom" && active != "hlmany") {
          P.viewState.hstatesv(qw, { active: "hlcustom" })
        }
      }
      P.viewState.addHist()
      this.apply(true)
    })

    $(`.c${qw}.${qw}${pointer}>a`).click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { picker } = this
      closeDialog(picker)

      const { qw, iid } = this
      const vals = {}
      vals[iid] = elem.html()
      P.viewState.cstatesv(qw, vals)
      P.viewState.hstatesv(qw, { active: "hlcustom" })
      P.viewState.addHist()
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
    const color = P.viewState.color(qw, iid) || colorDefault(qw == "q", iid)
    const target = qw == "q" ? sel : selw
    if (color) {
      target.css(stl, colors[color][qw])
      /* apply state to the selected cell
       */
    }
    select.prop("checked", P.viewState.iscolor(qw, iid))
    /* apply state to the checkbox
     */
    if (doHighlight) {
      P.highlight2(this)
    }
  }
}

export class ColorPicker2 {
  /* the ColorPicker associated with the view settings in a sidebar
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
   */
  constructor(qw, doHighlight) {
    const { shbStyle, colors } = Config

    this.code = "2"
    this.qw = qw
    this.picker = $(`#picker_${qw}one`)
    this.stl = shbStyle[this.qw]["prop"]
    this.sel = $(`#sel_${qw}one`)
    this.selw = $(`#sel_${qw}one>a`)

    this.sel.click(e => {
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

    $(`.c${qw}.${qw}one>a`).click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { picker } = this
      closeDialog(picker)
      const { qw } = this
      const curActive = P.viewState.active(qw)
      if (curActive != "hlone" && curActive != "hlcustom") {
        P.viewState.hstatesv(qw, { active: "hlcustom", sel_one: elem.html() })
      } else {
        P.viewState.hstatesv(qw, { sel_one: elem.html() })
      }
      P.viewState.addHist()
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
    const color = P.viewState.sel_one(qw) || colorDefault(qw, null)
    const target = qw == "q" ? sel : selw
    target.css(stl, colors[color][qw])
    /* apply state to the selected cell
     */
    if (doHighlight) {
      P.highlight2(this)
    }
  }
}
