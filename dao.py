import re
import urllib2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.blobstore import BlobInfo

from lib import crc16pure
from service.html_generator_service import HtmlGeneratorService
from service.interview_service import InterviewService
from service.dropbox_service import DropboxService

# DATA ACCESS OBJECT

# Regex patterns
checklist_pattern = re.compile(r'(.*)\[([FT])\]\[([FT])\]')
optionally_indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')

# Constants
SINGLE_VARIABLE = u'S'
REPEATING_VARIABLE = u'R'
TEXT = u'T'

CONTINUE_FLOW = u'C'
BEGIN_REPEATING_GROUP = u'B'
END_REPEATING_GROUP = u'E'

SMALL = u'S'
MEDIUM = u'M'
LARGE = u'L'
FILE = u'X'

PROJECT = u'J'
PRIVATE_TEMPLATE = u'V'
PUBLIC_TEMPLATE = u'U'

SITE_MASTER = u'SiteMaster'
SITE_MASTER_ADMIN = u'SiteTemplateAdmin'

SITEPERMISSION_ADMIN = u'sp-a'
SITEPERMISSION_ADMINSETTINGS = u'sp-as'
SITEPERMISSION_ADMINTEMPLATES = u'sp-at'
SITEPERMISSION_ADMINUSERS = u'sp-au'

TEMPLATEPERMISSION_OWN = u'tp-o'
TEMPLATEPERMISSION_EDIT = u'tp-e'
TEMPLATEPERMISSION_USE = u'tp-u'


# Entity classes

class Assignment(ndb.Model):
    """
        The datastore contains one Assignment entity for each assignment within a project.

        Parent must contain a Project key.
    """
    name = ndb.StringProperty(u'n', required=True)
    description = ndb.TextProperty(u'd')
    prereq_assignment_names = ndb.StringProperty(u'pan', repeated=True)
    is_repeating = ndb.BooleanProperty(u'ir')
    instructions_to_manager = ndb.TextProperty(u'itm')
    instructions_to_writer = ndb.TextProperty(u'itw')
    variable_names = ndb.StringProperty(u'vn', repeated=True)
    checklist_items = ndb.TextProperty(u'ci', repeated=True)

    def clone(self, project):
        return Assignment(name=self.name, description=self.description,
                          prereq_assignment_names=self.prereq_assignment_names, is_repeating=self.is_repeating,
                          instructions_to_manager=self.instructions_to_manager,
                          instructions_to_writer=self.instructions_to_writer,
                          variable_names=self.variable_names, checklist_items=self.checklist_items, parent=project.key)


class Document(ndb.Model):
    """
        The datastore contains one Document entity for each document within a project.

        Parent must contain a Project key.
    """
    name = ndb.StringProperty(u'n', required=True)
    internal_name = ndb.StringProperty(u'in', required=True)
    description = ndb.TextProperty(u'd')
    style_name = ndb.StringProperty(u'sn')
    content = ndb.TextProperty(u'c', compressed=True)
    blob_key = ndb.BlobKeyProperty(u'bk')
    filename = ndb.StringProperty(u'f')

    def clone(self, project):
        return Document(name=self.name, internal_name=self.internal_name, description=self.description,
                        style_name=self.style_name, content=self.content, parent=project.key)


class DocumentItem(ndb.Model):
    """
        The datastore contains one DocumentItem entity for each item within a document.

        Parent must contain a Document key.
    """
    item_type = ndb.StringProperty(u'it', required=True)  # SINGLE_VARIABLE/REPEATING_VARIABLE/TEXT
    variable_name = ndb.StringProperty(u'vn')
    text = ndb.TextProperty(u't')
    style_name = ndb.StringProperty(u'sn')
    flow_control = ndb.StringProperty(u'fc')  # CONTINUE_FLOW/BEGIN_REPEATING_GROUP/END_REPEATING_GROUP
    position = ndb.IntegerProperty(u'p', required=True)

    def clone(self, document):
        return DocumentItem(item_type=self.item_type, variable_name=self.variable_name, text=self.text,
                            style_name=self.style_name, flow_control=self.flow_control, position=self.position,
                            parent=document.key)


