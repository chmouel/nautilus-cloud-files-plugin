import nautilus
import sys
import urllib2
import gtk

sys.path.append("/home/chmouel/GIT/nautilus-plugin") #TODO
import main

class NautilusCloudFilesExtension(nautilus.MenuProvider):
    def __init__(self):
        selfname = type(self).__name__

    def menu_activate_cb(self, menu, files):
        #List the valid files
        stuff = [f for f in files if not f.is_gone() and self.is_valid(f)]
        stuff = map(lambda f: urllib2.unquote(f.get_uri()[7:]), stuff)

        main.FILES = stuff
        invoker = main.CloudFileUploader()
        invoker.main()
        #gtk.main()
        
    def get_file_items(self, window, files):
        files = [ f for f in files if self.is_valid(f)]
        if len(files) == 0:
            return
        print files

        item = nautilus.MenuItem('NautilusPython::upload_rscf_item',
                                 'Upload to Rackspace CF' ,
                                 'Upload to Rackspace CF',
                                 gtk.STOCK_FIND_AND_REPLACE
                                 )
        item.connect('activate', self.menu_activate_cb, files)
        return item,

    def is_valid(self, f):
        return f.get_uri_scheme() == 'file'
    

    
