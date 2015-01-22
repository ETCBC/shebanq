"""Original code source:
`Web2Py Slices - Widget Select or Add Option <http://www.web2pyslices.com/slice/show/1616/widget-select-or-add-option-ng>`_.
"""
from gluon.sqlhtml import OptionsWidget
from gluon.html import DIV, SPAN, A, SCRIPT
from gluon.compileapp import LOAD
from gluon import current


class SELECT_OR_ADD_OPTION(object):  # and even EDIT

    def __init__(self, referenced_table, controller="default", function="referenced_data", dialog_width=450):
        self.referenced_table = referenced_table
        self.controller = controller
        self.function = function
        self.dialog_width = dialog_width

    def widget(self, field, value):
        T = current.T
        # generate the standard widget for this field
        select_widget = OptionsWidget.widget(field, value)

        # get the widget's id (need to know later on so can tell receiving controller what to update)
        my_select_id = select_widget.attributes.get('_id', None)
        wrapper = DIV(_id=my_select_id + "__reference-actions__wrapper")
        wrapper.components.extend([select_widget, ])
        style_icons = {'new': "icon plus icon-plus", 'edit': "icon pen icon-pencil"}
        actions = ['new']
        if value:
            actions.append('edit')  # if we already have selected value
        for action in actions:
            extra_args = [my_select_id, action, self.referenced_table]
            if action == 'edit':
                extra_args.append(value)
            # create a div that will load the specified controller via ajax
            form_loader_div = DIV(LOAD(c=self.controller, f=self.function, args=extra_args, ajax=False, ajax_trap=False), _id=my_select_id + "_" + action + "_dialog-form", _title=action + ": " + self.referenced_table)
            # generate the "add/edit" button that will appear next the options widget and open our dialog
            action_button = A([SPAN(_class=style_icons[action]), SPAN(_class="buttontext button")], _title=T(action), _id=my_select_id + "_option_%s_trigger" % action, _class="button btn", _style="vertical-align:top")
            # create javascript for creating and opening the dialog
            js = '$( "#%s_%s_dialog-form" ).dialog({autoOpen: false, not__modal:true, show: "blind", hide: "explode", width: %s});' % (my_select_id, action, self.dialog_width)
            js += '$( "#%s_option_%s_trigger" ).click(function() { $( "#%s_%s_dialog-form" ).dialog( "open" );return false;}); ' % (my_select_id, action, my_select_id, action, )
            js += '$(function() { $( "#%s_option_%s_trigger" ).button({text: true, icons: { primary: "ui-icon-circle-plus"} }); });' % (my_select_id, action, )
            if action == 'edit':
                # hide if reference changed - as load is constructed for initial value only (or would need some lazy loading mechanizm)
                js += '$(function() {$("#%s").change(function() { $( "#%s_option_%s_trigger" ).hide(); } ) });' % (my_select_id, my_select_id, 'edit',)
            jq_script = SCRIPT(js, _type="text/javascript")
            wrapper.components.extend([form_loader_div, action_button, jq_script])
        return wrapper