class Interview(ndb.Model):
    """
        The datastore contains one Interview entity for each node in each interview hierarchy within a project.
        Each interview hierarchy within the project has a root node.

        Parent must contain a Project key.
    """
    name = ndb.StringProperty(u'n', required=True)
    root_interview_name = ndb.StringProperty(u'rin', required=True)
    prereq_interview_names = ndb.StringProperty(u'pin', repeated=True)  # Used only in the root node
    child_interview_names = ndb.StringProperty(u'cin', repeated=True)  # Used for nodes with child nodes
    is_writer_interview = ndb.BooleanProperty(u'iwi')
    menu_title = ndb.StringProperty(u'mt')  # Used only in the root node; defaults to u'Conduct Interview'
    content = ndb.TextProperty(u'content', compressed=True)  # None if navigation is directly to first child
    checklist_items = ndb.TextProperty(u'ci', repeated=True)
    auto_assign = ndb.BooleanProperty(
        u'aa')  # Used only for root nodes; True if this interview to be automatically assigned to creator of a new project
    generate_after = ndb.StringProperty(
        u'ga')  # Used only for root nodes; True if this interview to be cloned and auto-assigned after specified interview completed
    assign_interview_name = ndb.StringProperty(u'ain')  # Required if assign_button not None
    add_date = ndb.DateTimeProperty(u'ad', auto_now_add=True)
    update_date = ndb.DateTimeProperty(u'ud', auto_now=True)

    # Buttons
    assign_button = ndb.StringProperty(u'ab')  # No default
    child_button = ndb.StringProperty(u'chb')  # Defaults to u'Add'; not used if child_interview_names is None
    completed_button = ndb.StringProperty(u'cob')  # No default
    next_button = ndb.StringProperty(
        u'nb')  # Defaults to u'Continue'; not used if no next interview in parent's child_interview_names
    parent_button = ndb.StringProperty(
        u'pab')  # Defaults to u'Done'; if None, not displayed if next interview in parent's child_interview_names exists
    previous_button = ndb.StringProperty(
        u'prb')  # Defaults to u'Previous'; not used if no previous interview in parent's child_interview_names

    # Non-cloned properties
    assigned_email = ndb.StringProperty(
        u'ae')  # Used only for root nodes; identifies user who is to conduct this interview
    assigned_index = ndb.IntegerProperty(u'ai')  # Used only for root nodes; identifies index of a repeatable interview
    assigned_interview_id = ndb.IntegerProperty(u'aii')  # Identifies interview assigned by use of assign_button
    completed = ndb.BooleanProperty(u'c')  # Used only for root nodes
    has_been_reviewed = ndb.BooleanProperty(u'hbr')
    bookmark_interview_name = ndb.StringProperty(
        u'bin')  # Computed by engine; used only in the root node; defaults to first node with content
    child_count = ndb.IntegerProperty(u'cc')
    assignment_name = ndb.StringProperty(u'an')
    manager_instructions_to_writer = ndb.TextProperty(u'mitw')
    reviewer_comment = ndb.TextProperty(u'rc')

    def clone(self, project, suffix=u''):
        mask = u'{}.{}' if suffix else u'{}{}'

        prereq_interview_names_with_suffix = list()
        for prereq_interview_name in self.prereq_interview_names:
            prereq_interview_names_with_suffix.append(mask.format(prereq_interview_name, suffix))

        child_interview_names_with_suffix = []
        if self.child_interview_names:
            child_interview_names_with_suffix = [mask.format(name, suffix) for name in self.child_interview_names]

        return Interview(name=mask.format(self.name, suffix),
                         root_interview_name=mask.format(self.root_interview_name, suffix),
                         prereq_interview_names=prereq_interview_names_with_suffix,
                         child_interview_names=child_interview_names_with_suffix,
                         is_writer_interview=self.is_writer_interview, menu_title=self.menu_title, content=self.content,
                         checklist_items=self.checklist_items, auto_assign=self.auto_assign,
                         generate_after=self.generate_after, assign_interview_name=self.assign_interview_name,
                         assign_button=self.assign_button, child_button=self.child_button,
                         completed_button=self.completed_button, next_button=self.next_button,
                         parent_button=self.parent_button, previous_button=self.previous_button, parent=project.key)


class Project(ndb.Model):
    """
        The datastore contains one Project entity for each project on the site.
    """
    name = ndb.StringProperty(u'n', required=True)
    project_type = ndb.StringProperty(u't', required=True)  # PROJECT/PRIVATE_TEMPLATE/PUBLIC_TEMPLATE
    description = ndb.TextProperty(u'd')
    has_assignment_definition_changed = ndb.BooleanProperty(u'hadc')
    has_document_definition_changed = ndb.BooleanProperty(u'hddc')
    any_interview_conducted = ndb.BooleanProperty(u'aic')
    add_date = ndb.DateTimeProperty(u'ad', auto_now_add=True)
    update_date = ndb.DateTimeProperty(u'ud', auto_now=True)


class ProjectUser(ndb.Model):
    """
        The datastore contains one ProjectUser entity for each user associated with a project. At the time
        the user is added to the project, the user might or might not be registered as a site user.

        Parent must contain a Project key.
    """
    email = ndb.StringProperty(u'e', required=True)  # Stored as lowercase
    is_owner = ndb.BooleanProperty(u'io')
    project_roles = ndb.StringProperty(u'pr', repeated=True)  # A list of ProjectRole IDs
    add_date = ndb.DateTimeProperty(u'ad', auto_now_add=True)
    update_date = ndb.DateTimeProperty(u'ud', auto_now=True)


class SitePermission(ndb.Model):
    """
        The datastore contains one SitePermission entity for each site permission. Site permissions are used to
         authorize particular site functionality.

        Entity ID is the site permission ID, a short mnemonic string.
    """
    description = ndb.TextProperty(u'd', required=True)


class SiteRole(ndb.Model):
    """
        The datastore contains one SiteRole entity for each site-management role that can be assigned to a user. Each
        SiteRole contains a collection of the SitePermissions available to users with that role.

        Entity ID is the site role ID, a short mnemonic string.
    """
    description = ndb.TextProperty(u'd')
    site_permissions = ndb.StringProperty(u'sp', repeated=True)  # A list of SitePermission IDs


class SiteUser(ndb.Model):
    """
        The datastore contains one SiteUser entity for each registered user of the site.

        Entity ID is assigned automatically, since we don't want to use email addresses in links
        that specify the user.
    """
    email = ndb.StringProperty(u'e', required=True)  # Stored as lowercase
    site_roles = ndb.StringProperty(u'sr', repeated=True)  # A list of SiteRole IDs
    add_date = ndb.DateTimeProperty(u'ad', auto_now_add=True)
    update_date = ndb.DateTimeProperty(u'ud', auto_now=True)


class Style(ndb.Model):
    """
        The datastore contains one Style entity for each style definition within a template.

        Parent must contain a Project key for a public or private template.
    """
    name = ndb.StringProperty(u'n', required=True)
    description = ndb.TextProperty(u'd')
    css = ndb.TextProperty(u'c', compressed=True)

    def clone(self, project):
        return Style(name=self.name, description=self.description, css=self.css, parent=project.key)


class Variable(ndb.Model):
    """
        The datastore contains one Variable entity for each variable within a project.

        Parent must contain a Project key.
    """
    name = ndb.StringProperty(u'n', required=True)
    internal_name = ndb.StringProperty(u'in', required=True)
    input_field = ndb.StringProperty(u'if')  # SMALL/MEDIUM/LARGE/FILE
    description = ndb.TextProperty(u'd')
    is_repeating = ndb.BooleanProperty(u'ir')
    content = ndb.TextProperty(u'c', compressed=True)
    blob_key = ndb.BlobKeyProperty(u'bk')
    filename = ndb.StringProperty(u'f')

    def clone(self, project):
        return Variable(name=self.name, internal_name=self.internal_name, input_field=self.input_field,
                        # description=self.description, is_repeating=self.is_repeating, content=self.content, parent=project.key)
                        description=self.description, is_repeating=self.is_repeating, parent=project.key)


# Functions
def convert_name_to_internal_name(name):
    internal_name = re.sub(r'[\s]+', u'_', name.strip())
    internal_name = re.sub(r'[\W]+', u'', internal_name)
    if internal_name[0].isdigit():
        internal_name = u'v{}'.format(internal_name)
    internal_name = u'{}_{}'.format(internal_name, crc16pure.crc16xmodem(str(name)))
    return internal_name


def delete_interviews_for_assignment(template, assignment):
    for interview in Interview.query(ancestor=template.key).fetch():
        if interview.name.endswith(assignment.name):
            interview.key.delete()


def delete_project(project):
    for project_user_key in ProjectUser.query(ancestor=project.key).fetch(keys_only=True):
        project_user_key.delete()
    for assignment_key in Assignment.query(ancestor=project.key).fetch(keys_only=True):
        assignment_key.delete()
    for document in Document.query(ancestor=project.key).fetch():
        for document_item_key in DocumentItem.query(ancestor=document.key).fetch(keys_only=True):
            document_item_key.delete()
        if document.blob_key:
            blobstore.delete(document.blob_key)
        document.key.delete()
    for interview_key in Interview.query(ancestor=project.key).fetch(keys_only=True):
        interview_key.delete()
    for style_key in Style.query(ancestor=project.key).fetch(keys_only=True):
        style_key.delete()
    for variable in Variable.query(ancestor=project.key).fetch():
        if variable.blob_key:
            blobstore.delete(variable.blob_key)
        variable.key.delete()
    project.key.delete()


def delete_template(template):
    for template_user_key in ProjectUser.query(ancestor=template.key).fetch(keys_only=True):
        template_user_key.delete()
    for assignment_key in Assignment.query(ancestor=template.key).fetch(keys_only=True):
        assignment_key.delete()
    for document_key in Document.query(ancestor=template.key).fetch(keys_only=True):
        for document_item_key in DocumentItem.query(ancestor=document_key).fetch(keys_only=True):
            document_item_key.delete()
        document_key.delete()
    for interview_key in Interview.query(ancestor=template.key).fetch(keys_only=True):
        interview_key.delete()
    for style_key in Style.query(ancestor=template.key).fetch(keys_only=True):
        style_key.delete()
    for variable_key in Variable.query(ancestor=template.key).fetch(keys_only=True):
        variable_key.delete()
    template.key.delete()


def get_assignment_by_id(template, assignment_id):
    return Assignment.get_by_id(int(assignment_id), parent=template.key)


def get_assignment_by_name(template, assignment_name):
    for assignment in Assignment.query(Assignment.name == assignment_name, ancestor=template.key).fetch():
        return assignment


def get_assignment_names(template):
    return [assignment.name for assignment in
            Assignment.query(ancestor=template.key).order(Assignment.name)]


def get_assignments(template):
    return Assignment.query(ancestor=template.key).order(Assignment.name).fetch()


def get_current_site_user():
    current_user = users.get_current_user()
    if current_user:
        # TODO In future, use Google Accounts user ID rather than email to locate our SiteUser, so that we can still find user if user changes his/her Google Accounts email
        for site_user in SiteUser.query(SiteUser.email == current_user.email().lower()).fetch():
            return site_user


def get_document_by_id(template, document_id):
    return Document.get_by_id(int(document_id), parent=template.key)


def get_document_by_name(template, document_name):
    for document in Document.query(Document.name == document_name, ancestor=template.key).fetch():
        return document


def get_document_count(project):
    return Document.query(ancestor=project.key).count()


def get_document_item_count(document):
    return DocumentItem.query(ancestor=document.key).count()


def get_document_items(document):
    return DocumentItem.query(ancestor=document.key).order(
        DocumentItem.position).fetch()  # NOTE: This ".fetch()" is needed for html_generator_service  # TODO: Make use of ".fetch()" consistent in this module


def get_documents(project):
    return Document.query(ancestor=project.key).order(Document.name).fetch()


def get_indexed_variable(project, variable_name, index):
    indexed_variable_name = u'{}[{}]'.format(variable_name, index)
    variables = Variable.query(Variable.name == indexed_variable_name, ancestor=project.key).fetch()
    for variable in variables:
        if variable.input_field == FILE and variable.blob_key and variable.filename:
            return u'\n<!--B-KEY:{}-->\n[Insert "{}" here]\n'.format(variable.blob_key, variable.filename)
        else:
            return variable.content if variable.content else u''
    return u''


def get_interview_count(project):
    return Interview.query(ancestor=project.key).count()


def get_interview_by_id(project, interview_id):
    return Interview.get_by_id(int(interview_id), parent=project.key)


def get_interview_by_name(project, interview_name):
    for interview in Interview.query(Interview.name == interview_name, ancestor=project.key).fetch():
        return interview


def get_interviews(project):
    return Interview.query(ancestor=project.key).order(Interview.name).fetch()


def get_interviews_by_assignment_name(template, assignment_name):
    return Interview.query(Interview.assignment_name == assignment_name, ancestor=template.key).fetch()


def get_private_template_users(template):
    return ProjectUser.query(ancestor=template.key).fetch()


def get_private_templates():
    private_templates = list()
    for project_user_key in ProjectUser.query(ProjectUser.email == users.get_current_user().email().lower()).fetch(
            keys_only=True):
        template = get_project_by_id(project_user_key.parent().id())
        if template.project_type == PRIVATE_TEMPLATE:
            private_templates.append(template)
    private_templates.sort(cmp=lambda x, y: cmp(x.name, y.name))
    return private_templates


def get_private_templates_by_name(template_name):
    return Project.query(Project.name == template_name, Project.project_type == PRIVATE_TEMPLATE).fetch()


def get_project_by_id(project_id):
    return Project.get_by_id(int(project_id))


def get_project_user_by_email(project, email):
    for project_user in ProjectUser.query(ProjectUser.email == email.lower(), ancestor=project.key).fetch():
        return project_user


def get_project_user_by_id(project, project_user_id):
    return ProjectUser.get_by_id(int(project_user_id), parent=project.key)


