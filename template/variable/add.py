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
        variable_type = self.request.get(u'type')
        input_field = self.request.get(u'input_field')

        if not name:
            error_msg = u'You must specify a name for your variable definition'
        elif not variable_type:
            error_msg = u'You must specify whether this is a single or repeating variable'
        elif not input_field:
            error_msg = u'You must specify which size of input field to display'
        else:
            internal_name = dao.convert_name_to_internal_name(name)
            variable_entity = dao.get_variable_by_internal_name(template, internal_name)
            if variable_entity:
                error_msg = u'Adding variable failed, name collision in template: {}'.format(variable_entity.name)
            else:
                try:
                    dao.Variable(name=name, internal_name=internal_name, description=description,
                                 is_repeating=(variable_type == u'repeating'), input_field=input_field, content=u'',
                                 parent=template.key).put()
                    self.redirect(u'/template/variable?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding variable failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/variable/add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'type'] = self.request.get(u'type')
        jinja_template_values[u'input_field'] = self.request.get(u'input_field')

        self.response.out.write(jinja_template.render(jinja_template_values))