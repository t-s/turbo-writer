import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        document_entity = dao.get_document_by_id(template, self.request.get("document_id"))
        error_msg = None if document_entity else "Unable to access specified document"

        # Display the webpage
        self.render(template, document_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        document_entity = dao.get_document_by_id(template, self.request.get("document_id"))
        error_msg = None if document_entity else "Unable to access specified document"

        # Handle delete request
        if document_entity and self.request.get("delete"):
            try:
                document_entity.key.delete()
                self.redirect("/template/document?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Deleting document from template failed: {}".format(e)

        # Handle update request
        if document_entity and self.request.get("update"):
            try:
                document_entity.description = str(self.request.get("description"))
                document_entity.style_name = str(self.request.get("doc_style"))
                document_entity.put()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_document_html(document_entity)

                self.redirect("/template/document?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Updating document failed: {}".format(e)

        # Display the webpage
        self.render(template, document_entity, error_msg)

    def render(self, template, document_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/document/edit.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["document_id"] = document_entity.key.id()
        jinja_template_values["name"] = document_entity.name
        jinja_template_values["description"] = document_entity.description
        jinja_template_values["doc_style"] = document_entity.style_name
        jinja_template_values["doc_style_names"] = dao.get_style_names(template)

        self.response.out.write(jinja_template.render(jinja_template_values))