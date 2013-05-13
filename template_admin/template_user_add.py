import re
import webapp2
import dao
import ui

email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for template_permission in dao.get_all_template_permissions():
            permissions.append({u'name': template_permission, u'checked': u''})

        # Display the webpage
        self.render(template, permissions)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = u'Email address must be specified'
        elif email_pattern.match(submitted_email):
            # Test whether TemplateUser entity for that email already exists
            if dao.test_email_in_template(template, submitted_email):
                error_msg = u'Already a member of this template: {}'.format(submitted_email)
            else:
                # Attempt to add a new TemplateUser entity
                permissions = list()
                for permission in dao.get_all_template_permissions():
                    if self.request.get(permission):
                        permissions.append(permission)
                try:
                    dao.ProjectUser(email=submitted_email.lower(), parent=template.key, permissions=permissions).put()
                    self.redirect(u'/template_admin/template_user_admin?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding user to template failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for template_permission in dao.get_all_template_permissions():
            permission = {u'name': template_permission,
                          u'checked': u'checked' if self.request.get(template_permission) else u''}
            permissions.append(permission)

        # Display the webpage
        self.render(template, permissions, error_msg)

    def render(self, template, permissions, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template_admin/template_user_add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))