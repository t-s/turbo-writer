import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINTEMPLATES):
            webapp2.abort(401)

        # Get specified Template entity
        template_id = self.request.get("template_id")
        template = dao.get_template_by_id(template_id)
        error_msg = None if template else "Unable to access specified template"

        # Display the webpage
        self.render(template_id, template, error_msg)

    def post(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Get specified Template entity
        template_id = self.request.get("template_id")
        template = dao.get_template_by_id(template_id)
        error_msg = None if template else "Unable to access specified template"

        # Handle delete request
        if template and self.request.get("delete"):
            try:
                dao.delete_project(template)
                self.redirect("/site_admin/template_admin")
                return
            except Exception as e:
                error_msg = "Deleting template failed: {}".format(e)

        # Handle update request
        if template and self.request.get("update"):
            try:
                description = self.request.get("description")
                if not description:
                    raise Exception("You must provide a description for the template")
                template.description = self.request.get("description")
                template.put()
                self.redirect("/site_admin/template_admin")
                return
            except Exception as e:
                error_msg = "Updating template failed: {}".format(e)

        # Display the webpage
        self.render(template_id, template, error_msg)

    def render(self, template_entity_id, template_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "site_admin/template_edit.html")

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values["template_id"] = template_entity_id
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["name"] = template_entity.name
        jinja_template_values["description"] = template_entity.description

        self.response.out.write(jinja_template.render(jinja_template_values))