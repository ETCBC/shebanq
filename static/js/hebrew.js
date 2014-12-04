/*

Application workflow:

There is a skeleton page, filled with HTML.
The skeleton has the following parts:

A. Sidebar with
    w: viewsettings plus a list of word items
    q: viewsettings plus a list of query items
    m: viewsettings plus the metadata of an individual query
B. Main part with
    heading
    material selector (either book/chapter, or resultpages)
    m: viewsettings (share link plus text/data selector)
    material (either the verses of a passage or the verses of the resultpage of a query)

There is a dictionary viewstate, in which the current viewsettings are being maintained.
Viewstate is divided in groups, each group is serialized to a cookie with every change made by the user.
Viewstate is initialized from the querystring and/or the cookies, where the querystring wins.

Depending on user actions, parts of the skeleton are loaded with HTML, through AJAX calls.

The application goes through the following stages:

setup_ functions:
    insert the action items into the skeleton or a new load of html that has come from the server
    Does not change the viewstate, does not look at the viewstate

apply_ functions:
    looks at the viewstate and adapts the display of the page, this might entail ajax actions
    does not change the viewstate

The skeleton can be used to structure several kinds of pages:

passage page
    The sidebar contains A-w and A-q, but not A-m
    The main part B contains a verse list from a passage (a chapter)
    A-w and A-q are lists of relevant words (lexemes) and queries.

query page
    The sidebar contains A-m, but not A-w and A-q
    The main part B contains a page with a verse list of verses containing a result of the query.
    A-m shows the metadata of the query, and the query can be edited in place. 

word page
    The sidebar contains A-m, but not A-w and A-q
    The main part B contains a page with a verse list of verses containing an occurrence of a word (lexeme).
    A-m shows the metadata of the query, and the query can be edited in place. 

The cookies are

material
    the current book, chapter, query id, word id, pagekind (m=material, q=query, w=word),
    tp (text-or-data setting: whether the material is shown as plain text (txt_p) or as interlinear data (txt_il))

hebrewdata
    a list of switches controlling which fields are shown in the data view

highlights
    groups of settings controlling the highlight colors
    group q: for queries
    group w: for words

    Both groups contain the same settings:
    active (which is the active setting: hloff, hlone, hlcustom, hlmany)
    sel_one (the color if all queries are highlighted with one color)
    get (whether or not to retrieve the side list of relevant items)

colormap
    mappings between queries and colors and between words and colors, based on the id of queries and words

*/

// GLOBALS

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = '/'

var vcolors, vdefaultcolors, dncols, dnrows
var viewstate, viewfluid, style, title, side_fetched, material_fetched
var thebooks
var view_url, material_url, item_url, side_url
var page
var subtract = 250


// TOP LEVEL: DYNAMICS, PAGE, SKELETON

function dynamics() {
    viewfluid = {}
    page = new Page()
    page.go()
}

function Page() {
    this.mstate = viewstate['material']['']
    this.skeleton = new Skeleton()
    this.prev = {}
    for (x in this.mstate) {
        this.prev[x] = null
    }
    this.apply = function() {
        var pagekind = this.mstate['pagekind']
        var otherpagekind = (pagekind == 'w')?'q':(pagekind == 'q')?'w':''
        var thechapter = this.mstate['chapter']
        var thepage = this.mstate['page']
        this.skeleton.apply()
        $('#theitemlabel').html((pagekind == 'm')?'':style[pagekind]['Tag'])
        $('#thechapter').html((thechapter > 0)?thechapter:'')
        $('#thepage').html((thepage > 0)?'page '+thepage:'')
        for (x in this.mstate) {
            this.prev[x] = this.mstate[x]
        }
    }
    this.go = function() {
        var pagekind = this.mstate['pagekind']
        if (
            this.mstate['pagekind'] != this.prev['pagekind'] ||
            (this.prev['pagekind'] == 'm' && (this.mstate['book'] != this.prev['book'] || this.mstate['chapter'] != this.prev['chapter'])) ||
            (this.prev['pagekind'] != 'm' && (this.mstate[pagekind+'id'] != this.prev['iid'] || this.mstate['page'] != this.prev['page']))
        ) {
            material_fetched = {txt_p: false, txt_il: false}
        }
        savestate('material','')
        this.apply()
    }
}

