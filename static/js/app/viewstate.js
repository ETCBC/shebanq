/* eslint-env jquery */
/* globals Config, PG */

/**
 * @module viewstate
 */

/**
 * Handles settings that cusomise the view of the page
 *
 * @see Corresponds to [M:VIEWSETTINGS.page][viewsettings.VIEWSETTINGS.page].
 */
export class ViewState {
  constructor(init, pref) {
    this.data = init
    this.pref = pref
    this.fromPush = false

    this.addHist()
  }

  getVars() {
    const { data } = this
    let vars = ""
    let sep = "?"
    for (const [group, subData] of Object.entries(data)) {
      const extra = group == "colormap" ? "c_" : ""
      for (const [qw, keyValues] of Object.entries(subData)) {
        for (const [key, value] of Object.entries(keyValues)) {
          vars += `${sep}${extra}${qw}${key}=${value}`
          sep = "&"
        }
      }
    }
    return vars
  }

  /**
   * Sets the precise url by which the user can request a csv download from the server.
   *
   * @see Triggers [C:hebrew.item][controllers.hebrew.item].
   */
  csvUrl(vr, mr, qw, iid, tp, extra) {
    const { itemCsvUrl } = Config

    let vars = `?version=${vr}&mr=${mr}&qw=${qw}&iid=${iid}&tp=${tp}&extra=${extra}`
    const data = this.getHebrew()
    for (const [key, value] of Object.entries(data)) {
      vars += `&${key}=${value}`
    }
    return `${itemCsvUrl}${vars}`
  }

  goback() {
    const state = History.getState()
    if (!this.fromPush && state && state.data) {
      if (state.data != undefined) {
        this.data = state.data
      }
      PG.go()
    }
  }

  addHist() {
    const { itemStyle, pageUrl } = Config

    let title
    if (this.mr() == "m") {
      title = `[${this.version()}] ${this.book()} ${this.chapter()}:${this.verse()}`
    } else {
      title = `${itemStyle[this.qw()]["Tag"]} ${this.iid()} p${this.page()}`
    }
    this.fromPush = true
    History.pushState(this.data, title, pageUrl)
    this.fromPush = false
  }

  del(group, qw, name) {
    delete this.data[group][qw][name]
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  set(group, qw, values) {
    for (const [mb, value] of Object.entries(values)) {
      this.data[group][qw][mb] = value
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  reset(group, qw) {
    for (const mb in this.data[group][qw]) {
      delete this.data[group][qw][mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  setMaterial(values) {
    this.set("material", "", values)
  }
  setHebrew(values) {
    this.set("hebrewdata", "", values)
  }
  setHighlight(qw, values) {
    this.set("highlights", qw, values)
  }
  setColor(qw, values) {
    this.set("colormap", qw, values)
  }
  delColor(qw, name) {
    this.del("colormap", qw, name)
  }
  delColorsAll(qw) {
    this.reset("colormap", qw)
  }
  getMaterial() {
    return this.data["material"][""]
  }
  getHebrew() {
    return this.data["hebrewdata"][""]
  }
  mr() {
    return this.data["material"][""]["mr"]
  }
  qw() {
    return this.data["material"][""]["qw"]
  }
  tp() {
    return this.data["material"][""]["tp"]
  }
  tr() {
    return this.data["material"][""]["tr"]
  }
  lang() {
    return this.data["material"][""]["lang"]
  }
  iid() {
    return this.data["material"][""]["iid"]
  }
  version() {
    return this.data["material"][""]["version"]
  }
  book() {
    return this.data["material"][""]["book"]
  }
  chapter() {
    return this.data["material"][""]["chapter"]
  }
  verse() {
    return this.data["material"][""]["verse"]
  }
  page() {
    return this.data["material"][""]["page"]
  }
  get(qw) {
    return this.data["highlights"][qw]["get"]
  }
  active(qw) {
    return this.data["highlights"][qw]["active"]
  }
  sel_one(qw) {
    return this.data["highlights"][qw]["sel_one"]
  }
  is_published(qw) {
    return this.data["highlights"][qw]["pub"]
  }
  colorMap(qw) {
    return this.data["colormap"][qw]
  }
  color(qw, id) {
    return this.data["colormap"][qw][id]
  }
  isColor(qw, cl) {
    return cl in this.data["colormap"][qw]
  }
}
