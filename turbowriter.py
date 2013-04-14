import webapp2
from google.appengine.api import users

import dao
import ui
import project
import template
from my_account import *
from project_admin import *
from site_admin import *
from template_admin import *


class MainPage(webapp2.RequestHandler):
    def get(self):
        if dao.test_current_user_registered():
            jinja_template = ui.get_template(self, "index.html")
            jinja_template_values = dao.get_standard_site_values()
        elif users.get_current_user():
            jinja_template = ui.get_template(self, "register.html")
            jinja_template_values = dao.get_standard_site_values()
        else:
            jinja_template = ui.get_template(self, "login.html")
            jinja_template_values = {"url": users.create_login_url(self.request.uri)}

        self.response.out.write(jinja_template.render(jinja_template_values))


class Synopsis(webapp2.RequestHandler):
    def get(self):
        jinja_template = ui.get_template(self, "synopsis.html")
        jinja_template_values = dao.get_standard_site_values()
        self.response.out.write(jinja_template.render(jinja_template_values))

# Start the application

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

app.router.add(("/synopsis", Synopsis))

app.router.add(("/my_account/preferences", preferences.RequestHandler))

app.router.add(("/project", project.index.RequestHandler))
app.router.add(("/project/conduct_interview", project.conduct_interview.RequestHandler))
app.router.add(("/project/download_file/([^/]+)?", project.upload_file.DownloadHandler))
app.router.add(("/project/download_document/([^/]+)?", project.download_document.DownloadHandler))
app.router.add(("/project/produce_document", project.produce_document.RequestHandler))
app.router.add(("/project/upload_file", project.upload_file.RequestHandler))
app.router.add(("/project/upload_file_post", project.upload_file.UploadHandler))

app.router.add(("/project_admin/new_project", new_project.RequestHandler))
app.router.add(("/project_admin/new_project_based_on_template", new_project_based_on_template.RequestHandler))
app.router.add(("/project_admin/project_settings", project_settings.RequestHandler))
app.router.add(("/project_admin/project_user_admin", project_user_admin.RequestHandler))
app.router.add(("/project_admin/project_user_add", project_user_add.RequestHandler))
app.router.add(("/project_admin/project_user_edit", project_user_edit.RequestHandler))

app.router.add(("/site_admin/site_settings", site_settings.RequestHandler))
app.router.add(("/site_admin/template_admin", template_admin.RequestHandler))
app.router.add(("/site_admin/template_add", template_add.RequestHandler))
app.router.add(("/site_admin/template_edit", template_edit.RequestHandler))
app.router.add(("/site_admin/site_user_admin", site_user_admin.RequestHandler))
app.router.add(("/site_admin/site_user_add", site_user_add.RequestHandler))
app.router.add(("/site_admin/site_user_edit", site_user_edit.RequestHandler))

app.router.add(("/template", template.index.RequestHandler))

app.router.add(("/template/assignment", template.assignment.index.RequestHandler))
app.router.add(("/template/assignment/add", template.assignment.add.RequestHandler))
app.router.add(("/template/assignment/edit", template.assignment.edit.RequestHandler))
app.router.add(("/template/assignment/structure", template.assignment.structure.RequestHandler))

app.router.add(("/template/document", template.document.index.RequestHandler))
app.router.add(("/template/document/add", template.document.add.RequestHandler))
app.router.add(("/template/document/edit", template.document.edit.RequestHandler))
app.router.add(("/template/document/structure", template.document.structure.RequestHandler))

app.router.add(("/template/style", template.style.index.RequestHandler))
app.router.add(("/template/style/add", template.style.add.RequestHandler))
app.router.add(("/template/style/edit", template.style.edit.RequestHandler))

app.router.add(("/template/variable", template.variable.index.RequestHandler))
app.router.add(("/template/variable/add", template.variable.add.RequestHandler))
app.router.add(("/template/variable/edit", template.variable.edit.RequestHandler))

app.router.add(("/template_admin/new_template", new_template.RequestHandler))
app.router.add(("/template_admin/template_settings", template_settings.RequestHandler))
app.router.add(("/template_admin/template_user_admin", template_user_admin.RequestHandler))
app.router.add(("/template_admin/template_user_add", template_user_add.RequestHandler))
app.router.add(("/template_admin/template_user_edit", template_user_edit.RequestHandler))
