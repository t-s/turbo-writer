import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        assignment_list = list()

        for assignment_entity in dao.get_assignments(template):
            assignment = dict()
            assignment["id"] = assignment_entity.key.id()
            assignment["name"] = assignment_entity.name
            assignment["is_repeating"] = assignment_entity.is_repeating
            assignment_list.append(assignment)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/assignment/index.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["assignments"] = assignment_list

        self.response.out.write(jinja_template.render(jinja_template_values))