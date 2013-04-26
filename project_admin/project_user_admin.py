import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permitted(
                project):  # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        project_role_list = list()

        user_list = list()

        for project_user in dao.get_project_users(project):
            user = dict()
            user[u'project_user_id'] = project_user.key.id()
            user[u'email'] = project_user.email
            for project_role in project_role_list:
                user[project_role] = u'YES' if project_role in project_user.site_roles else u'NO'
            user_list.append(user)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_user_admin.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'roles'] = project_role_list
        jinja_template_values[u'role_count'] = len(project_role_list)
        jinja_template_values[u'users'] = user_list

        self.response.out.write(jinja_template.render(jinja_template_values))