function Skeleton() {
    this.material = new Material()
    this.sidebars = new Sidebars()
    this.apply = function() {
        this.material.apply()
        this.sidebars.apply()
    }
    $('#material_txt_p').css('height', (window.innerHeight - subtract)+'px')
    $('#material_txt_il').css('height', (2 * window.innerHeight - subtract)+'px')
}

// VIEWLINK

function Viewlink() {
    var that = this
    this.name = 'viewlink'
    this.hid = '#'+this.name
    viewfluid = {}
    viewfluid[this.name] = 'x'
    var hide = $(this.hid+'_hide')
    var show = $(this.hid+'_show')
    var content = $(this.hid+'_content')
    this.apply = function() {
        var setting = viewfluid[this.name]
        if (setting == 'v') {
            hide.show()
            show.hide()
            content.show()
            content.val(view_url+getvars())
            content.select()
        }
        else {
            hide.hide()
            show.show()
            content.hide()
        }
    }
    hide.click(function() {
        viewfluid[that.name] = 'x'
        that.apply()
    })
    show.click(function() {
        viewfluid[that.name] = 'v'
        that.apply()
    })
}

// MATERIAL

function Material() {
    var that = this
    this.mstate = viewstate['material']['']
    var pagekind = this.mstate['pagekind']
    this.name = 'material'
    this.hid = '#'+this.name
    this.cselect = $('#material_select')
    this.viewlink = new Viewlink()
    this.mselect = new MSelect()
    this.pselect = new PSelect()
    this.message = new MMessage()
    this.content = new MContent()
    this.msettings = new MSettings(this.content)
    this.apply = function() {
        this.viewlink.apply()
        this.msettings.apply()
        this.mselect.apply()
        this.pselect.apply()
        this.fetch()
    }
    this.fetch = function() {
        var pagekind = this.mstate['pagekind']
        var tp = this.mstate['tp']
        var vars = '?pagekind='+pagekind
        vars += '&tp='+tp
        if (pagekind == 'm') {
            vars += '&book='+this.mstate['book']
            vars += '&chapter='+this.mstate['chapter']
            do_fetch = this.mstate['book'] != 'x' && this.mstate['chapter'] > 0
        }
        else {
            vars += '&id='+this.mstate[pagekind+'id']
            vars += '&page='+this.mstate['page']
            do_fetch = this.mstate[pagekind+'id'] >=0
        }
        if (do_fetch && !material_fetched[tp]) {
            this.message.msg('fetching data ...')
            $.get(material_url+vars, function(html) {
                var response = $(html)
                that.pselect.add(response)
                that.message.add(response)
                that.content.add(response)
                material_fetched[tp] = true
                that.process()
            }, 'html')
        }
    }
    this.process = function() {
        var pagekind = this.mstate['pagekind']
        this.msettings.apply()
        page.skeleton.sidebars.after_material_fetch()
        if (pagekind != 'm') {
            this.pselect.apply()
            $('a.vref').click(function() {
                that.mstate['book'] = $(this).attr('book')
                that.mstate['chapter'] = $(this).attr('chapter')
                that.mstate['pagekind'] = 'm'
                savestate('material', '')
                page.go('m')
            })
        }
    }
    this.message.msg('choose a passage or a query or a word')
}

// MATERIAL: SELECTION

function MSelect() { // for book and chapter selection
    this.mstate = viewstate['material']['']
    var select = '#select_contents_chapter'
    this.name = 'select_passage'
    this.hid = '#'+this.name
    this.up = new SelectBook()
    this.select = new SelectItems(this.up, 'chapter')
    this.apply = function() {
        var pagekind = this.mstate['pagekind']
        if (pagekind == 'm') {
            this.up.apply()
            $(this.hid).show()
        }
        else {
            $(this.hid).hide()
        }
    }
}

