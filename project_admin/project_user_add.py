import re
import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        for project_role in project_role_list:
            role = {"name": project_role, "checked": False}
            view_role_list.append(role)

        # Display the webpage
        self.render(project, view_role_list)

    def post(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Validate the submitted email address
        submitted_email = self.request.get("email")
        if submitted_email == "":
            error_msg = None
        elif re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", submitted_email):
            if dao.test_email_in_project(project, submitted_email):
                error_msg = "Already a member of this project team: {}".format(submitted_email)
            else:
                # Attempt to add a new ProjectUser entity
                project_roles = list()
                for project_role in project_role_list:
                    if self.request.get(project_role):
                        project_roles.append(project_role)
                try:
                    dao.ProjectUser(email=submitted_email.lower(), parent=project.key).put()
                    self.redirect("/project_admin/project_user_admin?project_id={}".format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = "Adding member to project team failed: {}".format(e)
        else:
            error_msg = "Invalid email: {}".format(submitted_email)

        # Build list of project role checkboxes and whether they should be checked
        view_role_list = list()
        for project_role in project_role_list:
            role = {"name": project_role, "checked": self.request.get(project_role)}
            view_role_list.append(role)

        # Display the webpage
        self.render(project, view_role_list, error_msg)

    def render(self, project, view_role_list, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "project_admin/project_user_add.html")

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["email"] = self.request.get("email")
        jinja_template_values["roles"] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))