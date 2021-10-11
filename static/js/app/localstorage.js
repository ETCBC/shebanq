/* eslint-env jquery */

/**
 * @module localstorage
 */

/**
 * Set up sections of local storage for several kinds of settings:
 *
 * *   notes settings, and which notes are muted
 * *   queries settings, and which queries are muted
 */
export class LStorage {
  constructor() {
    this.lsQueries = $.initNamespaceStorage("lsQueries").localStorage
    this.lsNotes = $.initNamespaceStorage("lsNotes").localStorage
    this.lsQueriesMuted = $.initNamespaceStorage("lsQueriesMuted").localStorage
    this.lsNotesMuted = $.initNamespaceStorage("lsNotesMuted").localStorage
    /* on the Queries and Notes pages the user can "mute" queries.
     * Which items are muted,
     * is stored as key value pairs in this local storage bucket.
     * When shebanq shows relevant items next to a page, muting is taken into account.
     */
  }
}
