import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        site_role_list = dao.get_site_roles()

        user_list = list()

        for site_user in dao.get_site_users():
            user = dict()
            user["site_user_id"] = site_user.key.id()
            user["email"] = site_user.email
            for site_role in site_role_list:
                user[site_role] = "YES" if site_role in site_user.site_roles else "NO"
            user_list.append(user)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "site_admin/site_user_admin.html")

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values["roles"] = site_role_list
        jinja_template_values["role_count"] = len(site_role_list)
        jinja_template_values["users"] = user_list

        self.response.out.write(jinja_template.render(jinja_template_values))