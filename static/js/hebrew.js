/*

Application workflow:

There is a skeleton page, which has a main area and a left sidebar.
The skeleton is filled with static html, with certain divs in it that
will be filled on demand by means of ajax calls.

An actual page is composed by selectively showing and hiding parts of the skeleton and by filling
divs through ajax calls.

A page is represented by a javascript object with data and methods.

There are two kinds of pages:

    m: material (showing verses of a chapter)
    r: results  (showing verses of a result page)

An m-page has different sidebars than an r-page.

The skeleton has the following parts:

A. Sidebar with
    m-w: viewsettings plus a list of word items
    m-q: viewsettings plus a list of query items
    r-w: viewsettings plus the metadata of an individual word
    r-q: viewsettings plus the metadata of an individual query

B. Main part with
    heading
    material selector (m: book/chapter, r: resultpages)
    settings (text/data selector)
    material (either the verses of a passage or the verses of the resultpage of a query or word)
    share link

There is a viewstate, an object that maintains the viewsettings that can be modified by the user.
The viewstate object is a member of the page object.
Viewstate is divided in groups, each group is serialized to a cookie.
Viewstate is initialized from the querystring and/or the cookies.
When querystring and cookie conflict, the querystring wins.
Whenever a user clicks, the viewstate is changed and immediately saved in the corresponding cookie.

Depending on user actions, parts of the skeleton are loaded with HTML, through AJAX calls with methods that
perform actions when the data has been loaded.

The application goes through the following stages:

init functions:
    Decorate the fixed parts of the skeleton with jquery actions.
    Do not change the viewstate, do not look at the viewstate.

click functions (events):
    Change the viewstate in response to user actions.

apply functions:
    Look at the viewstate and adapt the display of the page, this might entail ajax actions.
    Do not change the viewstate.

process functions:
    Very much like init functions, but only for content that has been loaded through later AJAX calls.

The cookies are:

material
    the current book, chapter, result page, item id,
    qw (q=query, w=word, tells whether the item in question is a query or a word),
    mr (m=material, r=result of query or word search, corresponds to the two kinds of pages),
    tp (text-or-data setting: whether the material is shown as plain text (txt_p) or as interlinear data (txt_il))

hebrewdata
    a list of switches controlling which fields are shown in the interlinear data view

highlights
    groups of settings controlling the highlight colors
    group q: for queries
    group w: for words

    Both groups contain the same settings:
    active (which is the active setting: hloff, hlone, hlcustom, hlmany)
    sel_one (the color if all queries/words are highlighted with one color)
    get (whether or not to retrieve the side list of relevant items)

colormap
    mappings between queries and colors (q) and between words and colors (w), based on the id of queries and words

Window layout

All variable content is placed in divs with fixed height and scroll bars.
So the contents of sidebars and main area can be scrolled independently.
So the main parts of the page are always in view, at fairly stable places.

When editing a query it is important to make room for the query body.
When editing is happening, the sidebar will be widened at the expense of the main area.

Plans for the near future:

I. Load data view per verse, not per chapter. A click on the verse number should be the trigger.

II. Make SHEBANQ able to deal with several versions of the data.
Queries will get an execution record per version of the data.

Plans for distant future:

I. integrate the Queries page with this page.

The skeleton will have 4 columns, of which 2 or three are visible at a given time:

A: filter and level controls for the queries tree
B: the queries tree itself
C: an individual query, possibly in edit mode, or an individual word
D: material column: the verses of a chapter, or a page with occurrences of a word, or a page with query results

Then the hebrew.js and the queries.js can be integrated, redundant code can be erased, ajax messages can be done more consistently.

II. replace all usage of cookies by local storage.

The queries page already does not use cookies but local storage. 
Now the parsing of the request.vars occurs server side in Python, maybe it is better to defer all checks to the browser.
The browser can then keep all view settings to its own, without any need to communicate view settings with the server.

III. send all data from server to browser in JSON form.

The browser generates HTML out of the JSON.
I am not sure whether this is worth it. 
On the one hand it means smaller data transfers (but they are already fast enough), on the other hand, template code in python is
much more manageable than in Javascript.

*/

// GLOBALS

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = '/'

var ns = $.initNamespaceStorage('muting')
var muting = ns.localStorage // on the Queries page the user can "mute" queries. Which queries are muted, is stored as key value pairs in this local storage bucket.
// When shebanq shows relevant queries next to a page, muting is taken into account.

/* state variables */
var vcolors, vdefaultcolors, dncols, dnrows, thebooks, viewinit, style // parameters dumped by the server, mostly in json form
var viewfluid, side_fetched, material_fetched // transitory flags indicating whether kinds of material and sidebars have loaded content
var wb      // holds the one and only page object
var msg   // messages object

/* url values for AJAX calls from this application */
var page_view_url, query_url, word_url // urls that are presented as citatation urls (do not have https but http!)
var view_url, material_url, data_url, side_url, item_url, chart_url, queries_url, words_url, field_url, fields_url, bol_url // urls from which to fetch additional material through AJAX, the values come from the server
var pref    // prefix for the cookie names, in order to distinguish settings by the user or settings from clicking on a share link

/* fixed dimensions, measures, heights, widths, etc */
var subtract = 150 // the canvas holding the material gets a height equal to the window height minus this amount
var standard_height // height of canvas
var mql_small_height = '10em' // height of mql query body in sidebar
var mql_small_width = '97%' // height of mql query body in sidebar and in dialog
var mql_big_width_dia = '60%' // height of mql query body in sidebar and in dialog
var mql_big_width = '95%' // width of mql query body in sidebar and in dialog
var orig_side_width, orig_main_width // the widths of sidebar and main area just after loading the initial page
var edit_side_width = '55%' // the desired width of the sidebar when editing a query body
var edit_main_width = '40%' // the desired width of the main area when editing a query body
var chart_width = '400px' // dialog width for charts
var chart_cols = 30 // number of chapters in a row in a chart

// TOP LEVEL: DYNAMICS, PAGE, WINDOW, SKELETON

function dynamics() { // top level function, called when the page has loaded
    viewfluid = {}
    msg = new Msg() // a place where ajax messages can be shown to the user
    wb = new Page(new ViewState(viewinit, pref)) // wb is the handle to manipulate the whole page
    wb.init()
    wb.go()
}

function set_height() { // the heights of the sidebars are set, depending on the height of the window
    standard_height = window.innerHeight - subtract
    half_standard_height = (0.4 * standard_height) + 'px'
    $('#material_txt_p').css('height', standard_height+'px')
    $('#material_txt_il').css('height', (2 * standard_height)+'px')
    $('#side_material_mq').css('max-height', (0.75 * standard_height)+'px')
    $('#side_material_mw').css('max-height', (0.75 * standard_height)+'px')
    $('#words').css('height', standard_height+'px')
    $('#letters').css('height', standard_height+'px')
}

function get_width() { // save the orginal widths of sidebar and main area
    orig_side_width = $('.span3').css('width')
    orig_main_width = $('.span9').css('width')
}

function reset_main_width() { // restore the orginal widths of sidebar and main area
    if (orig_side_width != $('.span3').css('width')) {
        $('.span3').css('width', orig_side_width)
        $('.span9').css('width', orig_main_width)
    }
}

function set_edit_width() { // switch to increased sidebar width
    $('.span3').css('width', edit_side_width)
    $('.span9').css('width', edit_main_width)
}

