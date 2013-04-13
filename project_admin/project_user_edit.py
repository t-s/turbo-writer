import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Get specified ProjectUser entity
        project_user_id = self.request.get("project_user_id")
        project_user = dao.get_project_user_by_id(project, project_user_id)
        error_msg = None if project_user else "Unable to access specified project user"

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Display the webpage
        self.render(project, project_user_id, project_user, project_role_list, error_msg)

    def post(self):
        project = dao.get_project_by_id(self.request.get("project_id"))
        if not dao.test_project_permitted(project): # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        # Build list of ProjectRoles from the datastore
        project_role_list = list()

        # Get specified ProjectUser entity
        project_user_id = self.request.get("project_user_id")
        project_user = dao.get_project_user_by_id(project, project_user_id)
        error_msg = None if project_user else "Unable to access specified team member"

        # Handle delete request
        if project_user and self.request.get("delete"):
            try:
                project_user.key.delete()
                self.redirect("/project_admin/project_user_admin?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = "Deleting member from project team failed: {}".format(e)

        # Handle update request
        if project_user and self.request.get("update"):
            # Attempt to update the ProjectUser entity's roles
            project_roles = list()
            for project_role in project_role_list:
                if self.request.get(project_role):
                    project_roles.append(project_role)
            project_user.project_roles = project_roles
            try:
                project_user.put()
                self.redirect("/project_admin/project_user_admin?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = "Updating team member failed: {}".format(e)

        # Display the webpage
        self.render(project, project_user_id, project_user, project_role_list, error_msg)

    def render(self, project, project_user_id, project_user, project_role_list, error_msg):
        # Build list of project role checkboxes and whether they should be checked
        view_role_list = list()
        if project_user:
            for project_role in project_role_list:
                role = {"name": project_role, "checked": "checked" if project_role in project_user.project_roles else ""}
                view_role_list.append(role)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "project_admin/project_user_edit.html")

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["project_user_id"] = project_user_id
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["project"] = project
        jinja_template_values["email"] = project_user.email if project_user else "(unknown)"
        jinja_template_values["roles"] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))