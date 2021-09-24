/* eslint-env jquery */
/* globals Config, PG, VS */

import { Chart } from "./chart.js"
import { SideContent } from "./sidecontent.js"

export class Sidebars {
  /* TOP LEVEL: all four kinds of sidebars
   */
  constructor() {
    this.sidebar = {}
    for (const mr of ["m", "r"]) {
      for (const qw of ["q", "w", "n"]) {
        this.sidebar[`${mr}${qw}`] = new Sidebar(mr, qw)
      }
    }
    this.sideFetched = {}
  }

  apply() {
    for (const mr of ["m", "r"]) {
      for (const qw of ["q", "w", "n"]) {
        this.sidebar[`${mr}${qw}`].apply()
      }
    }
  }

  afterMaterialFetch() {
    for (const qw of ["q", "w", "n"]) {
      this.sideFetched[`m${qw}`] = false
    }
  }

  afterItemFetch() {
    for (const qw of ["q", "w", "n"]) {
      this.sideFetched[`r${qw}`] = false
    }
  }
}

/* SPECIFIC sidebars, the [mr][qw] type is frozen into the object
 *
 */

class Sidebar {
  /* the individual sidebar, parametrized with mr and qw
   * to specify one of the four kinds
   */
  constructor(mr, qw) {
    const { versions } = Config

    this.mr = mr
    this.qw = qw
    this.name = `side_bar_${mr}${qw}`
    this.hid = `#${this.name}`
    this.hide = $(`#side_hide_${mr}${qw}`)
    this.show = $(`#side_show_${mr}${qw}`)
    this.content = new SideContent(mr, qw)

    if (mr == "r") {
      this.chart = {}
      for (const v of versions) {
        this.addVersion(v)
      }
    }
    this.show.off("click").click(e => {
      e.preventDefault()
      VS.setHighlight(this.qw, { get: "v" })
      VS.addHist()
      this.apply()
    })

    this.hide.off("click").click(e => {
      e.preventDefault()
      VS.setHighlight(this.qw, { get: "x" })
      VS.addHist()
      this.apply()
    })
  }

  addVersion(v) {
    const { qw } = this
    this.chart[v] = new Chart(v, qw)
  }

  apply() {
    const { mr, qw, hide, show } = this
    const thebar = $(this.hid)
    const thelist = $(`#side_material_${mr}${qw}`)
    const theset = $(`#side_settings_${mr}${qw}`)
    if (this.mr != PG.mr || (this.mr == "r" && this.qw != PG.qw)) {
      thebar.hide()
    } else {
      thebar.show()
      theset.show()
      if (this.mr == "m") {
        if (VS.get(this.qw) == "x") {
          thelist.hide()
          theset.hide()
          hide.hide()
          show.show()
        } else {
          thelist.show()
          theset.show()
          hide.show()
          show.hide()
        }
      } else {
        hide.hide()
        show.hide()
      }
      this.content.apply()
    }
  }
}

