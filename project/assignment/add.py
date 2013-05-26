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

        if not name:
            error_msg = u'You must specify a name for your assignment definition'
        elif not variable_type:
            error_msg = u'You must specify whether this is a single or repeating assignment'
        else:
            assignment_entity = dao.get_assignment_by_name(project, name)
            if assignment_entity:
                error_msg = u'Adding assignment failed: Duplicate assignment name in project'
            else:
                try:
                    assignment_entity = dao.Assignment(name=name, description=description,
                                                       is_repeating=(variable_type == u'repeating'),
                                                       parent=project.key)
                    assignment_entity.put()
                    dao.touch_project_assignments(project)
                    self.redirect("/project/assignment?project_id={}".format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding assignment failed: {}'.format(e)

        # Display the webpage
        self.render(project, error_msg)

    def render(self, project, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/assignment/add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'type'] = self.request.get(u'type')

        self.response.out.write(jinja_template.render(jinja_template_values))