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
            jinja_template = ui.get_template(self, u'index.html')
            jinja_template_values = dao.get_standard_site_values()
        elif users.get_current_user():
            jinja_template = ui.get_template(self, u'register.html')
            jinja_template_values = dao.get_standard_site_values()
        else:
            jinja_template = ui.get_template(self, u'login.html')
            jinja_template_values = {u'url': users.create_login_url(self.request.uri)}

        self.response.out.write(jinja_template.render(jinja_template_values))


class Synopsis(webapp2.RequestHandler):
    def get(self):
        jinja_template = ui.get_template(self, u'synopsis.html')
        jinja_template_values = dao.get_standard_site_values()
        self.response.out.write(jinja_template.render(jinja_template_values))

# Start the application

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

app.router.add((u'/synopsis', Synopsis))

app.router.add((u'/my_account/preferences', preferences.RequestHandler))

app.router.add((u'/project', project.index.RequestHandler))
app.router.add((u'/project/conduct_interview', project.conduct_interview.RequestHandler))
app.router.add((u'/project/download_file/([^/]+)?', project.upload_file.DownloadHandler))
app.router.add((u'/project/download_document/([^/]+)?', project.download_document.DownloadHandler))
app.router.add((u'/project/produce_document', project.produce_document.RequestHandler))
app.router.add((u'/project/upload_file', project.upload_file.RequestHandler))
app.router.add((u'/project/upload_file_post', project.upload_file.UploadHandler))

app.router.add((u'/project/assignment', project.assignment.index.RequestHandler))
app.router.add((u'/project/assignment/add', project.assignment.add.RequestHandler))
app.router.add((u'/project/assignment/edit', project.assignment.edit.RequestHandler))
app.router.add((u'/project/assignment/structure', project.assignment.structure.RequestHandler))

app.router.add((u'/project/document', project.document.index.RequestHandler))
app.router.add((u'/project/document/add', project.document.add.RequestHandler))
app.router.add((u'/project/document/edit', project.document.edit.RequestHandler))
app.router.add((u'/project/document/structure', project.document.structure.RequestHandler))

app.router.add((u'/project/style', project.style.index.RequestHandler))
app.router.add((u'/project/style/add', project.style.add.RequestHandler))
app.router.add((u'/project/style/edit', project.style.edit.RequestHandler))

app.router.add((u'/project/variable', project.variable.index.RequestHandler))
app.router.add((u'/project/variable/add', project.variable.add.RequestHandler))
app.router.add((u'/project/variable/edit', project.variable.edit.RequestHandler))

app.router.add((u'/project_admin/new_project', new_project.RequestHandler))
app.router.add((u'/project_admin/new_project_based_on_template', new_project_based_on_template.RequestHandler))
app.router.add((u'/project_admin/project_settings', project_settings.RequestHandler))
app.router.add((u'/project_admin/project_user_admin', project_user_admin.RequestHandler))
app.router.add((u'/project_admin/project_user_add', project_user_add.RequestHandler))
app.router.add((u'/project_admin/project_user_edit', project_user_edit.RequestHandler))

app.router.add((u'/site_admin/site_settings', site_settings.RequestHandler))
app.router.add((u'/site_admin/template_admin', template_admin.RequestHandler))
app.router.add((u'/site_admin/template_add', template_add.RequestHandler))
app.router.add((u'/site_admin/template_edit', template_edit.RequestHandler))
app.router.add((u'/site_admin/site_user_admin', site_user_admin.RequestHandler))
app.router.add((u'/site_admin/site_user_add', site_user_add.RequestHandler))
app.router.add((u'/site_admin/site_user_edit', site_user_edit.RequestHandler))

app.router.add((u'/template', template.index.RequestHandler))

app.router.add((u'/template/assignment', template.assignment.index.RequestHandler))
app.router.add((u'/template/assignment/add', template.assignment.add.RequestHandler))
app.router.add((u'/template/assignment/edit', template.assignment.edit.RequestHandler))
app.router.add((u'/template/assignment/structure', template.assignment.structure.RequestHandler))

app.router.add((u'/template/document', template.document.index.RequestHandler))
app.router.add((u'/template/document/add', template.document.add.RequestHandler))
app.router.add((u'/template/document/edit', template.document.edit.RequestHandler))
app.router.add((u'/template/document/structure', template.document.structure.RequestHandler))

app.router.add((u'/template/style', template.style.index.RequestHandler))
app.router.add((u'/template/style/add', template.style.add.RequestHandler))
app.router.add((u'/template/style/edit', template.style.edit.RequestHandler))

app.router.add((u'/template/variable', template.variable.index.RequestHandler))
app.router.add((u'/template/variable/add', template.variable.add.RequestHandler))
app.router.add((u'/template/variable/edit', template.variable.edit.RequestHandler))

app.router.add((u'/template_admin/new_template', new_template.RequestHandler))
app.router.add((u'/template_admin/template_settings', template_settings.RequestHandler))
app.router.add((u'/template_admin/template_user_admin', template_user_admin.RequestHandler))
app.router.add((u'/template_admin/template_user_add', template_user_add.RequestHandler))
app.router.add((u'/template_admin/template_user_edit', template_user_edit.RequestHandler))
