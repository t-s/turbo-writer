import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(template, self.request.get(u'style_id'))
        error_msg = None if style_entity else u'Unable to access specified style'

        # Display the webpage
        self.render(template, style_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(template, self.request.get(u'style_id'))
        error_msg = None if style_entity else u'Unable to access specified style'

        # Handle delete request
        if style_entity and self.request.get(u'delete'):
            try:
                style_entity.key.delete()
                self.redirect(u'/template/style?template_id={}'.format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting style from template failed: {}'.format(e)

        # Handle update request
        if style_entity and self.request.get(u'update'):
            try:
                style_entity.description = self.request.get(u'description')
                style_entity.css = self.request.get(u'css')
                style_entity.put()
                self.redirect(u'/template/style?template_id={}'.format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating style failed: {}'.format(e)

        # Display the webpage
        self.render(template, style_entity, error_msg)

    def render(self, template, style_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/style/edit.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'style_id'] = style_entity.key.id()
        jinja_template_values[u'name'] = style_entity.name
        jinja_template_values[u'description'] = style_entity.description
        jinja_template_values[u'css'] = style_entity.css

        self.response.out.write(jinja_template.render(jinja_template_values))