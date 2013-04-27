import urllib

import webapp2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import dao
import ui

from service.interview_service import InterviewService


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'_project_id'))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        interview_service = InterviewService(project)
        interview_name = self.request.get(u'_interview_name')
        interview = interview_service.get_interview_by_name(interview_name)

        variable = dao.get_variable_by_internal_name(project, self.request.get(u'_variable_name'))

        index = self.request.get(u'_index')

        # Deliver HTTP response
        jinja_template = ui.get_template(self, u'project/upload_file.html')
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'project'] = project
        jinja_template_values[u'interview'] = interview
        jinja_template_values[u'variable'] = variable
        if index:
            jinja_template_values[u'show_index'] = True
            jinja_template_values[u'index'] = index

        jinja_template_values[u'upload_file_post_url'] = blobstore.create_upload_url('/project/upload_file_post')

        self.response.out.write(jinja_template.render(jinja_template_values))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        project = dao.get_project_by_id(self.request.get(u'_project_id'))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        interview_name = self.request.get(u'_interview_name')

        index = self.request.get(u'_index')

        blobs_info = self.get_uploads(u'upload_file')
        if blobs_info:
            blob_info = blobs_info[0]
            name = self.request.get(u'_variable_name')
            variable_name = u'{}[{}]'.format(name, index) if index else name
            dao.set_variable_blob_key(project, variable_name, blob_info.key())

        query_string_dict = {u'_project_id': project.key.id(),
                             u'_interview_name': interview_name.encode(u'utf-8')}
        if index:
            query_string_dict[u'_index'] = index
        query_string = urllib.urlencode(query_string_dict)
        url = u'/project/conduct_interview?{}'.format(query_string)
        self.redirect(url)


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        # Set header so that we can write Unicode body; note that headers must be
        # byte strings, not unicode strings
        self.response.content_type = 'charset=utf-8'

        blob_info = blobstore.BlobInfo.get(blob_key)
        if blob_info:
            try:
                self.send_blob(blob_key, save_as=self.request.get(u'filename'))
                # Set header again, in case cleared by send_blob
                self.response.content_type = 'charset=utf-8'
                self.response.write(u'Download successful')
            except:
                self.response.write(u'Download unsuccessful')
        else:
            self.response.write(u'Download unsuccessful')
