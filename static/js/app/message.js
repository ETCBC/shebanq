/* eslint-env jquery */

/**
 * @module message
 */

/**
 * Diagnostic output
 */
export class Message {
  constructor() {
    this.name = "material_message"
    this.hid = `#${this.name}`
  }

  add(response) {
    $(this.hid).html(response.children(this.hid).html())
  }

  msg(text) {
    $(this.hid).html(text)
  }
}

