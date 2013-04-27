import StringIO
import re
import zipfile

from google.appengine.api import files
from google.appengine.ext import blobstore

blob_key_pattern = re.compile(r'(.*)-->\n\[Insert "(.*)" here\].*')


class DocumentService:
    def generate_document(self, document, html_document):
        file_string = self.generate_zip(document, html_document)
        blob_file_name = files.blobstore.create(mime_type=u'application/octet-stream')
        with files.open(blob_file_name, u'a') as f:
            f.write(file_string)
        files.finalize(blob_file_name)
        if document.blob_key:
            blobstore.delete(document.blob_key)
        document.blob_key = files.blobstore.get_blob_key(blob_file_name)
        document.filename = u'{}.zip'.format(document.internal_name)
        document.put()

    def generate_zip(self, document, html_document):
        output_string = StringIO.StringIO()
        with zipfile.ZipFile(output_string, u'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(u'{}.html'.format(document.internal_name), html_document.encode(u'utf-8'))
            attachments = self.generate_attachments(html_document)
            if attachments:
                zip_file.writestr(u'attachments.zip', attachments)
        return output_string.getvalue()

    def generate_attachments(self, html_document):
        b_key_segments = html_document.split(u'\n<!--B-KEY:')[1:]  # Ignore text in front of first blob_key
        if b_key_segments:
            output_string = StringIO.StringIO()
            with zipfile.ZipFile(output_string, u'w', zipfile.ZIP_DEFLATED) as zip_file:
                for b_key_segment in b_key_segments:
                    match = blob_key_pattern.match(b_key_segment)
                    if match:
                        blob_reader = blobstore.BlobReader(match.group(1))
                        zip_file.writestr(match.group(2), blob_reader.read())
            return output_string.getvalue()
