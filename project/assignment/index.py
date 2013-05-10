import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permitted(
                project):  # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        assignment_list = list()

        for assignment_entity in dao.get_assignments(project):
            assignment = dict()
            assignment[u'id'] = assignment_entity.key.id()
            assignment[u'name'] = assignment_entity.name
            assignment[u'description'] = assignment_entity.description
            assignment[u'is_repeating'] = assignment_entity.is_repeating
            assignment_list.append(assignment)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/assignment/index.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'assignments'] = assignment_list

        self.response.out.write(jinja_template.render(jinja_template_values))