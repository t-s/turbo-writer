import re
import webapp2
import dao
import ui

email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for project_permission in dao.get_all_project_permissions():
            permissions.append({u'name': project_permission, u'checked': u''})

        # Display the webpage
        self.render(project, permissions)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = u'Email address must be specified'
        elif email_pattern.match(submitted_email):
            # Test whether ProjectUser entity for that email already exists
            if dao.test_email_in_project(project, submitted_email):
                error_msg = u'Already a member of this project: {}'.format(submitted_email)
            else:
                # Attempt to add a new ProjectUser entity
                permissions = list()
                for permission in dao.get_all_project_permissions():
                    if self.request.get(permission):
                        permissions.append(permission)
                if not dao.test_project_permissions(project, [dao.PROJECT_OWN]):
                    if dao.PROJECT_OWN in permissions:
                        webapp2.abort(401)
                try:
                    dao.ProjectUser(email=submitted_email.lower(), parent=project.key, permissions=permissions).put()
                    self.redirect(u'/project_admin/project_user_admin?project_id={}'.format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding user to project failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for project_permission in dao.get_all_project_permissions():
            permission = {u'name': project_permission,
                          u'checked': u'checked' if self.request.get(project_permission) else u''}
            permissions.append(permission)

        # Display the webpage
        self.render(project, permissions, error_msg)

    def render(self, project, permissions, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_user_add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))