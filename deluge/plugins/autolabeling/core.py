#
# core.py
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

import logging
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
import re
from deluge.plugins.label import core as labcore
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "label_regex_list":[] #list of dict label_id,regex,enabled
}

log = logging.getLogger(__name__)

class Core(CorePluginBase):

    label_regex_list = []
    label_plugin_enabled = False
    label_plugin = None

    def handleTorrentAdded(self, torrent_id, from_state):
	print "From_state : "+str(from_state)
	print "label_plugin_enabled : "+str(self.label_plugin_enabled)
	if(not from_state and self.label_plugin_enabled):
		print "Torrent added : "+torrent_id
		torrent = component.get("TorrentManager")[torrent_id]
		files = torrent.get_files()
		for file in files:
			for rule_dict in self.label_regex_list: 
				if(rule_dict["enabled"]):
					c = re.compile(rule_dict["regex"])
					m = c.search(file['path'])
					if(m != None):
						print "Found!"
						self.label_plugin.plugin.set_torrent(torrent_id,rule_dict["label_id"])

    def handlePluginEnabled(self, plugin):
	print "Plugin enabled: "+plugin
	if(plugin == "Label"):
		self.label_plugin_enabled = True
		self.label_plugin = component.get("CorePluginManager")[plugin]		
		#print self.label_plugin.plugin.labels
		#print self.label_plugin.plugin.labels['filmek']

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("autolabeling.conf", DEFAULT_PREFS)
        component.get("EventManager").register_event_handler("TorrentAddedEvent", self.handleTorrentAdded)
	component.get("EventManager").register_event_handler("PluginEnabledEvent", self.handlePluginEnabled)
	self.label_plugin_enabled = "Label" in component.get("CorePluginManager").get_enabled_plugins()
	if(self.label_plugin_enabled):
		self.label_plugin = component.get("CorePluginManager")["Label"]		
	
	self.label_regex_list = self.config["label_regex_list"]
	print "enable: "+str(self.config["label_regex_list"])
	
    def disable(self):
	component.get("EventManager").deregister_event_handler("TorrentAddedEvent", self.handleTorrentAdded)
        pass

    def update(self):
        pass	

    @export
    def get_rules(self):
	return self.config["label_regex_list"]

    @export
    def add(self, rule={}):
	self.label_regex_list.append(dict(rule))

    @export
    def remove(self, rule={}):
	for rule_dict in self.label_regex_list:
		if(rule_dict["regex"] == rule["regex"] and rule_dict["label_id"] == rule["label_id"] and rule_dict["enabled"] == rule["enabled"]):
			 self.label_regex_list.remove(rule_dict)

    @export
    def enabledisable(self, rule={}):
	for rule_dict in self.label_regex_list:
		if(rule_dict["regex"] == rule["regex"] and rule_dict["label_id"] == rule["label_id"] and rule_dict["enabled"] == rule["enabled"]):
			 rule_dict["enabled"] = not rule_dict["enabled"]

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config
