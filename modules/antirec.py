#!/usr/bin/env python
# -*- coding: utf-8

# Copyright (C) 2011 Stefan Hacker <dd0t@users.sourceforge.net>
# Copyright (C) 2015 Natenom <natenom@googlemail.com>
# All rights reserved.
#
# Antirec is based on the scripts onjoin.py, idlemove.py and seen.py
# (made by dd0t) from the Mumble Moderator project , available at
# http://gitorious.org/mumble-scripts/mumo
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

class antirec(MumoModule):
    default_config = {'antirec':(
				('servers', commaSeperatedIntegers, []),
				),
				lambda x: re.match('(all)|(server_\d+)', x):(
				('cantallowself', str, 'You can\'t allow yourself to record.'),
				('userremovedfromallowed', str, 'User %s has been removed from list.'),
				('userwasnotallowed', str, 'User %s was not on list, can\'t remove.'),
				('usergotpermission', str, 'User %s got permission from %s to record.'),
				('canallowrecording', str, 'allowrecord'),
				('punishment', str, 'DEAF'),
				('adminallowself', str, "FALSE"),
				('deafmessage', str, 'Recording not allowed. Stop it to get undeafened :)'),
				('kickmessage', str, 'Recording not allowed.'),
				('allowedchannels', str, '1')
				)
		    }

    def __init__(self, name, manager, configuration = None):
	MumoModule.__init__(self, name, manager, configuration)
	self.murmur = manager.getMurmurModule()
        self.action_allow_recording = manager.getUniqueAction()
        self.action_disallow_recording = manager.getUniqueAction()
        self.action_list_allowed = manager.getUniqueAction()

        self.list_state_before_recording = {}
        self.allowedusers = {} # Will contain one object for every virtual server.


    def connected(self):
	manager = self.manager()
	log = self.log()
	log.debug("Register for Server callbacks")

	servers = self.cfg().antirec.servers
	if not servers:
	    servers = manager.SERVERS_ALL

	manager.subscribeServerCallbacks(self, servers)
	
	# Craft the array for all virtual servers. Should also work for server later started servers.
	meta = manager.getMeta()
        servers = meta.getAllServers()

        for virtualserver in servers:
            if not virtualserver.id() in self.allowedusers:
                self.allowedusers[virtualserver.id()] = {}

    def disconnected(self): pass

    def __on_list_allowed(self, server, action, user, target):
        try:
	    scfg = getattr(self.cfg(), 'server_%d' % server.id())
	except AttributeError:
	    scfg = self.cfg().all

        assert action == self.action_list_allowed

        if len(self.allowedusers[server.id()]) > 0:
            listusers="<span style='color:red;'>Users with permission to record:</span>"
            listusers+="<ul>"
            for usernow in self.allowedusers[server.id()] :
                try:
                    listusers+="<li>%s</li>" % (server.getState(int(usernow)).name)
                except:
                    #user already disconnected...
                    pass

            listusers+="</ul>"
        else:
            listusers="There are no users with permission to record."

        server.sendMessage(user.session, listusers)

    def __on_allow_recording(self, server, action, user, target):
        try:
	    scfg = getattr(self.cfg(), 'server_%d' % server.id())
	except AttributeError:
	    scfg = self.cfg().all

        assert action == self.action_allow_recording
        self.log().info(user.name + " allowed recording for " + target.name)

        if (target.session == user.session) and (scfg.adminallowself == "FALSE"):
            server.sendMessage(user.session, scfg.cantallowself)
        else:
            self.allowedusers[server.id()][str(target.session)]=1

            try:
                server.sendMessageChannel(user.channel, False, scfg.usergotpermission % (server.getState(target.session).name, user.name))
            except:
                self.log().debug("SessionID %s does not exist :)" % target.session)

    def __on_disallow_recording(self, server, action, user, target):
        try:
	    scfg = getattr(self.cfg(), 'server_%d' % server.id())
	except AttributeError:
	    scfg = self.cfg().all

        assert action == self.action_disallow_recording
        self.log().info(user.name + " disallowed recording for " + target.name)

        try:
            del self.allowedusers[server.id()][str(target.session)]
            server.sendMessage(user.session, scfg.userremovedfromallowed % server.getState(target.session).name)
            curuser=server.getState(target.session)
            if (curuser.recording==True):
                curuser.deaf=True
                server.setState(curuser)
        except:
            server.sendMessage(user.session, scfg.userwasnotallowed % target.session)

    #
    #--- Server callback functions
    #

    def userTextMessage(self, server, user, message, current=None): pass

    def userConnected(self, server, user, context = None):
	# Adding the entries here means if mumo starts up after users
        # already connected they won't have the new entries before they
        # reconnect. You can also use the "connected" callback to
        # add the entries to already connected user. For simplicity
        # this is not done here.

        try:
	    scfg = getattr(self.cfg(), 'server_%d' % server.id())
	except AttributeError:
	    scfg = self.cfg().all

	self.log().info("Adding menu entries for " + user.name)

        manager = self.manager()
        
        # Add context menu to allowrecord group only
        ACL=server.getACL(0) # Check if user is in group canallowrecording defined in the root channel.
        for gruppe in ACL[1]:
            if (gruppe.name == scfg.canallowrecording):
                if (user.userid in gruppe.members):
                    #Benutzer ist in der Gruppe
                    manager.addContextMenuEntry(
                        server, # Server of user
                        user, # User which should receive the new entry
                        self.action_allow_recording, # Identifier for the action
                        "Allow the user to record", # Text in the client
                        self.__on_allow_recording, # Callback called when user uses the entry
                        self.murmur.ContextUser # We only want to show this entry on users
                    )

                    manager.addContextMenuEntry(
                        server, # Server of user
                        user, # User which should receive the new entry
                        self.action_disallow_recording, # Identifier for the action
                        "Disallow the user to record", # Text in the client
                        self.__on_disallow_recording, # Callback called when user uses the entry
                        self.murmur.ContextUser # We only want to show this entry on users
                    )
                    
                    manager.addContextMenuEntry(
                        server, # Server of user
                        user, # User which should receive the new entry
                        self.action_list_allowed, # Identifier for the action
                        "List users allowed to record", # Text in the client
                        self.__on_list_allowed, # Callback called when user uses the entry
                        self.murmur.ContextServer 
                    )

                break

    def userDisconnected(self, server, state, context = None):
	if str(state.session) in self.allowedusers[server.id()]:
	    del self.allowedusers[server.id()][str(state.session)]
	    self.log().debug("Session %s removed from allowedusers, %s disconnected" % (state.session, state.name))

    def userStateChanged(self, server, state, context = None):
	"""Wer aufnimmt, wird stumm-taub gestellt."""
	try:
	    scfg = getattr(self.cfg(), 'server_%d' % server.id())
	except AttributeError:
	    scfg = self.cfg().all

	allowedchannels_list=scfg.allowedchannels.split()
	if str(state.channel) in allowedchannels_list: #recording in these channels is allowed
		return

	if (state.recording==True) and (state.deaf==False):
	    self.list_state_before_recording[state.session]=state.deaf
	    if not (str(state.session) in self.allowedusers[server.id()]):
		if (scfg.punishment=="DEAF"):
		    state.deaf=True
		    server.setState(state)

		    server.sendMessageChannel(state.channel, False, scfg.deafmessage % (state.name))
		elif (scfg.punishment=="KICK"):
		    server.kickUser(state.session, scfg.kickmessage)

	#Wenn Benutzer in der Liste drin ist, hat er irgendwann aufgenommen; wenn er jetzt nicht mehr aufnimmt, bekommt er den deaf-Status von vor der Aufnahme :)
	if (state.recording==False) and (state.session in self.list_state_before_recording):
	    state.deaf = self.list_state_before_recording[state.session]
	    state.mute = self.list_state_before_recording[state.session]
	    server.setState(state)

	    del self.list_state_before_recording[state.session]


    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass
