/* eslint-env jquery */
/* globals PG, VS */

/**
 * @module sidesettings
 */

import { ColorPicker2 } from "./colorpicker.js"

/**
 * Handles the view controls belonging to a side bar with a list of items
 *
 * @see [M:viewdefs.Make]
 *
 * @see Page elements:
 *
 * *   [∈ highlight-published][elem-highlight-published]
 * *   [∈ highlight-reset][elem-highlight-reset]
 * *   [∈ highlight-many][elem-highlight-many]
 * *   [∈ highlight-custom][elem-highlight-custom]
 * *   [∈ highlight-one][elem-highlight-one]
 * *   [∈ highlight-off][elem-highlight-off]
 * *   [∈ highlight-select-single-color][elem-highlight-select-single-color]
 */
export class SideSettings {
  constructor(qw) {
    this.qw = qw

    const {
      sidebars: { sideFetched, sidebar },
    } = PG

    if (qw != "n") {
      this.picker2 = new ColorPicker2(this.qw, false)
      const highlightRadio = $(`.${qw}hradio`)
      highlightRadio.off("click").click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        VS.setHighlight(this.qw, { active: elem.attr("id").substring(1) })
        VS.addHist()
        PG.highlight2({ code: "3", qw: this.qw })
      })
    }
    if (qw == "q" || qw == "n") {
      const publishedCtl = $(`.${qw}pradio`)
      publishedCtl.off("click").click(e => {
        e.preventDefault()
        VS.setHighlight(this.qw, { pub: VS.is_published(this.qw) == "x" ? "v" : "x" })
        sideFetched[`m${this.qw}`] = false
        sidebar[`m${this.qw}`].content.apply()
      })
    }
  }

  apply() {
    const { qw } = this
    if (VS.get(qw) == "v") {
      if (qw != "n") {
        for (const picker of Object.values(PG.picker1List[qw])) {
          picker.apply(false)
        }
        PG.picker2[qw].apply(true)
      }
    }
    if (qw == "q" || qw == "n") {
      const publishedCtl = $(`.${qw}pradio`)
      if (VS.is_published(qw) == "v") {
        publishedCtl.addClass("ison")
      } else {
        publishedCtl.removeClass("ison")
      }
    }
  }
}
