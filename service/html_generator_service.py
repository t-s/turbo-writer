import dao


class HtmlGeneratorService():
    def __init__(self, template):
        self.template = template

    def generate_all_assignments(self):
        for assignment in dao.get_assignments(self.template):
            self.generate_interview_html(assignment)

    def generate_all_documents(self):
        for document in dao.get_documents(self.template):
            self.generate_document_html(document)

    def generate_all_html(self):
        self.generate_all_assignments()
        self.generate_all_documents()

    def generate_document_html(self, document):
        html = u''
        style = dao.get_style_by_name(self.template, document.style_name)
        if style:
            html += u'<div style="{}">'.format(style.css)
        else:
            html += u'<div>'
        begin_repeating_group = False
        within_repeating_group = False
        end_repeating_group = False
        index_variable_name = None
        document_items = dao.get_document_items(document)
        for index in range(len(document_items)):
            document_item = document_items[index]
            item_type = document_item.item_type
            if item_type != dao.TEXT and not document_item.variable_name:
                continue;
            flow_control = document_item.flow_control
            # Set begin/within/end repeating group and index_variable_name
            if within_repeating_group:
                if flow_control == dao.END_REPEATING_GROUP:
                    end_repeating_group = True
            else:
                if flow_control == dao.CONTINUE_FLOW and item_type == dao.REPEATING_VARIABLE:
                    begin_repeating_group = True
                    within_repeating_group = True
                    end_repeating_group = True
                    index_variable_name = document_item.variable_name
                elif flow_control == dao.BEGIN_REPEATING_GROUP:
                    for index2 in range(index + 1, len(document_items)):
                        document_item2 = document_items[index2]
                        if not index_variable_name and document_item2.item_type == dao.REPEATING_VARIABLE:
                            index_variable_name = document_item2.variable_name
                            break
                        if document_item2.flow_control == dao.END_REPEATING_GROUP:
                            break
                    if index_variable_name:
                        begin_repeating_group = True
                        within_repeating_group = True

            # Generate HTML for the document item
            if begin_repeating_group:
                internal_index_variable_name = dao.convert_name_to_internal_name(index_variable_name)
                html += u'{{% if {}_count %}}'.format(internal_index_variable_name)
                html += u'{{% for index in range(1, {}_count) %}}'.format(internal_index_variable_name)
                begin_repeating_group = False
            style = dao.get_style_by_name(self.template, document_item.style_name)
            if item_type == dao.TEXT:
                html = self.update_html(html, document_item.text,
                                        style)  # TODO How do we guard against cross-site scripting?
            else:
                internal_variable_name = dao.convert_name_to_internal_name(document_item.variable_name)
                if item_type == dao.SINGLE_VARIABLE:
                    content = u'{{{{ {} }}}}'.format(
                        internal_variable_name)  # TODO How do we guard against cross-site scripting?
                    html = self.update_html(html, content, style)
                else:
                    content = u'{{{{ get_indexed_variable(project, "{}", index) }}}}'.format(
                        internal_variable_name)  # TODO How do we guard against cross-site scripting?
                    html = self.update_html(html, content, style)
            if end_repeating_group:
                html += u'{% endfor %}'
                html += u'{% endif %}'
                begin_repeating_group = False
                within_repeating_group = False
                end_repeating_group = False
                index_variable_name = None
        html += u'</div>'
        document.content = html
        document.put()

    def generate_assign_reviewer_interview_html(self, assignment):
        interview = dao.Interview(name=u'assign_reviewer_{}'.format(assignment.name),
                                  root_interview_name=u'assign_reviewer_{}'.format(assignment.name),
                                  menu_title=assignment.name, assign_button=u'Assign Reviewer',
                                  assign_interview_name=u'review_{}'.format(assignment.name),
                                  assignment_name=assignment.name, parent=self.template.key)
        html = u'<h3>Assign Reviewer for "{}"</h3>'.format(
            u'{{ assignment_name | e }}' if assignment.is_repeating else assignment.name)
        html += u'{% if error_msg %}<p>'
        html += u'<span class="error">{{ error_msg | e }}</span>'
        html += u'</p>{% endif %}'
        html += u'{% if assigned_email %}<p>Assignment completed:</p>'
        html += u'<blockquote><div style="width: 500px; background-color: lightgray">'
        html += u'{{ assigned_email | e }}</div></blockquote>'
        html += u'{% else %}<table width="100%">'
        html += u'<tr><th>Team Member:</th>'
        html += u'<td><select name="_email"><option value="">(Select team member)</option>'
        html += u'{% for email in emails %}<option value="{{ email | e }}">{{ email | e }}</option>{% endfor %}'
        html += u'</select></td></tr></table>{% endif %}'
        interview.content = html
        if assignment.is_repeating:
            interview.generate_after = u'assign_writer_{}'.format(assignment.name)
        else:
            interview.auto_assign = True
        interview.put()

    def generate_assign_writer_interview_html(self, assignment):
        interview = dao.Interview(name=u'assign_writer_{}'.format(assignment.name),
                                  root_interview_name=u'assign_writer_parent_{}'.format(assignment.name),
                                  menu_title=assignment.name, assign_button=u'Assign Writer',
                                  assign_interview_name=u'write_{}'.format(assignment.name),
                                  assignment_name=assignment.name, parent=self.template.key)
        html = u'<h3>Assign Writer for "{}"</h3>'.format(assignment.name)
        html += u'{% if error_msg %}<p>'
        html += u'<span class="error">{{ error_msg | e }}</span>'
        html += u'</p>{% endif %}'
        html += u'{% if assigned_email %}<p>Assignment completed:</p>'
        html += u'<blockquote><div style="width: 500px; background-color: lightgray">'
        html += u'{{ assigned_email | e }}</div></blockquote>'
        html += u'{% else %}'
        html += u'<p><blockquote style="width: 500px; font-style: italic; background-color: lightgray">'
        html += u'{}'.format(assignment.instructions_to_manager)
        html += u'</blockquote></p>'
        html += u'<table width="100%">'
        if assignment.is_repeating:
            html += u'<tr><th>Assignment Name of This {}</th>'.format(assignment.name)
            html += u'<td><input name="_assignment_name" value="{{ assignment_name | e }}"></td></tr>'
        html += u'<tr><th>Team Member:</th>'
        html += u'<td><select name="_email"><option value="">(Select team member)</option>'
        html += u'{% for email in emails %}<option value="{{ email | e }}">{{ email | e }}</option>{% endfor %}'
        html += u'</select></td></tr>'
        html += u'<tr><th>Instructions:</th>'
        html += u'<td>{}</td></tr>'.format(assignment.instructions_to_writer)
        html += u'<tr><th>Additional instructions:</th><td>'
        html += u'<textarea name="_manager_instructions_to_writer" style="height: 200px; width: 500px">'
        html += u'{{ manager_instructions_to_writer | e }}</textarea></td></tr>'
        html += u'<tr><th>Checklist:</th>'
        html += u'<td>'
        for checklist_item in assignment.checklist_items:
            html += u'<li>{}</li>'.format(checklist_item)
        html += u'</td></tr>'
        html += u'</table>{% endif %}'
        interview.content = html
        if assignment.is_repeating:
            interview.root_interview_name = u'assign_writer_parent_{}'.format(assignment.name)
        else:
            interview.root_interview_name = u'assign_writer_{}'.format(assignment.name)
            interview.auto_assign = True
        interview.put()

    def generate_assign_writer_parent_interview_html(self, assignment):
        interview = dao.Interview(name=u'assign_writer_parent_{}'.format(assignment.name),
                                  root_interview_name=u'assign_writer_parent_{}'.format(assignment.name),
                                  completed_button=u'Done', child_button=u'Add Writing Assignment',
                                  child_interview_names=[u'assign_writer_{}'.format(assignment.name)],
                                  menu_title=u'{}'.format(assignment.name), assignment_name=assignment.name,
                                  parent=self.template.key)

        html = u'<h3>Assign Writers for "{}"</h3>'.format(assignment.name)

        interview.content = html
        interview.auto_assign = True
        interview.put()

    def generate_interview_html(self, assignment):
        dao.delete_interviews_for_assignment(self.template, assignment)
        self.generate_assign_writer_interview_html(assignment)
        self.generate_assign_reviewer_interview_html(assignment)
        self.generate_writer_interview_html(assignment)
        self.generate_reviewer_interview_html(assignment)
        if assignment.is_repeating:
            self.generate_assign_writer_parent_interview_html(assignment)

    def generate_reviewer_interview_html(self, assignment):
        interview = dao.Interview(name=u'review_{}'.format(assignment.name),
                                  root_interview_name=u'review_{}'.format(assignment.name),
                                  prereq_interview_names=[u'write_{}'.format(assignment.name)],
                                  checklist_items=assignment.checklist_items, menu_title=assignment.name,
                                  parent_button=u'Save Incomplete Review', completed_button=u'Review Completed',
                                  assignment_name=assignment.name, parent=self.template.key)
        html = u'<h3>Review "{}"</h3>'.format(
            u'{{ assignment_name | e }}' if assignment.is_repeating else assignment.name)
        html += u'''
            <script type="text/javascript" src="https://www.dropbox.com/static/api/1/dropbox.js" id="dropboxjs"
            data-app-key="dnerajsj9p29gc3"></script>
            '''
        html += u'<p><blockquote style="width: 500px; font-style: italic; background-color: lightgray">'
        html += u'{}'.format(assignment.instructions_to_writer)
        html += u'</blockquote></p>'
        if assignment.checklist_items:
            html += u'<h4><i>Checklist</i></h4>'
            html += u'<p><table border="1" cellpadding="5" cellspacing="0" style="width: 700px">'
            for index in range(len(assignment.checklist_items)):
                html += u'<tr>'
                html += u'<td style="text-align: center">Writer<br/><input type="checkbox" name="_writer_check_{}"' \
                        u'{{% if writer_check_{} %}} checked{{% endif %}}{{% if not writer %}} disabled{{% endif %}}' \
                        u'></td>'.format(index, index)
                html += u'{% if not writer or has_been_reviewed %}'
                html += u'<td style="text-align: center">Reviewer<br/><input type="checkbox" name="_reviewer_check_{}"' \
                        u'{{% if reviewer_check_{} %}} checked{{% endif %}}{{% if not reviewer %}} disabled{{% endif %}}' \
                        u'></td>'.format(index, index)
                html += u'{% endif %}'
                html += u'<td>{}</td>'.format(assignment.checklist_items[index])
                html += u'</tr>'
            html += u'</table></p>'
        html += u'<h4><i>Reviewer Comments</i></h4>'
        html += u'<textarea name="_reviewer_comment" style="height: 100px; width: 700px">{{ reviewer_comment | e }}</textarea>'
        html += self.get_html_for_variables(assignment)
        interview.content = html
        interview.put()

    def generate_writer_interview_html(self, assignment):
        prereq_interview_names = list()
        for prereq_assignment_name in assignment.prereq_assignment_names:
            prereq_interview_names.append(u'review_{}'.format(prereq_assignment_name))
        interview = dao.Interview(name=u'write_{}'.format(assignment.name),
                                  root_interview_name=u'write_{}'.format(assignment.name),
                                  checklist_items=assignment.checklist_items, is_writer_interview=True,
                                  prereq_interview_names=prereq_interview_names, menu_title=assignment.name,
                                  parent_button=u'Save Draft', completed_button=u'Writing Completed',
                                  assignment_name=assignment.name, parent=self.template.key)
        html = u'<h3>Write "{}"</h3>'.format(
            u'{{ assignment_name | e }}' if assignment.is_repeating else assignment.name)
        html += u'''
            <script type="text/javascript" src="https://www.dropbox.com/static/api/1/dropbox.js" id="dropboxjs"
            data-app-key="dnerajsj9p29gc3"></script>
            '''
        html += u'<p><blockquote style="width: 500px; font-style: italic; background-color: lightgray">'
        html += u'{}'.format(assignment.instructions_to_writer)
        html += u'</blockquote></p>'
        html += u'<p><blockquote style="width: 500px; font-style: italic; background-color: lightgray">'
        html += u'{{ manager_instructions_to_writer }}'
        html += u'</blockquote></p>'
        if assignment.checklist_items:
            html += u'<h4><i>Checklist</i></h4>'
            html += u'<p><table border="1" cellpadding="5" cellspacing="0" style="width: 700px">'
            for index in range(len(assignment.checklist_items)):
                html += u'<tr>'
                html += u'<td style="text-align: center">Writer<br/><input type="checkbox" name="_writer_check_{}"' \
                        u'{{% if writer_check_{} %}} checked{{% endif %}}{{% if not writer %}} disabled{{% endif %}}' \
                        u'></td>'.format(index, index)
                html += u'{% if has_been_reviewed %}'
                html += u'<td style="text-align: center">Reviewer<br/><input type="checkbox" name="_reviewer_check_{}"' \
                        u'{{% if reviewer_check_{} %}} checked{{% endif %}}{{% if not reviewer %}} disabled{{% endif %}}' \
                        u'></td>'.format(index, index)
                html += u'{% endif %}'
                html += u'<td>{}</td>'.format(assignment.checklist_items[index])
                html += u'</tr>'
            html += u'</table></p>'
        html += self.get_html_for_variables(assignment)
        interview.content = html
        interview.put()

    def get_html_for_variables(self, assignment):
        html = u'<p><table>'
        for variable_name in assignment.variable_names:
            variable = dao.get_variable_by_name(self.template, variable_name)
            if variable:
                html += u'<tr>'
                html += u'<th>{}:</th>'.format(variable_name)
                if variable.input_field == dao.SMALL:
                    html += u'<td><input name="{}" value="{{{{ {} | e }}}}"></td>'.format(variable.internal_name,
                                                                                          variable.internal_name)
                elif variable.input_field == dao.MEDIUM:
                    html += u'<td><input name="{}" style="width: 500px" value="{{{{ {} | e }}}}"></td>'.format(
                        variable.internal_name, variable.internal_name)
                elif variable.input_field == dao.LARGE:
                    html += u'<td><textarea name="{}" style="height: 200px; width: 500px">{{{{ {} | e }}}}</textarea></td>'.format(
                        variable.internal_name, variable.internal_name)
                else:
                    html += u'<td>'

                    html += u'{{% if {}_filename %}}'.format(variable.internal_name)
                    html += u'<a href="/project/download_file/{{{{ {}_blob_key }}}}?filename={{{{ {}_filename }}}}'.format(
                        variable.internal_name, variable.internal_name)
                    html += u'">Click here</a> to download "{{{{ {}_filename }}}}" for viewing and editing<br/><br/>'.format(
                        variable.internal_name)
                    html += u'{% endif %}'

                    html += u'To upload into TurboWriter:<br/><br/>'

                    html += u'<input type="submit"'
                    html += u' style="background-color: #f8f8f8; border-color: #eeeeee; border-radius: 3px; border-width: 1px; color: #777777; font-weight: bold; height: 25px; width: 152px;"'
                    html += u' value="Choose from Disk" name="'
                    html += u'_choose_{}'.format(variable.internal_name)
                    html += u'"><br/><br/>'

                    html += u'<input type="dropbox-chooser" name="{}" style="visibility: hidden;" data-link-type="direct"/>'.format(
                        variable.internal_name)

                    html += u'</td>'
                html += u'</tr>'
        html += u'</table></p>'
        return html

    def update_html(self, html, content, style):
        if content:
            if style:
                html += u'<p><span style="{}">{}</span></p>'.format(style.css, content)
            else:
                html += u'<p>{}</p>'.format(content)
        return html
