import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINSETTINGS):
            webapp2.abort(401)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "site_admin/site_settings.html")
        jinja_template_values = dao.get_standard_site_values()
        self.response.out.write(jinja_template.render(jinja_template_values))