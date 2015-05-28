
function deselectText() {
    if (document.selection) {
        document.selection.empty();
    } else if (window.getSelection) {
        window.getSelection().removeAllRanges();
    }
}
function selectText(containerid) {
    deselectText()
    if (document.selection) {
        var range = document.body.createTextRange();
        range.moveToElementText(document.getElementById(containerid));
        range.select();
    } else if (window.getSelection) {
        var range = document.createRange();
        range.selectNode(document.getElementById(containerid));
        window.getSelection().addRange(range);
    }
}

jQuery(function(){
	var script_source = jQuery('script[src*="share.js"]').attr('src');
        var params = function(name,default_value) {
            var match = RegExp('[?&]' + name + '=([^&]*)').exec(script_source);
            return match && decodeURIComponent(match[1].replace(/\+/g, ' '))||default_value;
        }
	var path = params('static','social');
	var url = encodeURIComponent(window.location.href);
	var host =  window.location.hostname;
	var title = escape(jQuery('title').text());
    var qmsg = {
        good: 'The results of this query have been obtained after the query body has been last modified',
        warning: 'This query has never been executed in SHEBANQ',
        error: 'The body of this query has been changed after its current results have been obtained.',
    }

	var tbar = '\
<div id="socialdrawer">\
    <p id="citeh">Cite</p>\
    <table align="center">\
        <tr>\
            <td class="clip_qx clr">\
                <a lnk="" href="#" id="clip_qx_md" title="markdown link" class="ctrl fa fa-level-down fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_qx_ht" title="html link" class="ctrl fa fa-link fa-lg fa-fw"></a>\
            </td>\
            <td class="clip_q clr">\
                <a lnk="" href="#" id="clip_q_md" title="markdown link" class="ctrl fa fa-level-down fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_q_ht" title="html link" class="ctrl fa fa-link fa-lg fa-fw"></a>\
            </td>\
            <td class="clip_w clr">\
                <a lnk="" href="#" id="clip_w_md" title="markdown link" class="ctrl fa fa-level-down fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_w_ht" title="html link" class="ctrl fa fa-link fa-lg fa-fw"></a>\
            </td>\
            <td class="clip_n clr">\
                <a lnk="" href="#" id="clip_n_md" title="markdown link" class="ctrl fa fa-level-down fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_n_ht" title="html link" class="ctrl fa fa-link fa-lg fa-fw"></a>\
            </td>\
            <td class="clip_pv clr">\
                <a lnk="" href="#" id="clip_pv_md" title="markdown link" class="ctrl fa fa-level-down fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_pv_ht" title="html link" class="ctrl fa fa-link fa-lg fa-fw"></a>\
                <a lnk="" href="#" id="clip_pv_cn" title="page content" class="ctrl fa fa-file-text-o fa-lg fa-fw"></a>\
            </td>\
        </tr>\
        <tr>\
            <th class="clip_qx" width="120px">query v</th>\
            <th class="clip_q" width="120px">query</th>\
            <th class="clip_w" width="120px">word</th>\
            <th class="clip_n" width="120px">note</th>\
            <th class="clip_pv" width="120px">page view</th>\
        </tr>\
        <tr class="citexpl">\
            <td class="clip_qx"><span id="xc_qx" class="ctrl fa fa-chevron-right fa-fw"></span><span id="x_qx" class="detail">cite query with its results on <i>this</i> data version</span></td>\
            <td class="clip_q"><span id="xc_q" class="ctrl fa fa-chevron-right fa-fw"></span><span id="x_q" class="detail">share link to query page</span></td>\
            <td class="clip_w"><span id="xc_w" class="ctrl fa fa-chevron-right fa-fw"></span><span id="x_w" class="detail">cite word with its occs on <i>this</i> data version</span></td>\
            <td class="clip_n"><span id="xc_n" class="ctrl fa fa-chevron-right fa-fw"></span><span id="x_n" class="detail">cite note set with its members</span></td>\
            <td class="clip_pv"><span id="xc_pv" class="ctrl fa fa-chevron-right fa-fw"></span><span id="x_pv" class="detail">share link to this page with view settings, or copy page contents to paste in mail, Evernote, etc.</span></td>\
        </tr>\
    </table>\
    <p id="cdiagpub"></p>\
    <p id="cdiagsts"></p>\
</div>\
';	
	// Add the share tool bar.
	jQuery('body').append(tbar); 
	var st = jQuery('#socialdrawer');
	st.css({'opacity':'.7','z-index':'3000','background':'#FFF','border':'solid 1px #666','border-width':' 1px 0 0 1px','height':'20px','width':'40px','position':'fixed','bottom':'0','right':'0','padding':'2px 5px','overflow':'hidden','-webkit-border-top-left-radius':' 12px','-moz-border-radius-topleft':' 12px','border-top-left-radius':' 12px','-moz-box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)','-webkit-box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)','box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)'});
	jQuery('#citeh').css({'margin':'2px 3px','text-shadow':' 1px 1px 1px #FFF','color':'#444','font-size':'12px','line-height':'1em'});
    jQuery('#socialdrawer td,#socialdrawer th').css({'width': '120px', 'text-align': 'center', 'border-left': '2px solid #888888', 'border-right': '2px solid #888888'});
    jQuery('#socialdrawer .detail').hide()
	// hover
    $('#clip_qx_md,#clip_qx_ht,#clip_q_md,#clip_q_ht,#clip_w_md,#clip_w_ht,#clip_n_md,#clip_n_ht,#clip_pv_md,#clip_pv_ht').click(function(e) {e.preventDefault();
        window.prompt('Press <Cmd-C> and then <Enter> to copy link on clipboard', $(this).attr('lnk'))
    })
    $('#clip_pv_cn').click(function(e) {e.preventDefault();
        var shebanq_url_raw = page_view_url+wb.vs.getvars()+'&pref=alt'
        var slink = $('#self_link')
        slink.show()
        slink.attr('href', shebanq_url_raw)
        selectText('material')
    })
    $('#xc_qx').click(function(e){e.preventDefault(); toggle_detail($(this), $('#x_qx')) })
    $('#xc_q').click(function(e){e.preventDefault(); toggle_detail($(this), $('#x_q')) })
    $('#xc_w').click(function(e){e.preventDefault(); toggle_detail($(this), $('#x_w')) })
    $('#xc_n').click(function(e){e.preventDefault(); toggle_detail($(this), $('#x_n')) })
    $('#xc_pv').click(function(e){e.preventDefault(); toggle_detail($(this), $('#x_pv')) })
	st.click(function(e){e.preventDefault();
        var shebanq_url_raw = page_view_url+wb.vs.getvars()+'&pref=alt'
        var shebanq_url = encodeURIComponent(shebanq_url_raw)
        var pvtitle
        $('#citeh').hide()
        $('#cdiagpub').html('')
        $('#cdiagsts').html('')
        $('.clip_qx.clr,.clip_q.clr,.clip_w.clr,.clip_n.clr,.clip_pv.clr,#cdiagpub,#cdiagsts').removeClass('error warning good special')
        if (wb.mr == 'm') {
            pvtitle = title
            $('.clip_qx').hide()
            $('.clip_q').hide()
            $('.clip_w').hide()
            $('.clip_n').hide()
        }
        else if (wb.mr == 'r') {
            var vr = wb.version
            var iinfo = wb.sidebars.sidebar['r'+wb.qw].content.info
            if (wb.qw == 'q') {
                pvtitle = iinfo.ufname+' '+iinfo.ulname+': '+iinfo.name
                var is_shared = iinfo.is_shared
                var is_pub = iinfo.versions[vr].is_published
                var qstatus = iinfo.versions[vr].status
                if (is_shared) {
                    if (!is_pub) {
                        $('.clip_qx.clr').addClass('warning')
                        $('#cdiagpub').addClass('warning')
                        $('#cdiagpub').html('Beware of citing this query. It has not been published. It may be changed later.')
                    }
                    else {
                        $('.clip_qx.clr').addClass('special')
                        $('#cdiagpub').addClass('special')
                        $('#cdiagpub').html('This query has been published. If that happened more than a week ago, it can be safely cited. It will not be changed anymore.')
                    }
                    $('.clip_q.clr').addClass(qstatus)
                    $('#cdiagsts').addClass(qstatus)
                    $('#cdiagsts').html(qmsg[qstatus])
                }
                else {
                    $('.clip_qx.clr').addClass('error')
                    $('.clip_q.clr').addClass('error')
                    $('.clip_pv.clr').addClass('error')
                    $('#cdiagpub').addClass('error')
                    $('#cdiagpub').html('This query is not accessible to others because it is not shared.')
                }
                var quote_url = query_url+'?id='+wb.iid
                var quotev_url = query_url+'?version='+vr+'&id='+wb.iid
                $('#clip_qx_md').attr('lnk', '['+pvtitle+']('+quotev_url+')')
                $('#clip_qx_ht').attr('lnk', quotev_url)
                $('#clip_q_md').attr('lnk', '['+pvtitle+']('+quote_url+')')
                $('#clip_q_ht').attr('lnk', quote_url)
                $('.clip_qx').show()
                $('.clip_q').show()
                $('.clip_w').hide()
                $('.clip_n').hide()
            }
            else if (wb.qw == 'w') {
                var vinfo = iinfo.versions[vr]
                pvtitle = vinfo.entryid_heb+' ('+vinfo.entryid+')'
                var quotev_url = word_url+'?version='+vr+'&id='+wb.iid
                $('#clip_w_md').attr('lnk', '['+pvtitle+']('+quotev_url+')')
                $('#clip_w_ht').attr('lnk', quotev_url)
                $('.clip_w.clr').addClass('special')
                $('.clip_qx').hide()
                $('.clip_q').hide()
                $('.clip_w').show()
                $('.clip_n').hide()
            }
            else if (wb.qw == 'n') {
                var ufname = escapeHTML(iinfo.ufname)
                var ulname = escapeHTML(iinfo.ulname)
                var kw = escapeHTML(iinfo.kw)
                pvtitle = ufname+' '+ulname+' - '+kw
                var quotev_url = note_url+'?version='+vr+'&id='+wb.iid+'&tp=txt_tb1'
                $('#clip_n_md').attr('lnk', '['+pvtitle+']('+quotev_url+')')
                $('#clip_n_ht').attr('lnk', quotev_url)
                $('.clip_n.clr').addClass('special')
                $('.clip_qx').hide()
                $('.clip_q').hide()
                $('.clip_w').hide()
                $('.clip_n').show()
            }
        }
        $('#clip_pv_md').attr('lnk', '['+pvtitle+']('+shebanq_url_raw+')')
        $('#clip_pv_ht').attr('lnk', shebanq_url_raw)
        $('#clip_pv_cn').attr('lnk', shebanq_url_raw)
        $('#clip_pv_cn').attr('tit', pvtitle)
        jQuery(this).animate({height:'260px', width:'570px', opacity: 0.95}, 300);
    });
	//leave
	st.mouseleave(function(){ 
        $('#self_link').hide()
        deselectText()
        $('#citeh').show()
	    st.animate({height:'20px', width: '40px', opacity: .7}, 300); 
	    return false;
    });
});
