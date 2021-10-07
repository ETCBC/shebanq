/* eslint-env jquery */
/* globals Config */

/**
 * @module main
 */

import { LStorage } from "./localstorage.js"
import { Page } from "./page.js"
import { ViewState } from "./viewstate.js"

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = "/"

const setup = () => {
  /* top level, called when the page has loaded
   * inserts the Config global var
   */
  const { viewInit, pref } = Config
  window.LS = new LStorage()
  const VS = new ViewState(viewInit, pref)
  window.VS = VS
  window.PG = new Page()
  History.Adapter.bind(window, "statechange", VS.goback.bind(VS))
}

const dynamics = () => {
  /* top level, called when the page has loaded
   * inserts the Config global var
   * PG is the handle to manipulate the whole page
   */
  window.PG.init()
  window.PG.go()
}

$(() => {
  setup()
  dynamics()
})
