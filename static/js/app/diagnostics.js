/* eslint-env jquery */

/**
 * @module diagnostics
 */

/**
 * Handles diagnostic messages on the HTML page.
 *
 * When something goes wrong, messages can be displayed in
 * divs. There will also be a control to clear those messages.
 */
export class Diagnostics {
  constructor(destination, onClear) {
    this.destination = $(`#${destination}`)
    this.trashCtl = $(`#trash_${destination}`)
    this.onClear = onClear

    this.trashCtl.off("click").click(e => {
      e.preventDefault()
      this.clear()
    })
    this.trashCtl.hide()
  }

  clear() {
    this.destination.html("")
    if (this.onClear != undefined) {
      this.onClear()
    }
    this.trashCtl.hide()
  }
  hide() {
    this.destination.hide()
    this.trashCtl.hide()
  }
  show() {
    this.destination.show()
    if (this.destination.html() != "") {
      this.trashCtl.show()
    }
  }
  msg(msgobj) {
    const text = this.destination.html()
    this.destination.html(`${text}<p class="${msgobj[0]}">${msgobj[1]}</p>`)
    this.trashCtl.show()
  }
}
