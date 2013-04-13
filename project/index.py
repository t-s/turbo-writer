import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get("project_id"))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        jinja_template = ui.get_template(self, "project/index.html")
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["project"] = project
        self.response.out.write(jinja_template.render(jinja_template_values))