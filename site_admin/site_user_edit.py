import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Get specified SiteUser entity
        site_user_id = self.request.get(u'site_user_id')
        site_user = dao.get_site_user_by_id(site_user_id)
        error_msg = None if site_user else u'Unable to access specified site user'

        # Display the webpage
        self.render(site_user_id, site_user, error_msg)

    def post(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

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
            # Attempt to update the SiteUser entity's permissions
            permissions = list()
            for permission in dao.get_all_site_permissions():
                if self.request.get(permission):
                    permissions.append(permission)
            site_user.site_permissions = permissions
            try:
                site_user.put()
                self.redirect(u'/site_admin/site_user_admin')
                return
            except Exception as e:
                error_msg = u'Updating site user failed: {}'.format(e)

        # Display the webpage
        self.render(site_user_id, site_user, error_msg)

    def render(self, site_user_id, site_user, error_msg):
        # Build list of permission checkboxes and whether they should be checked
        permissions = list()
        if site_user:
            for site_permission in dao.get_all_site_permissions():
                permission = {u'name': site_permission, u'checked': u'checked' if site_permission in site_user.site_permissions else u''}
                permissions.append(permission)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/site_user_edit.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'site_user_id'] = site_user_id
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = site_user.email if site_user else u'(unknown)'
        jinja_template_values[u'permissions'] = permissions

        self.response.out.write(jinja_template.render(jinja_template_values))