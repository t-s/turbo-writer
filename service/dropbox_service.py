# Write this module based on:
#
# https://www.dropbox.com/developers/chooser
#   Shows how to obtain a link to a file in the user's Dropbox account
#
# http://docs.python.org/2/howto/urllib2.html
#   Shows how to read the link:
#
#   import urllib2
#   response = urllib2.urlopen(link)
#   data = response.read()
#
# https://developers.google.com/appengine/docs/python/blobstore/overview#Writing_Files_to_the_Blobstore
#   Shows how to write files to the Blobstore
import urllib2

from google.appengine.api import files


class DropboxService:
    def store_file_as_blob(self, dropbox_link):
        response = urllib2.urlopen(dropbox_link)
        data = response.read()                         # TODO In future, read 10Mb at a time rather than entire file
        blob_file_name = files.blobstore.create(mime_type='application/octet-stream')
        with files.open(blob_file_name, 'a') as f:
            f.write(data)
        files.finalize(blob_file_name)
        return files.blobstore.get_blob_key(blob_file_name)
