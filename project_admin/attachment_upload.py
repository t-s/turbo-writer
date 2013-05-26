import urllib

import webapp2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        attachment = dao.get_attachment_by_id(project, self.request.get(u'attachment_id'))

        # Deliver HTTP response
        jinja_template = ui.get_template(self, u'project_admin/attachment_upload.html')
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'attachment'] = attachment
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'attachment_upload_post_url'] = blobstore.create_upload_url(
            u'/project_admin/attachment_upload_post')

        self.response.out.write(jinja_template.render(jinja_template_values))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        attachment = dao.get_attachment_by_id(project, self.request.get(u'attachment_id'))

        blobs_info = self.get_uploads(u'upload_file')
        if blobs_info:
            blob_info = blobs_info[0]
            dao.set_attachment_blob_key(attachment, blob_info.key(), blob_info.filename)

        self.redirect("/project_admin/attachment_admin?project_id={}".format(project.key.id()))
