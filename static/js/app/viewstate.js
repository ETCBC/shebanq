/* eslint-env jquery */
/* globals Config, P */

export class ViewState {
  constructor(init, pref) {
    this.data = init
    this.pref = pref
    this.from_push = false

    this.addHist()
  }

  getvars() {
    const { data } = this
    let vars = ""
    let sep = "?"
    for (const group in data) {
      const extra = group == "colormap" ? "c_" : ""
      for (const qw in data[group]) {
        for (const name in data[group][qw]) {
          vars += `${sep}${extra}${qw}${name}=${data[group][qw][name]}`
          sep = "&"
        }
      }
    }
    return vars
  }

  csv_url(vr, mr, qw, iid, tp, extra) {
    const { item_url } = Config

    let vars = `?version=${vr}&mr=${mr}&qw=${qw}&iid=${iid}&tp=${tp}&extra=${extra}`
    const data = P.vs.ddata()
    for (const name in data) {
      vars += `&${name}=${data[name]}`
    }
    return `${item_url}${vars}`
  }

  goback() {
    const state = History.getState()
    if (!this.from_push && state && state.data) {
      this.apply(state)
    }
  }

  addHist() {
    const { style, view_url } = Config

    let title
    if (this.mr() == "m") {
      title = `[${this.version()}] ${this.book()} ${this.chapter()}:${this.verse()}`
    } else {
      title = `${style[this.qw()]["Tag"]} ${this.iid()} p${this.page()}`
    }
    this.from_push = true
    History.pushState(this.data, title, view_url)
    this.from_push = false
  }

  apply(state) {
    if (state.data != undefined) {
      this.data = state.data
    }
    P.go()
  }

  delsv(group, qw, name) {
    delete this.data[group][qw][name]
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  setsv(group, qw, values) {
    for (const mb in values) {
      this.data[group][qw][mb] = values[mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  resetsv(group, qw) {
    for (const mb in this.data[group][qw]) {
      delete this.data[group][qw][mb]
    }
    $.cookie(this.pref + group + qw, this.data[group][qw])
  }

  mstatesv(values) {
    this.setsv("material", "", values)
  }
  dstatesv(values) {
    this.setsv("hebrewdata", "", values)
  }
  hstatesv(qw, values) {
    this.setsv("highlights", qw, values)
  }
  cstatesv(qw, values) {
    this.setsv("colormap", qw, values)
  }
  cstatex(qw, name) {
    this.delsv("colormap", qw, name)
  }
  cstatexx(qw) {
    this.resetsv("colormap", qw)
  }

  mstate() {
    return this.data["material"][""]
  }
  ddata() {
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
  pub(qw) {
    return this.data["highlights"][qw]["pub"]
  }
  colormap(qw) {
    return this.data["colormap"][qw]
  }
  color(qw, id) {
    return this.data["colormap"][qw][id]
  }
  iscolor(qw, cl) {
    return cl in this.data["colormap"][qw]
  }
}
