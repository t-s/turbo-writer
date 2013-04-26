import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Get specified SiteUser entity
        site_user_id = self.request.get(u'site_user_id')
        site_user = dao.get_site_user_by_id(site_user_id)
        error_msg = None if site_user else u'Unable to access specified site user'

        # Build list of SiteRoles from the datastore
        site_role_list = dao.get_site_roles()

        # Display the webpage
        self.render(site_user_id, site_user, site_role_list, error_msg)

    def post(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Build list of SiteRoles from the datastore
        site_role_list = dao.get_site_roles()

        # Get specified SiteUser entity
        site_user_id = self.request.get(u'site_user_id')
        site_user = dao.get_site_user_by_id(site_user_id)
        error_msg = None if site_user else u'Unable to access specified site user'

        # Handle delete request
        if site_user and self.request.get(u'delete'):
            try:
                site_user.key.delete()
                self.redirect(u'/site_admin/site_user_admin')
                return
            except Exception as e:
                error_msg = u'Deleting site user failed: {}'.format(e)

        # Handle update request
        if site_user and self.request.get(u'update'):
            # Attempt to update the SiteUser entity's roles
            site_roles = list()
            for site_role in site_role_list:
                if self.request.get(site_role):
                    site_roles.append(site_role)
            site_user.site_roles = site_roles
            try:
                site_user.put()
                self.redirect(u'/site_admin/site_user_admin')
                return
            except Exception as e:
                error_msg = u'Updating site user failed: {}'.format(e)

        # Display the webpage
        self.render(site_user_id, site_user, site_role_list, error_msg)

    def render(self, site_user_id, site_user, site_role_list, error_msg):
        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        if site_user:
            for site_role in site_role_list:
                role = {u'name': site_role, u'checked': u'checked' if site_role in site_user.site_roles else u''}
                view_role_list.append(role)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/site_user_edit.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'site_user_id'] = site_user_id
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = site_user.email if site_user else u'(unknown)'
        jinja_template_values[u'roles'] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))