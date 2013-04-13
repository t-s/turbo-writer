from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_info = blobstore.BlobInfo.get(blob_key)
        if blob_info:
            try:
                self.send_blob(blob_key, save_as=self.request.get("filename"))
                self.response.write("Download successful")
            except:
                self.response.write("Download unsuccessful")
        else:
            self.response.write("Download unsuccessful")
