import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        jinja_template = ui.get_template(self, u'template/index.html')
        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'template'] = template
        self.response.out.write(jinja_template.render(jinja_template_values))
