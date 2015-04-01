var versions, version, lan, letter

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

function set_vselect(v) {
    if (versions[v]) {
        $('#version_'+v).click(function(e) {e.preventDefault();
            version = v
            window.location.href = words_url+'?version='+v+'&lan='+lan+'&letter='+letter
        })
    }
}
function words_init() {
    $('.mvradio').removeClass('ison')
    for (var v in versions) {
        this.set_vselect(v)
    }
    $('#version_'+version).addClass('ison')
    var gotoword = Request.parameter('goto');
    set_heightw()
    $('[wii]').hide()
    $('[gi]').click(function(e) {e.preventDefault();
        var i = $(this).attr('gi')
        $('[wi="'+i+'"]').toggle()
        $('[wii="'+i+'"]').toggle()
    })
    $('[gi]').closest('td').removeClass('selecthlw')
    var wtarget = $('[gi='+gotoword+']').closest('td')
    if (wtarget != undefined) {
        wtarget.addClass('selecthlw')
        if (wtarget[0] != undefined) {
            wtarget[0].scrollIntoView()
        }
    }
}

