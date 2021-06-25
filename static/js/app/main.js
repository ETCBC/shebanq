/* eslint-env jquery */
/* globals Config */

import { Page, LStorage } from "./page.js"
import { ViewState } from "./viewstate.js"

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = "/"

const setup = () => {
  /* top level, called when the page has loaded
   * inserts the Config global var
   */
  const { viewinit, pref } = Config
  window.L = new LStorage
  window.P = new Page(new ViewState(viewinit, pref))
}

const dynamics = () => {
  /* top level, called when the page has loaded
   * inserts the Config global var
   * P is the handle to manipulate the whole page
   */
  window.P.init()
  window.P.go()
}

$(() => {
  setup()
  dynamics()
})
