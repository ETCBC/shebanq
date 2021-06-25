/* eslint-env jquery */

export class Msg {
  constructor(destination, on_clear) {
    this.destination = $(`#${destination}`)
    this.trashc = $(`#trash_${destination}`)
    this.on_clear = on_clear

    this.trashc.click(e => {
      e.preventDefault()
      this.clear()
    })
    this.trashc.hide()
  }

  clear() {
    this.destination.html("")
    if (this.on_clear != undefined) {
      this.on_clear()
    }
    this.trashc.hide()
  }
  hide() {
    this.destination.hide()
    this.trashc.hide()
  }
  show() {
    this.destination.show()
    if (this.destination.html() != "") {
      this.trashc.show()
    }
  }
  msg(msgobj) {
    const mtext = this.destination.html()
    this.destination.html(`${mtext}<p class="${msgobj[0]}">${msgobj[1]}</p>`)
    this.trashc.show()
  }
}
