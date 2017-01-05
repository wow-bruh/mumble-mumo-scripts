#!/usr/bin/env python
# -*- coding: utf-8
#
# dnd_spells.py
# This module allows asking the server to look for a spell in dungeons and dragons
#

import json
from mumo_module import MumoModule
from fuzzywuzzy import process

class dnd_spells(MumoModule):
    def __init__(self, name, manager, configuration=None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        # Load spells
        with open("spells.json") as spells_file:
            self.spells = json.loads(spells_file.read())
        self.spells_names = [item["name"].lower() for item in self.spells]

        # Load attribute name -> full length words mapping
        self.attr_map = {
            "name": "",

            "page": "Source: ",
            "range": "Range: ",
            "components": "Components: ",
            "material": "Material: ",
            "ritual": "Is a Ritual",
            "concentration": "Is a Concentration spell",
            "casting_time": "Time to cast: ",
            "level": "Level: ",
            "class": "Usable by ",
            "school": "School of ",
            "circle": "Circle of the ",
            "archetype": "Archetype: ",
            "duration": "Duration: ",
            "domains": "Domains: ",
            "patrons": "Patrons: ",
            "oaths": "Oaths: ",

            "desc": ""
        }

    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Register for Server callbacks")
        servers = manager.SERVERS_ALL
        manager.subscribeServerCallbacks(self, servers)

    def disconnected(self):
        pass

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
        spell_keys = spell.keys()
        msg = """Here's what I found that's my closest match for {looking_for}:<br>""".format(looking_for=search.encode("utf-8"))
        for k in self.attr_map:
            if k in spell_keys:
                msg = msg + self.attr_map[k] + spell[k] + "<br>"

        return msg

    def fuzzy_match(self, name):
        matching_spell = None
        # Check for an exact match first
        if name in self.spells_names:
            matching_spell = next((spell for spell in self.spells if spell["name"].lower() == name), None)
        if matching_spell is not None:
            return self.get_spell_info(name, matching_spell)

        # No direct match, let's attempt a fuzzy match
        matches = process.extract(name, self.spells_names, limit=3)
        if matches is None or len(matches) == 0:
            return "Well I couldn't even find a single spell in my database that matches that. That's bad."

        # Unsure matches go here
        if matches[0][1] < 50:
            msg = "I've found some stuff, but I'm not entirely sure that's what you mean. Mind giving me a bit more info? Those are the spells I found that might match:<br>"
            for item in matches:
                msg = msg + "<b>" + item[0].encode("utf-8").title() + "</b><br>"
            return msg

        matching_spell = next((spell for spell in self.spells if spell["name"].lower() == matches[0][0]), None)
        if matching_spell is None:
            return "Well I couldn't even find a single spell in my database. That's bad. For the record, I tried to match against " + matches[0][0]

        msg = self.get_spell_info(name, matching_spell)
        msg = msg + "<br>In case that's wrong, here are some other close matches I have in database:<br>"
        iterspell = iter(matches)
        next(iterspell)
        for item in iterspell:
            msg = msg + item[0].encode("utf-8").title() + "<br>"

        return msg

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


    def userConnected(self, server, state, context=None):
        pass
    def userDisconnected(self, server, state, context=None):
        pass
    def userStateChanged(self, server, state, context=None):
        pass

    def channelCreated(self, server, state, context=None):
        pass
    def channelRemoved(self, server, state, context=None):
        pass
    def channelStateChanged(self, server, state, context=None):
        pass
