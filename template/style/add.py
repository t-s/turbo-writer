import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Display the webpage
        self.render(template)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        name = self.request.get(u'name')
        description = self.request.get(u'description')
        css = self.request.get(u'css')

        if not name:
            error_msg = u'You must specify a name for your style definition'
        else:
            style_entity = dao.get_style_by_name(template, name)
            if style_entity:
                error_msg = u'Adding style failed: Duplicate style name in template'
            else:
                try:
                    dao.Style(name=name, description=description, css=css, parent=template.key).put()
                    self.redirect(u'/template/style?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding style failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/style/add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'css'] = self.request.get(u'css')

        self.response.out.write(jinja_template.render(jinja_template_values))