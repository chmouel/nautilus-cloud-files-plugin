import os
from monkeypatching import BackObject
import gtk.glade

#TODO
GLADE_DIR = os.path.join(os.path.dirname
                       (os.path.abspath(__file__)),
                       "glade")
TRANSIENT_WINDOW=None

class Upload(object):
    def __init__(self, cnx, filename, chosen_container):
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
        
        self.progressbar_label1.set_text("Uploading %s" % cf_object)
        
        fobj = open(self.filename, 'rb')
        ret = cf_object.write(fobj, callback=self.callback, verify=True)
        fobj.close()
        
    def show(self):
        global TRANSIENT_WINDOW
        
        gladefile = os.path.join(GLADE_DIR, 'dialog_progressbar.glade')
        window_tree = gtk.glade.XML(gladefile)

        self.progressbar_window = window_tree.get_widget("progressbar_window")
        self.progressbar_window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        if TRANSIENT_WINDOW:
            self.progressbar_window.set_transient_for(TRANSIENT_WINDOW)
            
        TRANSIENT_WINDOW = self.progressbar_window
        
        self.progressbar_label1 = window_tree.get_widget('label1')

        self.progressbar = window_tree.get_widget("progressbar1")
        button_cancel = window_tree.get_widget('button2')
        button_cancel.connect('clicked', self.quit)
        
        self.progressbar_window.show()

    def quit(self, *args, **kwargs):
        self.canceled = True
        self.progressbar_window.destroy()
        
    def callback(self, current, total):
        if self.canceled:
            return False

        current = current + 4096
        
        while gtk.events_pending():
            gtk.main_iteration()
        self.progressbar.set_fraction(float(current) / total)
        self.progressbar.set_text("%d / %d" % (current, total))

        if current == total:
            self.quit()
        
        return True

if __name__ == '__main__':
    import cloudfiles
    import os

    tests=["/tmp/big-1.mp3", "/tmp/big-2.mp3"]
    
    cnx = cloudfiles.get_connection(os.environ['RCLOUD_API_USER'], os.environ['RCLOUD_API_KEY'])
    container = cnx.get_container("public")

    for obj in tests:
        upload = Upload(cnx, obj, container)
        upload.run()
    
