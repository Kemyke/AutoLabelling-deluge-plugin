#
# gtkui.py
#
# Copyright (C) 2014 Kemy <kemyyy@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk
import gtk.glade
import logging

from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

log = logging.getLogger(__name__)

class AddRuleDialog:

    def __init__(self):
	pass

    def show(self, parent):	
        self.glade = gtk.glade.XML(get_resource("config_addrule.glade"))
	self.glade.signal_autoconnect({
            "on_rule_add":self.on_add,
            "on_rule_cancel":self.on_cancel})
	self.parent = parent
	
	liststore = gtk.ListStore(str)	

        def on_labels(labels):
            log.debug("Got Labels: %s", labels)
            for label in labels:
                liststore.append([label])

        def on_failure(failure):
            log.exception(failure)

	def on_get_enabled_plugins(result):
            if 'Label' in result:
                client.label.get_labels().addCallback(on_labels).addErrback(on_failure)

	client.core.get_enabled_plugins().addCallback(on_get_enabled_plugins)

	self.tbRule = self.glade.get_widget("tbRule")
	self.cbLabels = self.glade.get_widget("cbLabels")
	self.cbLabels.set_model(liststore)
	renderer_text = gtk.CellRendererText()
        self.cbLabels.pack_start(renderer_text, True)
        self.cbLabels.add_attribute(renderer_text, "text", 0)

        self.dialog = self.glade.get_widget("new_rule_dialog")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)
	self.dialog.run()

    def on_error_show(self, result):
	print "Error: "+str(result.value)

    def on_added(self, result):
	self.parent.handle_on_add()
        self.dialog.destroy()
    
    def on_add(self, Event=None):
	rule = {'enabled':True, 'label_id':self.cbLabels.get_active_text(), 'regex':self.tbRule.get_text()}
	client.autolabeling.add(rule).addCallbacks(self.on_added, self.on_error_show)

    def on_cancel(self, Event=None):
        self.dialog.destroy()

class GtkUI(GtkPluginBase):

    def _on_file_toggled(self, render, path):
	pass

    tvRules = None
    tsRules = None

    def on_new_rule(self, Event=None):
	self.add_new_rule_dialog.show(self)	

    def on_error_show(self, result):
	print "Error: "+str(result.value)

    def on_removed(self, result):
	print "Removed!"

    def on_enableddisabled(self, result):
	print "State changed!"

    def on_remove_rule(self, Event=None):
	current_selection = self.tvRules.get_selection().get_selected()
	row_data = current_selection[0].get(current_selection[1],0,1,2)
	rule = {'enabled':row_data[0], 'label_id':row_data[2], 'regex':row_data[1]}
	client.autolabeling.remove(rule).addCallbacks(self.on_removed, self.on_error_show)
        client.autolabeling.get_config().addCallback(self.cb_get_config)

    def on_enabledisable_rule(self, Event=None):
	current_selection = self.tvRules.get_selection().get_selected()
	row_data = current_selection[0].get(current_selection[1],0,1,2)
	rule = {'enabled':row_data[0], 'label_id':row_data[2], 'regex':row_data[1]}
	client.autolabeling.enabledisable(rule).addCallbacks(self.on_enableddisabled, self.on_error_show)
        client.autolabeling.get_config().addCallback(self.cb_get_config)

    def handle_on_add(self):
        client.autolabeling.get_config().addCallback(self.cb_get_config)

    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))
	self.glade.signal_autoconnect({
            "on_new_rule":self.on_new_rule})
	self.glade.signal_autoconnect({
            "on_remove_rule":self.on_remove_rule})
	self.glade.signal_autoconnect({
            "on_enabledisable_rule":self.on_enabledisable_rule})

	self.add_new_rule_dialog = AddRuleDialog()

        component.get("Preferences").add_page("AutoLabeling", self.glade.get_widget("autoLabelingConfigContainer"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
	
	#enabled?, regex, label
	self.tsRules = gtk.TreeStore(bool, str, str)

	self.tvRules = self.glade.get_widget("tvRules")

	render = gtk.CellRendererToggle()
        render.connect("toggled", self._on_file_toggled)
        column = gtk.TreeViewColumn(None, render, active=0, inconsistent=4)
	self.tvRules.append_column(column)

	render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Pattern"), render, text=1)
        self.tvRules.append_column(column)

	render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Label"), render, text=2)
        self.tvRules.append_column(column)

	self.tvRules.set_model(self.tsRules)

    def disable(self):
        component.get("Preferences").remove_page("AutoLabeling")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for AutoLabeling")
        config = {
            "label_regex_list":self.label_regex_list
        }
        client.autolabeling.set_config(config)

    def on_show_prefs(self):
        client.autolabeling.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        #"callback for on show_prefs"
	self.tsRules.clear()
	ite = self.tsRules.get_iter_first()
	self.label_regex_list = config["label_regex_list"]

	for rule_dict in self.label_regex_list:
		self.tsRules.append(ite, [rule_dict["enabled"], rule_dict["regex"], rule_dict["label_id"]])
