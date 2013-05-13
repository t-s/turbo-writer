import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(project, self.request.get(u'style_id'))
        error_msg = None if style_entity else u'Unable to access specified style'

        # Display the webpage
        self.render(project, style_entity, error_msg)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(project, self.request.get(u'style_id'))
        error_msg = None if style_entity else u'Unable to access specified style'

        # Handle delete request
        if style_entity and self.request.get(u'delete'):
            try:
                style_entity.key.delete()
                dao.touch_project_documents(project)
                self.redirect(u'/project/style?project_id={}'.format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting style from project failed: {}'.format(e)

        # Handle update request
        if style_entity and self.request.get(u'update'):
            try:
                style_entity.description = self.request.get(u'description')
                style_entity.css = self.request.get(u'css')
                style_entity.put()
                dao.touch_project_documents(project)
                self.redirect(u'/project/style?project_id={}'.format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating style failed: {}'.format(e)

        # Display the webpage
        self.render(project, style_entity, error_msg)

    def render(self, project, style_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/style/edit.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'style_id'] = style_entity.key.id()
        jinja_template_values[u'name'] = style_entity.name
        jinja_template_values[u'description'] = style_entity.description
        jinja_template_values[u'css'] = style_entity.css

        self.response.out.write(jinja_template.render(jinja_template_values))
