/* eslint-env jquery */
/* eslint-disable camelcase */

/* globals Config, set_heightw, versions, lan, letter */

let version

class RequestInfo {
  parameter(name) {
    return this.parameters()[name]
  }
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
  }
}

const set_vselect = (v, gotoword) => {
  const { words_url } = Config

  if (versions[v]) {
    $(`#version_${v}`).click(e => {
      e.preventDefault()
      version = v
      window.location.href =
        `${words_url}?version=${v}&lan=${lan}&letter=${letter}&goto=${gotoword}`
    })
  }
}

/* exported words_init */

const words_init = () => {
  $(".mvradio").removeClass("ison")
  const gotoword = RequestInfo.parameter("goto")
  for (const v in versions) {
    set_vselect(v, gotoword)
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
