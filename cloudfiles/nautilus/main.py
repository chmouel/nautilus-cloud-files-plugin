#!/usr/bin/env python
import os
import sys
import socket

import gtk.glade
import cloudfiles

from config import CloudFilesGconf
from constants import GLADE_DIR
from show_container import ShowContainersList

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

        container_list = ShowContainersList(CF_CONNECTION, self.stuff_to_upload)
        container_list.show()
        
if __name__ == '__main__':
    stuff_to_upload = sys.argv[1:]
    if not stuff_to_upload:
        print "You need to specify files on the command line"
        sys.exit(0)

    c = CloudFileUploader(stuff_to_upload)
    c.main()
    gtk.main()
            
