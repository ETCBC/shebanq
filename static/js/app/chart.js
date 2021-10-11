/* eslint-env jquery */
/* globals Config, PG, VS */

/**
 * @module chart
 */

import { colorDefault } from "./helpers.js"

/**
 * number of chapters in a row in a chart
 */
const chartCols = 30


/**
 * Class for chart slection and generation
 *
 * @see also the server code [M:CHART][chart.CHART].
 */
export class Chart {
  constructor(vr, qw) {
    this.vr = vr
    this.qw = qw
    this.control = `#select_control_chart_${vr}_${qw}`
    this.select = `#select_contents_chart_${vr}_${qw}`
    this.loaded = {}
  }

  init() {
    $(this.control).off("click").click(e => {
      e.preventDefault()
      this.apply()
    })
  }

  /**
   * Method for chart slection and generation
   */
  apply() {
    if (!this.loaded[`${this.qw}_${PG.iid}`]) {
      if ($(`#select_contents_chart_${this.vr}_${this.qw}_${PG.iid}`).length == 0) {
        $(this.select).append(
          `<span id="select_contents_chart_${this.vr}_${this.qw}_${PG.iid}"></span>`
        )
      }
      this.fetch(PG.iid)
    } else {
      this.show()
    }
  }

  /**
   * get the material by AJAX if needed, and process the material afterward
   *
   * @see Triggers [C:hebrew.chart][controllers.hebrew.chart]
   */
  fetch(iid) {
    const { chartUrl } = Config

    const vars = `?version=${this.vr}&qw=${this.qw}&iid=${iid}`
    $(`${this.select}_${iid}`).load(
      `${chartUrl}${vars}`,
      () => {
        this.loaded[`${this.qw}_${iid}`] = true
        this.process(iid)
      },
      "html"
    )
  }

  process(iid) {
    this.genHtml(iid)
    $(`${this.select}_${iid} .chartnav`).each((i, el) => {
      const elem = $(el)
      this.addItem(elem, iid)
    })
    $("#theitemc").off("click").click(e => {
      e.preventDefault()
      const vals = {}
      vals["iid"] = iid
      vals["mr"] = "r"
      vals["version"] = this.vr
      vals["qw"] = this.qw
      VS.setMaterial(vals)
      VS.addHist()
      PG.go()
    })
    $("#theitemc").html(`Back to ${$("#theitem").html()} (version ${this.vr})`)
    /* fill in the Back to query/word line in a chart
     */
    this.present(iid)
    this.show(iid)
  }

  present(iid) {
    const { itemStyle } = Config
    const { chartWidth } = PG

    $(`${this.select}_${iid}`).dialog({
      autoOpen: false,
      dialogClass: "items",
      closeOnEscape: true,
      close: () => {
        this.loaded[`${this.qw}_${iid}`] = false
        $(`${this.select}_${iid}`).html("")
      },
      modal: false,
      title: `chart for ${itemStyle[this.qw]["tag"]} (version ${this.vr})`,
      width: chartWidth,
      position: { my: "left top", at: "left top", of: window },
    })
  }

  show(iid) {
    $(`${this.select}_${iid}`).dialog("open")
  }

  genHtml(iid) {
    /**
     * generate a chart
     */
    const { itemStyle, colorsCls } = Config

    const msg = $("#r_msg").val()

    let nBooks = 0
    let bookList = $(`#r_chartorder${this.qw}`).val()
    let bookData = $(`#r_chart${this.qw}`).val()
    if (bookList) {
      bookList = $.parseJSON(bookList)
      bookData = $.parseJSON(bookData)
      nBooks = bookList.length
    } else {
      bookList = []
      bookData = {}
    }
    let html = ""
    if (msg) {
      html += `<p>${msg}</p>`
    }
    html += `
      <p>
        <a id="theitemc"
          title="back to ${itemStyle[this.qw]["tag"]} (version ${this.vr})"
          href="#">back</a>
      </p>
      <table class="chart">`

    const nColorsC = colorsCls.length
    for (const book of bookList) {
      const blocks = bookData[book]
      html += `
        <tr>
          <td class="bnm">${book}</td>
          <td class="chp"><table class="chp">
        <tr>`
      let col = 0
      for (const blockInfo of blocks) {
        if (col == chartCols) {
          html += "</tr><tr>"
          col = 0
        }
        const chapterNum = blockInfo[0]
        const chapterRange = `${blockInfo[1]}-${blockInfo[2]}`
        const blockResults = blockInfo[3]
        const blockSize = blockInfo[4]
        const blockCategory =
          blockResults >= nColorsC ? nColorsC - 1 : blockResults
        const z = colorsCls[blockCategory]
        let fill = "&nbsp;"
        let size = ""
        let cls = ""
        if (blockSize < 25) {
          fill = "="
          cls = "s1"
        } else if (blockSize < 75) {
          fill = "-"
          cls = "s5"
        }
        if (blockSize < 100) {
          size = ` (${blockSize}%)`
        }
        html += `
          <td class="${z}">
            <a
              title="${chapterRange}${size}: ${blockResults}"
              class="chartnav ${cls}"
              href="#"
              b=${book} ch="${chapterNum}"
            >${fill}</a>
          </td>`
        col++
      }
      html += "</tr></table></td></tr>"
    }
    html += "</table>"
    $(`${this.select}_${iid}`).html(html)
    return nBooks
  }

  addItem(item, iid) {
    item.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      let vals = {}
      vals["book"] = elem.attr("b")
      vals["chapter"] = elem.attr("ch")
      vals["mr"] = "m"
      vals["version"] = this.vr
      VS.setMaterial(vals)
      VS.setHighlight("q", { sel_one: "white", active: "hlcustom" })
      VS.setHighlight("w", { sel_one: "black", active: "hlcustom" })
      VS.delColorsAll("q")
      VS.delColorsAll("w")
      if (this.qw != "n") {
        vals = {}
        vals[iid] = VS.colorMap(this.qw)[iid] || colorDefault(this.qw == "q", iid)
        VS.setColor(this.qw, vals)
      }
      VS.addHist()
      PG.go()
    })
  }
}
