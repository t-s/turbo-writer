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

        # Display the webpage
        self.render(project)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        name = self.request.get(u'name')
        description = self.request.get(u'description')

        if not name:
            error_msg = u'You must specify a name for your attachment'
        else:
            attachment = dao.get_attachment_by_name(project, name)
            if attachment:
                error_msg = u'Adding attachment failed: Duplicate attachment name in project'
            else:
                try:
                    attachment = dao.Attachment(name=name,
                                                description=description,
                                                parent=project.key)
                    if self.request.get(u'choose_from_dropbox'):
                        # For Choose from Dropbox, we can transfer the file to the blob store, then return here
                        value = self.fill(self.request.get(u'choose_from_dropbox'))
                        filename = urllib2.unquote(value.split(u'/')[-1])
                        blob_key = DropboxService().store_file_as_blob(value)
                        dao.set_attachment_blob_key(attachment, blob_key, filename)
                    attachment.put()
                    if self.request.get(u'choose_from_disk'):
                        # For Choose from Disk, we need to redirect to another page
                        query_string_dict = {u'name': name,
                                             u'project_id': project.key.id(),
                                             u'attachment_id': attachment.key.id()}
                        query_string = urllib.urlencode(query_string_dict)
                        self.redirect("/project_admin/attachment_upload?{}".format(query_string))
                        return
                    self.redirect("/project_admin/attachment_admin?project_id={}".format(project.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding attachment failed: {}'.format(e)

        # Display the webpage
        self.render(project, error_msg, name, description)

    def render(self, project, error_msg=None, name=u'', description=u''):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/attachment_add.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = name
        jinja_template_values[u'description'] = description

        self.response.out.write(jinja_template.render(jinja_template_values))