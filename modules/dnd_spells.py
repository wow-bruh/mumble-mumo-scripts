#!/usr/bin/env python
# -*- coding: utf-8
#
# dnd_spells.py
# This module allows asking the server to look for a spell in dungeons and dragons
#

import json
import codecs
import collections
from mumo_module import MumoModule
from fuzzywuzzy import process

class dnd_spells(MumoModule):
    def __init__(self, name, manager, configuration=None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        # Load spells
        self.spells = dict()
        self.spells_names = dict()
        with open("resources/dnd_spells/spells.json") as spells_file:
            self.spells["dnd"] = json.loads(spells_file.read().decode("utf-8"))
            self.spells_names["dnd"] = [item["name"].lower() for item in self.spells["dnd"]]
        with open("resources/dnd_spells/pf_spells.json") as spells_files:
            self.spells["pathfinder"] = json.loads(spells_file.read().decode("utf-8"))
            self.spells_names["pathfinder"] = [item["name"].lower() for item in self.spells["pathfinder"]]

        # Load attribute name -> full length words mapping
        self.attr_map = {"dnd": collections.OrderedDict([
            ("name", u"<b>"),
            ("level", u"</b><b> • Level</b>: "),
            ("school", u"<b> • School</b>: "),

            ("page", u"<b> • Source</b>: "),
            ("range", u"<b> • Range</b>: "),
            ("components", u"<b> • Components</b>: "),
            ("material", u"<b> • Material</b>: "),
            ("ritual", u"<b> • Is a Ritual: </b>"),
            ("concentration", u"<b> • Is a Concentration spell: </b>"),
            ("casting_time", u"<b> • Time to cast: </b>"),
            ("class", u"<b> • Usable by</b>: "),
            ("circle", u"<b> • Circle</b>: "),
            ("archetype", u"<b> • Archetype</b>: "),
            ("duration", u"<b> • Duration</b>: "),
            ("domains", u"<b> • Domains</b>: "),
            ("patrons", u"<b> • Patrons</b>: "),
            ("oaths", u"<b> • Oaths</b>: "),

            ("desc", u"<br><br>")
        ]),
        "pathfinder": collections.OrderedDict([
            ("name", "<b>"),
            ("level", u"</b><b> • Level</b>: "),
            ("school", u"<b> • School</b>: "),
            ("subschool", u"<b> • Subschool</b>: "),
            ("effect", u"<b> • Effect: </b>"),

            ("range", u"<b> • Range</b>: "),
            ("area", u"<b> • Area: </b>"),
            ("duration", u"<b> • Duration: </b>"),
            ("target", u"<b> • Target: </b>"),
            
            ("components", u"<b> • Components</b>: "),
            ("casting_time", u"<b> • Time to cast: </b>"),
            ("saving_throw", u"<b> • Saving Throw: </b>"),
            ("spell_resistance", u"<b> • Spell Resistance: </b>"),

            ("description", u"<br><br>")
        ])}

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

    def get_spell_info(self, search, spell, key):
        spell_keys = spell.keys()
        msg = """Here's what I found that's my closest match for {looking_for}:<br>""".format(looking_for=search.encode("utf-8"))
        for k in self.attr_map[key]:
            if k in spell_keys:
                msg = msg + self.attr_map[key][k].encode("utf-8") + spell[k].encode("utf-8") + "<br>"

        return msg

    # Returns the appropriate key at which to look for spells, relative to the user's channel
    # Todo: make that less of an awful hack
    def get_spell_list(self, user, server):
        chan = user.channel
        all_chans = server.getChannels()
        if chan in all_chans:
            if all_chans[chan] == "Dungeons and Dragons":
                return "dnd"
            elif all_chans[chan] == "Pathfinder":
                return "pathfinder"
            else:
                return None

    def fuzzy_match(self, name, key):
        matching_spell = None
        # Check for an exact match first
        if name in self.spells_names[key]:
            matching_spell = next((spell for spell in self.spells[key] if spell["name"].lower() == name), None)
        if matching_spell is not None:
            return self.get_spell_info(name, matching_spell, key)

        # No direct match, let's attempt a fuzzy match
        matches = process.extract(name, self.spells_names[key], limit=3)
        if matches is None or len(matches) == 0:
            return "Well I couldn't even find a single spell in my database that matches that. That's bad."

        # Unsure matches go here
        if matches[0][1] < 50:
            msg = "I've found some stuff, but I'm not entirely sure that's what you mean. Mind giving me a bit more info? Those are the spells I found that might match:<br>"
            for item in matches:
                msg = msg + "<b>" + item[0].encode("utf-8").title() + "</b><br>"
            return msg

        matching_spell = next((spell for spell in self.spells[key] if spell["name"].lower() == matches[0][0]), None)
        if matching_spell is None:
            return "Well I couldn't even find a single spell in my database. That's bad. For the record, I tried to match against " + matches[0][0]

        msg = self.get_spell_info(name, matching_spell, key)
        msg = msg + "<br>In case that's wrong, here are some other close matches I have in database:<br>"
        # Skip the first match, we already returned it
        iterspell = iter(matches)
        next(iterspell)
        for item in iterspell:
            msg = msg + item[0].encode("utf-8").title() + "<br>"

        return msg

    def userTextMessage(self, server, user, message, current=None):
        # Ensure we're using the keyword
        if not message.text.startswith("!spell"):
            return
        key = self.get_spell_list(user, server)
        if key is None:
            server.sendMessage(user.session, "This bot only works in the D&D/Pathfinder channels")

        # Get the searched spell name
        split = message.text.split(" ", 1)
        if len(split) != 2:
            return
        name = split[1].lower()

        msg = self.fuzzy_match(name, key)
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