function Page(vs) { // the one and only page object
    this.vs = vs    // the viewstate
    History.Adapter.bind(window,'statechange', this.vs.goback)

    this.init = function() { // dress up the skeleton, initialize state variables
        this.material = new Material()
        this.sidebars = new Sidebars()
        set_height()
        get_width()
        this.listsettings = {}
        for (var qw in {q: 1, w: 1}) {
            this.listsettings[qw] = new ListSettings(qw)
            this.picker2[qw] = this.listsettings[qw].picker2
        }
        this.prev = {}
        for (var x in this.vs.mstate()) {
            this.prev[x] = null
        }
        material_fetched = {txt_p: false, txt_il: false}
    }
    this.apply = function() { // apply the viewstate: hide and show material as prescribed by the viewstate
        this.material.apply()
        this.sidebars.apply()
    }
    this.go = function() { // go to another page view, check whether initial content has to be loaded
        reset_main_width()
        this.apply()
    }
    this.go_material = function() { // load other material, whilst keeping the sidebars the same
        this.material.apply()
    }

/*

the origin must be an object which has a member indicating the type of origin and the kind of page.

1: a color picker 1 from an item in a list
1a: the color picker 1 on an item page
2: a color picker 2 on a list page
3: a button of the list view settings
4: a click on a word in the text
5: when the data or text representation is loaded

*/
    this.highlight2 = function(origin) { /* all highlighting goes through this function
        highlighting is holistic: when the user changes a view settings, all highlights have to be reevaluated.
        The only reduction is that word highlighting is completely orthogonal to query result highlighting.
    */
        var that = this
        var qw = origin.qw
        var code = origin.code
        var active = wb.vs.active(qw)
        if (active == 'hlreset') { // all viewsettings for either queries or words are restored to 'factory' settings
            this.vs.cstatexx(qw)
            this.vs.hstatesv(qw, {active: 'hlcustom', sel_one: defcolor(qw, null)})
            this.listsettings[qw].apply()
            return
        }
        var hlradio = $('.'+qw+'hradio')
        var activeo = $('#'+qw+active)
        hlradio.removeClass('ison')
        activeo.addClass('ison')
        var cmap = this.vs.colormap(qw)

        var paintings = {}

        /* first we are going to compute what to paint, resulting in a list of paint instructions.
        Then we apply the paint instructions in one batch.
        */

        /* computing the paint instructions */

        if (code == '1a') { /* highlights on an r-page (with a single query or word), coming from the associated Color1Picker             
                This is simple coloring, using a single color.
            */
            var iid = origin.iid
            var paint = cmap[iid] || defcolor(null, iid)
            if (qw == 'q') {
                $($.parseJSON($('#themonads').val())).each(function(i, m) {
                    paintings[m] = paint
                })
            }
            else {
                paintings[iid] = paint
            }
            this.paint(qw, paintings)
            return
        }

        /* all other cases: highlights on an m-page, responding to a user action
            This is complex coloring, using multiple colors.
            First we determine which monads need to be highlighted.
        */
        var selclr = wb.vs.sel_one(qw)
        var custitems = {}
        var plainitems = {}

        if (qw == 'q') { /* Queries: highlight customised items with priority over uncustomised items
                If a word belongs to several query results, the last-applied coloring determines the color that the user sees.
                We want to promote the customised colors over the non-customized ones, so we compute customized coloring after 
                uncustomized coloring.
                Skip the muted queries
            */
            $('#side_list_'+qw+' li').each(function() {
                var iid = $(this).attr('iid')
                if (!(muting.isSet(iid+''))) {
                    var monads = $.parseJSON($('#'+qw+iid).attr('monads'))
                    if (wb.vs.iscolor(qw, iid)) {
                        custitems[iid] = monads
                    }
                    else {
                        plainitems[iid] = monads
                    }
                }
            })
        }
        else { // Words: they are disjoint, no priority needed
            $('#side_list_'+qw+' li').each(function() {
                var iid = $(this).attr('iid')
                if (wb.vs.iscolor(qw, iid)) {
                    custitems[iid] = 1
                }
                else {
                    plainitems[iid] = 1
                }
                var all = $('#'+qw+iid)
                if (active == 'hlmany' || wb.vs.iscolor(qw, iid)) {
                    all.show()
                }
                else {
                    all.hide()
                }
            })
        }
        var chunks = [custitems, plainitems]

        var cselect = function(iid) { // assigns a color to an individual monad, based on the viewsettings
            if (active == 'hloff') {paint = style[qw]['off']} /*
                viewsetting says: do not color any item */
            else if (active == 'hlone') {paint = selclr} /*
                viewsetting says: color every applicable item with the same color */
            else if (active == 'hlmany') {paint = cmap[iid] || defcolor(null, iid)} /*
                viewsetting says:
                color every item with customized color (if customized) else with query/word-dependent default color */
            else if (active == 'hlcustom') {paint = cmap[iid] || selclr} /*
                viewsetting says:
                color every item with customized color (if customized) else with a single chosen color */
            else {paint = selclr} /*
                but this should not occur */
            return paint
        }

        if (qw == 'q') { // Queries: compute the monads to be painted and the colors needed for it
            for (var c = 0; c < 2; c++ ) {
                var chunk = chunks[c]
                for (var iid in chunk) {
                    var color = cselect(iid)
                    var monads = chunk[iid]
                    for (var m in monads) {
                        monad = monads[m]
                        if (!(monad in paintings)) {
                            paintings[monad] = color;
                        }
                    }
                }
            }
        }
        else { // Words: gather the lexeme_ids to be painted and the colors needed for it
            for (var c = 0; c < 2; c++ ) {
                var chunk = chunks[c]
                for (var iid in chunk) {
                    var color = style[qw]['off']
                    if (c == 0) { // do not color the plain items when dealing with words (as opposed to queries)
                        color = cselect(iid)
                    }
                    paintings[iid] = color
                }
            }
        }
        /* finally, the computed colors are applied */
        this.paint(qw, paintings)
    }

    this.paint = function(qw, paintings) { // Execute a series of computed paint instructions
        var stl = style[qw]['prop']
        var container = '#material_'+wb.vs.tp()
        var att = (qw == 'q')?'m':'l'
        for (var item in paintings) {
            var color = paintings[item]
            $(container+' span['+att+'="'+item+'"]').css(stl, vcolors[color][qw])
        }
    }

    this.picker2 = {}
    this.picker1 = {q: {}, w: {}}               // will collect the two Colorpicker1 objects, indexed as q w 
    this.picker1list = {q: {}, w: {}}           // will collect the two lists of Colorpicker1 objects, index as q w and then by iid
}

// MATERIAL

