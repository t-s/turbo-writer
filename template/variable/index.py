import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        variable_list = list()

        for variable_entity in dao.get_variables(template):
            variable = dict()
            variable[u'id'] = variable_entity.key.id()
            variable[u'name'] = variable_entity.name
            variable[u'description'] = variable_entity.description
            variable[u'is_repeating'] = variable_entity.is_repeating
            variable[u'input_field'] = variable_entity.input_field
            variable_list.append(variable)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/variable/index.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'variables'] = variable_list

        self.response.out.write(jinja_template.render(jinja_template_values))