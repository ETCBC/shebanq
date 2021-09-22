/* eslint-env jquery */

export class Message {
  /* diagnostic output
   */
  constructor() {
    this.name = "material_message"
    this.hid = `#${this.name}`
  }

  add(response) {
    $(this.hid).html(response.children(this.hid).html())
  }

  msg(m) {
    $(this.hid).html(m)
  }
}

