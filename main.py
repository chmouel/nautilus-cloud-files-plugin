#!/usr/bin/env python
import os
import sys
import socket

import cloudfiles

import gtk.glade

from config import CloudFilesGconf
from progressbar import Upload
from constants import GLADE_DIR, EXCLUDE_CONTAINERS

CF_CONNECTION = None
USERNAME = None
API_KEY = None

class CheckUsernameKey(object):
    """
    Check Username and Key
    """

    def __init__(self):
        self.dialog_error = None
        self.init_dialog_error()
        
    def hide_widget(self, widget, *args, **kwargs):
        widget.hide()
        return True

    def check(self, username, api_key):
        global CF_CONNECTION
        
        try:
            CF_CONNECTION = cloudfiles.get_connection(username, api_key)
        except(cloudfiles.errors.AuthenticationError,
               cloudfiles.errors.AuthenticationFailed):
            self.dialog_error.set_markup(
                'Your username (%s) or API Key (%s) does not seem to match or are incorrect.' % \
                    (username, api_key)
                )
            self.dialog_error.run()
            return False
        except(socket.gaierror):
            self.dialog_error.set_markup(
                'Cannot connect to Rackspace Cloud Files.')
            self.dialog_error.run()
            return False
        return True

    def init_dialog_error(self, parent=None):
        self.dialog_error = gtk.MessageDialog(parent=parent,
                                              type=gtk.MESSAGE_ERROR,
                                              flags=gtk.DIALOG_MODAL,
                                              buttons=gtk.BUTTONS_CLOSE,
                                              message_format='Error.')
        self.dialog_error.set_title("Cloud Files Uploader")
        self.dialog_error.connect('delete-event', self.hide_widget)
        self.dialog_error.connect('response', self.hide_widget)

class ShowContainersList(object):
    def __init__(self, stuff_to_upload):
        self.container_master_button = None
        self.containers_list_window = None
        self.container_new_entry = None
        self.gconf_key = CloudFilesGconf()
        self.default_container = self.gconf_key.get_entry("default_container", "string")
        self.stuff_to_upload = stuff_to_upload
        
    def list_containers(self):
        if not CF_CONNECTION:
            return []
        try:
            return [ cnt for cnt in CF_CONNECTION.list_containers() \
                         if cnt not in EXCLUDE_CONTAINERS ]
        except(cloudfiles.errors.ResponseError):
            return []

    def create_new_container(self, container):
        if not CF_CONNECTION:
            return
        try:
            return CF_CONNECTION.create_container(container)
        except(cloudfiles.errors.ResponseError):
            return
    
    def add_radiobutton(self, vbox):
        containers = self.list_containers()

        for container in sorted(containers):
            button = gtk.RadioButton(self.container_master_button, container)
            vbox.pack_start(button, True, True, 0)
            if self.default_container and container == self.default_container:
                button.set_active(True)
            button.show()
            
            if not self.container_master_button:
                self.container_master_button = button

    def ok(self, *args):
        new_container = self.container_new_entry.get_text()
        if new_container:
            container = self.create_new_container(new_container)
        else:
            for button in self.container_master_button.get_group():
                if button.get_active():
                    container = CF_CONNECTION.get_container(
                        button.get_label()
                        )
        self.containers_list_window.destroy()

        self.gconf_key.set_entry("default_container", str(container), "string")
        
        cnt = 0
        for obj in self.stuff_to_upload:
            upload = Upload(obj, container)
            upload.run()
            cnt += 1

    def quit(self, *args, **kwargs):
        self.containers_list_window.destroy()
            
    def show(self):
        gladefile = os.path.join(GLADE_DIR, 'dialog_containers_list.glade')
        window_tree = gtk.glade.XML(gladefile)
        
        self.containers_list_window = \
            window_tree.get_widget('dialog_containers_list')

        self.container_new_entry = window_tree.get_widget('entry1')
        
        vbox1 = window_tree.get_widget('vbox1')
        self.add_radiobutton(vbox1)

        button_ok = window_tree.get_widget('button1')
        button_cancel = window_tree.get_widget('button2')

        button_ok.connect('clicked', self.ok)
        button_ok.set_flags(gtk.CAN_DEFAULT)
        button_ok.grab_default()
        
        button_cancel.connect('clicked', self.quit)
        self.containers_list_window.connect('destroy', self.quit)
        self.containers_list_window.run()
        
