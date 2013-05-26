import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        variable_entity = dao.get_variable_by_id(template, self.request.get(u'variable_id'))
        error_msg = None if variable_entity else u'Unable to access specified variable'

        # Display the webpage
        self.render(template, variable_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        variable_entity = dao.get_variable_by_id(template, self.request.get(u'variable_id'))
        error_msg = None if variable_entity else u'Unable to access specified variable'

        # Handle delete request
        if variable_entity and self.request.get(u'delete'):
            try:
                variable_entity.key.delete()
                self.redirect("/template/variable?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting variable from template failed: {}'.format(e)

        # Handle update request
        if variable_entity and self.request.get(u'update'):
            try:
                variable_entity.description = self.request.get(u'description')
                variable_entity.is_repeating = (self.request.get(u'type') == u'repeating')
                variable_entity.input_field = self.request.get(u'input_field')
                variable_entity.put()
                self.redirect("/template/variable?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating variable failed: {}'.format(e)

        # Display the webpage
        self.render(template, variable_entity, error_msg)

    def render(self, template, variable_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/variable/edit.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'variable_id'] = variable_entity.key.id()
        jinja_template_values[u'name'] = variable_entity.name
        jinja_template_values[u'description'] = variable_entity.description
        jinja_template_values[u'type'] = u'repeating' if variable_entity.is_repeating else u'single'
        jinja_template_values[u'input_field'] = variable_entity.input_field

        self.response.out.write(jinja_template.render(jinja_template_values))