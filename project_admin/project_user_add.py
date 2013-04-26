import re
import webapp2
import dao
import ui


email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permitted(
                project):  # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        for project_role in project_role_list:
            role = {u'name': project_role, u'checked': False}
            view_role_list.append(role)

        # Display the webpage
        self.render(project, view_role_list)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permitted(
                project):  # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = None
        elif email_pattern.match(submitted_email):
            if dao.test_email_in_project(project, submitted_email):
                error_msg = u'Already a member of this project team: {}'.format(submitted_email)
            else:
                # Attempt to add a new ProjectUser entity
                project_roles = list()
                for project_role in project_role_list:
                    if self.request.get(project_role):
                        project_roles.append(project_role)
                try:
                    dao.ProjectUser(email=submitted_email.lower(), parent=project.key).put()
                    self.redirect(u'/project_admin/project_user_admin?project_id={}'.format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding member to project team failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of project role checkboxes and whether they should be checked
        view_role_list = list()
        for project_role in project_role_list:
            role = {u'name': project_role, u'checked': self.request.get(project_role)}
            view_role_list.append(role)

        # Display the webpage
        self.render(project, view_role_list, error_msg)

    def render(self, project, view_role_list, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_user_add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'roles'] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))