function PSelect() { // for result page selection
    this.mstate = viewstate['material']['']
    var select = '#select_contents_page'
    this.name = 'select_pages'
    this.hid = '#'+this.name
    this.select = new SelectItems(null, 'page')
    this.apply = function() {
        var pagekind = this.mstate['pagekind']
        if (pagekind != 'm') {
            this.select.apply()
            $(this.hid).show()
        }
        else {
            $(this.hid).hide()
        }
    }
    this.add = function(response) {
        var pagekind = this.mstate['pagekind']
        if (pagekind != 'm') {
            $(select).html(response.find(select).html())
        }
    }
}

function SelectBook() {
    var that = this
    this.mstate = viewstate['material']['']
    this.name = 'select_book'
    this.hid = '#'+this.name
    this.content = $(this.hid)
    this.selected = null
    this.apply = function () {
        var thebook = this.mstate['book']
        this.content.show()
        this.content.val(thebook)
        if (this.selected != thebook) {
            this.chapters.gen_html()
            this.chapters.apply()
        }
        this.selected = thebook
    }
    this.content.change(function () {
        that.mstate['book'] = that.content.val()
        that.mstate['pagekind'] = 'm'
        savestate('material', '')
        page.go()
    })
    this.gen_html = function() {
        var ht = '<option value="x">choose a book ...</option>'
        for (i in thebooksorder) {
            book =  thebooksorder[i]
            ht += '<option value="'+book+'">'+book+'</option>'
        }
        this.content.append($(ht))
    }
    this.gen_html()
    this.content.val(this.mstate['book'])
}

function SelectItems(up, key) { // both for chapters and for result pages
    var that = this
    this.mstate = viewstate['material']['']
    this.key = key
    this.tag = (key == 'chapter')?'passage':'pages'
    this.up = up
    this.name = 'select_contents_'+this.key
    this.hid = '#'+this.name
    this.control = '#select_control_'+this.key
    if (this.up) {
        this.up.chapters = this
    }
    this.present = function() {
        $(this.hid).dialog({
            autoOpen: false,
            dialogClass: 'items',
            closeOnEscape: true,
            modal: false,
            title: 'choose '+that.key,
            position: {my: 'right top', at: 'left top', of: $('#select_'+that.tag)},
            width: '450px',
        })
    }
    this.gen_html = function() {
        if (this.key == 'chapter') {
            var thebook = this.mstate['book']
            var theitem = this.mstate['chapter']
            var nitems = (thebook != 'x')?thebooks[thebook]:0
            var itemlist = new Array(nitems)
            for  (i = 0; i < nitems; i++) {itemlist[i] = i+1}
        }
        else { // 'page'
            var theitem = this.mstate['page']
            var nitems = $('#rp_pages').val()
            var itemlist = []
            if (nitems) {
                itemlist = $.parseJSON($('#rp_pagelist').val())
            }
        }
        var ht = ''
        if (nitems != undefined) {
            if (nitems != 0) {
                ht = '<div class="pagination"><ul>'
                for (i in itemlist) {
                    item = itemlist[i]
                    if (theitem == item) {
                        ht += '<li class="active"><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
                    }
                    else {
                        ht += '<li><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
                    }
                }
                ht += '</ul></div>'
            }
            $(this.hid).html(ht)
        }
        return nitems
    }
    this.add_item = function(item) {
        item.click(function() {
            if ($(that.hid).dialog('instance') && $(that.hid).dialog('isOpen')) {$(that.hid).dialog('close')}
            var newobj = $(this).closest('li')
            var isloaded = newobj.hasClass('active')
            if (!isloaded) {
                var newitem = $(this).attr('item')
                that.mstate[that.key] = newitem 
                savestate('material', '')
                page.go()
            }
        })
    }
    this.apply = function() {
        var pagekind = this.mstate['pagekind']
        var showit = false
        if (pagekind != 'm' && this.key == 'page') {
            showit = this.gen_html() > 0 
        }
        else if (pagekind == 'm' && this.key == 'chapter') {
            showit = true
        }
        if (!showit) {
            $(this.control).hide()
        }
        else {
            $('.itemnav').each(function() {
                that.add_item($(this))
            })
            $(this.control).show()
        }
        this.present()
    }
    $(this.control).click(function () {
        $(that.hid).dialog('open')
        savestate('material', '')
    })
}

