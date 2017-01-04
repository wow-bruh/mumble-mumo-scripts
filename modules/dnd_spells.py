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

    def get_spell_info(self, search, spell):
        msg = """
Here's what I found that's my closest match for {looking_for}:<br><b>
{spell_name}</b>
{spell_desc}
Higher Level: {spell_higher_level}<br>
Range: {spell_range}
<br>
<b>FLO YOU GODDAMN PRICK LIMIT THAT TO DND CHANNEL</b>
""".format(looking_for = search.encode("utf-8"),
            spell_name = spell["name"].encode("utf-8"),
            spell_desc = spell["desc"].encode("utf-8"),
            spell_higher_level = spell["higher_level"].encode("utf-8") if "higher_level" in spell.keys() else "",
            spell_range = spell["range"].encode("utf-8") if "range" in spell.keys() else "")

        return msg
    
    def fuzzy_match(self, name):
        matching_spell = None
        # Check for an exact match first
        if name in self.spells_names:
            matching_spell = next(spell for spell in self.spells if spell["name"] == name, None)
        if matching_spell is not None:
            return self.get_spell_info(name, matching_spell);
        
        # No direct match, let's attempt a fuzzy match
        matches = process.extract(name, self.spells_names, limit=3)
        if matches is None or len(matches) == 0:
            return "Well I couldn't even find a single spell in my database. That's bad."

        # Unsure matches go here
        if matches[0][1] < 50:
            msg = "I've found some stuff, but I'm not entirely sure that's what you mean. Mind giving me a bit more info? Those are the spells I found that might match:<br>"
            for item in matches:
                msg = "<b>"msg + item[0] + "</b><br>"
            return msg

        matching_spell = next(spell for spell in self.spells if spell["name"] == matches[0][0], None)
        if matching_spell is None:		
            return "Well I couldn't even find a single spell in my database. That's bad."
        
        return self.get_spell_info(name, matching_spell)

    def userTextMessage(self, server, user, message, current=None):
        # Ensure we're using the keyword
        if not message.text.startswith("!spell"):
            return

        # Get the searched spell name
        split = message.text.split(" ", 1)
        if len(split) != 2:
            return
        name = split[1].lower()
        
        msg = self.fuzzy_match(name)
        server.sendMessageChannel(user.channel, False, msg)

    
    def userConnected(self, server, state, context = None): pass
    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass
    
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass

