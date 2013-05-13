import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Get specified ProjectUser entity
        project_user_id = self.request.get(u'project_user_id')
        project_user = dao.get_project_user_by_id(project, project_user_id)
        error_msg = None if project_user else u'Unable to access specified project user'

        # Display the webpage
        self.render(project, project_user_id, project_user, error_msg)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Get specified ProjectUser entity
        project_user_id = self.request.get(u'project_user_id')
        project_user = dao.get_project_user_by_id(project, project_user_id)
        error_msg = None if project_user else u'Unable to access specified project user'

        # Handle delete request
        if project_user and self.request.get(u'delete'):
            try:
                self.require_owner(project, exclude_user=project_user)
                project_user.key.delete()
                self.redirect(u'/project_admin/project_user_admin?project_id={}'.format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting project user failed: {}'.format(e)

        # Handle update request
        if project_user and self.request.get(u'update'):
            # Attempt to update the ProjectUser entity's permissions
            permissions = list()
            for permission in dao.get_all_project_permissions():
                if self.request.get(permission):
                    permissions.append(permission)
            if not dao.test_project_permissions(project, [dao.PROJECT_OWN]):
                if (dao.PROJECT_OWN in project_user.permissions and dao.PROJECT_OWN not in permissions) or (
                        dao.PROJECT_OWN not in project_user.permissions and dao.PROJECT_OWN in permissions):
                    webapp2.abort(401)
            project_user.permissions = permissions
            try:
                self.require_owner(project)
                project_user.put()
                self.redirect(u'/project_admin/project_user_admin?project_id={}'.format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating project user failed: {}'.format(e)

        # Display the webpage
        self.render(project, project_user_id, project_user, error_msg)

    def render(self, project, project_user_id, project_user, error_msg):
        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        if project_user:
            for project_permission in dao.get_all_project_permissions():
                permission = {u'name': project_permission,
                              u'checked': u'checked' if project_permission in project_user.permissions else u''}
                permissions.append(permission)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/project_user_edit.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'project_user_id'] = project_user_id
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = project_user.email if project_user else u'(unknown)'
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))

    def require_owner(self, project, exclude_user=None):
        any_owner = False
        for user in dao.get_project_users(project):
            if exclude_user and user == exclude_user:
                continue
            if dao.PROJECT_OWN in user.permissions:
                any_owner = True
                break
        if not any_owner:
            raise Exception("Project must have an owner")
