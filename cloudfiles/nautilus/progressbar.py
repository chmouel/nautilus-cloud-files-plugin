#!/usr/bin/python
import os
from monkeypatching import BackObject
from constants import GLADE_DIR
import gtk.glade

#TODO
class Upload(object):
    def __init__(self, filename, chosen_container):
        self.canceled = False
        self.filename = filename
        self.chosen_container = chosen_container
        self.progressbar = None
        self.progressbar_label1 = None
        
    def run(self):
        cf_object = BackObject(
            self.chosen_container,
            os.path.basename(self.filename)
            )

        self.show()

        title = "Uploading %s" % (cf_object)
        self.window.set_title(title)
        self.progressbar_label1.set_text(title)
        
        fobj = open(self.filename, 'rb')
        ret = cf_object.write(fobj, callback=self.callback, verify=True)
        fobj.close()

        if ret == "Aborted":
            return False
        else:
            return cf_object.public_uri()
            
    def show(self):
        gladefile = os.path.join(GLADE_DIR, 'dialog_progressbar.glade')
        window_tree = gtk.glade.XML(gladefile)

        self.window = window_tree.get_widget("progressbar_window")
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.progressbar_label1 = window_tree.get_widget('label1')

        self.progressbar = window_tree.get_widget("progressbar1")
        button_cancel = window_tree.get_widget('button2')
        button_cancel.connect('clicked', self.quit)
        
        self.window.show()

    def quit(self, *args, **kwargs):
        self.canceled = True
        self.window.destroy()
        
    def callback(self, current, total):
        if self.canceled:
            return False

        while gtk.events_pending():
            gtk.main_iteration()

        current = current + 4096
        self.progressbar.set_fraction(float(current) / total)
        self.progressbar.set_text("%d / %d" % (current, total))

        if current >= total:
            self.window.destroy()
        
        return True

if __name__ == '__main__':
    import cloudfiles

    tests=["/tmp/big-1.mp3", "/tmp/big-2.mp3"]
    
    cnx = cloudfiles.get_connection(os.environ['RCLOUD_API_USER'], os.environ['RCLOUD_API_KEY'])
    container = cnx.get_container("public")

    for obj in tests:
        upload = Upload(obj, container)
        upload.run()
    