function Material() { // Object corresponding to everything that controls the material in the main part (not in the side bars)
    var that = this
    this.name = 'material'
    this.hid = '#'+this.name
    this.mselect = new MSelect()
    this.pselect = new PSelect()
    this.message = new MMessage()
    this.content = new MContent()
    this.msettings = new MSettings(this.content)
    this.adapt = function() {
        this.fetch()
    }
    this.apply = function() { // apply viewsettings to current material
        wb.mr = wb.vs.mr()
        wb.qw = wb.vs.qw()
        wb.iid = wb.vs.iid()
        if (
            wb.mr != wb.prev['mr'] || wb.qw != wb.prev['qw'] ||
            (wb.mr == 'm' && (wb.vs.book() != wb.prev['book'] || wb.vs.chapter() != wb.prev['chapter'])) ||
            (wb.mr == 'r' && (wb.iid != wb.prev['iid'] || wb.vs.page() != wb.prev['page']))
        ) {
            material_fetched = {txt_p: false, txt_il: false}
        }
        this.mselect.apply()
        this.pselect.apply()
        this.msettings.apply()
        var book = wb.vs.book()
        var chapter = wb.vs.chapter()
        var page = wb.vs.page()
        $('#theitemlabel').html('')
        $('#thebook').html((book != 'x')?book:'book')
        $('#thechapter').html((chapter > 0)?chapter:'chapter')
        $('#thepage').html((page > 0)?''+page:'')
        for (var x in wb.vs.mstate()) {
            wb.prev[x] = wb.vs.mstate()[x]
        }
    }
    this.fetch = function() { // get the material by AJAX if needed, and process the material afterward
        var vars = '?mr='+wb.mr+'&tp='+wb.vs.tp()+'&qw='+wb.qw
        if (wb.mr == 'm') {
            vars += '&book='+wb.vs.book()
            vars += '&chapter='+wb.vs.chapter()
            do_fetch = wb.vs.book() != 'x' && wb.vs.chapter() > 0
        }
        else {
            vars += '&iid='+wb.iid
            vars += '&page='+wb.vs.page()
            do_fetch = wb.iid >=0
        }
        if (do_fetch && !material_fetched[wb.vs.tp()]) {
            this.message.msg('fetching data ...')
            wb.sidebars.after_material_fetch()
            $.get(material_url+vars, function(html) {
                var response = $(html)
                that.pselect.add(response)
                that.message.add(response)
                that.content.add(response)
                material_fetched[wb.vs.tp()] = true
                that.process()
            }, 'html')
        }
        else {
            wb.highlight2({code: '5', qw: 'w'})
            if (wb.vs.tp() == 'txt_il') {
                this.msettings.hebrewsettings.apply()
            }
        }
    }
    this.process = function() { // process new material obtained by an AJAX call
        if (wb.mr == 'r') {
            this.pselect.apply()
            wb.picker1[wb.qw].adapt(wb.iid, true)
            $('a.cref').click(function(e) {e.preventDefault();
                wb.vs.mstatesv({book: $(this).attr('book'), chapter: $(this).attr('chapter'), mr: 'm'})
                wb.vs.addHist()
                wb.go()
            })
        }
        else {
            this.add_word_actions()
        }
        var vrefs = $('.vradio')
        vrefs.each(function() {
            var book = $(this).attr('b')
            var chapter = $(this).attr('c')
            var verse = $(this).attr('v')
            $(this).attr('title', 'interlinear data')
        })
        vrefs.click(function(e) {e.preventDefault();
            var bk = $(this).attr('b')
            var ch= $(this).attr('c')
            var vs= $(this).attr('v')
            var dat = $('#txt_il_'+bk+'_'+ch+'_'+vs)
            var txt = $('#txt_p_'+bk+'_'+ch+'_'+vs)
            var legendc = $('#datalegend_control')
            if ($(this).hasClass('ison')) {
                $(this).removeClass('ison')
                $(this).attr('title', 'interlinear data')
                legendc.hide()
                dat.hide()
                txt.show()
            }
            else {
                $(this).addClass('ison')
                $(this).attr('title', 'text only')
                legendc.show()
                dat.show()
                txt.hide()
                if (dat.attr('l') == 'x') {
                    dat.html('fetching data for '+bk+' '+ch+':'+vs+' ...')
                    dat.load(data_url+'?book='+bk+'&chapter='+ch+'&verse='+vs, function() {
                        dat.attr('l', 'v')
                        that.msettings.hebrewsettings.apply()
                        if (wb.mr == 'r') {
                            wb.picker1[wb.qw].adapt(wb.iid, true)
                        }
                        else {
                            wb.highlight2({code: '5', qw: 'w'})
                            wb.highlight2({code: '5', qw: 'q'})
                            //that.add_word_actions()
                        }
                    }, 'html')
                }
            }
        })
        if (wb.vs.tp() == 'txt_il') {
            this.msettings.hebrewsettings.apply()
        }
    }
    this.add_word_actions = function() { // Make words clickable, so that they show up in the sidebar
        $('#material_'+wb.vs.tp()+' span[l]').click(function(e) {e.preventDefault();
            var iid = $(this).attr('l')
            var qw = 'w'
            var all = $('#'+qw+iid)
            if (wb.vs.iscolor(qw, iid)) {
                wb.vs.cstatex(qw, iid)
                all.hide()
            }
            else {
                vals = {}
                vals[iid] = defcolor(null, iid)
                wb.vs.cstatesv(qw, vals)
                all.show()
            }
            var active = wb.vs.active(qw)
            if (active != 'hlcustom' && active != 'hlmany') {
                wb.vs.hstatesv(qw, {active: 'hlcustom'})
            }
            if (wb.vs.get('w') == 'v') {
                wb.picker1list['w'][iid].apply(false)
            }
            wb.highlight2({code: '4', qw: qw})
            wb.vs.addHist()
        })
        if (material_fetched['txt_p'] && material_fetched['txt_il']) {
            wb.highlight2({code: '5', qw: 'q'})
            wb.highlight2({code: '5', qw: 'w'})
        }
    }
    this.message.msg('choose a passage or a query or a word')
}

// MATERIAL: SELECTION

function MSelect() { // for book and chapter selection
    this.name = 'select_passage'
    this.hid = '#'+this.name
    this.book = new SelectBook()
    this.select = new SelectItems('chapter')
    this.apply = function() { // apply material viewsettings to current material
        var bol = $('#bol_lnk')
        if (wb.mr == 'm') {
            this.book.apply()
            this.select.apply()
            $(this.hid).show()
            var book = wb.vs.book()
            var chapter = wb.vs.chapter()
            if (book != 'x' && chapter > 0) {
                bol.attr('href', bol_url+'/ETCBC4/'+book+'/'+chapter)
                bol.show()
            }
            else {
                bol.hide()
            }
        }
        else {
            $(this.hid).hide()
            bol.hide()
        }
    }
}

function PSelect() { // for result page selection
    var select = '#select_contents_page'
    this.name = 'select_pages'
    this.hid = '#'+this.name
    this.select = new SelectItems('page')
    this.apply = function() { // apply result page selection: fill in headings on the page
        if (wb.mr == 'r') {
            this.select.apply()
            $(this.hid).show()
        }
        else {
            $(this.hid).hide()
        }
    }
    this.add = function(response) { // add the content portion of the response to the content portion of the page
        if (wb.mr == 'r') {
            $(select).html(response.find(select).html())
        }
    }
}

function SelectBook() { // book selection
    var that = this
    this.name = 'select_contents_book'
    this.hid = '#'+this.name
    this.control = '#select_control_book'
    this.present = function() {
        $(this.hid).dialog({
            autoOpen: false,
            dialogClass: 'items',
            closeOnEscape: true,
            modal: false,
            title: 'choose book',
            width: '460px',
        })
    }
    this.gen_html = function() { // generate a new book selector
        var thebook = wb.vs.book()
        var nitems = thebooksorder.length
        this.lastitem = nitems
        var ht = ''
        ht += '<div class="pagination"><ul>'
        for (var i in thebooksorder) {
            item = thebooksorder[i]
            if (thebook == item) {
                ht += '<li class="active"><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
            }
            else {
                ht += '<li><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
            }
        }
        ht += '</ul></div>'
        $(this.hid).html(ht)
        return nitems
    }
    this.add_item = function(item) {
        item.click(function(e) {e.preventDefault();
            var newobj = $(this).closest('li')
            var isloaded = newobj.hasClass('active')
            if (!isloaded) {
                vals = {}
                vals['book'] = $(this).attr('item')
                vals['chapter'] = '1'
                wb.vs.mstatesv(vals)
                wb.vs.addHist()
                wb.go()
            }
        })
    }
    this.apply = function() {
        var showit = false
        this.gen_html()
        $('#select_contents_book .itemnav').each(function() {
            that.add_item($(this))
        })
        $(this.control).show()
        this.present()
    }
    $(this.control).click(function(e) {e.preventDefault();
        $(that.hid).dialog('open')
    })
}

