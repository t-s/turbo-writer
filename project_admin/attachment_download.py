from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import webapp2

import dao


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        attachment = dao.get_attachment_by_id(project, self.request.get(u'attachment_id'))
        if not attachment:
            self.response.write(u'Download unsuccessful')

        blob_info = blobstore.BlobInfo.get(attachment.blob_key)
        if blob_info:
            try:
                # Set header so that we can write Unicode body; note that headers must be
                # byte strings, not unicode strings
                self.response.content_type = 'charset=utf-8'
                self.send_blob(attachment.blob_key, save_as=attachment.filename)
                # Set header again, in case cleared by send_blob
                self.response.content_type = 'charset=utf-8'
                self.response.write(u'Download successful')  # TODO Is this needed?
            except:
                self.response.write(u'Download unsuccessful')
        else:
            self.response.write(u'Download unsuccessful')
