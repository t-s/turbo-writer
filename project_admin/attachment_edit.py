import urllib
import urllib2

import webapp2

import dao
import ui

from service.dropbox_service import DropboxService


class RequestHandler(webapp2.RequestHandler):
    def fill(self, s):
        return s if s else u''

    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        attachment = dao.get_attachment_by_id(project, self.request.get(u'attachment_id'))

        # Display the webpage
        self.render(project, attachment)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        attachment_entity = dao.get_attachment_by_id(project, self.request.get(u'attachment_id'))
        error_msg = None if attachment_entity else u'Unable to access specified attachment'

        # Handle delete request
        if attachment_entity and self.request.get(u'delete'):
            try:
                attachment_entity.key.delete()
                self.redirect("/project_admin/attachment_admin?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting attachment from project failed: {}'.format(e)

        # Handle update request
        if attachment_entity and self.request.get(u'update'):
            try:
                attachment_entity.description = self.request.get(u'description')
                attachment_entity.attachment_type = self.request.get(u'attachment_type')
                if self.request.get(u'choose_from_dropbox'):
                    # For Choose from Dropbox, we can transfer the file to the blob store, then return here
                    value = self.fill(self.request.get(u'choose_from_dropbox'))
                    filename = urllib2.unquote(value.split(u'/')[-1])
                    blob_key = DropboxService().store_file_as_blob(value)
                    dao.set_attachment_blob_key(attachment_entity, blob_key, filename)
                attachment_entity.put()
                self.redirect("/project_admin/attachment_admin?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating document failed: {}'.format(e)

        if self.request.get(u'choose_from_disk'):
            # For Choose from Disk, we need to redirect to another page
            query_string_dict = {u'name': attachment_entity.name,
                                 u'project_id': project.key.id(),
                                 u'attachment_id': attachment_entity.key.id()}
            query_string = urllib.urlencode(query_string_dict)
            self.redirect("/project_admin/attachment_upload?{}".format(query_string))
            return

        # Display the webpage
        self.render(project, attachment_entity, error_msg)

    def render(self, project, attachment, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/attachment_edit.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'attachment_id'] = attachment.key.id()
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = attachment.name
        jinja_template_values[u'description'] = attachment.description
        jinja_template_values[u'filename'] = attachment.filename

        self.response.out.write(jinja_template.render(jinja_template_values))