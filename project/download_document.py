from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_info = blobstore.BlobInfo.get(blob_key)
        if blob_info:
            try:
                filename = self.request.get(u'filename')
                self.send_blob(blob_key, save_as=filename)
                self.response.write('Download successful')  # Writing Unicode string throws exception
            except:
                self.response.write('Download unsuccessful')  # Writing Unicode string throws exception
        else:
            self.response.write('Download unsuccessful')  # Writing Unicode string throws exception
