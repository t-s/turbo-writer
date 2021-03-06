import re
import webapp2
import dao
import ui

email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for site_permission in dao.get_all_site_permissions():
            permissions.append({u'name': site_permission, u'checked': u''})

        # Display the webpage
        self.render(permissions)

    def post(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = u'Email address must be specified'
        elif email_pattern.match(submitted_email):
            # Test whether SiteUser entity for that email already exists
            if dao.test_email_registered(submitted_email):
                error_msg = u'Already registered at this site: {}'.format(submitted_email)
            else:
                # Attempt to add a new SiteUser entity
                permissions = list()
                for permission in dao.get_all_site_permissions():
                    if self.request.get(permission):
                        permissions.append(permission)
                try:
                    dao.SiteUser(email=submitted_email.lower(), site_permissions=permissions).put()
                    self.redirect("/site_admin/site_user_admin")
                    return
                except Exception as e:
                    error_msg = u'Adding user to site failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        for site_permission in dao.get_all_site_permissions():
            permission = {u'name': site_permission,
                          u'checked': u'checked' if self.request.get(site_permission) else u''}
            permissions.append(permission)

        # Display the webpage
        self.render(permissions, error_msg)

    def render(self, permissions, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/site_user_add.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))