function SelectItems(key) { // both for chapters and for result pages
    var that = this
    this.key = key
    this.other_key = (key == 'chapter')?'page':'chapter'
    this.name = 'select_contents_'+this.key
    this.other_name = 'select_contents_'+this.other_key
    this.hid = '#'+this.name
    this.other_hid = '#'+this.other_name
    this.control = '#select_control_'+this.key
    this.prev = $('#prev_'+this.key)
    this.next = $('#next_'+this.key)
    this.go = function() {
        if (this.key == 'chapter') {
            wb.go()
        }
        else {
            wb.go_material()
        }
    }
    this.prev.click(function(e) {e.preventDefault();
        vals = {}
        vals[that.key] = $(this).attr('contents')
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
        that.go()
    })
    this.next.click(function(e) {e.preventDefault();
        vals = {}
        vals[that.key] = $(this).attr('contents')
        wb.vs.mstatesv(vals)
        wb.vs.addHist()
        that.go()
    })
    this.present = function() {
        close_dialog($(this.other_hid))
        $(this.hid).dialog({
            autoOpen: false,
            dialogClass: 'items',
            closeOnEscape: true,
            modal: false,
            title: 'choose '+that.key,
            width: '270px',
        })
    }
    this.gen_html = function() { // generate a new page selector
        if (this.key == 'chapter') {
            var thebook = wb.vs.book()
            var theitem = wb.vs.chapter()
            var nitems = (thebook != 'x')?thebooks[thebook]:0
            this.lastitem = nitems
            var itemlist = new Array(nitems)
            for  (i = 0; i < nitems; i++) {itemlist[i] = i+1}
        }
        else { // 'page'
            var theitem = wb.vs.page()
            var nitems = $('#rp_pages').val()
            this.lastitem = nitems
            var itemlist = []
            if (nitems) {
                itemlist = $.parseJSON($('#rp_pagelist').val())
            }
        }
        var ht = ''
        if (nitems != undefined) {
            if (nitems != 0) {
                ht = '<div class="pagination"><ul>'
                for (var i in itemlist) {
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
        item.click(function(e) {e.preventDefault();
            var newobj = $(this).closest('li')
            var isloaded = newobj.hasClass('active')
            if (!isloaded) {
                vals = {}
                vals[that.key] = $(this).attr('item')
                wb.vs.mstatesv(vals)
                wb.vs.addHist()
                that.go()
            }
        })
    }
    this.apply = function() {
        var showit = false
        showit = this.gen_html() > 0 
        if (!showit) {
            $(this.control).hide()
        }
        else {
            $('#select_contents_'+this.key+' .itemnav').each(function() {
                that.add_item($(this))
            })
            $(this.control).show()
            thisitem = parseInt(this.key == 'page'?wb.vs.page():wb.vs.chapter())
            if (thisitem == undefined || thisitem == 1) {
                this.prev.hide()
            }
            else {
                this.prev.attr('contents', '' + (thisitem - 1))
                this.prev.show()
            }
            if (thisitem == undefined || thisitem == this.lastitem) {
                this.next.hide()
            }
            else {
                this.next.attr('contents', '' + (thisitem + 1))
                this.next.show()
            }
        }
        this.present()
    }
    $(this.control).click(function(e) {e.preventDefault();
        $(that.hid).dialog('open')
    })
}

function CSelect(qw) { // for chart selection
    var that = this
    this.qw = qw
    this.control = '#select_control_chart'+qw
    this.select = '#select_contents_chart'+qw
    this.loaded = null
    $(this.control).click(function(e) {e.preventDefault();
        that.apply()
    })
    this.apply = function() {
        if (that.loaded != wb.iid) {
            this.fetch()
        }
        else {
            this.show()
        }
    }
    this.fetch = function() {
        vars = '?qw='+this.qw+'&iid='+wb.iid
        $(this.select).load(chart_url+vars, function () {
            that.loaded = wb.iid
            that.process()
        }, 'html')
    }
    this.process = function() {
        this.gen_html()
        $('.cnav').each(function() {
            that.add_item($(this))
        })
        var iid = wb.iid
        $('#theitemc').click(function(e) {e.preventDefault();
            vals = {}
            vals['iid'] = iid
            vals['mr'] = 'r'
            vals['qw'] = that.qw
            wb.vs.mstatesv(vals)
            wb.vs.addHist()
            wb.go()
        })
        $('#theitemc').html('Back to '+$('#theitem').html()) // fill in the Back to query/word line in a chart
        this.present()
        this.show()
    }

    this.present = function() {
        $(this.select).dialog({
            autoOpen: false,
            dialogClass: 'items',
            closeOnEscape: true,
            modal: false,
            title: 'chart for '+style[that.qw]['tag'],
            width: chart_width,
            position: { my: "left top", at: "left top", of: window }
        })
    }
    this.show = function() {
        $(this.select).dialog('open')
    }

    this.gen_html = function() { // generate a new chart
        nbooks = 0
        var booklist = $('#r_chartorder'+this.qw).val()
        var bookdata = $('#r_chart'+this.qw).val()
        if (booklist) {
            booklist = $.parseJSON(booklist)
            bookdata = $.parseJSON(bookdata)
            nbooks = booklist.length
        }
        else {
            booklist = []
            bookdata = {}
        }
        var ht = ''
        ht += '<p><a id="theitemc" title="back to '+style[this.qw]['tag']+'" href="#">back</a></p>'
        ht += '<table class="chart">'
        var ccl = ccolors.length
        for (var b in booklist) {
            var book = booklist[b]
            var blocks = bookdata[book]
            ht += '<tr><td class="bnm">'+book+'</td><td class="chp"><table class="chp"><tr>'
            l = 0
            for (var i=0; i < blocks.length; i++) {
                if (l == chart_cols) {
                    ht += '</tr><tr>'
                    l = 0
                }
                var block_info = blocks[i]
                var chnum = block_info[0]
                var ch_range = block_info[1]+'-'+block_info[2]
                var blres = block_info[3]
                var blsize = block_info[4]
                blres_select = (blres >= ccl)?ccl-1:blres
                z = ccolors[blres_select]
                s = '&nbsp;'
                sz = ''
                sc = ''
                if (blsize < 25) {
                    s = '='
                    sc = 's1'
                }
                else if (blsize < 75) {
                    s = '-'
                    sc = 's5'
                }
                if (blsize < 100) {
                    sz = ' ('+blsize+'%)' 
                }
                ht += '<td class="'+z+'"><a title="'+ch_range+sz+': '+blres+'" class="cnav '+sc+'" href="#" b='+book+' ch="'+chnum+'">'+s+'</a></td>'
                l++
            }
            ht += '</tr></table></td></tr>'
        }
        ht += '</table>'
        $(this.select).html(ht)
        return nbooks
    }
    this.add_item = function(item) {
        var iid = wb.iid
        item.click(function(e) {e.preventDefault();
            vals = {}
            vals['book'] = $(this).attr('b')
            vals['chapter'] = $(this).attr('ch')
            vals['mr'] = 'm'
            wb.vs.mstatesv(vals)
            wb.vs.hstatesv('q', {sel_one: 'white', active: 'hlcustom'})
            wb.vs.hstatesv('w', {sel_one: 'black', active: 'hlcustom'})
            var thiscolor = wb.vs.colormap(that.qw)[iid] || defcolor(null, iid)
            wb.vs.cstatexx('q')
            wb.vs.cstatexx('w')
            vals = {}
            vals[iid] = thiscolor
            wb.vs.cstatesv(that.qw, vals)
            wb.vs.addHist()
            wb.go()
        })
    }
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
    var tps = {txt_p: 'txt_il', txt_il: 'txt_p'}
    this.name_text = 'material_text'
    this.name_data = 'material_data'
    this.hid_text = '#'+this.name_text
    this.hid_data = '#'+this.name_data
    this.hid_content = '#material_content'
    this.select = function() {
        this.name_yes = 'material_'+wb.vs.tp()
        this.name_no = 'material_'+tps[wb.vs.tp()]
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

// MATERIAL SETTINGS (for choosing between plain text and interlinear data)

function MSettings(content) {
    var that = this
    var hltext = $('#mtxt_p')
    var hldata = $('#mtxt_il')
    var legend = $('#datalegend')
    var legendc = $('#datalegend_control')
    this.name = 'material_settings'
    this.hid = '#'+this.name
    this.content = content
    this.hebrewsettings = new HebrewSettings()
    legendc.click(function(e) {e.preventDefault();
        legend.dialog({
            autoOpen: true,
            dialogClass: 'legend',
            closeOnEscape: true,
            modal: false,
            title: 'legend',
            width: '600px',
        })
    })
    this.apply = function() {
        var hlradio = $('.mhradio')
        hlradio.removeClass('ison')
        $('#m'+wb.vs.tp()).addClass('ison')
        this.content.show()
        if (wb.vs.tp() == 'txt_il') {
            legend.hide()
            legendc.show()
        }
        else {
            legend.hide()
            legendc.hide()
        }
        set_csv(wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
        wb.material.adapt()
    }
    $('.mhradio').click(function(e) {e.preventDefault();
        wb.vs.mstatesv({tp: $(this).attr('id').substring(1)})
        wb.vs.addHist()
        that.apply()
    })
}

// HEBREW DATA (which fields to show if interlinear text is displayed)

function HebrewSettings() {
    for (var fld in wb.vs.hdata()) {
        this[fld] = new HebrewSetting(fld)
    }
    this.apply = function() {
        for (var fld in wb.vs.hdata()) {
            this[fld].apply()
        }
    }
}

function HebrewSetting(fld) {
    var that = this
    this.name = fld
    this.hid = '#'+this.name
    $(this.hid).click(function(e) {
        vals = {}
        vals[fld] = $(this).prop('checked')?'v':'x'
        wb.vs.dstatesv(vals)
        wb.vs.addHist()
        that.applysetting()
    })
    this.apply = function() {
        var val = wb.vs.hdata()[this.name]
        $(this.hid).prop('checked', val == 'v')
        this.applysetting()
    }
    this.applysetting = function() {
        if (wb.vs.hdata()[this.name] == 'v') {
            $('.'+this.name).each(function () {$(this).show()})
        }
        else {
            $('.'+this.name).each(function () {$(this).hide()})
        }
        set_csv(wb.vs.mr(), wb.vs.qw(), wb.vs.iid())
    }
}

// SIDEBARS

/*

The main material kan be two kinds (mr)

m = material: chapters from books
r = query/word results

There are four kinds of sidebars, indicated by two letters, of which the first indicates the mr

mq = list of queries relevant to main material
mw = list of words relevant to main material
rq = display of query record, the main material are the query results
rw = display of word record, the main material are the word results

The list sidebars (m) have a color picker for selecting a uniform highlight color,
plus controls for deciding whether no, uniform, custom, or many colors will be used.

The record-side bars (r) only have a single color picker, for 
choosing the color associated with the item (a query or a word).

When items are displayed in the list sidebars, they each have a color picker that
is identical to the one used for that item in the record sidebar.

The colorpickers for choosing an associated item color, consist of a checkbox and a proper colorpicker.
The checkbox indicates whether the color is customized. 
A color gets customized when the user selects an other color than the default one, or by checking the box.

When the user has chosen custom colors, all highlights will be done with the uniform color, except
the customized ones.

Queries are highlighted by background color, words by foreground colors.
Although the names for background and foreground colors are identical, their actual values are not.
Foreground colors are darkened, background colors are lightened.
This is done for better visibility.

All color asscociations are preserved in cookies, one for queries, and one for words.
Nowhere else are they stored, but they can be exported as a (lomg) link.
By using the share link, the user can preserve color settings in a notebook, or mail them to colleagues.

*/

function Sidebars() { // TOP LEVEL: all four kinds of sidebars
    this.sidebar = {}
    for (var mr in {m: 1, r: 1}) {
        for (var qw in {q: 1, w: 1}) {
            this.sidebar[mr+qw] = new Sidebar(mr, qw)
        }
    }
    side_fetched = {}
    this.apply = function() {
        for (var mr in {m: 1, r: 1}) {
            for (var qw in {q: 1, w: 1}) {
                this.sidebar[mr+qw].apply()
            }
        }
    }
    this.after_material_fetch = function() {
        for (var qw in {q: 1, w: 1}) {
            side_fetched['m'+qw] = false
        }
    }
    this.after_item_fetch = function() {
        for (var qw in {q: 1, w: 1}) {
            side_fetched['r'+qw] = false
        }
    }
}

// SPECIFIC sidebars, the [mr][qw] type is frozen into the object

function Sidebar(mr, qw) { // the individual sidebar, parametrized with qr and mw to specify one of the four kinds
    var that = this
    this.mr = mr
    this.qw = qw
    this.name = 'side_bar_'+mr+qw
    this.hid = '#'+this.name
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+mr+qw)
    var theset = $('#side_settings_'+mr+qw)
    var hide = $('#side_hide_'+mr+qw)
    var show = $('#side_show_'+mr+qw)
    this.content = new SContent(mr, qw)
    if (mr == 'r') {
        this.cselect = new CSelect(qw)
    }
    this.apply = function() {
        if ((this.mr != wb.mr) || (this.mr == 'r' && this.qw != wb.qw)) {
            thebar.hide()
        }
        else {
            thebar.show()
            theset.show()
            if (this.mr == 'm') {
                if (wb.vs.get(this.qw) == 'x') {
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
            else {
                hide.hide()
                show.hide()
            }
            this.content.apply()
        }
    }
    show.click(function(e){e.preventDefault();
        wb.vs.hstatesv(that.qw, {get: 'v'})
        wb.vs.addHist()
        that.apply()
    })
    hide.click(function(e){e.preventDefault();
        wb.vs.hstatesv(that.qw, {get: 'x'})
        wb.vs.addHist()
        that.apply()
    })
}

// SIDELIST MATERIAL

function SContent(mr, qw) { // the contents of an individual sidebar
    var that = this
    this.mr = mr
    this.qw = qw
    this.other_mr = (this.mr == 'm')?'r':'m'
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+mr+qw)
    var hide = $('#side_hide_'+mr+qw)
    var show = $('#side_show_'+mr+qw)
    this.name = 'side_material_'+mr+qw
    this.hid = '#'+this.name
    this.msg = function(m) {
        $(this.hid).html(m)
    }
    this.process = function() {
        wb.sidebars.after_item_fetch()
        this.sidelistitems()
        if (this.mr == 'm') {
            wb.listsettings[this.qw].apply()
        }
        else {
            var iid = wb.vs.iid()
            set_csv(mr, qw, iid)
            if (qw == 'q') {
                var oname = escapeHTML(q.oname)
                var pname = escapeHTML(q.pname)
                var uname = escapeHTML(q.uname)
                var qname = escapeHTML(q.name)
                $('#itemtag').val(uname+': '+qname)
                $('#gobackq').attr('href', queries_url+'?goto='+iid)
                $('#nameu').html(uname)
                $('#nameul').attr('href', 'mailto:'+q.uemail)
                $('#nameo').html(oname)
                $('#nameol').attr('href', q.owebsite)
                $('#namep').html(pname)
                $('#namepl').attr('href', q.pwebsite)
                $('#nameqm').html(qname)
                $('#nameq').val(q.name)
                $('#qid').val(q.id)
                $('#is_pub_c').attr('qid', q.id)
                $('#descm').html(q.description_md)
                $('#descq').val(q.description)
                $('#mqlq').val(q.mql)
                $('#ispub_ro').attr('class', 'ui-icon ui-icon-'+((q.is_published == 'T')?'check':'closethick'))
                $('#ispub_c').prop('checked', q.is_published == 'T')
                $('#created_on').html(q.created_on)
                $('#modified_on').html(q.modified_on)
                $('#executed_on').html(q.executed_on)
                $('#statq').removeClass('error warning good').addClass(q.status)
                this.setstatus(null)
            }
            else {
                var g_entry_heb = escapeHTML(w.g_entry_heb)
                var g_entry = escapeHTML(w.g_entry)
                var entry_heb = escapeHTML(w.entry_heb)
                var entry = escapeHTML(w.entry)
                var entryid_heb = escapeHTML(w.entryid_heb)
                var entryid = escapeHTML(w.entryid)
                var pos = escapeHTML(w.pos)
                var subpos = escapeHTML(w.subpos)
                var nametype = escapeHTML(w.nametype)
                var root = escapeHTML(w.root)
                var lan = escapeHTML(w.lan)
                var gloss = escapeHTML(w.gloss)
                $('#itemtag').val(entry_heb+': '+entryid)
                $('#gobackw').attr('href', words_url+'?lan='+lan+'&letter='+entry_heb.charCodeAt(0)+'&goto='+w.id)
                $('#g_entry_heb').html(g_entry_heb)
                $('#g_entry').html(g_entry)
                $('#entry_heb').html(entry_heb)
                $('#entry').html(entry)
                $('#entryid_heb').html(entryid_heb)
                $('#entryid').html(entryid)
                $('#pos').html(pos)
                $('#subpos').html(subpos)
                $('#nametype').html(nametype)
                $('#root').html(root)
                $('#lan').html(lan)
                $('#gloss').html(gloss)
            }
        }

        $('#theitem').html($('#itemtag').val()+' ')                              // fill in the title of the query/word above the verse material
        if (this.mr == 'm') {  // in the sidebar list of queries: the mql query body can be popped up as a dialog for viewing it in a larger canvas
            $('.fullc').click(function(e) {e.preventDefault();
                var thisiid = $(this).attr('iid')
                var mqlq = $('#area_'+thisiid)
                var dia = $('#bigq_'+thisiid).dialog({
                    dialogClass: 'mql_dialog',
                    closeOnEscape: true,
                    close: function() {
                        dia.dialog('destroy')
                        var mqlq = $('#area_'+thisiid)
                        mqlq.removeClass('mql_dia')
                        mqlq.addClass('mql small')
                        mqlq.css('height', mql_small_height)
                        mqlq.css('width', mql_small_width)
                    },
                    modal: false,
                    title: 'mql query body',
                    position: {my: 'left top', at: 'left top', of: window},
                    width: '600px',
                })
                mqlq.removeClass('mql small')
                mqlq.addClass('mql_dia')
                mqlq.css('height', standard_height)
                mqlq.css('width', mql_big_width)
            })
        }
        else { // in the sidebar item view of a single query: the mql query body can be popped up as a dialog for viewing it in a larger canvas
            var fullc = $('.fullc')
            var mqlq = $('#mqlq')
            var descm = $('#descm')
            fullc.click(function(e) {e.preventDefault();
                fullc.hide()
                var dia = $('#bigger').closest('div').dialog({
                    dialogClass: 'mql_dialog',
                    closeOnEscape: true,
                    close: function() {
                        dia.dialog('destroy')
                        var mqlq = $('textarea.mql_dia')
                        mqlq.removeClass('mql_dia')
                        mqlq.addClass('mql')
                        mqlq.css('height', mql_small_height)
                        mqlq.css('width', mql_small_width)
                        descm.removeClass('desc_dia')
                        descm.addClass('desc')
                        descm.css('height', mql_small_height)
                        descm.css('width', mql_small_width)
                        fullc.show()
                    },
                    modal: false,
                    title: 'description and mql query body',
                    position: {my: 'left top', at: 'left top', of: window},
                    width: mql_big_width_dia,
                    height: standard_height,
                })
                mqlq.removeClass('mql')
                mqlq.addClass('mql_dia')
                mqlq.css('height', half_standard_height)
                mqlq.css('width', mql_big_width)
                descm.removeClass('desc')
                descm.addClass('desc_dia')
                descm.css('height', half_standard_height)
                descm.css('width', mql_big_width)
            })
            msg.set_dest('#dbmsg_q')
            $('#is_pub_c').click(function(e) {
                val = $(this).prop('checked')
                that.sendval($(this).attr('qid'), 'is_published', val?'T':'')
            })
            var detlq = $('.detail')
            var editq = $('#editq')
            var execq = $('#execq')
            var saveq = $('#saveq')
            var doneq = $('#doneq')
            var nameq = $('#nameq')
            var descq = $('#descq')
            var descm = $('#descm')
            nameq.hide()
            descq.hide()
            descm.show()
            detlq.show()
            editq.show()
            execq.hide()
            saveq.hide()
            doneq.hide()
            editq.click(function(e) {e.preventDefault();
                set_edit_width()
                nameq.show()
                descq.show()
                descm.hide()
                detlq.hide()
                editq.hide()
                execq.show()
                saveq.show()
                doneq.show()
                mqlq.prop('readonly', false)
                mqlq.css('height', '20em')
            })
            doneq.click(function(e) {e.preventDefault();
                reset_main_width()
                nameq.hide()
                descq.hide()
                descm.show()
                detlq.show()
                editq.show()
                execq.hide()
                saveq.hide()
                doneq.hide()
                mqlq.prop('readonly', true)
                mqlq.css('height', '10em')
            })
            saveq.click(function(e) {e.preventDefault();
                var data = {
                    qid: $('#qid').val(),
                    name: $('#nameq').val(),
                    description: $('#descq').val(),
                    mql: $('#mqlq').val(),
                    execute: false,
                }
                that.sendvals(data)
            })
            execq.click(function(e) {e.preventDefault();
                var data = {
                    qid: $('#qid').val(),
                    name: $('#nameq').val(),
                    description: $('#descq').val(),
                    mql: $('#mqlq').val(),
                    execute: true,
                }
                that.sendvals(data)
            })
        }
    }
    this.setstatus = function(cls) {
        var statq = (cls != null)?cls:$('#statq').attr('class');
        var statm = (statq == 'good')?'results up to date':((statq == 'error')?'results outdated':'never executed')
        $('#statm').html(statm)
    }
    this.sendval = function(iid, fname, val) {
        var good = false
        var senddata = {}
        senddata.qid = iid
        senddata.fname = fname
        senddata.val = val
        $.post(field_url, senddata, function(json) {
            good = json.good
            msg.clear()
            json.msgs.forEach(function(m) {
                msg.msg(m)
            })
        }, 'json')
    }
    this.sendvals = function(senddata) {
        var good = false
        var execute = senddata.execute;
        $.post(fields_url, senddata, function(json) {
            good = json.good
            var q = json.q
            msg.clear()
            json.msgs.forEach(function(m) {
                msg.msg(m)
            })
            if (good) {
                $('#nameqm').html(escapeHTML(q.name))
                $('#nameq').val(q.name)
                $('#descm').html(q.description_md)
                $('#descq').val(q.description)
                $('#mqlq').val(q.mql)
                $('#statq').removeClass('error warning good').addClass(q.status)
                that.setstatus(q.status)
            }
            if (execute) {
                material_fetched = {txt_p: false, txt_il: false}
                wb.material.adapt()
            }
        }, 'json')
    }
    this.apply = function() {
        if (wb.mr == this.mr && (this.mr == 'r' || wb.vs.get(this.qw) == 'v')) {
            this.fetch()
        }
    }
    this.fetch = function() {
        var thebook = wb.vs.book()
        var thechapter = wb.vs.chapter()
        var vars = '?mr='+this.mr+'&qw='+this.qw
        var do_fetch = false
        var extra = ''
        if (this.mr == 'm') {
            vars += '&book='+wb.vs.book()
            vars += '&chapter='+wb.vs.chapter()
            do_fetch = wb.vs.book() != 'x' && wb.vs.chapter() > 0
            extra = 'm'
        }
        else {
            vars += '&iid='+wb.iid
            do_fetch = wb.iid >=0
            extra = this.qw+'m'
        }
        if (do_fetch && !side_fetched[this.mr+this.qw]) {
            this.msg('fetching '+style[this.qw]['tag'+(this.mr=='m'?'s':'')]+' ...')
            if (this.mr == 'm') {
                thelist.load(side_url+extra+vars, function () {
                    side_fetched[that.mr+that.qw] = true
                    that.process()
                }, 'html')
            }
            else {
                $.get(side_url+extra+vars, function (html) {
                    thelist.html(html)
                    side_fetched[that.mr+that.qw] = true
                    that.process()
                }, 'html')

            }
        }
    }
    this.sidelistitems = function() { // the list of items in an m-sidebar
        if (this.mr == 'm') {
            wb.picker1list[that.qw] = {}
            var qwlist = $('#side_list_'+this.qw+' li')
            qwlist.each(function() {
                var iid = $(this).attr('iid') 
                that.sidelistitem(iid)
                wb.picker1list[that.qw][iid] = new Colorpicker1(that.qw, iid, false, false)
            })
        }
    }
    this.sidelistitem = function(iid) { // individual item in an m-sidebar
        var itop = $('#'+this.qw+iid) 
        var more = $('#m_'+this.qw+iid) 
        var head = $('#h_'+this.qw+iid) 
        var desc = $('#d_'+this.qw+iid) 
        var item = $('#item_'+this.qw+iid) 
        var all = $('#'+this.qw+iid)
        desc.hide()
        more.click(function(e) {e.preventDefault();
            desc.toggle()
        })
        item.click(function(e) {e.preventDefault();
            var qw = that.qw
            wb.vs.mstatesv({mr: that.other_mr, qw: qw, iid: $(this).attr('iid'), page: 1})
            wb.vs.addHist()
            wb.go()
        })
        if (this.qw == 'w') {
            if (!wb.vs.iscolor(this.qw, iid)) {
                all.hide()
            }
        }
        if (this.qw == 'q') {
            if (muting.isSet('q'+iid)) {
                itop.hide()
            }
            else {
                itop.show()
            }
        }
    }
    if (this.mr == 'r') {
        wb.picker1[this.qw] = new Colorpicker1(this.qw, null, true, false)
    }
}

// SIDELIST VIEW SETTINGS

function ListSettings(qw) { // the view controls belonging to a side bar with a list of items
    var that = this
    this.qw = qw
    var hlradio = $('.'+qw+'hradio')

    this.apply = function() {
        if (wb.vs.get(this.qw) == 'v') {
            for (var iid in wb.picker1list[this.qw]) {
                wb.picker1list[this.qw][iid].apply(false)
            }
            wb.picker2[this.qw].apply(true)
        }
    }
    this.picker2 = new Colorpicker2(this.qw, false)
    hlradio.click(function(e) {e.preventDefault();
        wb.vs.hstatesv(that.qw, {active: $(this).attr('id').substring(1)})
        wb.vs.addHist()
        wb.highlight2({code: '3', qw: that.qw})
    })
}

function set_csv(mr, qw, iid) {
    if (mr == 'r') {
        $('#csv_lnk'+qw).attr('href', wb.vs.csv_url())
        $('#csvitemdesc'+qw).html(style[qw]['t']+iid+'.csv')
    }
}

function Colorpicker1(qw, iid, is_item, do_highlight) { // the colorpicker associated with individual items
/*
    These pickers show up
        in lists of items (in mq and mw sidebars) and
        near individual items (in rq and rw sidebars)

    They also have a checkbox, stating whether the color counts as customized.
    Customized colors are held in a global colormap, which is saved in a cookie upon every picking action.

    All actions are processed by the highlight2 (!) method of the associated Settings object.
*/
    var that = this
    this.code = is_item?'1a':'1'
    this.qw = qw
    this.iid = iid
    var is_item = is_item
    var pointer = is_item?'me':iid
    var stl = style[this.qw]['prop']
    var sel = $('#sel_'+this.qw+pointer)
    var selw = $('#sel_'+this.qw+pointer+'>a')
    var selc = $('#selc_'+this.qw+pointer)
    var picker = $('#picker_'+this.qw+pointer)
   
    this.adapt = function(iid, do_highlight) {
        this.iid = iid
        this.apply(do_highlight)
    }
    this.apply = function(do_highlight) {
        var color = wb.vs.color(this.qw, this.iid) || defcolor(null, this.iid)
        var target = (this.qw == 'q')?sel:selw
        target.css(stl, vcolors[color][this.qw])                  // apply state to the selected cell
        selc.prop('checked', wb.vs.iscolor(this.qw, this.iid))                   // apply state to the checkbox
        if (do_highlight) {
            wb.highlight2(this)
        }
    }

    sel.click(function(e) {e.preventDefault();
        picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: selc},
            width: '200px',
        })
    })
    selc.click(function(e) {
                        // process a click on the selectbox of the picker
        var was_cust = wb.vs.iscolor(that.qw, that.iid)
        close_dialog(picker)
        if (was_cust) {
            wb.vs.cstatex(that.qw, that.iid)
        }
        else {
            vals = {}
            vals[that.iid] = defcolor(null, that.iid)
            wb.vs.cstatesv(that.qw, vals)
            var active = wb.vs.active(that.qw)
            if (active != 'hlcustom' && active != 'hlmany') {
                wb.vs.hstatesv(that.qw, {active: 'hlcustom'})
            }
        }
        wb.vs.addHist()
        that.apply(true)
    })
    $('.c'+this.qw+'.'+this.qw+pointer+'>a').click(function(e) {e.preventDefault();
        // process a click on a colored cell of the picker
        close_dialog(picker)
        vals = {}
        vals[that.iid] = $(this).html()
        wb.vs.cstatesv(that.qw, vals)
        wb.vs.hstatesv(that.qw, {active: 'hlcustom'})
        wb.vs.addHist()
        that.apply(true)
    })
    picker.hide()
    $('.c'+this.qw+'.'+this.qw+pointer+'>a').each(function() { //initialize the individual color cells in the picker
        var target = (that.qw == 'q')?$(this).closest('td'):$(this)
        target.css(stl, vcolors[$(this).html()][that.qw])
    })
    this.apply(do_highlight)
}

function Colorpicker2(qw, do_highlight) { // the colorpicker associated with the view settings in a sidebar
/*
    These pickers show up at the top of the individual sidebars, only on mq and mw sidebars.
    They are used to control the uniform color with which the results are to be painted.
    They can be configured for dealing with background or foreground painting.
    The paint actions depend on the mode of coloring that the user has selected in settings.
    So the paint logic is more involved.
    But there is no associated checkbox.
    The selected color is stored in the highlight settings, which are synchronized in a cookie. 

    All actions are processed by the highlight2 method of the associated Settings object.
*/
    var that = this
    this.code = '2'
    this.qw = qw
    var stl = style[this.qw]['prop']
    var sel = $('#sel_'+this.qw+'one')
    var selw = $('#sel_'+this.qw+'one>a')
    var picker = $('#picker_'+this.qw+'one')
    
    this.apply = function(do_highlight) {
        var color = wb.vs.sel_one(this.qw) || defcolor(this.qw, null)
        target = (this.qw == 'q')?sel:selw
        target.css(stl, vcolors[color][this.qw]) // apply state to the selected cell
        if (do_highlight) {
            wb.highlight2(this)
        }
    }
    sel.click(function(e) {e.preventDefault();
        picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: sel},
            width: '200px',
        })
    })
    $('.c'+this.qw+'.'+this.qw+'one>a').click(function(e) {e.preventDefault();
                // process a click on a colored cell of the picker
        close_dialog(picker)
        var current_active = wb.vs.active(that.qw)
        if (current_active != 'hlone' && current_active != 'hlcustom') {
            wb.vs.hstatesv(that.qw, {active: 'hlcustom', sel_one: $(this).html()})
        }
        else {
            wb.vs.hstatesv(that.qw, {sel_one: $(this).html()})
        }
        wb.vs.addHist()
        that.apply(true)
    })
    picker.hide()
    $('.c'+this.qw+'.'+this.qw+'one>a').each(function() { //initialize the individual color cells in the picker
        target = (that.qw == 'q')?$(this).closest('td'):$(this)
        target.css(stl, vcolors[$(this).html()][that.qw])
    })
    this.apply(do_highlight)
}

