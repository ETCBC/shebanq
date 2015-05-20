var pn_url, n_url, record_url
var ns = $.initNamespaceStorage('muting')
var vs = $.initNamespaceStorage('nsview')
var muting = ns.localStorage
var nsview = vs.localStorage
var ftree, msgflt, msgopn, rdata
var subtract = 80 // the canvas holding the material gets a height equal to the window height minus this amount
var control_height = 100 // height for messages and controls

var escapeHTML = (function () {
    'use strict';
    var chr = {
        '&': '&amp;', '<': '&lt;',  '>': '&gt;'
    };
    return function (text) {
        return text.replace(/[&<>]/g, function (a) { return chr[a]; });
    };
}());

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

function View() {
    var that = this
    this.prevstate = false
    if (!nsview.isSet('simple')) {
        nsview.set('simple', true)
    }
    this.nvradio = $('.nvradio')
    this.csimple = $('#c_view_simple')
    this.cadvanced = $('#c_view_advanced')

    this.adjust_view = function() {
        var simple = nsview.get('simple');
        this.nvradio.removeClass('ison');
        (simple?this.csimple:this.cadvanced).addClass('ison')
        if (this.prevstate != simple) {
            if (simple) {
                $('.brn').hide()
            }
            else {
                $('.brn').show()
            }
            this.prevstate = simple
        }
    }

    this.csimple.click(function(e) {e.preventDefault();
        nsview.set('simple', true)
        that.adjust_view()
    })
    this.cadvanced.click(function(e) {e.preventDefault();
        nsview.set('simple', false)
        that.adjust_view()
    })
    this.adjust_view()
}

function Level() {
    var that = this
    var levels = {u: 1, n: 2}
    this.expand_all = function() {
        ftree.ftw.visit(function(n) {
            n.setExpanded(true, {noAnimation: true, noEvents: true})
        }, true)
    }

    this.expand_level = function(level) {
        $('.nlradio').removeClass('ison')
        $('#level_'+level).addClass('ison')
        nsview.set('level', level)
        if (level in levels) {
            var numlevel = levels[level]
            ftree.ftw.visit(function(n) {
                var nlevel = n.getLevel()
                n.setExpanded(nlevel <= numlevel , {noAnimation: true, noEvents: true})
            }, true)
        }
    }

    this.initlevel = function() {
        this.expand_level(nsview.get('level'))
    }
    $('.nlradio').removeClass('ison')
    if (!nsview.isSet('level')) {nsview.set('level', 'u')}
    $('#level_u').click(function(e) {e.preventDefault();that.expand_level('u')})
    $('#level_n').click(function(e) {e.preventDefault();that.expand_level('n')})
    $('#level_').click(function(e) {e.preventDefault();that.expand_level('')})
}

function Filter() {
    var that = this
    this.patc = $('#filter_contents')

    this.clear = function() {
        ftree.ftw.clearFilter()
        msgflt.clear()
        msgflt.msg(['good', 'no filter applied'])
        $('.nfradio').removeClass('ison')
        nsview.remove('filter_mode')
        $('#filter_clear').hide()
        $('#amatches').html('')
        $('#cmatches').html('')
        $('#nmatches').html('')
        $('#count_u').html(rdata.u)
        $('#count_n').html(rdata.n)
    }
    this.pnsearch = function(kind) {
        var pat = this.patc.val()
        nsview.set('filter_pat', pat);
        var amatches = 0
        var cmatches = 0
        var nmatches = 0
        if (pat == '') {
            amatches = -1
            cmatches = -1
            nmatches = -1
        }
        $('.nfradio').removeClass('ison')
        if (pat == '') {
            this.clear()
            return
        }
        else {
            msgflt.clear()
            msgflt.msg(['special', 'filter applied'])
        }
        $('#filter_control_'+kind).addClass('ison')
        nsview.set('filter_mode', kind)

        ftree.level.expand_all()
        if (kind == 'a') {
            amatches = ftree.ftw.filterNodes(pat, false)
            $('#amatches').html(amatches>=0?('('+amatches+')'):'')
        }
        else if (kind == 'c') {
            cmatches = ftree.ftw.filterBranches(pat)
            $('#cmatches').html(cmatches>=0?('('+cmatches+')'):'')
        }
        else if (kind == 'n') {
            nmatches = ftree.ftw.filterNodes(pat, true)
            $('#nmatches').html(nmatches>=0?('('+nmatches+')'):'')
        }
        $('#filter_clear').show()
        var submatch = 'span.fancytree-submatch'
        var match = 'span.fancytree-match'
        var base_u = base_p+'ul>li>'
        var match_u = $(base_u+match).length
        var submatch_u = $(base_u+submatch).length
        var base_n = base_n+'ul>li>'
        var match_n = $(base_n+match).length
        $('#count_u').html('<span class="match">'+match_u+'</span> <span class="brn submatch">'+submatch_u+'</span>')
        $('#count_n').html('<span class="match">'+match_n+'</span>')
        if (ftree.view.simple) {
            $('.brn').hide()
        }
    }

    $('#filter_clear').hide()
    $('#filter_contents').val(nsview.isSet('filter_pat')?nsview.get('filter_pat'):'')
    if (nsview.isSet('filter_mode')) {
        this.pnsearch(nsview.get('filter_mode'))
        $('#filter_clear').show()
    }


    $('#filter_control_a').click(function(e) {e.preventDefault();that.pnsearch('a')})
    $('#filter_control_c').click(function(e) {e.preventDefault();that.pnsearch('c')})
    $('#filter_control_n').click(function(e) {e.preventDefault();that.pnsearch('q')})

    $('#filter_clear').click(function(e) {e.preventDefault();that.clear()})
}

