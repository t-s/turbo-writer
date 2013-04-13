import dao


class HtmlGeneratorService():
    def __init__(self, template):
        self.template = template

    def generate_all_html(self):
        for assignment in dao.get_assignments(self.template):
            self.generate_interview_html(assignment)
        for document in dao.get_documents(self.template):
            self.generate_document_html(document)

    def generate_document_html(self, document):
        html = ""
        style = dao.get_style_by_name(self.template, document.style_name)
        if style:
            html += "<div style=\"{}\">".format(style.css)
        else:
            html += "<div>"
        begin_repeating_group = False
        within_repeating_group = False
        end_repeating_group = False
        index_variable_name = None
        document_items = dao.get_document_items(document)
        for index in range(len(document_items)):
            document_item = document_items[index]
            item_type = document_item.item_type
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
                html += "{{% if {}_count %}}".format(internal_index_variable_name)
                html += "{{% for index in range(1, {}_count) %}}".format(internal_index_variable_name)
                begin_repeating_group = False
            style = dao.get_style_by_name(self.template, document_item.style_name)
            if item_type == dao.TEXT:
                html = self.update_html(html, document_item.text,
                                        style) # TODO How do we guard against cross-site scripting?
            else:
                internal_variable_name = dao.convert_name_to_internal_name(document_item.variable_name)
                if item_type == dao.SINGLE_VARIABLE:
                    content = "{{{{ {} }}}}".format(
                        internal_variable_name) # TODO How do we guard against cross-site scripting?
                    html = self.update_html(html, content, style)
                else:
                    content = "{{{{ get_indexed_variable(project, '{}', index) }}}}".format(
                        internal_variable_name) # TODO How do we guard against cross-site scripting?
                    html = self.update_html(html, content, style)
            if end_repeating_group:
                html += "{% endfor %}"
                html += "{% endif %}"
                begin_repeating_group = False
                within_repeating_group = False
                end_repeating_group = False
                index_variable_name = None
        html += "</div>"
        document.content = html
        document.put()

    def generate_assign_reviewer_interview_html(self, assignment):
        interview = dao.Interview(name="assign_reviewer_{}".format(assignment.name),
                                  root_interview_name="assign_reviewer_{}".format(assignment.name),
                                  menu_title=assignment.name, assign_button="Assign Reviewer",
                                  assign_interview_name="review_{}".format(assignment.name), parent=self.template.key)
        html = "<h3>Assign Reviewer for \"{}\"</h3>".format(
            "{{ assignment_name | e }}" if assignment.is_repeating else assignment.name)
        html += "{% if error_msg %}<p>"
        html += "<span class='error'>{{ error_msg | e }}</span>"
        html += "</p>{% endif %}"
        html += "{% if assigned_email %}<p>Assignment completed:</p>"
        html += "<blockquote><div style='width: 500px; background-color: lightgray'>"
        html += "{{ assigned_email | e }}</div></blockquote>"
        html += "{% else %}<table width='100%'>"
        html += "<tr><th>Team Member:</th>"
        html += "<td><select name='_email'><option value=''>(Select team member)</option>"
        html += "{% for email in emails %}<option value='{{ email | e }}'>{{ email | e }}</option>{% endfor %}"
        html += "</select></td></tr></table>{% endif %}"
        interview.content = html
        if assignment.is_repeating:
            interview.generate_after = "assign_writer_{}".format(assignment.name)
        else:
            interview.auto_assign = True
        interview.put()

    def generate_assign_writer_interview_html(self, assignment):
        interview = dao.Interview(name="assign_writer_{}".format(assignment.name),
                                  root_interview_name="assign_writer_parent_{}".format(assignment.name),
                                  menu_title=assignment.name, assign_button="Assign Writer",
                                  assign_interview_name="write_{}".format(assignment.name), parent=self.template.key)
        html = "<h3>Assign Writer for \"{}\"</h3>".format(assignment.name)
        html += "{% if error_msg %}<p>"
        html += "<span class='error'>{{ error_msg | e }}</span>"
        html += "</p>{% endif %}"
        html += "{% if assigned_email %}<p>Assignment completed:</p>"
        html += "<blockquote><div style='width: 500px; background-color: lightgray'>"
        html += "{{ assigned_email | e }}</div></blockquote>"
        html += "{% else %}"
        html += "<p><blockquote style='width: 500px; font-style: italic; background-color: lightgray'>"
        html += "{}".format(assignment.instructions_to_manager)
        html += "</blockquote></p>"
        html += "<table width='100%'>"
        if assignment.is_repeating:
            html += "<tr><th>Assignment Name of This {}</th>".format(assignment.name)
            html += "<td><input name='_assignment_name' value='{{ assignment_name | e }}'></td></tr>"
        html += "<tr><th>Team Member:</th>"
        html += "<td><select name='_email'><option value=''>(Select team member)</option>"
        html += "{% for email in emails %}<option value='{{ email | e }}'>{{ email | e }}</option>{% endfor %}"
        html += "</select></td></tr>"
        html += "<tr><th>Instructions:</th>"
        html += "<td>{}</td></tr>".format(assignment.instructions_to_writer)
        html += "<tr><th>Additional instructions:</th><td>"
        html += "<textarea name='_manager_instructions_to_writer' style='height: 200px; width: 500px'>"
        html += "{{ manager_instructions_to_writer | e }}</textarea></td></tr>"
        html += "<tr><th>Checklist:</th>"
        html += "<td>"
        for checklist_item in assignment.checklist_items:
            html += "<li>{}</li>".format(checklist_item)
        html += "</td></tr>"
        html += "</table>{% endif %}"
        interview.content = html
        if assignment.is_repeating:
            interview.root_interview_name = "assign_writer_parent_{}".format(assignment.name)
        else:
            interview.root_interview_name = "assign_writer_{}".format(assignment.name)
            interview.auto_assign = True
        interview.put()

    def generate_assign_writer_parent_interview_html(self, assignment):
        interview = dao.Interview(name="assign_writer_parent_{}".format(assignment.name),
                                  root_interview_name="assign_writer_parent_{}".format(assignment.name),
                                  completed_button="Done", child_button="Add Writing Assignment",
                                  child_interview_names="assign_writer_{}".format(assignment.name),
                                  menu_title="{}".format(assignment.name), parent=self.template.key)

        html = "<h3>Assign Writers for \"{}\"</h3>".format(assignment.name)

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
        interview = dao.Interview(name="review_{}".format(assignment.name),
                                  root_interview_name="review_{}".format(assignment.name),
                                  prereq_interview_names=["write_{}".format(assignment.name)],
                                  checklist_items=assignment.checklist_items,
                                  menu_title=assignment.name, parent_button="Save Incomplete Review",
                                  completed_button="Review Completed",
                                  parent=self.template.key)
        html = "<h3>Review \"{}\"</h3>".format(
            "{{ assignment_name | e }}" if assignment.is_repeating else assignment.name)
        html += """
            <script type="text/javascript" src="https://www.dropbox.com/static/api/1/dropbox.js" id="dropboxjs"
            data-app-key="dnerajsj9p29gc3"></script>
            """
        html += "<p><blockquote style='width: 500px; font-style: italic; background-color: lightgray'>"
        html += "{}".format(assignment.instructions_to_writer)
        html += "</blockquote></p>"
        if assignment.checklist_items:
            html += "<h4><i>Checklist</i></h4>"
            html += "<p><table border='1' cellpadding='5' cellspacing='0' style='width: 700px'>"
            for index in range(len(assignment.checklist_items)):
                html += "<tr>"
                html += "<td style='text-align: center'>Writer<br/><input type='checkbox' name='_writer_check_{}'" \
                        "{{% if writer_check_{} %}} checked{{% endif %}}{{% if not writer %}} disabled{{% endif %}}" \
                        "></td>".format(index, index)
                html += "{% if not writer or has_been_reviewed %}"
                html += "<td style='text-align: center'>Reviewer<br/><input type='checkbox' name='_reviewer_check_{}'" \
                        "{{% if reviewer_check_{} %}} checked{{% endif %}}{{% if not reviewer %}} disabled{{% endif %}}" \
                        "></td>".format(index, index)
                html += "{% endif %}"
                html += "<td>{}</td>".format(assignment.checklist_items[index])
                html += "</tr>"
            html += "</table></p>"
        html += "<h4><i>Reviewer Comments</i></h4>"
        html += "<textarea name='_reviewer_comment' style='height: 100px; width: 700px'>{{ reviewer_comment | e }}</textarea>"
        html += self.get_html_for_variables(assignment)
        interview.content = html
        interview.put()

    def generate_writer_interview_html(self, assignment):
        prereq_interview_names = list()
        for prereq_assignment_name in assignment.prereq_assignment_names:
            prereq_interview_names.append("review_{}".format(prereq_assignment_name))
        interview = dao.Interview(name="write_{}".format(assignment.name),
                                  root_interview_name="write_{}".format(assignment.name),
                                  checklist_items=assignment.checklist_items, is_writer_interview=True,
                                  prereq_interview_names=prereq_interview_names, menu_title=assignment.name,
                                  parent_button="Save Draft", completed_button="Writing Completed",
                                  parent=self.template.key)
        html = "<h3>Write \"{}\"</h3>".format(
            "{{ assignment_name | e }}" if assignment.is_repeating else assignment.name)
        html += """
            <script type="text/javascript" src="https://www.dropbox.com/static/api/1/dropbox.js" id="dropboxjs"
            data-app-key="dnerajsj9p29gc3"></script>
            """
        html += "<p><blockquote style='width: 500px; font-style: italic; background-color: lightgray'>"
        html += "{}".format(assignment.instructions_to_writer)
        html += "</blockquote></p>"
        html += "<p><blockquote style='width: 500px; font-style: italic; background-color: lightgray'>"
        html += "{{ manager_instructions_to_writer }}"
        html += "</blockquote></p>"
        if assignment.checklist_items:
            html += "<h4><i>Checklist</i></h4>"
            html += "<p><table border='1' cellpadding='5' cellspacing='0' style='width: 700px'>"
            for index in range(len(assignment.checklist_items)):
                html += "<tr>"
                html += "<td style='text-align: center'>Writer<br/><input type='checkbox' name='_writer_check_{}'" \
                        "{{% if writer_check_{} %}} checked{{% endif %}}{{% if not writer %}} disabled{{% endif %}}" \
                        "></td>".format(index, index)
                html += "{% if has_been_reviewed %}"
                html += "<td style='text-align: center'>Reviewer<br/><input type='checkbox' name='_reviewer_check_{}'" \
                        "{{% if reviewer_check_{} %}} checked{{% endif %}}{{% if not reviewer %}} disabled{{% endif %}}" \
                        "></td>".format(index, index)
                html += "{% endif %}"
                html += "<td>{}</td>".format(assignment.checklist_items[index])
                html += "</tr>"
            html += "</table></p>"
        html += self.get_html_for_variables(assignment)
        interview.content = html
        interview.put()

    def get_html_for_variables(self, assignment):
        html = "<p><table>"
        for variable_name in assignment.variable_names:
            variable = dao.get_variable_by_name(self.template, variable_name)
            if variable:
                html += "<tr>"
                html += "<th>{}:</th>".format(variable_name)
                if variable.input_field == dao.SMALL:
                    html += "<td><input name='{}' value='{{{{ {} | e }}}}'></td>".format(variable.internal_name,
                                                                                         variable.internal_name)
                elif variable.input_field == dao.MEDIUM:
                    html += "<td><input name='{}' style='width: 500px' value='{{{{ {} | e }}}}'></td>".format(
                        variable.internal_name, variable.internal_name)
                elif variable.input_field == dao.LARGE:
                    html += "<td><textarea name='{}' style='height: 200px; width: 500px'>{{{{ {} | e }}}}</textarea></td>".format(
                        variable.internal_name, variable.internal_name)
                else:
                    html += "<td>"

                    html += "{{% if {}_filename %}}".format(variable.internal_name)
                    html += "<a href='/project/download_file/{{{{ {}_blob_key }}}}?filename={{{{ {}_filename }}}}".format(
                        variable.internal_name, variable.internal_name)
                    html += "'>Click here</a> to download \"{{{{ {}_filename }}}}\" for viewing and editing<br/><br/>".format(
                        variable.internal_name)
                    html += "{% endif %}"

                    html += "To upload into TurboWriter:<br/><br/>"

                    html += "<input type='button'"
                    html += " style='background-color: #f8f8f8; border-color: #eeeeee; border-radius: 3px; border-width: 1px; color: #777777; font-weight: bold; height: 25px; width: 152px;'"
                    html += " value='Choose from Disk' onclick='"
                    html += "document.location=\"/project/upload_file?_project_id={{ project.key.id() }}&"
                    html += "_interview_name={{{{ interview.name }}}}&_variable_name={}".format(variable.internal_name)
                    html += "{% if index %}&_index={{ index }}{% endif %}\""
                    html += "'><br/><br/>"

                    html += "<input type='dropbox-chooser' name='{}' style='visibility: hidden;' data-link-type='direct'/>".format(
                        variable.internal_name)

                    html += "</td>"
                html += "</tr>"
        html += "</table></p>"
        return html

    def update_html(self, html, content, style):
        if content:
            if style:
                html += "<p><span style=\"{}\">{}</span></p>".format(style.css, content)
            else:
                html += "<p>{}</p>".format(content)
        return html
