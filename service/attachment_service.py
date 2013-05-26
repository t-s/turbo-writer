import StringIO
import zipfile

from google.appengine.api import files
from google.appengine.ext import blobstore

import dao


class AttachmentService:
    def generate_attachments(self, project):
        file_string = self.generate_attachments_zip(project)
        blob_file_name = files.blobstore.create(mime_type=u'application/octet-stream')
        with files.open(blob_file_name, u'a') as f:
            f.write(file_string)
        files.finalize(blob_file_name)
        if project.blob_key:
            blobstore.delete(project.blob_key)
        project.blob_key = files.blobstore.get_blob_key(blob_file_name)
        project.filename = u'{}.zip'.format(project.internal_name)
        project.put()

    def generate_attachments_zip(self, project):
        output_string = StringIO.StringIO()
        with zipfile.ZipFile(output_string, u'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in dao.get_attachments_by_project(project):
                blob_reader = blobstore.BlobReader(attachment.blob_key)
                zip_file.writestr(attachment.filename, blob_reader.read())
        return output_string.getvalue()
