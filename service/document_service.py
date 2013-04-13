import StringIO
import re
import zipfile

from google.appengine.api import files
from google.appengine.ext import blobstore

blob_key_pattern = re.compile(r"(.*)-->\n\[Insert \"(.*)\" here\].*")


class DocumentService:
    def generate_document(self, project, document, html_document):
        file_string = self.generate_zip(document, html_document)
        blob_file_name = files.blobstore.create(mime_type='application/octet-stream')
        with files.open(blob_file_name, 'a') as f:
            f.write(file_string)
        files.finalize(blob_file_name)
        if document.blob_key:
            blobstore.delete(document.blob_key)
        document.blob_key = files.blobstore.get_blob_key(blob_file_name)
        document.filename = "{}.zip".format(document.internal_name)
        document.put()

    def generate_zip(self, document, html_document):
        output_string = StringIO.StringIO()
        with zipfile.ZipFile(output_string, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("{}.html".format(document.internal_name), html_document)
            zip_file.writestr("attachments.zip", self.generate_attachments(document, html_document))
        return output_string.getvalue()

    def generate_attachments(self, document, html_document):
        output_string = StringIO.StringIO()
        with zipfile.ZipFile(output_string, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for b_key_segment in html_document.split("\n<!--B-KEY:")[1:]: # Ignore text in front of first blob_key
                match = blob_key_pattern.match(b_key_segment)
                if match:
                    blob_reader = blobstore.BlobReader(match.group(1))
                    zip_file.writestr(match.group(2), blob_reader.read())
        return output_string.getvalue()