// MATERIAL (messages when retrieving, storing the contents)

function MMessage() { // diagnostic output
    this.name = 'material_message'
    this.hid = '#'+this.name
    this.add = function(response) {
        $(this.hid).html(response.children(this.hid).html())
    }
    this.msg = function(m) {
        $(this.hid).html(m)
    }
}

function MContent() { // the actual Hebrew content, either plain text or interlinear data
    this.mstate = viewstate['material']['']
    var tps = {txt_p: 'txt_il', txt_il: 'txt_p'}
    this.name_text = 'material_text'
    this.name_data = 'material_data'
    this.hid_text = '#'+this.name_text
    this.hid_data = '#'+this.name_data
    this.hid_content = '#material_content'
    this.select = function() {
        var tp = this.mstate['tp']
        this.name_yes = 'material_'+tp
        this.name_no = 'material_'+tps[tp]
        this.hid_yes = '#'+this.name_yes
        this.hid_no = '#'+this.name_no
    }
    this.add = function(response) {
        this.select()
        $(this.hid_yes).html(response.children(this.hid_content).html())
    }
    this.show = function() {
        this.select()
        $(this.hid_yes).show()
        $(this.hid_no).hide()
    }
}

// MATERIAL SETTINGS (for choosing between plain text and interlnear data)

function MSettings(content) {
    var that = this
    this.mstate = viewstate['material']['']
    var hltext = $('#mtxt_p')
    var hldata = $('#mtxt_il')
    var legend = $('#datalegend')
    var legendc = $('#datalegend_control')
    this.name = 'material_settings'
    this.hid = '#'+this.name
    this.content = content
    this.hebrewsettings = new HebrewSettings()
    $('.mhradio').click(function() {
        var activen = $(this).attr('id').substring(1)
        that.mstate['tp'] = activen 
        that.mstate['pagekind'] = 'm'
        savestate('material','')
        page.go()
    })
    legendc.click(function () {
        legend.dialog({
            dialogClass: 'legend',
            closeOnEscape: true,
            modal: false,
            title: 'choose data features',
            position: {my: 'right top', at: 'left top', of: $(that.hid)},
            width: '550px',
        })
    })
    this.apply = function() {
        var tp = this.mstate['tp']
        var hlradio = $('.mhradio')
        hlradio.removeClass('ison')
        $('#m'+tp).addClass('ison')
        this.content.show()
        if (tp == 'txt_il') {
            legendc.show()
            this.hebrewsettings.apply()
        }
        else {
            legend.hide()
            legendc.hide()
        }
    }
}

// HEBREW DATA (which fields to show if interlinear text is displayed)

function HebrewSettings() {
    this.dstate = viewstate['hebrewdata']['']
    for (fld in this.dstate) {
        this[fld] = new HebrewSetting(fld)
    }
    this.apply = function() {
        for (fld in this.dstate) {
            this[fld].apply()
        }
    }
}

function HebrewSetting(fld) {
    var that = this
    this.dstate = viewstate['hebrewdata']['']
    this.name = fld
    this.hid = '#'+this.name
    $(this.hid).click(function() {
        that.dstate[fld] = $(this).prop('checked')?'v':'x'
        savestate('hebrewdata')
        that.applysetting()
    })
    this.apply = function() {
        var val = this.dstate[this.name]
        $(this.hid).prop('checked', val == 'v')
        this.applysetting()
    }
    this.applysetting = function() {
        if (this.dstate[this.name] == 'v') {
            $('.'+this.name).each(function () {$(this).show()})
        }
        else {
            $('.'+this.name).each(function () {$(this).hide()})
        }
    }
}

// SIDEBARS

/*

The main material kan be three kinds (pagekind)

m = material: chapters from books
q = query results
w = word results

There are four kinds of sidebars, indicated by two letters, of which the first indicates the pagekind

mq = list of queries relevant to main material
mw = list of words relevant to main material
qm = display of query record, the main material are the query results
qw = display of word record, the main material are the word results

*/

