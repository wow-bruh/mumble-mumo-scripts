#!/usr/bin/env python
# -*- coding: utf-8

# Copyright (C) 2010-2011 Stefan Hacker <dd0t@users.sourceforge.net>
# Copyright (C) 2015 Natenom <natenom@googlemail.com>
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

from mumo_module import (commaSeperatedIntegers,
                         MumoModule)
import re
from time import sleep

class mod_suffixes(MumoModule):
    default_config = {}

    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()

    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Register for Server callbacks")

        servers = manager.SERVERS_ALL

        manager.subscribeServerCallbacks(self, servers)

    def disconnected(self): pass

    #
    #--- Server callback functions
    #

    def userConnected(self, server, state, context = None):
        sleep(2)
        state = server.getState(state.session) # Get state again after sleep to prevent from interrering with deaftoafk script, see https://github.com/Natenom/mumo-os-suffixes/issues/2; jupp, there are probably better solutions...

        log = self.log()
        #self.log().debug("User connected. OS: %s, Version: %s, Username: %s, Session ID: %s." % (state.os, state.version, state.name, state.session))

        if state.userid == -1:
            # Ignore unregistered users.
            return

	prefix = ""

	acl = server.getACL(0)
	for group in acl[1]:
		if state.userid in group.members:
			if group.name == "admin":
				prefix = "(A)"
			elif group.name == "mods":
				prefix = "(M)"

        if len(prefix) > 0:
            state.name = prefix + " " + state.name
            try:
                server.setState(state)
            except self.murmur.InvalidSessionException:
                self.log().debug("User disconnected before I could change his status.")

    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass
    def userTextMessage(self, server, user, message, current=None): pass
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass

