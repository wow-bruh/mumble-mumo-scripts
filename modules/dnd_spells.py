#!/usr/bin/env python
# -*- coding: utf-8

# Copyright (C) 2011 Stefan Hacker <dd0t@users.sourceforge.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the Mumble Developers nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# `AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# seen.py
# This module allows asking the server for the last time it saw a specific player
#

from mumo_module import (commaSeperatedIntegers,
                         MumoModule)
from datetime import timedelta
import json
import operator
from fuzzywuzzy import process

class dnd_spells(MumoModule):
    
    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        with open("spells.json") as spells_file:
            self.spells = json.loads(spells_file.read())
        self.spells_names = [item["name"].lower() for item in self.spells]
        

    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Register for Server callbacks")
        servers = manager.SERVERS_ALL
            
        manager.subscribeServerCallbacks(self, servers)
    
    def disconnected(self): pass
    
    def sendMessage(self, server, user, message, msg):
        if message.channels:
            server.sendMessageChannel(user.channel, False, msg)
        else:
            server.sendMessage(user.session, msg)
            server.sendMessage(message.sessions[0], msg)
    #
    #--- Server callback functions
    #
    
    def userTextMessage(self, server, user, message, current=None):
        # Ensure we're using the keyword
        if not message.text.startswith("!spell"):
            return

        # Get the searched spell name
        split = message.text.split(" ", 1)
        if len(split) != 2:
            return

        # Attempt to find matching spells in there
        matching = process.extractOne(split[1].lower(), self.spells_names)
	#self.log().debug("Comparing against: " + str(self.spells_names))

        # Find a matching spell in the data
        matching_spell = None
	#self.log().debug("Found by fuzzy search: " + matching[0])
        for item in self.spells:
	    #self.log().debug("Comparing against: " + item["name"])
            if item["name"].lower() == matching[0]:
                matching_spell = item
        if matching_spell is None:		
	    #self.log().debug("Didn't find any fuck")
            return
        
        msg = """
Here's what I found that's my closest match for {looking_for}:<br><b>
{spell_name}</b><br>
{spell_desc}<br>
Higher Level: {spell_higher_level}<br>
Range: {spell_range}
<br>
<b>FLO YOU GODDAMN PRICK LIMIT THAT TO DND CHANNEL</b>
""".format(
	looking_for = split[1].encode("utf-8"),
	spell_name = matching_spell["name"].encode("utf-8"),
	spell_desc = matching_spell["desc"].encode("utf-8"),
	spell_higher_level = matching_spell["higher_level"].encode("utf-8") if "higher_level" in matching_spell.keys() else "",
	spell_range = matching_spell["range"].encode("utf-8") if "range" in matching_spell.keys() else "")
	#self.log().debug(msg)        
        server.sendMessageChannel(user.channel, False, msg)

    
    def userConnected(self, server, state, context = None): pass
    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass
    
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass

