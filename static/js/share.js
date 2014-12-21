/**

   Created and copyrighted by Massimo Di Pierro <massimo.dipierro@gmail.com>
   (MIT license)  

   Example:

   <script src="share.js"></script>

**/

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
	var twit = 'http://twitter.com/home?status='+title+'%20'+url;
	var facebook = 'http://www.facebook.com/sharer.php?u='+url;
	var gplus = 'https://plus.google.com/share?url='+url;
	var tbar = '<div id="socialdrawer"><span>Cite<br/>&nbsp;&nbsp;</span><div id="sicons"><a lnk="" href="#" id="clipquery" title="citation link for this query">query</a><a lnk="" href="#" id="clipword" title="citation link for this word">word</a>&nbsp;&nbsp;<a lnk="" href="#" id="clipview" title="link to this view">page view</a>&nbsp;<a class="sicon" target="_blank" href="'+twit+'" id="twit" title="Share on twitter"><img src="'+path+'/twitter.png"  alt="Share view on Twitter" width="32" height="32" /></a></div></div>';	
	// Add the share tool bar.
	jQuery('body').append(tbar); 
	var st = jQuery('#socialdrawer');
	st.css({'opacity':'.7','z-index':'3000','background':'#FFF','border':'solid 1px #666','border-width':' 1px 0 0 1px','height':'20px','width':'40px','position':'fixed','bottom':'0','right':'0','padding':'2px 5px','overflow':'hidden','-webkit-border-top-left-radius':' 12px','-moz-border-radius-topleft':' 12px','border-top-left-radius':' 12px','-moz-box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)','-webkit-box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)','box-shadow':' -3px -3px 3px rgba(0,0,0,0.5)'});
	jQuery('#socialdrawer .sicon').css({'float':'right','width':'32px','margin':'3px 2px 2px 2px','padding':'0','cursor':'pointer'});
	jQuery('#socialdrawer span').css({'float':'left','margin':'2px 3px','text-shadow':' 1px 1px 1px #FFF','color':'#444','font-size':'12px','line-height':'1em'});
        jQuery('#socialdrawer img').hide();
	// hover
    $('#clipview,#clipquery,#clipword').click(function() {
        window.prompt('Press <Cmd-C> and then <Enter> to copy link on clipboard', $(this).attr('lnk'))
    })
	st.click(function(){
        var shebanq_url_raw = view_url+wb.vs.getvars()+'&pref=alt'
        var shebanq_url = encodeURIComponent(shebanq_url_raw)
	    var twit = 'http://twitter.com/home?status='+title+'%20';
        if (wb.mr == 'm') {
            $('#clipquery').hide()
            $('#clipword').hide()
        }
        else {
            if (wb.qw == 'q') {
                var quote_url = view_url+'?mr=r&qw=q&iid='+wb.iid
                $('#clipquery').attr('lnk', quote_url)
                $('#clipquery').show()
                $('#clipword').hide()
            }
            else {
                var quote_url = view_url+'?mr=r&qw=w&iid='+wb.iid
                $('#clipword').attr('lnk', quote_url)
                $('#clipquery').hide()
                $('#clipword').show()
            }
        }
        $('#clipview').attr('lnk', shebanq_url_raw)
        $('#twit').attr('href', twit+shebanq_url)
		jQuery(this).animate({height:'40px', width:'200px', opacity: 0.95}, 300);
		jQuery('#socialdrawer img').show();
    });
	//leave
	st.mouseleave(function(){ 
	    st.animate({height:'20px', width: '40px', opacity: .7}, 300); 
	    jQuery('#socialdrawer img').hide();
	    return false;
	    }  );
    });
