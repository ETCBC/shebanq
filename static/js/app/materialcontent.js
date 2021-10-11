/* eslint-env jquery */
/* globals Config, VS */

/**
 * @module materialcontent
 */

/**
 * Deals with the actual Hebrew content.
 *
 * It provides a name for material,
 * such as the name of the query of which the material
 * is a result verse list.
 *
 * It can cycle through the Hebrew and phonetic
 * representations of the material.
 */
export class MaterialContent {
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

