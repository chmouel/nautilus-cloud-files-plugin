import os
import gobject
import pynotify
import gtk.glade
import cloudfiles

from config import CloudFilesGconf
from progressbar import Upload
from constants import GLADE_DIR, EXCLUDE_CONTAINERS, short_url

class ShowContainersList(object):
    def __init__(self, cnx, stuff_to_upload):
        self.cnx = cnx
        self.chosen_container = None
        self.container_master_button = None
        self.containers_list_window = None
        self.container_new_entry = None
        self.gconf_key = CloudFilesGconf()
        self.button_clipboard = None
        self.list_store = None
        self.default_container = \
            self.gconf_key.get_entry("default_container",
                                     "string")
        self.stuff_to_upload = stuff_to_upload
        
    def list_containers(self):
        if not self.cnx:
            return []
        try:
            return [ cnt for cnt in self.cnx.list_containers() \
                         if cnt not in EXCLUDE_CONTAINERS ]
        except(cloudfiles.errors.ResponseError):
            return []

    def create_new_container(self, container):
        if not self.cnx:
            return
        try:
            return self.cnx.create_container(container)
        except(cloudfiles.errors.ResponseError):
            return
    
    def ok(self, *args):
        new_container = self.container_new_entry.get_text()
        if new_container:
            container = self.create_new_container(new_container)
        else:
            if not self.chosen_container:
                if self.default_container:
                    self.chosen_container = self.default_container
                else:
                    return False
            container = self.cnx.get_container(self.chosen_container)
        self.containers_list_window.destroy()

        self.gconf_key.set_entry("copy_to_clipboard",
                                 self.button_clipboard.get_active(), "boolean")
        self.gconf_key.set_entry("default_container",
                                 str(container), "string")

        public_uris = []
        for obj in self.stuff_to_upload:
            pynotify.init("Uploading %s" % obj)
            upload = Upload(obj, container)
            try:
                ret = upload.run()
            except(cloudfiles.errors.ContainerNotPublic):
                ret = "NotPublic"

            if not ret:
                conclusion = "Aborted"
            else:
                conclusion = "uploaded to %s" % (container)
                if ret != "NotPublic":
                    public_uris.append(ret)
                    
            title = "Rackspace Cloud Files Upload"
            msg = "File %s %s" % (obj, conclusion)

            if self.button_clipboard.get_active() and public_uris:
                cb = gtk.clipboard_get('CLIPBOARD')
                cb.clear()
                cb.set_text(" ".join(map(short_url, public_uris)))
            
            n = pynotify.Notification(title, msg, gtk.STOCK_FIND_AND_REPLACE)
            n.set_timeout(pynotify.EXPIRES_DEFAULT)
            n.show()
            
    def quit(self, *args, **kwargs):
        self.containers_list_window.destroy()

    def toggled(self, cell_renderer, col, treeview):
        tree_iter = self.list_store.get_iter(col)
        old_value = self.list_store.get_value(tree_iter, 1)
        new_value = not old_value

        def untoggle_entries(lst_store, path, tree_iter):
            self.list_store.set_value(tree_iter, 1, False)
        self.list_store.foreach(untoggle_entries)

        self.chosen_container = self.list_store.get_value(tree_iter, 0)
        self.list_store.set_value(tree_iter, 1, new_value)
        
    def add_tree_list(self, vbox):
        self.list_store = gtk.ListStore(gobject.TYPE_STRING,
                                        gobject.TYPE_BOOLEAN,
                                        gobject.TYPE_STRING)
        
        # use list store as treemodel for treeview
        treeview = gtk.TreeView(self.list_store)

        # draw checkboxes
        bool_cell_renderer = gtk.CellRendererToggle()
        bool_cell_renderer.set_radio(True)
        bool_cell_renderer.set_property('activatable', 1)
        bool_cell_renderer.connect('toggled', self.toggled, treeview)
        bool_col = gtk.TreeViewColumn("",
                                      bool_cell_renderer, 
                                      active=1)

        treeview.insert_column(bool_col, -1)

        str_cell_renderer = gtk.CellRendererText()
        text_col = gtk.TreeViewColumn("Choose Container",
                                      str_cell_renderer, text=0)
        str_cell_renderer.set_property('background-set' , True)
        str_cell_renderer.set_property('foreground-set' , True)
        text_col.set_attributes(str_cell_renderer,text=0, background=2)
    
        treeview.insert_column(text_col, -1)

        treeview.set_reorderable(1) 
        treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)
        treeview.show()
        treeview.columns_autosize()

        background_color="#EEEEEE"
        containers = self.list_containers()
        for container in sorted(containers):
            background_color = background_color == "#EEEEEE" and "#FFFFFF" or "#EEEEEE"
            checked = 0
            if container == self.default_container:
                checked = 1
            self.list_store.append([container, checked, background_color])
        
        vbox.pack_start(treeview, True, True, 0)
        #self.containers_list_window.add(treeview)
        
    def show(self):
        gladefile = os.path.join(GLADE_DIR, 'dialog_containers_list.glade')
        window_tree = gtk.glade.XML(gladefile)
        
        self.containers_list_window = \
            window_tree.get_widget('dialog_containers_list')

        self.containers_list_window.set_position(gtk.WIN_POS_CENTER)
        
        self.container_new_entry = window_tree.get_widget('entry1')
        vbox1 = window_tree.get_widget('vbox1')
        self.add_tree_list(vbox1)

        button_ok = window_tree.get_widget('button1')
        button_cancel = window_tree.get_widget('button2')
        self.button_clipboard = window_tree.get_widget('checkbutton1')

        default_clipboard = self.gconf_key.get_entry("copy_to_clipboard",
                                                     "boolean")
        self.button_clipboard.set_active(default_clipboard)
        
        button_ok.connect('clicked', self.ok)
        button_ok.set_flags(gtk.CAN_DEFAULT)
        button_ok.grab_default()

        
        button_cancel.connect('clicked', self.quit)
        self.containers_list_window.connect('destroy', self.quit)
        self.containers_list_window.run()
