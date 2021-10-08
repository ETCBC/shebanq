/* eslint-env jquery */
/* globals Config */

/**
 * @module queryrecent
 */

import { Diagnostics } from "./diagnostics.js"

/**
 * Controls the widget for recent queries on the
 * query overview page.
 */
export class QueryRecent {
  constructor(treeObj) {
    this.treeObj = treeObj
    this.loaded = false
    this.queries = []
    this.diagnostics = new Diagnostics("msg_qr")
    this.refreshCtl = $("#reload_recentq")

    this.diagnostics.clear()
    this.refreshCtl.off("click").click(e => {
      e.preventDefault()
      this.fetch()
    })
    this.apply()
  }

  apply() {
    this.fetch()
  }

  /**
   * get the material by AJAX if needed, and process the material afterward
   *
   * @see Triggers [C:hebrew.queriesr][controllers.hebrew.queriesr]
   */
  fetch() {
    const { queriesRecentJsonUrl } = Config

    this.diagnostics.msg(["info", "fetching recent queries ..."])
    $.post(queriesRecentJsonUrl, {}, json => {
      this.loaded = true
      this.diagnostics.clear()
      const { msgs, good, queries } = json
      for (const mg of msgs) {
        this.diagnostics.msg(mg)
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
    for (const query of queries) {
      const { id, text, title, version } = query
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
      elem.off("click").click(e => {
        e.preventDefault()
        treeObj.filter.clear()
        treeObj.gotoQuery(elem.attr("query_id"))
      })
    })
  }
}
