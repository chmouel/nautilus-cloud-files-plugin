from setuptools import setup
import glob

PACKAGE = 'nautilus-cloud-files'
VERSION = '0.1'

setup(name = PACKAGE, version = VERSION,
      license = "MIT",
      description = "Plugin to upload to Rackspace Cloud Files",
      author = "Chmouel Boudjnah",
      author_email = "chmouel@chmouel.com",
      url = "http://github.com/chmouel/nautilus-cloud-files-plugin",
      packages= [ "cloudfiles.nautilus" ],
      data_files=[
        ('share/nautilus-cloud-files-plugin/glade', glob.glob('glade/*')),
        ('lib/nautilus/extensions-2.0/python', ["extensions/nautilus_cloudfiles.py"])
        ]
      )
