/********************** CHAPTER OPTIONS **************************************/
// HELPER function to generate the options from a last chapter number.
function replace_select_options(selectBox, last_chapter_num) {
    $(selectBox).empty();
    for(var i=1; i<=last_chapter_num; i++){
        $(selectBox)
            .append($("<option></option>")
            .attr("value", i)
            .text(i));
    }
};

// Get last chapter number of the current selected book on book option change.
function get_last_chapter_num() {
    $("select#verses_form_Book").change(function () {
        ajax('last_chapter_num', ['Book'], ':eval');
    });

    // Replace chapter options with current chapter options after ajax call
    // finishes.
    $( document ).ajaxComplete(function(event, xhr, settings) {
        if ( settings.url === 'last_chapter_num' ) {
            replace_select_options('#verses_form_Chapter', xhr.responseText);
        }
    });
}
/*****************************************************************************/
/********************** HIGHLIGHTS *******************************************/
/* Cases:
 * 1. Get queries: on select 'highlight all queries' checkbox highlight monads
 *    of all queries;
 * 2. Get queries: on select query checkbox highlight selected queries;
 * 3. Request var: on page load highlight specific monads from an input field.
 */


function jsviewlink(vars) {
    $("#cviewlink").hide();
    $("#xviewlink").hide();

    $("#xviewlink").click(function() {
        $("#cviewlink").hide()
        $("#xviewlink").hide()
        $("#yviewlink").show()
    })
    $("#yviewlink").click(function() {
        $("#yviewlink").hide()
        $("#xviewlink").show()
        $('#cviewlink').each(function () {
            $( this ).val(view_url + "&" + vars)
            $( this ).show()
            $( this ).select()
        })
    })
}

function jsqueriesview(init) {
    $('#h_queries').hide()
    $('#s_queries').click(function(){
        $('#s_queries').hide()
        $('#h_queries').show()
        $('#qbar').show()
    })
    $('#h_queries').click(function(){
        $('#h_queries').hide()
        $('#s_queries').show()
        $('#qbar').hide()
    })
    if (init == 1) {
       $('#fetchqueries').click()
       $('#s_queries').hide()
    }
}

function jsqueryview(qid) {
    $('#l_' + qid).hide()
    $('#d_' + qid).hide()
    $('#l_' + qid).click(function() {
        $('#l_' + qid).hide()
        $('#m_' + qid).show()
        $('#d_' + qid).hide()
    })
    $('#m_' + qid).click(function() {
        $('#l_' + qid).show()
        $('#m_' + qid).hide()
        $('#d_' + qid).show()
    })
    add_highlights(null, qid)
}

function jscolorpicker(qid, initc, monads) {
    $('#picker_' + qid).hide()
    $('#sel_' + qid).click(function() {
        $('#picker_' + qid).show()
    })
    $('.cc.' + qid).click(function() {
        $('#picker_' + qid).hide()
        $('#sel_' + qid).css('background-color', $(this).css('background-color'))
        $('#sel_' + qid).html($(this).html())
        add_highlights(monads, qid);
    })
    if (initc != '') {
        $('#sel_' + qid).css('background-color', initc)
    }
}

function set_highlights() {
    $('#qhloff').click(function() {
        $('#qhloff').hide()
        $('#qhlon').show()
        $("#queries li").each(function(index, item) {
            clear_highlights($(item).attr('monads'));
        })
    })
    $('#qhlon').click(function() {
        $('#qhlon').hide()
        $('#qhloff').show()
        $("#queries li").each(function(index, item) {
            add_highlights($(item).attr('monads'), $(item).attr('qid'));
        })
    })
    $('#qhlon').hide()
}

function clear_highlights(monads) {
    var mn = (monads == null)? $('#query_' + qid).attr('monads') : monads
    mn = $.parseJSON(mn);

    qhc = '#ffffff'
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc);
    })
}

function add_highlights(monads, qid) {
    var mn = (monads == null)? $('#query_' + qid).attr('monads') : monads
    mn = $.parseJSON(mn);

    qhc = $('#sel_' + qid).css('background-color')
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc);
    })
}

/*****************************************************************************/


$( document ).ready(function () {
    get_last_chapter_num();             // Chapter options
});
