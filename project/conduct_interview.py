import re
import urllib

import webapp2
from google.appengine.api import users

import dao
import ui
from service.interview_service import InterviewService

dot_pattern_with_one_group = re.compile(r'(.*)\.\d*')
indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')


class RequestHandler(webapp2.RequestHandler):
    def assign_email(self, interview, interview_service, email, index):
        # Generate assignment
        if index:
            assigned_interview = interview_service.clone_hierarchy(interview.assign_interview_name, index)
        else:
            assigned_interview = interview_service.get_interview_by_name(interview.assign_interview_name)
        assigned_interview.assigned_email = email

        assignment_name = self.request.get(u'_assignment_name')
        if not assignment_name:
            assignment_name = interview.assignment_name
        if assignment_name:
            assigned_interview.assignment_name = assigned_interview.menu_title = assignment_name

        manager_instructions_to_writer = self.request.get(u'_manager_instructions_to_writer')
        if manager_instructions_to_writer:
            assigned_interview.manager_instructions_to_writer = manager_instructions_to_writer

        assigned_interview.put()
        interview.assigned_interview_id = assigned_interview.key.id()
        interview.put()
        # Generate "generate_after" interview if specified
        match = dot_pattern_with_one_group.match(interview.name)
        if match:
            basename = match.group(1)
            for interview_name in interview_service.get_root_interview_names():
                match2 = dot_pattern_with_one_group.match(interview_name)
                if not match2:
                    interview_to_generate = interview_service.get_interview_by_name(interview_name)
                    if interview_to_generate.generate_after == basename:
                        cloned_interview = interview_service.clone_hierarchy(interview_name, interview.assigned_index)
                        cloned_interview.assigned_email = users.get_current_user().email().lower()
                        cloned_interview.assigned_index = int(index)
                        if assignment_name:
                            cloned_interview.assignment_name = cloned_interview.menu_title = assignment_name
                        cloned_interview.put()

    def fill(self, s):
        return s if s else u''

    def generate_email_assignment(self, project, interview, interview_service, inner_template_values):
        if interview.assign_button:
            inner_template_values[u'emails'] = [project_user.email for project_user in
                                                dao.get_project_users(project)]
            assigned_interview = interview_service.get_interview_by_name(interview.assign_interview_name)
            if assigned_interview:
                inner_template_values[u'_email'] = assigned_interview.assigned_email

    def generate_variable_value(self, inner_template_values, variable):
        match = indexed_name_pattern.match(variable.internal_name)
        internal_name = match.group(1) if match else variable.internal_name
        inner_template_values[internal_name] = self.fill(variable.content)

    def generate_variable_values(self, project, index, inner_template_values):
        indexed_variable_max_indices = dict()
        for variable in dao.get_variables(project):
            indexed_variable_match_object = indexed_name_pattern.match(variable.name)
            if indexed_variable_match_object:
                variable_name = indexed_variable_match_object.group(1)
                variable_index = indexed_variable_match_object.group(2)
                if index and int(variable_index) == int(index):
                    self.generate_variable_value(inner_template_values, variable)
                old_max_index = indexed_variable_max_indices[
                    variable_name] if variable_name in indexed_variable_max_indices else None
                if not old_max_index or int(variable_index) > old_max_index:
                    indexed_variable_max_indices[variable_name] = int(variable_index)
            else:
                self.generate_variable_value(inner_template_values, variable)
        for variable_name in iter(indexed_variable_max_indices):
            count_name = u'{}_count'.format(variable_name)
            count = int(indexed_variable_max_indices[variable_name]) + 1
            inner_template_values[count_name] = count

    def get(self):
        project = dao.get_project_by_id(self.request.get(u'_project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        interview_service = InterviewService(project)
        interview_name = self.request.get(u'_interview_name')
        interview = interview_service.get_interview_by_name(interview_name)

        if interview_name.startswith(u'review_'):
            any_checkmarks = False
            for checklist_item in interview.checklist_items:
                if u'[T]' in checklist_item:
                    any_checkmarks = True
            if not any_checkmarks:
                for prereq_interview in interview_service.get_prereq_interviews(interview):
                    if prereq_interview.name.startswith(u'write_'):
                        interview.checklist_items = prereq_interview.checklist_items
                        interview.put()

        index = self.request.get(u'_index')

        self.render(project, interview_name, interview_service, index)

    def merge_checklists(self, writer_interview, reviewer_interview):
        any_change = False
        for index in range(len(writer_interview.checklist_items)):
            writer_match = dao.parse_checklist_item(writer_interview.checklist_items[index])
            reviewer_match = dao.parse_checklist_item(reviewer_interview.checklist_items[index])
            if writer_match and reviewer_match:
                if writer_match.group(2) != reviewer_match.group(2):
                    any_change = True
                    reviewer_interview.checklist_items[index] = re.sub(r'\[[TF]\]',
                                                                       u'[{}]'.format(writer_match.group(2)),
                                                                       reviewer_interview.checklist_items[index],
                                                                       count=1)
        if any_change:
            reviewer_interview.put()

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'_project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        index = self.request.get(u'_index')
        from_console = self.request.get(u'_from_console')
        from_document_id = self.request.get(u'_from_document_id')

        self.store_variables(project, index)

        # Execute requested navigation
        interview_service = InterviewService(project)
        interview_name = self.request.get(u'_post_interview_name')
        interview = interview_service.get_interview_by_name(interview_name)

        self.update_checklists(interview)
        if interview.name.startswith(u'write_') and interview.completed:
            reviewer_interview = interview_service.get_interview_by_name(u'review_{}'.format(interview.name[6:]))
            self.merge_checklists(interview, reviewer_interview)

        assignment_name = self.request.get(u'_assignment_name')
        if assignment_name:
            interview.assignment_name = assignment_name

        manager_instructions_to_writer = self.request.get(u'_manager_instructions_to_writer')
        if manager_instructions_to_writer:
            interview.manager_instructions_to_writer = manager_instructions_to_writer

        reviewer_comment = self.request.get(u'_reviewer_comment')
        if reviewer_comment:
            interview.reviewer_comment = reviewer_comment

        interview.put()

        project.any_interview_conducted = True
        project.put()

        if self.request.get(u'_previous'):
            self.render(project, interview_service.get_previous_name(interview_name), interview_service, index)
            return
        elif self.request.get(u'_next'):
            self.render(project, interview_service.get_next_name(interview_name), interview_service, index)
            return
        elif self.request.get(u'_assign'):
            email = self.request.get(u'_email')
            if email:
                self.assign_email(interview, interview_service, email, index)
                parent = interview_service.get_closest_ancestor_interview_with_content(interview.name)
                if parent:
                    self.render_parent(project, parent, interview_service)
                    return
            else:
                error_msg = u'Assign failed: You must select an email address'
                self.render(project, interview_name, interview_service, index, error_msg=error_msg)
                return
        elif self.request.get(u'_not_needed'):
            interview.assigned_interview_id = -1
            interview.put()
            parent = interview_service.get_closest_ancestor_interview_with_content(interview.name)
            if parent:
                self.render_parent(project, parent, interview_service)
                return
        elif self.request.get(u'_completed'):
            root_interview = interview_service.get_interview_by_name(interview.root_interview_name)
            root_interview.completed = True
            root_interview.put()
        elif self.request.get(u'_child'):
            if not interview.child_count:
                interview.child_count = 1
            cloned_interview = interview_service.clone_hierarchy(interview.name, interview.child_count)
            interview.child_count += 1
            interview.put()
            child_interview = interview_service.get_first_child_interview_with_content(cloned_interview.name)
            self.render(project, child_interview.name, interview_service, index=cloned_interview.assigned_index)
            return
        elif self.request.get(u'_parent'):
            root_interview = interview_service.get_interview_by_name(interview.root_interview_name)
            root_interview.completed = False
            root_interview.put()
            parent = interview_service.get_closest_ancestor_interview_with_content(interview.name)
            if parent:
                name = parent.name
                match = dot_pattern_with_one_group.match(name)
                if match:
                    name = match.group(1)
                self.render(project, name, interview_service, None)
                return
        else:
            for param in self.request.POST:
                if param.startswith(u'_choose_'):
                    query_string_dict = {u'_project_id': project.key.id(),
                                         u'_interview_name': interview_name.encode(u'utf-8'),
                                         u'_variable_name': param[8:].encode(u'utf-8')}
                    if index:
                        query_string_dict[u'_index'] = index
                    query_string = urllib.urlencode(query_string_dict)
                    self.redirect("/project/upload_file?{}".format(query_string))
                    return
        if from_console:
            self.redirect("/project_admin/console?project_id={}".format(project.key.id()))
        elif from_document_id:
            self.redirect("/project/produce_document?project_id={}&document_id={}".format(project.key.id(),
                          from_document_id))
        else:
            self.redirect("/project?project_id={}".format(project.key.id()))

    def render(self, project, interview_name, interview_service, index, error_msg=None):
        interview_service.set_bookmark(interview_name)
        interview = interview_service.get_interview_by_name(interview_name)

        # Render inner template
        inner_template_values = dict()

        inner_template_values[u'project'] = project
        inner_template_values[u'interview'] = interview
        inner_template_values[u'index'] = index

        inner_template_values[u'error_msg'] = error_msg

        self.generate_variable_values(project, index, inner_template_values)

        self.generate_email_assignment(project, interview, interview_service,
                                       inner_template_values)

        inner_template_values[u'assignment_name'] = self.fill(interview.assignment_name)
        inner_template_values[u'writer'] = interview.is_writer_interview
        inner_template_values[u'reviewer'] = not interview.is_writer_interview
        inner_template_values[u'reviewer_comment'] = self.fill(interview.reviewer_comment)
        inner_template_values[
            u'manager_instructions_to_writer'] = self.fill(interview.manager_instructions_to_writer)

        inner_template_values[u'has_been_reviewed'] = interview.has_been_reviewed

        from_document_id = self.request.get(u'_from_document_id')
        if from_document_id:
            inner_template_values[u'from_document_id'] = from_document_id

        for checklist_index in range(len(interview.checklist_items)):
            checklist_item = interview.checklist_items[checklist_index]
            match = dao.parse_checklist_item(checklist_item)
            inner_template_values[u'writer_check_{}'.format(checklist_index)] = (match.group(2) == u'T')
            inner_template_values[u'reviewer_check_{}'.format(checklist_index)] = (match.group(3) == u'T')

        inner_template = ui.from_string(self, interview.content)
        html_document = inner_template.render(inner_template_values)

        # Deliver HTTP response
        jinja_template = ui.get_template(self, u'project/conduct_interview.html')

        jinja_template_values = dao.get_standard_project_values(project)

        jinja_template_values[u'post_interview_name'] = interview_name
        if index:
            jinja_template_values[u'show_index'] = True
            jinja_template_values[u'index'] = index
        jinja_template_values[u'html_document'] = html_document

        if interview_service.get_previous_name(interview_name):
            jinja_template_values[
                u'previous_button'] = interview.previous_button if interview.previous_button else u'Previous'

        if interview_service.get_next_name(interview_name):
            jinja_template_values[
                u'next_button'] = interview.next_button if interview.next_button else u'Skip Assign'

        if interview.parent_button:
            jinja_template_values[u'parent_button'] = interview.parent_button

        if interview.child_interview_names:
            jinja_template_values[u'child_button'] = interview.child_button if interview.child_button else u'Add'

        jinja_template_values[u'assign_button'] = interview.assign_button

        if interview.not_needed_button:
            jinja_template_values[u'not_needed_button'] = interview.not_needed_button

        if interview.completed_button:
            jinja_template_values[u'completed_button'] = interview.completed_button

        if self.request.get(u'_from_console'):
            jinja_template_values[u'from_console'] = True

        from_document_id = self.request.get(u'_from_document_id')
        if from_document_id:
            jinja_template_values[u'from_document_id'] = from_document_id

        self.response.out.write(jinja_template.render(jinja_template_values))

    def render_parent(self, project, parent, interview_service):
        name = parent.name
        match = dot_pattern_with_one_group.match(name)
        if match:
            name = match.group(1)
        self.render(project, name, interview_service, None)

    def store_variables(self, project, index):
        # Note that posted parameters that are not variable names use an underscore prefix.
        for name in self.request.arguments():
            if name[0] != u'_':
                value = self.fill(self.request.get(name))
                variable_name = u'{}[{}]'.format(name, index) if index else name
                dao.set_variable(project, variable_name, value)

    def update_checklists(self, interview):
        for index in range(len(interview.checklist_items)):
            match = dao.parse_checklist_item(interview.checklist_items[index])
            if interview.is_writer_interview:
                writer_check = u'T' if self.request.get(u'_writer_check_{}'.format(index)) else u'F'
                reviewer_check = match.group(3)
            else:
                writer_check = match.group(2)
                reviewer_check = u'T' if self.request.get(u'_reviewer_check_{}'.format(index)) else u'F'
            interview.checklist_items[index] = u'{}[{}][{}]'.format(match.group(1), writer_check, reviewer_check)