function defcolor(qw, iid) {// compute the default color
/*
    The data for the computation comes from the server and is stored in the javascript global variables
        vdefaultcolors
        dncols, dnrows
*/
    if (qw == null) {
        var mod = iid % vdefaultcolors.length
        result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
    }
    else {
        result = style[qw]['default']
    }
    return result
}

// VIEW STATE


function ViewState(init, pref) {
    var that = this
    this.data = init
    this.pref = pref
    this.from_push = false

    this.getvars = function() {
        var vars = ''
        var sep = '?'
        for (var group in this.data) {
            for (var qw in this.data[group]) {
                for (var name in this.data[group][qw]) {
                    vars += sep+qw+name+'='+this.data[group][qw][name] 
                    sep = '&'
                }
            }
        }
        return vars
    }
    this.csv_url = function() {
        return item_url+this.getvars()
    }
    this.goback = function() {
        var state = History.getState()
        if (!that.from_push && state && state.data) {
            that.apply(state)
        }
    }
    this.addHist = function() {
        var title = (this.mr() == 'm')?(that.book()+' '+that.chapter()):(style[that.qw()]['Tag']+' '+that.iid()+' p'+that.page())
        that.from_push = true
        History.pushState(that.data, title, view_url)
        that.from_push = false
    }
    this.apply = function(state, load_it) {
        if (state.data != undefined) {
            that.data = state.data
        }
        wb.go()
    }
    this.delsv = function(group, qw, name) {
        delete this.data[group][qw][name]
        $.cookie(this.pref+group+qw, this.data[group][qw])
    }

    this.setsv = function(group, qw, values) {
        for (var mb in values) {
            this.data[group][qw][mb] = values[mb]
        }
        $.cookie(this.pref+group+qw, this.data[group][qw])
    }

    this.resetsv = function(group, qw) {
        for (var mb in this.data[group][qw]) {
            delete this.data[group][qw][mb]
        }
        $.cookie(this.pref+group+qw, this.data[group][qw])
    }
    this.mstatesv = function(values) { this.setsv('material', '', values) }
    this.dstatesv = function(values) { this.setsv('hebrewdata', '', values) }
    this.hstatesv = function(qw, values) { this.setsv('highlights', qw, values) }
    this.cstatesv = function(qw, values) { this.setsv('colormap', qw, values) }
    this.cstatex = function(qw, name) { this.delsv('colormap', qw, name) }
    this.cstatexx = function(qw) { this.resetsv('colormap', qw) }

    this.mstate =function() {return this.data['material']['']}
    this.hdata =function() {return this.data['hebrewdata']['']}
    this.mr = function() {return this.data['material']['']['mr']}
    this.qw = function() {return this.data['material']['']['qw']}
    this.tp = function() {return this.data['material']['']['tp']}
    this.iid = function() {return this.data['material']['']['iid']}
    this.book = function() {return this.data['material']['']['book']}
    this.chapter = function() {return this.data['material']['']['chapter']}
    this.page = function() {return this.data['material']['']['page']}
    this.get = function(qw) {return this.data['highlights'][qw]['get']}
    this.active = function(qw) {return this.data['highlights'][qw]['active']}
    this.sel_one = function(qw) {return this.data['highlights'][qw]['sel_one']}
    this.colormap = function(qw) {return this.data['colormap'][qw]}
    this.color = function(qw, id) {return this.data['colormap'][qw][id]}
    this.iscolor = function(qw, cl) {return cl in this.data['colormap'][qw]} 

    this.addHist()
}