function Sidebars() { // TOP LEVEL: all four kinds of sidebars
    this.hstate_all = viewstate['highlights']
    for (k in this.hstate_all) {
        this['m'+k] = new Sidebar('m', k)
        this[k+'m'] = new Sidebar(k, 'm')
    }
    side_fetched = {}
    this.apply = function() {
        for (k in this.hstate_all) {
            this['m'+k].apply()
            this[k+'m'].apply()
        }
    }
    this.after_material_fetch = function() {
        for (k in this.hstate_all) {
            delete side_fetched['m'+k]
        }
    }
    this.after_item_fetch = function() {
        for (k in this.hstate_all) {
            delete side_fetched[k+'m']
        }
    }
}

// SPECIFIC sidebars, the [mqw][mqw] type is frozen into the object

function Sidebar(pagekind, k) {
    var that = this
    this.pagekind = pagekind
    this.k = k
    this.name = 'side_bar_'+this.pagekind+this.k
    this.hid = '#'+this.name
    this.mstate = viewstate['material']['']
    this.hstate = (this.k == 'm')?{}:viewstate['highlights'][this.k]
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+this.pagekind+this.k)
    var theset = $('#side_settings_'+this.pagekind+this.k)
    var hide = $('#side_hide_'+this.pagekind+this.k)
    var show = $('#side_show_'+this.pagekind+this.k)
    this.ssettings = new SSettings(this.pagekind, this.k)
    this.content = new SContent(this.pagekind, this.k, this.ssettings)
    this.apply = function() {
        var currentpagekind = this.mstate['pagekind']
        if (currentpagekind != this.pagekind) {
            thebar.hide()
        }
        else {
            thebar.show()
            if (this.hstate['get'] == 'x') {
                thelist.hide()
                theset.hide()
                hide.hide()
                show.show()
            }
            else {
                thelist.show()
                theset.show()
                hide.show()
                show.hide()
            }
        }
        this.content.apply()
    }
    if (this.pagekind == 'm') {
        show.click(function(){
            that.hstate['get'] = 'v'
            savestate('highlights',that.k)
            that.apply()
        })
        hide.click(function(){
            that.hstate['get'] = 'x'
            savestate('highlights',that.k)
            that.apply()
        })
    }
}

// SIDELIST MATERIAL

function SContent(pagekind, k, ssettings) {
    var that = this
    this.pagekind = pagekind
    this.k = k
    this.ik = (this.pagekind == 'm')?this.k:this.pagekind
    this.mstate = viewstate['material']['']
    this.hstate = (this.pagekind != 'm')?{}:viewstate['highlights'][this.k]
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+this.pagekind+this.k)
    var hide = $('#side_hide_'+this.pagekind+this.k)
    var show = $('#side_show_'+this.pagekind+this.k)
    this.name = 'side_material_'+this.pagekind+this.k
    this.hid = '#'+this.name
    this.ssettings = ssettings
    this.colorpickers = []
    this.msg = function(m) {
        $(this.hid).html(m)
    }
    this.fetch = function() {
        var thebook = this.mstate['book']
        var thechapter = this.mstate['chapter']
        var vars = '?pagekind='+this.pagekind+'&k='+this.k
        var do_fetch = false
        var extra = ''
        if (this.pagekind == 'm') {
            vars += '&book='+this.mstate['book']
            vars += '&chapter='+this.mstate['chapter']
            do_fetch = this.mstate['book'] != 'x' && this.mstate['chapter'] > 0
            extra = 'm'
        }
        else {
            vars += '&id='+this.mstate[this.pagekind+'id']
            do_fetch = this.mstate[this.pagekind+'id'] >=0
            extra = this.pagekind+'m'
        }
        if (do_fetch && !side_fetched[this.pagekind+this.k]) {
            this.msg('fetching '+style[this.k]['tags']+' ...')
            if (this.pagekind == 'm') {
                thelist.load(side_url+extra+vars, function () {
                    side_fetched[that.pagekind+that.k] = true
                    that.process()
                }, 'html')
            }
            else {
                $.get(side_url+extra+vars, function (html) {
                    thelist.html(html)
                    side_fetched[that.pagekind+that.k] = true
                    that.process()
                }, 'html')

            }
        }
    }
    this.sidelistitems = function() {
        if (this.pagekind == 'm') {
            var klist = $('#side_list_'+this.k+' li')
            klist.each(function() {
                var iid = $(this).attr('iid') 
                that.sidelistitem(iid)
                that.colorpickers.push(new Colorpicker(that.ssettings, that.ik, iid, null))
            })
        }
    }
    this.sidelistitem = function(iid) {
        var more = $('#m_'+this.k+iid) 
        var head = $('#h_'+this.k+iid) 
        var desc = $('#d_'+this.k+iid) 
        var item = $('#item_'+this.k+iid) 
        desc.hide()
        more.click(function() {
            desc.toggle()
        })
        item.click(function() {
            var k = that.k
            that.mstate['pagekind'] = k
            that.mstate[k+'id'] = $(this).attr('iid')
            that.mstate['page'] = 1
            page.go()
        })
    }
    this.process = function() {
        page.skeleton.sidebars.after_item_fetch()
        this.ssettings.apply()
        this.sidelistitems()
        $('#theitem').html($('#itemtag').val()+':')
    }
    this.apply = function() {
        var currentpagekind = this.mstate['pagekind']
        if (currentpagekind == this.pagekind && (this.pagekind != 'm' || this.hstate['get'] == 'v')) {
            this.fetch()
        }
    }
}

