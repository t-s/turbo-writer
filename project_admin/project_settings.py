import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Display the webpage
        self.render(project)

    def post(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)
        error_msg = None

        # Handle delete request
        if self.request.get("delete"):
            try:
                dao.delete_project(project)
                self.redirect("/")
                return
            except Exception as e:
                error_msg = "Deleting project failed: {}".format(e)

        # Handle update request
        if self.request.get("update"):
            try:
                project.description = self.request.get("description")
                project.put()
                self.redirect("/project?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = "Updating project failed: {}".format(e)

        # Display the webpage
        self.render(project, error_msg)

    def render(self, project, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "project_admin/project_settings.html")

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["project"] = project
        jinja_template_values["error_msg"] = error_msg

        self.response.out.write(jinja_template.render(jinja_template_values))