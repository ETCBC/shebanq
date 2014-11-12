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

function jscolorpicker(qid, initc, monads) {
    $('#picker_' + qid).hide()
    $('#sel_' + qid).click(function() {
        $('#picker_' + qid).show()
    })
    var mn = (monads == null)? $('#query_' + qid).attr('monads') : monads
    $('.cc.' + qid).click(function() {
        $('#picker_' + qid).hide()
        $('#sel_' + qid).css('background-color', $(this).css('background-color'))
        $('#sel_' + qid).html($(this).html())
        add_highlights(mn, qid);
    })
    if (initc != '') {
        $('#sel_' + qid).css('background-color', initc)
    }
}

// Helper: clear all highlights present in the text.
function clear_all_highlights() {
    $('.highlight').each(function () {
        $( this ).removeClass('highlight');
    });
}

// Helper: Add highlights based on monads variable.
function add_highlights(monads, qid) {
    monads = $.parseJSON(monads);

    // Add a 'highlight' class to each monad SPAN
    qhc = $('#sel_' + qid).css('background-color')
    $.each(monads, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc);
    });
}

// 1. Highlight all monads of all queries on 'highlight all queries' check.
function add_all_monads_highlights() {
    $("#queries li").each( function(index, item) {
        add_highlights($(item).attr('monads'), $(item).attr('qid'));
    });
}

// 2. Highlight monads of the selected/checked queries, the trigger is: checking
// a query checkbox.
function highlight_selected_queries() {
    $("#queries input[type=checkbox]").change(function() {
        clear_all_highlights();
        $("#queries input:checked").each( function(index, item) {
            add_highlights($(item).closest("li").attr('monads'), $(item).closest("li").attr('qid'));
        });
    });
}

// 3. Highlight specific monads using a global w2p_monads variable.
function add_specific_monad_highlights() {
    if (!(typeof w2p_monads === 'undefined')){
        clear_all_highlights();
        add_highlights(w2p_monads);
    }
}
/*****************************************************************************/


$( document ).ready(function () {
    add_all_monads_highlights();        // Highlights case 1
    highlight_selected_queries();       // Highlights case 2
    add_specific_monad_highlights();    // Highlights case 3

    get_last_chapter_num();             // Chapter options
});
