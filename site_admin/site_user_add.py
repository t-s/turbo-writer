import re
import webapp2
import dao
import ui

email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Build list of SiteRoles from the datastore
        site_role_list = dao.get_site_roles()

        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        for site_role in site_role_list:
            role = {u'name': site_role, u'checked': False}
            view_role_list.append(role)

        # Display the webpage
        self.render(view_role_list)

    def post(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Build list of SiteRoles from the datastore
        site_role_list = dao.get_site_roles()

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = None
        elif email_pattern.match(submitted_email):
            # Test whether SiteUser entity for that email already exists
            if dao.test_email_registered(submitted_email):
                error_msg = u'Already registered at this site: {}'.format(submitted_email)
            else:
                # Attempt to add a new SiteUser entity
                site_roles = list()
                for site_role in site_role_list:
                    if self.request.get(site_role):
                        site_roles.append(site_role)
                try:
                    dao.SiteUser(email=submitted_email.lower(), site_roles=site_roles).put()
                    self.redirect(u'/site_admin/site_user_admin')
                    return
                except Exception as e:
                    error_msg = u'Adding user to site failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        for site_role in site_role_list:
            role = {u'name': site_role, u'checked': self.request.get(site_role)}
            view_role_list.append(role)

        # Display the webpage
        self.render(view_role_list, error_msg)

    def render(self, view_role_list, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/site_user_add.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'roles'] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))