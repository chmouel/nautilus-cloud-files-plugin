#!/usr/bin/env python
import os
import sys
import socket
import threading

import cloudfiles

import gtk.glade
gtk.gdk.threads_init()

from config import CloudFilesGconf
from monkeypatching import BackObject

CF_CONNECTION=None
USERNAME=None
API_KEY=None
EXCLUDE_CONTAINERS=['.CDN_ACCESS_LOGS']

#TODO: some better checking
FILES = sys.argv[1:]

#TODO: consts
GLADE_DIR = os.path.join(os.path.dirname
                       (os.path.abspath(__file__)),
                       "glade")
OFFLINE_TESTING=True

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
                'Your username (%s) or API Key (%s) does not seem to match or are incorrect.' % (username, api_key)
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

class Upload(threading.Thread):
    def __init__(self, cnx, filename, chosen_container):
        self.canceled = False
        self.filename = filename
        self.chosen_container = chosen_container
        self.glade_dir = os.path.join(os.path.dirname
                                      (os.path.abspath(__file__)),
                                      "glade")
        threading.Thread.__init__(self) 

    def run(self):
        cf_object = BackObject(
            self.chosen_container,
            os.path.basename(self.filename)
            )

        self.show_progressbar()
        self.progressbar_label1.set_text("Uploading %s" % cf_object)
        
        fobj = open(self.filename, 'rb')
        ret = cf_object.write(fobj, callback=self.callback, verify=True)
        fobj.close()
        
    def show_progressbar(self):
        gladefile = os.path.join(self.glade_dir, 'dialog_progressbar.glade')
        window_tree = gtk.glade.XML(gladefile)

        self.progressbar_window = window_tree.get_widget("progressbar_window")
        self.progressbar_label1 = window_tree.get_widget('label1')

        self.progressbar = window_tree.get_widget("progressbar1")        
        button_cancel = window_tree.get_widget('button2')
        button_cancel.connect('clicked', self.quit)
        
        self.progressbar_window.show()


    def quit(self, *args, **kwargs):
        self.canceled = True
        
    def callback(self, current, total):
        if self.canceled:
            return False
        
        while gtk.events_pending():
            gtk.main_iteration()
        self.progressbar.set_fraction(float(current) / total)
        self.progressbar.set_text("%d / %d" % (current, total))

        return True
        
class ShowContainersList(object):
    def __init__(self):
        #TODO: record
        self.container_master_button = None

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
    
    def _add_radiobutton(self, vbox):
        containers = self.list_containers()

        for container in sorted(containers):
            button = gtk.RadioButton(self.container_master_button, container)
            vbox.pack_start(button, True, True, 0)
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

        cnt = 0
        for obj in FILES:
            if cnt >= 1:
                cnx = cloudfiles.get_connection(USERNAME, API_KEY)
            else:
                cnx = CF_CONNECTION
            
            upload = Upload(cnx, obj, container)
            upload.start()

            cnt += 1
        return
        
    def show(self):
        gladefile = os.path.join(GLADE_DIR, 'dialog_containers_list.glade')
        window_tree = gtk.glade.XML(gladefile)
        
        self.containers_list_window = \
            window_tree.get_widget('dialog_containers_list')

        self.container_new_entry = window_tree.get_widget('entry1')
        
        vbox1 = window_tree.get_widget('vbox1')
        self._add_radiobutton(vbox1)
        
        button_ok = window_tree.get_widget('button1')
        button_cancel = window_tree.get_widget('button2')

        button_ok.connect('clicked', self.ok)
        button_cancel.connect('clicked', gtk.main_quit)

        self.containers_list_window.connect('destroy', gtk.main_quit)
        self.containers_list_window.show()
        
class AskUsernameKey(object):
    def __init__(self, username=None):
        self.username = username
        self.api_key = None
        
    def clicked(self, *kargs, **kwargs):
        self.username = self.entry_username.get_text()
        self.api_key = self.entry_api_key.get_text()

        if not self.username:
            self.entry_message.set_text("You have not entered a Username")
            self.entry_message.show()
            return False
        
        if not self.api_key:
            self.entry_message.set_text("You have not entered an API Key")
            self.entry_message.show()
            return False
        
        check_username = CheckUsernameKey()        
        if check_username.check(self.username, self.api_key):
            container_list = ShowContainersList()
            container_list.show()
        else:
            self.entry_message.set_text("Authentication has failed")
            self.entry_message.show()
            return False
            
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
        button_cancel.connect('clicked', gtk.main_quit)
        self.auth_window.connect('destroy', gtk.main_quit)
        self.auth_window.show()
        return 
    
class CloudFileUploader(object):

    def __init__(self):
        self.gconf_key = CloudFilesGconf()
        
    def main(self):
        global USERNAME, API_KEY
        
        username = self.gconf_key.get_entry("username", "string")
        api_key = self.gconf_key.get_entry("api_key", "string")

        check_username = CheckUsernameKey()
        if all([username, api_key]) and \
                check_username.check(username, api_key):
            USERNAME=username
            API_KEY=api_key
            #TODO: set gconf here
            container_list = ShowContainersList()
            container_list.show()
        else:
            ask = AskUsernameKey(username=username)
            ask.show()
            
if __name__ == '__main__':
    if not FILES:
        print "You need to specify files on the command line"
        sys.exit(0)

    c = CloudFileUploader()
    c.main()
    gtk.main()
            
