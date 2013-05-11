import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_TEMPLATES):
            webapp2.abort(401)

        jinja_template = ui.get_template(self, u'site_admin/template_admin.html')
        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'templates'] = dao.get_public_templates()
        self.response.out.write(jinja_template.render(jinja_template_values))