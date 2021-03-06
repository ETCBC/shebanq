/* eslint-env jquery */
/* eslint-disable no-new */
/* globals Config, ConfigW */

import { set_heightw } from "./page.js"

const RequestInfo = {
  parameter(name) {
    return this.parameters()[name]
  },
  parameters(uriGiven) {
    const uri = uriGiven || window.location.search
    if (uri.indexOf("?") === -1) {
      return {}
    }
    const query = uri.slice(1)
    const params = query.split("&")
    const result = {}
    let i = 0
    while (i < params.length) {
      const parameter = params[i].split("=")
      result[parameter[0]] = parameter[1]
      i++
    }
    return result
  },
}

class View {
  constructor(version) {
    this.version = version
    this.init()
  }

  set_vselect(v, gotoword) {
    const { words_url } = Config
    const { lan, letter } = ConfigW

    $(`#version_${v}`).click(e => {
      e.preventDefault()
      this.version = v
      window.location.href = `${words_url}?version=${v}&lan=${lan}&letter=${letter}&goto=${gotoword}`
    })
  }

  init() {
    $(".mvradio").removeClass("ison")
    const gotoword = RequestInfo.parameter("goto")
    const { versions } = Config
    const { version } = this

    for (const v of versions) {
      this.set_vselect(v, gotoword)
    }

    $(`#version_${version}`).addClass("ison")
    set_heightw()
    $("[wii]").hide()
    $("[gi]").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const i = elem.attr("gi")
      $(`[wi="${i}"]`).toggle()
      $(`[wii="${i}"]`).toggle()
    })
    $("[gi]").closest("td").removeClass("selecthlw")
    const wtarget = $(`[gi=${gotoword}]`).closest("td")
    if (wtarget != undefined) {
      wtarget.addClass("selecthlw")
      if (wtarget[0] != undefined) {
        wtarget[0].scrollIntoView()
      }
    }
  }
}

$(() => {
  const { version } = ConfigW
  new View(version)
})