function Msg(destination) {
    var that = this
    this.destination = $('#'+destination)
    this.trashc = $('#trash_'+destination)
    this.clear = function() {
        this.destination.html('')
        this.trashc.hide()
    }
    this.trashc.click(function(e) {e.preventDefault();
        that.clear()
    })
    this.msg = function(msgobj) {
        var mtext = this.destination.html()
        this.destination.html(mtext+'<p class="'+msgobj[0]+'">'+msgobj[1]+'</p>')
        this.trashc.show()
    }
    this.trashc.hide()
}
function Tree() {
    var that = this
    this.tps = {u: 'user', n:'note'}

    this.store_select = function(node) {
        if (!node.folder) {
            var iid = node.key
            if (node.selected) {
                muting.set(iid, 1)
            }
            else {
                if (muting.isSet(iid)) {
                    muting.remove(iid)
                }
            }
        }
    }
    this.store_select_deep = function(node) {
        this.store_select(node)
        var children = node.children
        if (children != null) {
            for (n in children) {
                this.store_select_deep(children[n])
            }
        }
    }
    this.dress_notes = function() {
        $('#notes a.md').addClass('fa fa-level-down')
        $('#notes a[nid]').each(function() {
            var vr = $(this).attr('v')
            var extra = (vr == undefined)?'':'&version='+vr;
            $(this).attr('href', n_url+'?iid='+$(this).attr('nid')+extra+'&page=1&mr=r&qw=n')
        })
        $('#notes a.md').click(function(e) {e.preventDefault();
            var uname = $(this).closest('ul').closest('li').find('span[n]').html()
            var tit = $(this).prev()
            var lnk = tit.attr('href')
            var nname = tit.html()
            window.prompt('Press <Cmd-C> and then <Enter> to copy link on clipboard', '['+uname+': '+nname+']('+lnk+')')
        })
    }
    this.gotonote = function(nid) {
        if (nid != undefined && nid != '0') {
            var nnode = this.ftw.getNodeByKey('q'+nid)
            nnode.makeVisible({noAnimation: true})
            $('.treehl').removeClass('treehl')
            $('a[nid='+nid+']').closest('span').addClass('treehl')
            $(nnode.li)[0].scrollIntoView()
        }
    }

    $("#notes").fancytree({
        extensions: ["persist", "filter"],
        checkbox: true,
        selectMode: 3,
        activeVisible: true,
        toggleEffect: false,
        clickFolderMode: 2,
        focusOnSelect: false,
        quicksearch: true,
        icons: false,
        persist: {
            store: 'local',
            types: 'expanded selected',
        },
        source: {
            url: pn_url,
            dataType: "json",
        },
        filter: {
            mode: 'hide',
        },
        init: function(e, data) {
            muting.removeAll()
            that.ftw =  $("#notes").fancytree('getTree')
            var s = that.ftw.getSelectedNodes(true)
            for (i in s) {
                that.store_select_deep(s[i])
            }
            that.ftw.render(true, true)
            that.dress_notes()
            rdata = that.ftw.rootNode.children[0].data
            $('#count_u').html(rdata.u)
            $('#count_n').html(rdata.n)
            msgopn = new Msg('opqmsgs')
            msgflt = new Msg('filter_msg')
            that.view = new View()
            that.level = new Level()
            that.filter = new Filter()
            that.level.initlevel()
            that.gotonote($('#nid').val()) 
        },
        expand: function(e, data) {
            if (that.level != undefined) {
                that.level.expand_level('')
            }
        },
        collapse: function(e, data) {
            if (that.level != undefined) {
                that.level.expand_level('')
            }
        },
        select: function(e, data) {
            that.store_select_deep(data.node)
        },
    })
    var standard_height = window.innerHeight - subtract
    var form_height = standard_height - control_height
    var standard_width = window.innerWidth
    var canvas_left = $('.left-sidebar')
    var canvas_middle = $('.span6')
    var canvas_right = $('.right-sidebar')
    canvas_left.css('height', standard_height+'px')
    $('#notes').css('height', standard_height+'px')
    $('#opqforms').css('height', form_height+'px')
    $('#opqctrl').css('height', control_height+'px')
    canvas_right.css('height', standard_height+'px')
}

$(function(){
    ftree = new Tree()
})
