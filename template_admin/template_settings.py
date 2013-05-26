import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Display the webpage
        self.render(template)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)
        error_msg = None

        # Handle delete request
        if self.request.get(u'delete'):
            if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN]):
                webapp2.abort(401)
            try:
                dao.delete_template(template)
                self.redirect("/")
                return
            except Exception as e:
                error_msg = u'Deleting template failed: {}'.format(e)

        # Handle update request
        if self.request.get(u'update'):
            try:
                template.description = self.request.get(u'description')
                template.put()
                self.redirect("/template?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating template failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template_admin/template_settings.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'template'] = template
        jinja_template_values[u'error_msg'] = error_msg

        self.response.out.write(jinja_template.render(jinja_template_values))