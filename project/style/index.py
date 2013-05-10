import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permitted(
                project):  # TODO Test that current user's role includes project-admin permission
            webapp2.abort(401)

        style_list = list()

        for style_entity in dao.get_styles(project):
            style = dict()
            style[u'id'] = style_entity.key.id()
            style[u'name'] = style_entity.name
            style[u'description'] = style_entity.description
            style[u'css'] = style_entity.css
            style_list.append(style)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/style/index.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'styles'] = style_list

        self.response.out.write(jinja_template.render(jinja_template_values))