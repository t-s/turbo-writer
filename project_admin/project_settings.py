import webapp2
from google.appengine.api import users

import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Display the webpage
        self.render(project)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)
        error_msg = None

        # Handle delete request
        if self.request.get(u'delete'):
            if not dao.test_project_permissions(project, [dao.PROJECT_OWN]):
                webapp2.abort(401)
            try:
                dao.delete_project(project)
                self.redirect("/")
                return
            except Exception as e:
                error_msg = u'Deleting project failed: {}'.format(e)

        # Handle update request
        if self.request.get(u'update'):
            current_user = users.get_current_user()
            current_email = current_user.email().lower()
            try:
                name = self.request.get(u'name').strip()
                if name != project.name:
                    if not name:
                        raise Exception(u'You must provide a name for your project')
                    for test_project in dao.get_projects_by_name(name):
                        if dao.test_email_is_project_owner(test_project, current_email):
                            raise Exception(u'Sorry, you already own a different project named \"{}\"'.format(name))
                    project.name = name
                project.description = self.request.get(u'description')
                project.put()
                self.redirect("/project?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating project failed: {}'.format(e)

        # Display the webpage
        self.render(project, error_msg)

    def render(self, project, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_settings.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg

        self.response.out.write(jinja_template.render(jinja_template_values))
