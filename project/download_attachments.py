import re
import StringIO
import zipfile

import webapp2
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files
from google.appengine.ext import blobstore

import dao


indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))

        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        zipfile_string = self.generate_attachments(project)

        # Generate blob file
        blob_file_name = files.blobstore.create(mime_type=u'application/octet-stream')
        with files.open(blob_file_name, u'a') as f:
            f.write(zipfile_string)
        files.finalize(blob_file_name)

        # Save blob_key so that it can be deleted later, after document has been downloaded
        if project.attachments_blob_key:
            blobstore.delete(project.attachments_blob_key)
        project.attachments_blob_key = files.blobstore.get_blob_key(blob_file_name)
        project.put()

        filename = u'attachments.zip'

        # Set header so that we can write Unicode body; note that headers must be
        # byte strings, not unicode strings
        self.response.content_type = 'charset=utf-8'

        blob_info = blobstore.BlobInfo.get(project.attachments_blob_key)
        if blob_info:
            success = True
            try:
                self.send_blob(project.attachments_blob_key, save_as=filename)
            except:
                success = False

            # Set header again, in case cleared by send_blob
            self.response.content_type = 'charset=utf-8'
            self.response.write(u'Download {}'.format(u'successful' if success else u'unsuccessful'))
        else:
            self.response.write(u'Download unsuccessful')

    def generate_attachments(self, project):
        output_string = StringIO.StringIO()
        with zipfile.ZipFile(output_string, u'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in dao.get_attachments_by_project(project):
                blob_reader = blobstore.BlobReader(attachment.blob_key)
                zip_file.writestr(attachment.filename, blob_reader.read())
        return output_string.getvalue()
