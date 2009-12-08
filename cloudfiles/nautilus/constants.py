import os
import urllib2
import urllib

def detect_glade():
    glade_cwd=os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "../", "../", "glade"))
    if os.path.exists(glade_cwd):
        return glade_cwd
    else:
        return "/usr/share/nautilus-cloud-files-plugin/glade"


GLADE_DIR = detect_glade()
EXCLUDE_CONTAINERS = ['.CDN_ACCESS_LOGS']
SHORTENER="http://is.gd/api.php?longurl=%s"
short_url = lambda x: urllib.urlopen(SHORTENER % urllib2.quote(x)).read().strip()
