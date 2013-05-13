import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Display the webpage
        self.render(project)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
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
            variable_entity = dao.get_variable_by_internal_name(project, internal_name)
            if variable_entity:
                error_msg = u'Adding variable failed, name collision in project: {}'.format(variable_entity.name)
            else:
                try:
                    dao.Variable(name=name, internal_name=internal_name, description=description,
                                 is_repeating=(variable_type == u'repeating'), input_field=input_field, content=u'',
                                 parent=project.key).put()
                    dao.touch_project_assignments(project)
                    self.redirect(u'/project/variable?project_id={}'.format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding variable failed: {}'.format(e)

        # Display the webpage
        self.render(project, error_msg)

    def render(self, project, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/variable/add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'type'] = self.request.get(u'type')
        jinja_template_values[u'input_field'] = self.request.get(u'input_field')

        self.response.out.write(jinja_template.render(jinja_template_values))