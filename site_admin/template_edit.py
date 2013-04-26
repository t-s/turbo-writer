import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINTEMPLATES):
            webapp2.abort(401)

        # Get specified Template entity
        template_id = self.request.get(u'template_id')
        template = dao.get_template_by_id(template_id)
        error_msg = None if template else u'Unable to access specified template'

        # Display the webpage
        self.render(template_id, template, error_msg)

    def post(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINUSERS):
            webapp2.abort(401)

        # Get specified Template entity
        template_id = self.request.get(u'template_id')
        template = dao.get_template_by_id(template_id)
        error_msg = None if template else u'Unable to access specified template'

        # Handle delete request
        if template and self.request.get(u'delete'):
            try:
                dao.delete_project(template)
                self.redirect(u'/site_admin/template_admin')
                return
            except Exception as e:
                error_msg = u'Deleting template failed: {}'.format(e)

        # Handle update request
        if template and self.request.get(u'update'):
            try:
                description = self.request.get(u'description')
                if not description:
                    raise Exception(u'You must provide a description for the template')
                template.description = self.request.get(u'description')
                template.put()
                self.redirect(u'/site_admin/template_admin')
                return
            except Exception as e:
                error_msg = u'Updating template failed: {}'.format(e)

        # Display the webpage
        self.render(template_id, template, error_msg)

    def render(self, template_entity_id, template_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/template_edit.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'template_id'] = template_entity_id
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = template_entity.name
        jinja_template_values[u'description'] = template_entity.description

        self.response.out.write(jinja_template.render(jinja_template_values))