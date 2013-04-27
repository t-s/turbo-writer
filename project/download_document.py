from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        # Set header so that we can write Unicode body; note that headers must be
        # byte strings, not unicode strings
        self.response.content_type = 'charset=utf-8'

        blob_info = blobstore.BlobInfo.get(blob_key)
        if blob_info:
            try:
                filename = self.request.get(u'filename')
                self.send_blob(blob_key, save_as=filename)
                # Set header again, in case cleared by send_blob
                self.response.content_type = 'charset=utf-8'
                self.response.write(u'Download successful')
            except:
                self.response.write(u'Download unsuccessful')
        else:
            self.response.write(u'Download unsuccessful')
