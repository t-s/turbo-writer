import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_user_admin.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'users'] = dao.get_project_users(project)

        self.response.out.write(jinja_template.render(jinja_template_values))