function close_dialog(dia) {
    if (dia && dia.dialog('instance') && dia.dialog('isOpen')) {dia.dialog('close')}
}

/* Words */

var Request = {
    parameter: function(name) {
        return this.parameters()[name]
    },
    parameters: function(uri) {
        var i, parameter, params, query, result;
        result = {};
        if (!uri) {
            uri = window.location.search;
        }
        if (uri.indexOf("?") === -1) {
            return {};
        }
        query = uri.slice(1);
        params = query.split("&");
        i = 0;
        while (i < params.length) {
            parameter = params[i].split("=");
            result[parameter[0]] = parameter[1];
            i++;
        }
        return result;
    }
}

function words_init() {
    var gotoword = Request.parameter('goto');
    set_height()
    $('[wii]').hide()
    $('[gi]').click(function(e) {e.preventDefault();
        var i = $(this).attr('gi')
        $('[wi="'+i+'"]').toggle()
        $('[wii="'+i+'"]').toggle()
    })
    $('[gi]').closest('td').removeClass('selecthlw')
    var wtarget = $('[gi='+gotoword+']').closest('td')
    wtarget.addClass('selecthlw')
    wtarget[0].scrollIntoView()
}

/* GENERIC */

var escapeHTML = (function () {
    'use strict';
    var chr = {
        '&': '&amp;', '<': '&lt;',  '>': '&gt;'
    };
    return function (text) {
        return text.replace(/[&<>]/g, function (a) { return chr[a]; });
    };
}());

function Msg() {
    var that = this
    this.destination = $('#material_message')
    this.clear = function() {
        this.destination.html('')
        this.trashc.hide()
    }
    this.set_dest = function(dest) {
        this.destination = $(dest)
        this.trashc = $('.trashc')
        this.trashc.click(function(e) {e.preventDefault();
            that.clear()
            that.trashc.hide()
        })
        that.trashc.hide()
    }
    this.msg = function(msgobj) {
        var msgc = this.destination;
        mtext = msgc.html()
        msgc.html(mtext+'<p class="'+msgobj[0]+'">'+msgobj[1]+'</p>')
        this.trashc.show()
    }
}
