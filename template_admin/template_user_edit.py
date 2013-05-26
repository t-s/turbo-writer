import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Get specified ProjectUser entity
        template_user_id = self.request.get(u'template_user_id')
        template_user = dao.get_template_user_by_id(template, template_user_id)
        error_msg = None if template_user else u'Unable to access specified template user'

        # Display the webpage
        self.render(template, template_user_id, template_user, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Get specified TemplateUser entity
        template_user_id = self.request.get(u'template_user_id')
        template_user = dao.get_template_user_by_id(template, template_user_id)
        error_msg = None if template_user else u'Unable to access specified template user'

        # Handle delete request
        if template_user and self.request.get(u'delete'):
            try:
                self.require_owner(template, exclude_user=template_user)
                template_user.key.delete()
                self.redirect("/template_admin/template_user_admin?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting template user failed: {}'.format(e)

        # Handle update request
        if template_user and self.request.get(u'update'):
            # Attempt to update the TemplateUser entity's permissions
            permissions = list()
            for permission in dao.get_all_template_permissions():
                if self.request.get(permission):
                    permissions.append(permission)
            if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN]):
                if (dao.TEMPLATE_OWN in template_user.permissions and dao.TEMPLATE_OWN not in permissions) or (
                            dao.TEMPLATE_OWN not in template_user.permissions and dao.TEMPLATE_OWN in permissions):
                    webapp2.abort(401)
            template_user.permissions = permissions
            try:
                self.require_owner(template)
                template_user.put()
                self.redirect("/template_admin/template_user_admin?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating template user failed: {}'.format(e)

        # Display the webpage
        self.render(template, template_user_id, template_user, error_msg)

    def render(self, template, template_user_id, template_user, error_msg):
        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        if template_user:
            for template_permission in dao.get_all_template_permissions():
                permission = {u'name': template_permission, u'checked': u'checked' if template_permission in template_user.permissions else u''}
                permissions.append(permission)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template_admin/template_user_edit.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'template_user_id'] = template_user_id
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = template_user.email if template_user else u'(unknown)'
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))

    def require_owner(self, template, exclude_user=None):
        any_owner = False
        for user in dao.get_template_users(template):
            if exclude_user and user == exclude_user:
                continue
            if dao.TEMPLATE_OWN in user.permissions:
                any_owner = True
                break
        if not any_owner:
            raise Exception("Template must have an owner")