def get_project_users(project):
    return ProjectUser.query(ancestor=project.key).order(ProjectUser.email).fetch()


def get_projects_by_name(project_name):
    return Project.query(Project.name == project_name, Project.project_type == PROJECT).fetch()


def get_public_templates():
    return Project.query(Project.project_type == PUBLIC_TEMPLATE).order(Project.name)


def get_public_templates_by_name(template_name):
    return Project.query(Project.name == template_name, Project.project_type == PUBLIC_TEMPLATE).fetch()


def get_site_roles():
    return [site_role_key.id() for site_role_key in SiteRole.query().order(SiteRole.key).fetch(keys_only=True)]


def get_site_user_by_email(email):
    for site_user in SiteUser.query(SiteUser.email == email).fetch():
        return site_user


def get_site_user_by_id(site_user_id):
    return SiteUser.get_by_id(int(site_user_id))


def get_site_users():
    return SiteUser.query().order(SiteUser.email)


def get_standard_project_values(project):
    jinja_template_values = get_standard_site_values()
    current_user = users.get_current_user()
    current_email = current_user.email().lower()
    jinja_template_values[u'project'] = project

    # For updated definitions, generate new HTML
    update_project = False
    if not project.any_interview_conducted and project.has_assignment_definition_changed:
        html_generator_service = HtmlGeneratorService(project)
        html_generator_service.generate_all_assignments()
        for interview in get_interviews(project):
            if interview.auto_assign:
                interview.assigned_email = current_email
                interview.put()
        project.has_assignment_definition_changed = False
        update_project = True

    if project.has_document_definition_changed:
        html_generator_service = HtmlGeneratorService(project)
        html_generator_service.generate_all_documents()
        project.has_document_definition_changed = False
        update_project = True

    if update_project:
        project.put()

    # Set documents
    jinja_template_values[u'documents'] = get_documents(project)

    # Load interviews
    interview_service = InterviewService(project)

    # Compute progress
    interview_count = 0
    interview_complete = 0
    checklist_count = 0
    checklist_complete = 0
    for root_interview_name in interview_service.get_root_interview_names():
        interview = interview_service.get_interview_by_name(root_interview_name)
        if interview and interview.assigned_email:
            interview_count += 1
            if interview.completed or interview.assigned_interview_id:
                interview_complete += 1
            for checklist_item in interview.checklist_items:
                checklist_count += 1
                match = parse_checklist_item(checklist_item)
                if interview.name.startswith(u'write_') and match.group(2) == u'T':
                    checklist_complete += 1
                if interview.name.startswith(u'review_') and match.group(3) == u'T':
                    checklist_complete += 1
    interview_percent = u'&ndash;'
    if interview_count > 0:
        interview_percent = u'{}%'.format(interview_complete * 100 / interview_count)
    checklist_percent = u'&ndash;'
    if checklist_count > 0:
        checklist_percent = u'{}%'.format(checklist_complete * 100 / checklist_count)
    jinja_template_values[u'interview_count'] = interview_count
    jinja_template_values[u'interview_complete'] = interview_complete
    jinja_template_values[u'interview_percent'] = interview_percent
    jinja_template_values[u'checklist_count'] = checklist_count
    jinja_template_values[u'checklist_complete'] = checklist_complete
    jinja_template_values[u'checklist_percent'] = checklist_percent

    # Set workflow
    workflow_interviews = list()
    for root_interview_name in interview_service.get_root_interview_names():
        interview = interview_service.get_interview_by_name(root_interview_name)
        if interview and interview.assigned_email == current_email and not interview.completed and not interview.assigned_interview_id and interview_service.are_prereqs_complete(
                interview):
            bookmark_interview_name = interview.bookmark_interview_name
            content_interview_entity = interview_service.get_interview_by_name(
                bookmark_interview_name) if bookmark_interview_name else interview_service.get_first_interview_with_content(
                interview.name)
            if content_interview_entity:
                workflow_interview = dict()
                workflow_interview[u'name'] = content_interview_entity.name
                try:
                    # if assigned_index has been filled in, include u'index' in the URL's query string
                    workflow_interview[u'index'] = int(content_interview_entity.assigned_index)
                    workflow_interview[u'show_index'] = True
                except:
                    pass
                workflow_interview[
                    u'menu_title'] = interview.menu_title if interview.menu_title else u'Conduct Interview'
                workflow_interview[u'add_date'] = content_interview_entity.add_date
                workflow_interviews.append(workflow_interview)

    assign_writer_interviews = list()
    assign_reviewer_interviews = list()
    writer_interviews = list()
    reviewer_interviews = list()

    for interview in workflow_interviews:
        name = interview[u'name']
        if name.startswith(u'assign_writer_'):
            assign_writer_interviews.append(interview)
        elif name.startswith(u'assign_reviewer_'):
            assign_reviewer_interviews.append(interview)
        elif name.startswith(u'write_'):
            writer_interviews.append(interview)
        else:
            reviewer_interviews.append(interview)

    jinja_template_values[u'assign_writer_interviews'] = assign_writer_interviews
    jinja_template_values[u'assign_reviewer_interviews'] = assign_reviewer_interviews
    jinja_template_values[u'writer_interviews'] = writer_interviews
    jinja_template_values[u'reviewer_interviews'] = reviewer_interviews

    project_user = get_project_user_by_email(project, current_email)
    if project_user:
        jinja_template_values[u'is_owner'] = project_user.is_owner

    jinja_template_values[u'any_interviews'] = project.any_interview_conducted

    return jinja_template_values


def get_standard_site_values():
    current_user = users.get_current_user()
    jinja_template_values = {u'url': users.create_logout_url(u'/'), u'email': current_user.email()}
    if current_user:
        for site_user in SiteUser.query(SiteUser.email == current_user.email().lower()):
            for site_role in site_user.site_roles:
                site_role_entity = SiteRole.get_by_id(site_role)
                if SITEPERMISSION_ADMIN in site_role_entity.site_permissions:
                    jinja_template_values[u'SITEPERMISSION_ADMIN'] = True
                if SITEPERMISSION_ADMINSETTINGS in site_role_entity.site_permissions:
                    jinja_template_values[u'SITEPERMISSION_ADMINSETTINGS'] = True
                if SITEPERMISSION_ADMINTEMPLATES in site_role_entity.site_permissions:
                    jinja_template_values[u'SITEPERMISSION_ADMINTEMPLATES'] = True
                if SITEPERMISSION_ADMINUSERS in site_role_entity.site_permissions:
                    jinja_template_values['SITEPERMISSION_ADMINUSERS'] = True
            user_projects = list()
            user_templates = list()
            for project_user in ProjectUser.query(ProjectUser.email == site_user.email):
                project = project_user.key.parent().get()
                if project.project_type == PROJECT:
                    user_projects.append({u'project_id': project.key.id(), u'name': project.name})
                elif project.project_type == PRIVATE_TEMPLATE and project_user.is_owner:
                    user_templates.append({u'template_id': project.key.id(), u'name': project.name})
            jinja_template_values[u'user_projects'] = user_projects
            jinja_template_values[u'user_templates'] = user_templates
    return jinja_template_values


def get_standard_template_values(template):
    jinja_template_values = get_standard_site_values()
    current_user = users.get_current_user()
    current_email = current_user.email()
    jinja_template_values[u'template'] = template

    template_user = get_template_user_by_email(template, current_email)
    if template_user:
        jinja_template_values[u'is_owner'] = template_user.is_owner

    return jinja_template_values


def get_style_by_id(template, style_id):
    return Style.get_by_id(int(style_id), parent=template.key)


def get_style_by_name(template, style_name):
    for style in Style.query(Style.name == style_name, ancestor=template.key):
        return style


def get_repeating_names(template):
    return [variable.name for variable in
            Variable.query(Variable.is_repeating == True, ancestor=template.key).order(Variable.name)]


def get_single_names(template):
    return [variable.name for variable in
            Variable.query(Variable.is_repeating == False, ancestor=template.key).order(Variable.name)]


def get_style_names(template):
    return [style.name for style in Style.query(ancestor=template.key).order(Style.name)]


def get_styles(template):
    return Style.query(ancestor=template.key).order(Style.name).fetch()


def get_template_by_id(template_id):
    return Project.get_by_id(int(template_id))


def get_template_user_by_id(template, template_user_id):
    return ProjectUser.get_by_id(int(template_user_id), parent=template.key)


def get_template_user_by_email(template, email):
    for template_user in ProjectUser.query(ProjectUser.email == email.lower(), ancestor=template.key).fetch():
        return template_user


def get_template_users(template):
    return ProjectUser.query(ancestor=template.key).order(ProjectUser.email).fetch()


def get_variable_by_id(template, variable_id):
    return Variable.get_by_id(int(variable_id), parent=template.key)


def get_variable_by_internal_name(template, internal_name):
    for variable in Variable.query(Variable.internal_name == internal_name, ancestor=template.key).fetch():
        return variable


def get_variable_by_name(template, variable_name):
    for variable in Variable.query(Variable.name == variable_name, ancestor=template.key).fetch():
        return variable


def get_variables(project):
    return Variable.query(ancestor=project.key).order(Variable.name).fetch()


def parse_checklist_item(checklist_item):
    match = None
    while True:
        match = checklist_pattern.search(checklist_item)
        if match:
            break
        checklist_item += u'[F][F]'
    return match


def set_bookmark(root_interview, current_interview):
    if root_interview and current_interview:
        root_interview.bookmark_interview_name = current_interview.name
        root_interview.put()


def set_variable(project, internal_name, value):
    for variable in Variable.query(Variable.internal_name == internal_name, ancestor=project.key):
        set_variable_content(variable, value)
        variable.put()
        return
    match = optionally_indexed_name_pattern.match(internal_name)
    if match:
        base_name = match.group(1)
        if not base_name:
            raise Exception(u'Unexpected call to set_variable #1: internal_name={}'.format(internal_name))
        base_variable = get_variable_by_internal_name(project, base_name)
        if not base_variable:
            raise Exception(u'Unexpected call to set_variable #2: internal_name={}'.format(internal_name))
        variable = Variable(name=internal_name, internal_name=internal_name,
                            input_field=base_variable.input_field, parent=project.key)
        set_variable_content(variable, value)
        variable.put()
    else:
        raise Exception(u'Unexpected call to set_variable #3: internal_name={}'.format(internal_name))


def set_variable_blob_key(project, internal_name, blob_key):
    for variable in Variable.query(Variable.internal_name == internal_name, ancestor=project.key):
        if variable.blob_key:
            blobstore.delete(variable.blob_key)
        variable.blob_key = blob_key
        variable.filename = BlobInfo.get(blob_key).filename
        variable.put()
        return
    match = optionally_indexed_name_pattern.match(internal_name)
    if match:
        base_name = match.group(1)
        if not base_name:
            raise Exception(u'Unexpected call to set_variable_blob_key #1: internal_name={}'.format(internal_name))
        base_variable = get_variable_by_name(project, base_name)
        if not base_variable:
            raise Exception(u'Unexpected call to set_variable_blob_key #2: internal_name={}'.format(internal_name))
        if base_variable.input_field != FILE:
            raise Exception(u'Unexpected call to set_variable_blob_key #3: internal_name={}'.format(internal_name))
        variable = Variable(name=internal_name, internal_name=internal_name, input_field=base_variable.input_field,
                            parent=project.key)
        variable.blob_key = blob_key
        variable.filename = BlobInfo.get(blob_key).filename
        variable.put()
    else:
        raise Exception(u'Unexpected call to set_variable_blob_key #4: internal_name={}'.format(internal_name))


def set_variable_content(variable, value):
    if variable.input_field == FILE and value:
        # Must be a Dropbox file, since UploadHandler doesn't go thru this code
        blob_key = DropboxService().store_file_as_blob(value)
        if variable.blob_key:
            blobstore.delete(variable.blob_key)
        variable.blob_key = blob_key
        variable.filename = urllib2.unquote(value.split(u'/')[-1])
    else:
        variable.content = value


def test_current_user_registered():
    current_user = users.get_current_user()
    return current_user and SiteUser.query(SiteUser.email == current_user.email().lower()).count()


def test_email_in_project(project, submitted_email):
    return ProjectUser.query(ProjectUser.email == submitted_email.lower(), ancestor=project.key).count()


def test_email_in_template(template, submitted_email):
    return ProjectUser.query(ProjectUser.email == submitted_email.lower(), ancestor=template.key).count()


def test_email_is_project_owner(project, email):
    return ProjectUser.query(ProjectUser.email == email.lower(), ProjectUser.is_owner == True,
                             ancestor=project.key).count()


def test_email_is_template_owner(template, email):
    return ProjectUser.query(ProjectUser.email == email.lower(), ProjectUser.is_owner == True,
                             ancestor=template.key).count()


def test_email_registered(email):
    return SiteUser.query(SiteUser.email == email.lower()).count()


def test_permission(permission):
    current_user = users.get_current_user()
    if current_user:
        for user_entity in SiteUser.query(SiteUser.email == current_user.email().lower()):
            for site_role in user_entity.site_roles:
                site_role_entity = SiteRole.get_by_id(site_role)
                if permission in site_role_entity.site_permissions:
                    return True


def test_project_permitted(project):
    site_user = get_current_site_user()
    if site_user:
        for project in get_projects_by_name(project.name):
            if test_email_in_project(project, site_user.email):
                return True


def test_template_permitted(template):
    site_user = get_current_site_user()
    if site_user:
        for template in get_private_templates_by_name(template.name):
            if test_email_in_template(template, site_user.email):
                return True


def touch_project_assignments(project):
    project.has_assignment_definition_changed = True
    project.put()


def touch_project_documents(project):
    project.has_document_definition_changed = True
    project.put()


# If datastore contains no site users, initialize it
if not SiteUser.query().count():
    # Add site permissions
    SitePermission(id=SITEPERMISSION_ADMIN, description=u'View the Site Administration menu').put()
    SitePermission(id=SITEPERMISSION_ADMINSETTINGS, description=u'Maintain master properties for the site').put()
    SitePermission(id=SITEPERMISSION_ADMINTEMPLATES,
                   description=u'Maintain templates in the site\'s Template Gallery').put()
    SitePermission(id=SITEPERMISSION_ADMINUSERS, description=u'Maintain user entities for the site').put()

    # Add site roles
    SiteRole(id=SITE_MASTER,
             description=u'Site Master Administrator',
             site_permissions=[SITEPERMISSION_ADMIN, SITEPERMISSION_ADMINSETTINGS, SITEPERMISSION_ADMINUSERS,
                               SITEPERMISSION_ADMINTEMPLATES]).put()
    SiteRole(id=SITE_MASTER_ADMIN,
             description=u'Site Template Administrator',
             site_permissions=[SITEPERMISSION_ADMIN, SITEPERMISSION_ADMINTEMPLATES]).put()

    # Add site users: site masters
    SiteUser(email=u'LDRidgeway@gmail.com'.lower(), site_roles=[SITE_MASTER, SITE_MASTER_ADMIN]).put()
    SiteUser(email=u'ltlamberton@gmail.com'.lower(), site_roles=[SITE_MASTER, SITE_MASTER_ADMIN]).put()
    SiteUser(email=u'awieder@zephyrmediacommunications.com'.lower(), site_roles=[SITE_MASTER, SITE_MASTER_ADMIN]).put()
    SiteUser(email=u'awieder@ztech-group.com'.lower(), site_roles=[SITE_MASTER, SITE_MASTER_ADMIN]).put()
    # SiteUser(email=u'MHanderhan@meesha.net'.lower(), site_roles=[SITE_MASTER, SITE_MASTER_ADMIN]).put()

