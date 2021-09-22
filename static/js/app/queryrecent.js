/* eslint-env jquery */
/* globals Config */

import { Diagnostics } from "./diagnostics.js"

export class QueryRecent {
  constructor(treeObj) {
    this.treeObj = treeObj
    this.loaded = false
    this.queries = []
    this.diagnostics = new Diagnostics("msg_qr")
    this.refreshCtl = $("#reload_recentq")

    this.diagnostics.clear()
    this.refreshCtl.click(e => {
      e.preventDefault()
      this.fetch()
    })
    this.apply()
  }

  apply() {
    this.fetch()
  }

  fetch() {
    const { queriesRecentJsonUrl } = Config

    this.diagnostics.msg(["info", "fetching recent queries ..."])
    $.post(queriesRecentJsonUrl, {}, json => {
      this.loaded = true
      this.diagnostics.clear()
      const { msgs, good, queries } = json
      for (const m of msgs) {
        this.diagnostics.msg(m)
      }
      if (good) {
        this.queries = queries
        this.process()
      }
    })
  }
  process() {
    this.genHtml()
    this.dressQueries()
  }
  genHtml() {
    const dest = $("#recentqi")
    const { queries } = this
    let html = ""
    for (let n = 0; n < queries.length; n++) {
      const { id, text, title, version } = queries[n]
      html += `<a class="q" query_id="${id}"
          v="${version}" href="#"
          title="${title}">${text}</a><br/>
      `
    }
    dest.html(html)
  }

  dressQueries() {
    const { treeObj } = this
    $("#recentqi a[query_id]").each((i, el) => {
      const elem = $(el)
      elem.click(e => {
        e.preventDefault()
        treeObj.filter.clear()
        treeObj.gotoQuery(elem.attr("query_id"))
      })
    })
  }
}