// SIDELIST VIEW SETTINGS

/*

There are two kinds of side bars:

mq, mw: lists of items (queries or words)
qm, wm: one record of a query or a word

The list sidebars have a color picker for selecting a uniform highlight color,
plus controls for deciding whether no, uniform, custom, or many colors will be used.

The one-record-side bars only have a single color picker, for 
choosing the color associated with the item (a query or a word).

When items are displayed in the list sidebars, they each have a color picker that
is identical to the one used for the record.

The colorpickers for choosing an associated item color, consist of a checkbox and a proper colorpicker.
The checkbox indicates whether the color is customized. 
A color gets customized when the user selects an other color than the default one, or by checking the box.

When the user has chosen custom colors, all highlights will be done with the uniform color, except
his customized ones.

Queries are highlighted by background color, word by foreground colors.
Although the names for background and foreground colors are identical, their actual values are not.
Foreground colors are darkened, background colors are lightened.

All color asscociations are preserved in cookies, one for queries, and one for words.
Nowhere else are they stored.
By using the share link, the user can preserve color settings in a notebook, or mail them to colleaugues.

*/

function SSettings(pagekind, k) { // the view controls belonging to the sidebar as a whole
    var that = this
    this.pagekind = pagekind
    this.k = k
    this.ik = (this.pagekind == 'm')?this.k:this.pagekind
    this.mstate = viewstate['material']['']
    this.hstate = viewstate['highlights'][this.k]
    this.cstate_all = viewstate['colormap']
    this.cstate = this.cstate_all[this.ik]
    var viewlist = $('#side_settings_'+this.pagekind+this.k)
    this.name = 'side_settings_'+this.pagekind+this.k
    this.hid = '#'+this.name
    this.iid = this.mstate[this.pagekind+'id']
    this.apply = function() {
        var currentpagekind = this.mstate['pagekind']
        if (currentpagekind == this.pagekind) { 
            if (this.pagekind == 'm') {
                this.highlights()
            }
            else {
                this.picker = new Colorpicker(this, this.ik, this.iid, 'me')
                this.paint()
            }
        }
    }
    this.highlights = function(picked) {
        var that = this
        var activen = this.hstate['active']
        var active = $('#'+this.k+activen)
        var klist = $('#side_list_'+this.k+' li')
        var selo = $('#sel_'+this.k+'one')
        var hlradio = $('.'+this.k+'hradio')
        var hloff = $('#'+this.k+'hloff')
        var hlone = $('#'+this.k+'hlone')
        var hlcustom = $('#'+this.k+'hlcustom')
        var hlmany = $('#'+this.k+'hlmany')
        var hlreset = $('#'+this.k+'hlreset')
        var stl = style[this.k]['prop']
        var selclr = selo.css(stl)

        if (picked && activen != 'hlcustom' && activen != 'hlone') {
            this.hstate['active'] = 'hlcustom'
            activen = 'hlcustom'
            active = $('#'+this.k+activen)
        }
        hlradio.removeClass('ison')
        active.addClass('ison')

        if (activen == 'hloff') {
            klist.each(function(index, item) {
                that.paint($(item).attr('iid'), style[that.k]['off'])
            })
        }
        else if (activen == 'hlone') {
            klist.each(function(index, item) {
                that.paint($(item).attr('iid'), selclr)
            })
        }
        else if (activen == 'hlcustom') {
            klist.each(function(index, item) {
                var iid =  $(item).attr('iid')
                if (!(iid in that.cstate)) {
                    that.paint(iid, selclr)
                }
            })
            klist.each(function(index, item) {
                var iid =  $(item).attr('iid')
                if (iid in that.cstate) {
                    that.paint(iid, that.cstate[iid])
                }
            })
        }
        else if (activen =='hlmany') {
            klist.each(function(index, item) {
                that.paint($(item).attr('iid'), null)
            })
        }
        else if (activen == 'hlreset') {
            var selclr2 = defcolor(this.ik, null)
            hlreset.removeClass('ison')
            hlcustom.addClass('ison')
            selo.css(stl, vcolors[selclr2][this.k])
            this.hstate['active'] = 'hlcustom'
            this.hstate['sel_one'] = selclr2
            this.cstate_all[this.ik] = {}
            klist.each(function(index, item) {
                var iid =  $(item).attr('iid')
                var sel = $('#sel_'+that.k+iid)
                var selc = $('#selc_'+that.k+iid)
                var selclr = defcolor(that.ik, null)
                sel.css(stl, vcolors[selclr][that.k])
                selc.prop('checked', false)
                that.paint(iid, vcolors[selclr2][that.k])
            })
        }
    }
    this.highlight = function(iid) {
        var iid = iid || this.iid
        var sel = $('#sel_'+this.k+iid)
        var selo = $('#sel_'+this.k+'one')
        var hlcustom = $('#'+this.k+'hlcustom')
        var hlmany = $('#'+this.k+'hlmany')
        var defc = sel.attr('defc')
        var iscust = iid in this.cstate
        var stl = style[this.k]['prop']
        var hlcustomon = hlcustom.hasClass('ison') 
        var hlmanyon = hlmany.hasClass('ison') 
        if (hlmanyon || hlcustomon) {
            if (hlmanyon) {
                this.paint(iid, defcolor('m', iid))
            }
            else {
                if (iscust) {
                    this.paint(iid, this.cstate[iid])
                }
                else {
                    selclr = selo.css(stl)
                    this.paint(iid, selclr)
                }
            }
        }
    }
    this.paint = function(iid, clr) {
        var iid = iid || this.iid
        var monads = (this.pagekind == 'm')? $.parseJSON($('#'+this.ik+iid).attr('monads')) : $.parseJSON($('#themonads').val())
        var stl = style[this.ik]['prop']
        var hc = clr
        if (hc == null) {
            cid = (this.pagekind == 'm')?iid:'me'
            hc =  $('#sel_'+this.ik+cid).css(stl)
        }
        $.each(monads, function(index, item) {
            $('span[m="'+item+'"]').css(stl, hc)
        })
    }

    if (this.pagekind == 'm') {
        this.picker = new Colorpicker2(this, this.k)
        $('.'+this.k+'hradio').click(function() {
            that.hstate['active'] = $(this).attr('id').substring(1)
            savestate('highlights', that.k)
            that.apply()
        })
    }
}

