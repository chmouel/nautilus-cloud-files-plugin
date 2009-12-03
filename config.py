# -*- Mode: Python -*-
# from python istanbul Copyright GPL
import gconf

# TODO: move to consts
GCONF_CF_DIR_KEY = '/apps/rackspace-cloud-files'

class GConfClient(object):
    def __init__(self, directory):
        self.client = gconf.client_get_default()
        self.client.add_dir (directory, gconf.CLIENT_PRELOAD_NONE)
        self.directory = directory + "/"

    def get_entry(self, key, type_):
        k = self.directory + key
        if type_ == "string":
            s = self.client.get_string(k)
        elif type_ == "boolean":
            s = self.client.get_bool(k)
        elif type_ == "integer":
            s = self.client.get_int(k)
        elif type_ == "float":
            s = self.client.get_float(k)
        return s

    def set_entry(self, key, entry, type_):
        k = self.directory + key
        if type_ == "boolean":
            self.client.set_bool(k, entry)
        elif type_ == "string":
            self.client.set_string(k, entry)
        elif type_ == "integer":
            self.client.set_int(k, entry)
        elif type_ == "float":
            self.client.set_float(k, entry)

    def unset_entry(self,key):
        self.client.unset(self.directory + key)

class CloudFilesGconf(GConfClient):
    def __init__(self):
        GConfClient.__init__(self, GCONF_CF_DIR_KEY)
