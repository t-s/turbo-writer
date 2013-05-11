import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/site_user_admin.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'users'] = dao.get_site_users()

        self.response.out.write(jinja_template.render(jinja_template_values))
