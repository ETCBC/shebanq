<a name="module_notes"></a>

## notes

* [notes](#module_notes)
    * `static`
        * [.Notes](#module_notes.Notes)
    * `inner`
        * [~NoteVerse](#module_notes..NoteVerse)
            * [.fetch()](#module_notes..NoteVerse+fetch)
            * [.sendnotes()](#module_notes..NoteVerse+sendnotes)

<a name="module_notes.Notes"></a>

### notes.Notes
Controls notes on **text** pages

**Kind**: static class of [<code>notes</code>](#module_notes)  
**See**: [notetree](.) for the notes overview page.  
<a name="module_notes..NoteVerse"></a>

### notes~NoteVerse
Controls the notes belonging to a single verse.

**Kind**: inner class of [<code>notes</code>](#module_notes)  

* [~NoteVerse](#module_notes..NoteVerse)
    * [.fetch()](#module_notes..NoteVerse+fetch)
    * [.sendnotes()](#module_notes..NoteVerse+sendnotes)

<a name="module_notes..NoteVerse+fetch"></a>

#### noteVerse.fetch()
get the notes belonging to the current verse.

**Kind**: instance method of [<code>NoteVerse</code>](#module_notes..NoteVerse)  
**See**: Triggers [C:hebrew.getversenotes][controllers.hebrew.getversenotes]  
<a name="module_notes..NoteVerse+sendnotes"></a>

#### noteVerse.sendnotes()
sends edited notes to the server in order to be saved.

**Kind**: instance method of [<code>NoteVerse</code>](#module_notes..NoteVerse)  
**See**: Triggers [C:hebrew.putversenotes][controllers.hebrew.putversenotes]  