'''
# If datastore contains no templates in the Template Gallery, initialize it
if not Project.query(Project.project_type == PUBLIC_TEMPLATE).count():
    novel_template = Project(name="Novel",
                             project_type=PRIVATE_TEMPLATE,
                             description="Use this template to write a novel.").put()

    Document(name="Novel", internal_name="Novel",
             description="This is the actual novel.",
             content="""
<div style="font-size: {{ font_size }}pt; font-family: '{{ font_family }}';
        margin-left: {{ margin }}px; margin-right: {{ margin }}px">
    <h2 style="text-align: center">
        {{ title }}
    </h2>
    <h3 style="text-align: center">Prologue</h3>
    {{ novel_prologue }}
    <h3 style="text-align: center">{{ title }}</h3>
    {% for index in range(chapter_count) %}
        {% if get_indexed_variable(project, "chapter_title", index) %}
            <h4>{{ get_indexed_variable(project, "chapter_title", index) }}</h4>
            {{ get_indexed_variable(project, "chapter", index) }}
        {% endif %}
    {% endfor %}
    <h3 style="text-align: center">Epilogue</h3>
    {{ novel_epilogue }}
    <p style="text-align: center">
        THE END
    </p>
</div>
        """, parent=novel_template).put()

    Interview(name="make_assignments",
              root_interview_name="make_assignments",
              child_interview_names="title_and_format|assign_prologue_writer|assign_chapter_writers|assign_epilogue_writer|assign_reviewer",
              menu_title="Title, format, and assignments",
              auto_assign=True,
              parent=novel_template).put()

    Interview(name="title_and_format",
              root_interview_name="make_assignments",
              content="""
<h3>Title and Format Specifications</h3>
<p>
    Provide the title and formatting information for producing the novel.
</p>
<table>
    <tr>
        <th style="text-align: right">Title of the Novel:</th>
        <td><input name="title" value='{{ title | e }}' style="width: 500px"></td>
    </tr>
    <tr>
        <th style="text-align: right">Font size in points:</th>
        <td><input name="font_size" value={{ font_size | e }}></td>
    </tr>
    <tr>
        <th style="text-align: right">Font family:</th>
        <td><input name="font_family" value='{{ font_family | e }}'></td>
    </tr>
    <tr>
        <th style="text-align: right">Margin:</th>
        <td><input name="margin" value={{ margin | e }}></td>
    </tr>
</table>
        """, parent=novel_template).put()

    Interview(name="assign_prologue_writer",
              root_interview_name="make_assignments",
              assign_button="Assign Writer",
              assign_interview_name="prologue_interview",
              content="""
<h3>Assign a Writer for the Prologue</h3>
{% if assigned_email %}
    <p>
        Prologue writer assignment completed:
    </p>
    <blockquote>
        <div style="width: 500px; background-color: lightgray">
            {{ assigned_email | e }}
        </div>
    </blockquote>
{% else %}
    <p>
        Select a team member to write the prologue, enter your instructions, and click "Assign Writer".
    </p>
    <table width="100%">
        <tr>
            <th style="text-align: right; vertical-align: text-top">Team Member:</th>
            <td>
                <select name="_email">
                    <option value="">(Select team member)</option>
                    {% for email in emails %}
                        <option value="{{ email | e }}">{{ email | e }}</option>
                    {% endfor %}
                </select>
            </td>
        </tr>
        <tr>
            <th style="text-align: right; vertical-align: text-top">Instructions:</th>
            <td>
                <textarea name="prologue_instructions"
                    style="height: 200px; width: 500px">{{ prologue_instructions | e }}</textarea>
            </td>
        </tr>
    </table>
{% endif %}
<br/><br/>
        """, parent=novel_template).put()

    Interview(name="assign_chapter_writers",
              root_interview_name="make_assignments",
              child_button="Add Chapter",
              child_interview_names="assign_chapter_writer",
              content="""
<h3>Assign a Writer for Each Chapter</h3>
<p>
    Use the "Add Chapter" button to assign each chapter writing assignment.
</p>
{% if chapter_title_count %}
    <p>
        Chapter titles so far:
        <ul>
            {% for index in range(chapter_title_count) %}
                {% if get_indexed_variable(project, "chapter_title", index) %}
                    <li>{{ get_indexed_variable(project, "chapter_title", index) | e }}</li>
                {% endif %}
            {% endfor %}
        </ul>
    </p>
{% endif %}
        """, parent=novel_template).put()

    Interview(name="assign_chapter_writer",
              root_interview_name="make_assignments",
              assign_button="Assign Writer",
              assign_interview_name="chapter_interview",
              content="""
<h3>Assign a Writer for This Chapter</h3>
{% if assigned_email %}
    <p>
        Chapter writer assignment completed:
    </p>
    <blockquote>
        <div style="width: 500px; background-color: lightgray">
            {{ assigned_email | e }}
        </div>
    </blockquote>
{% else %}
    <p>
        Select a team member to write the chapter, enter your instructions, and click "Assign Writer".
    </p>
    <table width="100%">
        <tr>
            <th style="text-align: right; vertical-align: text-top">Team Member:</th>
            <td>
                <select name="_email">
                    <option value="">(Select team member)</option>
                    {% for email in emails %}
                        <option value="{{ email | e }}">{{ email | e }}</option>
                    {% endfor %}
                </select>
            </td>
        </tr>
        <tr>
            <th style="text-align: right; vertical-align: text-top">Chapter Title:</th>
            <td>
                <input name="chapter_title" style="width: 500px" value="{{ chapter_title | e }}"/>
            </td>
        </tr>
        <tr>
            <th style="text-align: right; vertical-align: text-top">Instructions:</th>
            <td>
                <textarea name="chapter_instructions"
                    style="height: 200px; width: 500px">{{ chapter_instructions | e }}</textarea>
            </td>
        </tr>
    </table>
{% endif %}
<br/><br/>
        """, parent=novel_template).put()

    Interview(name="assign_epilogue_writer",
              root_interview_name="make_assignments",
              assign_button="Assign Writer",
              assign_interview_name="epilogue_interview",
              content="""
<h3>Assign a Writer for the Epilogue</h3>
{% if assigned_email %}
    <p>
        Epilogue writer assignment completed:
    </p>
    <blockquote>
        <div style="width: 500px; background-color: lightgray">
            {{ assigned_email | e }}
        </div>
    </blockquote>
{% else %}
    <p>
        Select a team member to write the epilogue, enter your instructions, and click "Assign Writer".
    </p>
    <table width="100%">
        <tr>
            <th style="text-align: right; vertical-align: text-top">Team Member:</th>
            <td>
                <select name="_email">
                    <option value="">(Select team member)</option>
                    {% for email in emails %}
                        <option value="{{ email | e }}">{{ email | e }}</option>
                    {% endfor %}
                </select>
            </td>
        </tr>
        <tr>
            <th style="text-align: right; vertical-align: text-top">Instructions:</th>
            <td>
                <textarea name="epilogue_instructions"
                    style="height: 200px; width: 500px">{{ epilogue_instructions | e }}</textarea>
            </td>
        </tr>
    </table>
{% endif %}
<br/><br/>
        """, parent=novel_template).put()

    Interview(name="assign_reviewer",
              root_interview_name="make_assignments",
              assign_button="Assign Reviewer",
              assign_interview_name="review",
              content="""
<h3>Assign a Reviewer for All Content</h3>
{% if assigned_email %}
    <p>
        Reviewer assignment completed:
    </p>
    <blockquote>
        <div style="width: 500px; background-color: lightgray">
            {{ assigned_email | e }}
        </div>
    </blockquote>
{% else %}
    <p>
        Select a team member to review the novel contents, enter your instructions, and
        click "Assign Writer". Suggestions:
        <ul>
            <li>Assign someone who can check grammar.
            <li>Assign someone who can check style consistency.
        </ul>
    </p>
    <table width="100%">
        <tr>
            <th style="text-align: right; vertical-align: text-top">Team Member:</th>
            <td>
                <select name="_email">
                    <option value="">(Select team member)</option>
                    {% for email in emails %}
                        <option value="{{ email | e }}">{{ email | e }}</option>
                    {% endfor %}
                </select>
            </td>
        </tr>
        <tr>
            <th style="text-align: right; vertical-align: text-top">Instructions:</th>
            <td>
                <textarea name="review_instructions"
                    style="height: 200px; width: 500px">{{ review_instructions | e }}</textarea>
            </td>
        </tr>
    </table>
{% endif %}
<br/><br/>
        """, parent=novel_template).put()

    Interview(name="prologue_interview",
              root_interview_name="prologue_interview",
              menu_title="Write prologue",
              parent_button="Save",
              completed_button="Interview Completed",
              content="""
<h3>Prologue of the Novel</h3>
<p>
    Provide the prologue of the novel. Instructions from project leader:
    <blockquote style="width: 500px; font-style: italic; background-color: lightgray">
        &nbsp; {{ prologue_instructions }}
    </blockquote>
<p>
<table>
    <tr>
        <th style="text-align: right; vertical-align: text-top">Prologue of the Novel:</th>
        <td>
            <textarea name="novel_prologue" style="height: 200px; width: 500px">{{ novel_prologue | e }}</textarea>
        </td>
    </tr>
</table>
        """, parent=novel_template).put()

    Interview(name="chapter_interview",
              root_interview_name="chapter_interview",
              menu_title="Write chapter of the novel",
              parent_button="Save",
              completed_button="Interview Completed",
              content="""
<h3>Chapter of the Novel</h3>
<p>
    Provide the chapter of the novel. Instructions from project leader:
    <blockquote style="width: 500px; font-style: italic; background-color: lightgray">
        &nbsp; {{ chapter_instructions }}
    </blockquote>
<p>
<table>
    <tr>
        <th style="text-align: right; vertical-align: text-top">Chapter Title:</th>
        <td>
            <input name="chapter_title" style="width: 500px" value="{{ chapter_title | e }}"/>
        </td>
    </tr>
    <tr>
        <th style="text-align: right; vertical-align: text-top">Chapter:</th>
        <td>
            <textarea name="chapter" style="height: 200px; width: 500px">{{ chapter | e }}</textarea>
        </td>
    </tr>
</table>
        """, parent=novel_template).put()

    Interview(name="epilogue_interview",
              root_interview_name="epilogue_interview",
              menu_title="Write epilogue",
              parent_button="Save",
              completed_button="Interview Completed",
              content="""
<h3>Epilogue of the Novel</h3>
<p>
    Provide the epilogue of the novel. Instructions from project leader:
    <blockquote style="width: 500px; font-style: italic; background-color: lightgray">
        &nbsp; {{ epilogue_instructions }}
    </blockquote>
<p>
<table>
    <tr>
        <th style="text-align: right; vertical-align: text-top">Epilogue of the Novel:</th>
        <td>
            <textarea name="novel_epilogue" style="height: 200px; width: 500px">{{ novel_epilogue | e }}</textarea>
        </td>
    </tr>
</table>
        """, parent=novel_template).put()

    Interview(name="review",
              root_interview_name="review",
              prereq_interview_names=["prologue_interview", "chapter_interview", "epilogue_interview"],
              menu_title="Review everything",
              parent_button="Save",
              content="""
<h3>Review</h3>
<p>
    Review all content of the novel. Instructions from project leader:
    <blockquote style="width: 500px; font-style: italic; background-color: lightgray">
        &nbsp; {{ review_instructions }}
    </blockquote>
<p>
<table>
    <tr>
        <th style="text-align: right">Title of the Novel:</th>
        <td><input name="title" value='{{ title | e }}' style="width: 500px"></td>
    </tr>
    <tr>
        <th style="text-align: right; vertical-align: text-top">Prologue of the Novel:</th>
        <td>
            <textarea name="novel_prologue" style="height: 200px; width: 500px">{{ novel_prologue | e }}</textarea>
        </td>
    </tr>
    {% for index in range(chapter_count) %}
        {% if get_indexed_variable(project, "chapter_title", index) %}
            <tr>
                <th style="text-align: right; vertical-align: text-top">Chapter Title:</th>
                <td>
                    <input name="chapter_title" style="width: 500px" value="{{
                        get_indexed_variable(project, "chapter_title", index) | e }}"/>
                </td>
            </tr>
            <tr>
                <th style="text-align: right; vertical-align: text-top">Chapter:</th>
                <td>
                    <textarea name="chapter" style="height: 200px; width: 500px">{{
                        get_indexed_variable(project, "chapter", index) | e }}</textarea>
                </td>
            </tr>
        {% endif %}
    {% endfor %}
    <tr>
        <th style="text-align: right; vertical-align: text-top">Epilogue of the Novel:</th>
        <td>
            <textarea name="novel_epilogue" style="height: 200px; width: 500px">{{ novel_epilogue | e }}</textarea>
        </td>
    </tr>
</table>
        """, parent=novel_template).put()

    # Default values for variables
    Variable(name="font_size", internal_name="font_size", input_field=SMALL, content="14", parent=novel_template).put()

    Variable(name="font_family", internal_name="font_family", input_field=SMALL, content="Courier New",
             parent=novel_template).put()

    Variable(name="margin", internal_name="margin", input_field=SMALL, content="150", parent=novel_template).put()

    Variable(name="title", internal_name="title", input_field=MEDIUM, content="""
Sample Novel
        """, parent=novel_template).put()

    Variable(name="novel_prologue", internal_name="novel_prologue", input_field=LARGE,
             content="""
<p>
    This is where you write the prologue for the novel.
</p>
        """, parent=novel_template).put()

    Variable(name="chapter_title[0]", internal_name="chapter_title[0]", input_field=MEDIUM,
             content="""
Chapter One. A Beginning
        """, parent=novel_template).put()

    Variable(name="chapter[0]", internal_name="chapter[0]", input_field=LARGE,
             content="""
<p>
    It was a dark and stormy night. Snoopy was attempting to write his first novel.
</p>
<p>
    Suddenly, the sun came up and all was bright and cheerful. <i><u>Terrible</u></i> conditions for writing
    a novel. And even worse if the novel was to be your first. Snoopy felt sick.
</p>
        """, parent=novel_template).put()

    Variable(name="novel_epilogue", internal_name="novel_epilogue", input_field=LARGE,
             content="""
<p>
    This is where you write the epilogue for the novel.
</p>
        """, parent=novel_template).put()
'''
