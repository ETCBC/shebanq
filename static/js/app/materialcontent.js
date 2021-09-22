/* eslint-env jquery */
/* globals Config, VS */

export class MaterialContent {
  /* the actual Hebrew content, either plain text or tabbed data
   */
  constructor() {
    this.nameContent = "#material_content"
    this.select = () => {}
  }

  add(response) {
    $(`#material_${VS.tp()}`).html(response.children(this.nameContent).html())
  }

  show() {
    const { nextTp } = Config

    const thisTp = VS.tp()
    for (const tp in nextTp) {
      const thisMaterial = $(`#material_${tp}`)
      if (thisTp == tp) {
        thisMaterial.show()
      } else {
        thisMaterial.hide()
      }
    }
  }
}

