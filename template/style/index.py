import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)
        style_list = list()

        for style_entity in dao.get_styles(template):
            style = dict()
            style[u'id'] = style_entity.key.id()
            style[u'name'] = style_entity.name
            style[u'description'] = style_entity.description
            style[u'css'] = style_entity.css
            style_list.append(style)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/style/index.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'styles'] = style_list

        self.response.out.write(jinja_template.render(jinja_template_values))