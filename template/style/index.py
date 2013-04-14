import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        style_list = list()

        for style_entity in dao.get_styles(template):
            style = dict()
            style["id"] = style_entity.key.id()
            style["name"] = style_entity.name
            style["description"] = style_entity.description
            style["css"] = style_entity.css
            style_list.append(style)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/style/index.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["styles"] = style_list

        self.response.out.write(jinja_template.render(jinja_template_values))