function Colorpicker(ssettings, ik, iid, rid) {
    var that = this
    this.ssettings = ssettings
    this.ik = ik
    this.cstate_all = viewstate['colormap']
    this.cstate = this.cstate_all[this.ik]
    if (rid == null) {rid = iid}
    this.iid = iid
    this.rid = rid
    var sel = $('#sel_'+this.ik+rid)
    var selc = $('#selc_'+this.ik+rid)
    this.picker = $('#picker_'+this.ik+rid)
    var stl = style[this.ik]['prop']
    this.colorn = this.cstate[this.iid] || defcolor('m', this.iid)
   
    this.picker.hide()
    sel.click(function() {
        that.picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: selc},
            width: '200px',
        })
    })
    selc.click(function() {
        var was_cust = that.iid in that.cstate
        if (that.picker.dialog('instance') && that.picker.dialog('isOpen')) {that.picker.dialog('close')}
        if (was_cust) {
            sel.css(stl, vcolors[that.colorn][that.ik])
            delete that.cstate[that.iid]
        }
        else {
            that.cstate[that.iid] = defcolor('m', that.iid)
        }
        selc.prop('checked', that.iid in that.cstate)
        that.ssettings.highlight(that.iid)
        savestate('colormap', that.ik)
    })
    $('.c'+this.ik+'.'+this.ik+rid).click(function() {
        if (that.picker.dialog('instance') && that.picker.dialog('isOpen')) {that.picker.dialog('close')}
        sel.css(stl, $(this).css(stl))
        that.cstate[that.iid] = $(this).html()
        selc.prop('checked', true)
        that.ssettings.highlight(that.iid)
        savestate('colormap', that.ik)
    })
    $('.c'+this.ik+'.'+this.ik+rid).each(function() {
        $(this).css(stl, vcolors[$(this).html()][that.ik])
    })
    sel.css(stl, vcolors[this.colorn][this.ik])
    selc.prop('checked', this.iid in this.cstate)
}

