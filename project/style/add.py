import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        # Display the webpage
        self.render(project)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        name = self.request.get(u'name')
        description = self.request.get(u'description')
        css = self.request.get(u'css')

        if not name:
            error_msg = u'You must specify a name for your style definition'
        else:
            style_entity = dao.get_style_by_name(project, name)
            if style_entity:
                error_msg = u'Adding style failed: Duplicate style name in project'
            else:
                try:
                    dao.Style(name=name, description=description, css=css, parent=project.key).put()
                    dao.touch_project_documents(project)
                    self.redirect(u'/project/style?project_id={}'.format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding style failed: {}'.format(e)

        # Display the webpage
        self.render(project, error_msg)

    def render(self, project, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/style/add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'css'] = self.request.get(u'css')

        self.response.out.write(jinja_template.render(jinja_template_values))