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
 * 1. Monads of 1 query (click trigger);
 * 2. Monads of all queries;
 * 3. Specific monads from an input field.
 */

// Helper: clear all highlights present in the text.
function clear_all_highlights() {
    $('.highlight').each(function () {
        $( this ).removeClass('highlight');
    });
}

// Helper: Add highlights based on monads variable.
function add_highlights(monads) {
    monads = $.parseJSON(monads);

    // Add a 'highlight' class to each monad SPAN
    $.each(monads, function(index, item) {
        $('span[m="' + item + '"]').addClass('highlight');
    });
}

// 1. Highlight monads of 1 query: use click on query trigger to highlight
// monads in text.
function add_query_highlights() {
    $("#queries li").click(function() {
        clear_all_highlights();
        add_highlights($(this).attr('monads'));
    });
}

// 2. Highlight all monads from all queries.
function add_all_monads_highlights() {
    clear_all_highlights();
    $("#queries li").each( function(index, item) {
        add_highlights($(item).attr('monads'));
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
    add_query_highlights();             // Highlights case 2
    add_specific_monad_highlights();    // Highlights case 3

    get_last_chapter_num();             // Chapter options
});
