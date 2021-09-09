/* eslint-env jquery */
/* globals Config, P */

import { close_dialog, defcolor } from "./helpers.js"

export class Colorpicker1 {
  /* the colorpicker associated with individual items
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
  constructor(qw, iid, is_item, do_highlight) {
    const { style, vcolors } = Config

    const pointer = is_item ? "me" : iid
    this.code = is_item ? "1a" : "1"
    this.qw = qw
    this.iid = iid
    this.picker = $(`#picker_${qw}${pointer}`)
    this.stl = style[qw]["prop"]
    this.sel = $(`#sel_${qw}${pointer}`)
    this.selw = $(`#sel_${qw}${pointer}>a`)
    this.selc = $(`#selc_${qw}${pointer}`)

    this.sel.click(e => {
      e.preventDefault()
      this.picker.dialog({
        dialogClass: "picker_dialog",
        closeOnEscape: true,
        modal: true,
        title: "choose a color",
        position: { my: "right top", at: "left top", of: this.selc },
        width: "200px",
      })
    })

    this.selc.click(() => {
      /* process a click on the selectbox of the picker
       */
      const { qw, iid, picker } = this
      const was_cust = P.vs.iscolor(qw, iid)
      close_dialog(picker)
      if (was_cust) {
        P.vs.cstatex(qw, iid)
      } else {
        const vals = {}
        vals[iid] = defcolor(qw == "q", iid)
        P.vs.cstatesv(qw, vals)
        const active = P.vs.active(qw)
        if (active != "hlcustom" && active != "hlmany") {
          P.vs.hstatesv(qw, { active: "hlcustom" })
        }
      }
      P.vs.addHist()
      this.apply(true)
    })

    $(`.c${qw}.${qw}${pointer}>a`).click(e => {
      /* process a click on a colored cell of the picker
       */
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const { picker } = this
      close_dialog(picker)

      const { qw, iid } = this
      const vals = {}
      vals[iid] = elem.html()
      P.vs.cstatesv(qw, vals)
      P.vs.hstatesv(qw, { active: "hlcustom" })
      P.vs.addHist()
      this.apply(true)
    })

    this.picker.hide()
    $(`.c${qw}.${qw}${pointer}>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(this.stl, vcolors[elem.html()][qw])
    })
    this.apply(do_highlight)
  }

  adapt(iid, do_highlight) {
    this.iid = iid
    this.apply(do_highlight)
  }

  apply(do_highlight) {
    const { vcolors } = Config

    const { qw, iid, stl, sel, selc, selw } = this
    const color = P.vs.color(qw, iid) || defcolor(qw == "q", iid)
    const target = qw == "q" ? sel : selw
    if (color) {
      target.css(stl, vcolors[color][qw])
      /* apply state to the selected cell
       */
    }
    selc.prop("checked", P.vs.iscolor(qw, iid))
    /* apply state to the checkbox
     */
    if (do_highlight) {
      P.highlight2(this)
    }
  }
}

export class Colorpicker2 {
  /* the colorpicker associated with the view settings in a sidebar
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
  constructor(qw, do_highlight) {
    const { style, vcolors } = Config

    this.code = "2"
    this.qw = qw
    this.picker = $(`#picker_${qw}one`)
    this.stl = style[this.qw]["prop"]
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
      close_dialog(picker)
      const { qw } = this
      const current_active = P.vs.active(qw)
      if (current_active != "hlone" && current_active != "hlcustom") {
        P.vs.hstatesv(qw, { active: "hlcustom", sel_one: elem.html() })
      } else {
        P.vs.hstatesv(qw, { sel_one: elem.html() })
      }
      P.vs.addHist()
      this.apply(true)
    })

    this.picker.hide()

    $(`.c${qw}.${qw}one>a`).each((i, el) => {
      /* initialize the individual color cells in the picker
       */
      const elem = $(el)
      const { qw, stl } = this
      const target = qw == "q" ? elem.closest("td") : elem
      target.css(stl, vcolors[elem.html()][qw])
    })
    this.apply(do_highlight)
  }

  apply(do_highlight) {
    const { vcolors } = Config

    const { qw, stl, sel, selw } = this
    const color = P.vs.sel_one(qw) || defcolor(qw, null)
    const target = qw == "q" ? sel : selw
    target.css(stl, vcolors[color][qw])
    /* apply state to the selected cell
     */
    if (do_highlight) {
      P.highlight2(this)
    }
  }
}
