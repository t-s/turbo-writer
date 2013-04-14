import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        document_list = list()

        for document_entity in dao.get_documents(template):
            document = dict()
            document["id"] = document_entity.key.id()
            document["name"] = document_entity.name
            document["description"] = document_entity.description
            document["style"] = document_entity.style_name
            document_list.append(document)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/document/index.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["documents"] = document_list

        self.response.out.write(jinja_template.render(jinja_template_values))