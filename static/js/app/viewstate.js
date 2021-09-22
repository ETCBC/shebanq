/* eslint-env jquery */
/* globals Config, PG */

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
    for (const group in data) {
      const extra = group == "colorMap" ? "c_" : ""
      for (const qw in data[group]) {
        for (const name in data[group][qw]) {
          vars += `${sep}${extra}${qw}${name}=${data[group][qw][name]}`
          sep = "&"
        }
      }
    }
    return vars
  }

  csvUrl(vr, mr, qw, iid, tp, extra) {
    const { itemCsvUrl } = Config

    let vars = `?version=${vr}&mr=${mr}&qw=${qw}&iid=${iid}&tp=${tp}&extra=${extra}`
    const data = this.getHebrew()
    for (const name in data) {
      vars += `&${name}=${data[name]}`
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
    for (const mb in values) {
      this.data[group][qw][mb] = values[mb]
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
    this.set("colorMap", qw, values)
  }
  delColor(qw, name) {
    this.del("colorMap", qw, name)
  }
  delColorsAll(qw) {
    this.reset("colorMap", qw)
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
    return this.data["colorMap"][qw]
  }
  color(qw, id) {
    return this.data["colorMap"][qw][id]
  }
  isColor(qw, cl) {
    return cl in this.data["colorMap"][qw]
  }
}
