/* eslint-env jquery */
/* eslint-disable no-new */
/* globals Config, ConfigW */

/**
 * @module words
 */

import { DOC_NAME } from "./helpers.js"


const setHeightW = () => {
  /* the heights of the sidebars are set, depending on the height of the window
   */
  const subtractForWordsPage = 80
  const standardHeight = window.innerHeight - subtractForWordsPage
  $("#words").css("height", `${standardHeight}px`)
  $("#letters").css("height", `${standardHeight}px`)
}


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

/**
 * Handles a words overview page
 */
class View {
  constructor(version) {
    this.version = version
    this.init()
  }

  /**
   * Switch to another version
   *
   * @see [∈ version][elem-version]
   */
  selectVersion(v, gotoWord) {
    const { wordsPageUrl, featureHost } = Config
    const { lan, letter } = ConfigW
    const thisFeaturehost = `${featureHost}/${DOC_NAME}`
    $(".source").attr("href", thisFeaturehost)

    $(`#version_${v}`).off("click").click(e => {
      e.preventDefault()
      this.version = v
      window.location.href = `${wordsPageUrl}?version=${v}&lan=${lan}&letter=${letter}&goto=${gotoWord}`
    })
  }

  init() {
    $(".mvradio").removeClass("ison")
    const gotoWord = RequestInfo.parameter("goto")
    const { versions } = Config
    const { version } = this

    for (const v of versions) {
      this.selectVersion(v, gotoWord)
    }

    $(`#version_${version}`).addClass("ison")
    setHeightW()
    $("[wii]").hide()
    $("[gi]").off("click").click(e => {
      e.preventDefault()
      const elem = $(e.delegateTarget)
      const i = elem.attr("gi")
      $(`[wi="${i}"]`).toggle()
      $(`[wii="${i}"]`).toggle()
    })
    $("[gi]").closest("td").removeClass("selecthlw")
    const wordDest = $(`[gi=${gotoWord}]`).closest("td")
    if (wordDest != undefined) {
      wordDest.addClass("selecthlw")
      if (wordDest[0] != undefined) {
        wordDest[0].scrollIntoView()
      }
    }
  }
}

$(() => {
  const { version } = ConfigW
  new View(version)
})
