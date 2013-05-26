import re
import webapp2
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files
from google.appengine.ext import blobstore

import dao
import ui

indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def generate_html_document(self, project, document):
        inner_template_values = dict()
        inner_template_values[u'project'] = project
        self.generate_variable_values(project, inner_template_values)
        inner_template = ui.from_string(self, document.content)
        return inner_template.render(inner_template_values)

    def generate_variable_values(self, project, inner_template_values):
        indexed_variable_max_indices = dict()
        for variable in dao.get_variables(project):
            indexed_variable_match_object = indexed_name_pattern.match(variable.name)
            if indexed_variable_match_object:
                variable_name = indexed_variable_match_object.group(1)
                variable_index = indexed_variable_match_object.group(2)
                old_max_index = indexed_variable_max_indices[
                    variable_name] if variable_name in indexed_variable_max_indices else None
                if not old_max_index or int(variable_index) > old_max_index:
                    indexed_variable_max_indices[variable_name] = int(variable_index)
            else:
                content = variable.content if variable.content else u''
                inner_template_values[variable.internal_name] = content
        for variable_name in iter(indexed_variable_max_indices):
            count_name = u'{}_count'.format(variable_name)
            # Because of how "range" works, count needs to be max index + 1
            count = int(indexed_variable_max_indices[variable_name]) + 1
            inner_template_values[count_name] = count

    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))

        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        document = dao.get_document_by_id(project, self.request.get(u'document_id'))

        html_document = self.generate_html_document(project, document)

        # Generate blob file
        blob_file_name = files.blobstore.create(mime_type=u'application/octet-stream')
        with files.open(blob_file_name, u'a') as f:
            f.write(html_document)
        files.finalize(blob_file_name)

        # Save blob_key so that it can be deleted later, after document has been downloaded
        if document.blob_key:
            blobstore.delete(document.blob_key)
        document.blob_key = files.blobstore.get_blob_key(blob_file_name)
        document.put()

        filename = u'{}.html'.format(document.internal_name)

        # Set header so that we can write Unicode body; note that headers must be
        # byte strings, not unicode strings
        self.response.content_type = 'charset=utf-8'

        blob_info = blobstore.BlobInfo.get(document.blob_key)
        if blob_info:
            success = True
            try:
                self.send_blob(document.blob_key, save_as=filename)
            except:
                success = False

            # Set header again, in case cleared by send_blob
            self.response.content_type = 'charset=utf-8'
            self.response.write(u'Download {}'.format(u'successful' if success else u'unsuccessful'))
        else:
            self.response.write(u'Download unsuccessful')
