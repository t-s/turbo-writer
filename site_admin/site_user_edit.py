import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Get specified SiteUser entity
        site_user_id = self.request.get("site_user_id")
        site_user = dao.get_site_user_by_id(site_user_id)
        error_msg = None if site_user else "Unable to access specified site user"

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
        site_user_id = self.request.get("site_user_id")
        site_user = dao.get_site_user_by_id(site_user_id)
        error_msg = None if site_user else "Unable to access specified site user"

        # Handle delete request
        if site_user and self.request.get("delete"):
            try:
                site_user.key.delete()
                self.redirect("/site_admin/site_user_admin")
                return
            except Exception as e:
                error_msg = "Deleting site user failed: {}".format(e)

        # Handle update request
        if site_user and self.request.get("update"):
            # Attempt to update the SiteUser entity's roles
            site_roles = list()
            for site_role in site_role_list:
                if self.request.get(site_role):
                    site_roles.append(site_role)
            site_user.site_roles = site_roles
            try:
                site_user.put()
                self.redirect("/site_admin/site_user_admin")
                return
            except Exception as e:
                error_msg = "Updating site user failed: {}".format(e)

        # Display the webpage
        self.render(site_user_id, site_user, site_role_list, error_msg)

    def render(self, site_user_id, site_user, site_role_list, error_msg):
        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        if site_user:
            for site_role in site_role_list:
                role = {"name": site_role, "checked": "checked" if site_role in site_user.site_roles else ""}
                view_role_list.append(role)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "site_admin/site_user_edit.html")

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values["site_user_id"] = site_user_id
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["email"] = site_user.email if site_user else "(unknown)"
        jinja_template_values["roles"] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))