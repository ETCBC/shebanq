/* eslint-env jquery */
/* globals Config, PG, VS */

/**
 * @module featuresettings
 */

/*
 * Manages the selection of linguistic features to be displayed
 * when the data of a verse is shown.
 */
export class FeatureSettings {
  constructor() {
    for (const fld in VS.getHebrew()) {
      this[fld] = new FeatureSetting(fld)
    }
  }

  apply() {
    const { versions } = Config

    for (const fld in VS.getHebrew()) {
      this[fld].apply()
    }
    for (const v of versions) {
      PG.setCsv(v, VS.mr(), VS.qw(), VS.iid())
    }
  }
}

/**
 * Handles the display a single lingusitic feature.
 */
class FeatureSetting {
  constructor(fld) {
    const { versions } = Config

    this.name = fld
    this.hid = `#${this.name}`
    $(this.hid).off("click").click(e => {
      const elem = $(e.delegateTarget)
      const vals = {}
      vals[fld] = elem.prop("checked") ? "v" : "x"
      VS.setHebrew(vals)
      VS.addHist()
      this.applysetting()
      for (const v of versions) {
        PG.setCsv(v, VS.mr(), VS.qw(), VS.iid())
      }
    })
  }

  apply() {
    const val = VS.getHebrew()[this.name]
    $(this.hid).prop("checked", val == "v")
    this.applysetting()
  }

  applysetting() {
    if (VS.getHebrew()[this.name] == "v") {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.show()
      })
    } else {
      $(`.${this.name}`).each((i, el) => {
        const elem = $(el)
        elem.hide()
      })
    }
  }
}