class AskUsernameKey(object):
    def __init__(self, username=None):
        self.username = username
        self.api_key = None
        self.auth_window = None
        self.entry_username = None
        self.entry_api_key = None
        self.entry_message = None
        self.gconf_key = CloudFilesGconf()
        self.authenticated = False
        
    def clicked(self, *kargs, **kwargs):
        self.username = self.entry_username.get_text()
        self.api_key = self.entry_api_key.get_text()

        if not self.username:
            self.entry_message.set_text("You have not entered a Username")
            self.entry_message.show()
        
        if not self.api_key:
            self.entry_message.set_text("You have not entered an API Key")
            self.entry_message.show()
        
        check_username = CheckUsernameKey()        
        if check_username.check(self.username, self.api_key):
            self.authenticated = True
            self.auth_window.destroy()
            self.gconf_key.set_entry("username", self.username, "string")
            self.gconf_key.set_entry("api_key", self.api_key, "string")
            return True

        self.entry_message.set_text("Authentication has failed")
        self.entry_message.show()

    def quit(self, *args, **kwargs):
        self.auth_window.destroy()
        
    def show(self):
        gladefile = os.path.join(GLADE_DIR, 'dialog_authentication.glade')
        window_tree = gtk.glade.XML(gladefile)

        self.entry_username = window_tree.get_widget("entry_username")
        self.entry_api_key = window_tree.get_widget("entry_api_key")
        self.entry_message = window_tree.get_widget("entry_message")

        if not self.entry_message.get_text():
            self.entry_message.hide()
        
        if self.username:
            self.entry_username.set_text(self.username)
            self.entry_api_key.grab_focus()

        if self.api_key:
            self.entry_username.set_text(self.api_key)
            
        self.auth_window = window_tree.get_widget('dialog_authentication')
        button_ok = window_tree.get_widget('button1')
        button_cancel = window_tree.get_widget('button2')

        button_ok.connect('clicked', self.clicked)
        button_cancel.connect('clicked', self.quit)
        self.auth_window.connect('destroy', self.quit)
        self.auth_window.run()
    
class CloudFileUploader(object):

    def __init__(self, stuff_to_upload):
        self.gconf_key = CloudFilesGconf()
        self.stuff_to_upload = stuff_to_upload
        
    def main(self):
        global USERNAME, API_KEY
        
        username = self.gconf_key.get_entry("username", "string")
        api_key = self.gconf_key.get_entry("api_key", "string")

        check_username = CheckUsernameKey()
        if not(all([username, api_key]) and \
                   check_username.check(username, api_key)):
            ask = AskUsernameKey(username=username)
            ask.show()

            if not ask.authenticated:
                #make sure it has been destroyed
                ask.auth_window.destroy()
                return
            
            username = self.gconf_key.get_entry("username", "string")
            api_key = self.gconf_key.get_entry("api_key", "string")

            
        USERNAME = username
        API_KEY = api_key

        self.gconf_key.set_entry("username", username, "string")
        self.gconf_key.set_entry("api_key", api_key, "string")

        container_list = ShowContainersList(self.stuff_to_upload)
        container_list.show()
        
if __name__ == '__main__':
    stuff_to_upload = sys.argv[1:]
    if not stuff_to_upload:
        print "You need to specify files on the command line"
        sys.exit(0)

    c = CloudFileUploader(stuff_to_upload)
    c.main()
    gtk.main()
            