function Colorpicker2(ssettings, k) {
    var that = this
    this.ssettings = ssettings
    this.k = k
    this.hstate = viewstate['highlights'][this.k]
    var lab = 'one'
    var sel = $('#sel_'+this.k+lab)
    this.picker = $('#picker_'+this.k+lab)
    var stl = style[this.k]['prop']
    var colorn = this.hstate['sel_'+lab] || defcolor(this.k, null)
    this.picker.hide()
    sel.click(function() {
        that.picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: sel},
            width: '200px',
        })
    })
    $('.c'+this.k+'.'+this.k+lab).click(function() {
        if (that.picker.dialog('instance') && that.picker.dialog('isOpen')) {that.picker.dialog('close')}
        sel.css(stl, $(this).css(stl))
        that.hstate['sel_'+lab] = $(this).html()
        that.ssettings.highlights(true)
        savestate('highlights',that.k)
    })
    $('.c'+this.k+'.'+this.k+lab).each(function() {
        $(this).css(stl, vcolors[$(this).html()][that.k])
    })
    sel.css(stl, vcolors[colorn][this.k])
}

function defcolor(k, iid) {
    if (k == 'm') {
        var mod = iid % vdefaultcolors.length
        result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
    }
    else {
        result = style[k]['default']
    }
    return result
}

// SAVING STATE

function getvars() {
    var vars = ''
    var sep = '?'
    for (group in viewstate) {
        for (k in viewstate[group]) {
            for (name in viewstate[group][k]) {
                vars += sep+k+name+'='+viewstate[group][k][name] 
                sep = '&'
            }
        }
    }
    return vars
}

function savestate(group, k) {$.cookie(group+k, viewstate[group][k])}

/*

We run the edit form for queries as an AJAX component in a DIV (see Chapter 12 of the Web2py book about LOAD).
That works fine, except that for some reason the extra buttons do not record themselves in the form
or request vars after pressing.
So, here is a workaround: we add some click event to the buttons to leave a trace in some hidden input fields.

*/
function activate_buttons() {
    $('.smb').each(function() {
        $(this).click(function() {
            $('.smb').each(function() {
                var name = $(this).attr('name')
                $('#'+name).val(false)
            })
            var name = $(this).attr('name')
            $('#'+name).val(true)
        })
    })
}
