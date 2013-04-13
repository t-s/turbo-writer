import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import dao
import ui
from service.interview_service import InterviewService


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get("_project_id"))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        interview_service = InterviewService(project)
        interview_name = self.request.get("_interview_name")
        interview = interview_service.get_interview_by_name(interview_name)

        variable = dao.get_variable_by_internal_name(project, self.request.get("_variable_name"))

        index = self.request.get("_index")

        # Deliver HTTP response
        jinja_template = ui.get_template(self, "project/upload_file.html")
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["project"] = project
        jinja_template_values["interview"] = interview
        jinja_template_values["variable"] = variable
        if index:
            jinja_template_values["show_index"] = True
            jinja_template_values["index"] = str(index)

        jinja_template_values["upload_file_post_url"] = blobstore.create_upload_url('/project/upload_file_post')

        self.response.out.write(jinja_template.render(jinja_template_values))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        project = dao.get_project_by_id(self.request.get("_project_id"))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        interview_service = InterviewService(project)
        interview_name = self.request.get("_interview_name")
        interview = interview_service.get_interview_by_name(interview_name)

        index = self.request.get("index")

        blobs_info = self.get_uploads("upload_file")
        if blobs_info:
            blob_info = blobs_info[0]
            name = self.request.get("_variable_name")
            variable_name = "{}[{}]".format(name, index) if index else name
            dao.set_variable_blob_key(project, variable_name, blob_info.key())

        suffix = "&_index={}".format(index) if index else ""
        self.redirect(
            "/project/conduct_interview?_project_id={}&_interview_name={}{}".format(project.key.id(), interview.name,
                                                                                    suffix))


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
