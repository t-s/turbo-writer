import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        variable_list = list()

        for variable_entity in dao.get_variables(project):
            variable = dict()
            variable[u'id'] = variable_entity.key.id()
            variable[u'name'] = variable_entity.name
            variable[u'description'] = variable_entity.description
            variable[u'is_repeating'] = variable_entity.is_repeating
            variable[u'input_field'] = variable_entity.input_field
            variable_list.append(variable)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/variable/index.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'variables'] = variable_list

        self.response.out.write(jinja_template.render(jinja_template_values))