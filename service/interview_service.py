import re

import dao

interview_name_pattern = re.compile(r"(.*)\.\d*")
interview_basename_pattern1 = re.compile(r"(.*_)*(.*)\.\d*")
interview_basename_pattern2 = re.compile(r"(.*_)*(.*)")


class InterviewService():
    def __init__(self, project):
        self.project = project
        self.interviews = dao.get_interviews(project)
        self.sort_interviews_by_dependency()

    def are_prereqs_complete(self, i1):
        if i1.prereq_interview_names:
            for prereq_interview_name in i1.prereq_interview_names:
                re1 = interview_name_pattern.match(prereq_interview_name)
                n1 = re1.group(1) if re1 else prereq_interview_name
                prereq_found = False
                for i2 in self.interviews:
                    if i2.assigned_email:
                        re2 = interview_name_pattern.match(i2.name)
                        n2 = re2.group(1) if re2 else i2.name
                        if n1 == n2:
                            # If either of the interviews doesn't have an assigned index, or they they both do
                            # and the assigned indexes are the same, check whether the prereq is complete
                            try:
                                if int(i1.assigned_index) != int(i2.assigned_index):
                                    continue
                            except:
                                pass
                            prereq_found = True
                            if not i2.completed:
                                return False
                if not prereq_found:
                    return False
        return True

    def clone_hierarchy(self, interview_name, suffix, internal=False):
        interview = self.get_interview_by_name(interview_name)
        if interview:
            cloned_interview = interview.clone(self.project, suffix)
            cloned_interview.assigned_index = int(suffix)
            cloned_interview.put()
            child_interview_names = []
            if cloned_interview.child_interview_names:
                child_interview_names = str(cloned_interview.child_interview_names).split("|")
            for child_interview_name in child_interview_names:
                tokens = child_interview_name.split(".")
                child_interview_name_base = ".".join(tokens[0:len(tokens) - 1])
                self.clone_hierarchy(child_interview_name_base, suffix, internal=True)
            if not internal:
                self.__init__(self.project)
            return cloned_interview

    def delete_hierarchy(self, interview_name): # TODO Delete if not needed
        root_interview_name = self.get_interview_by_name(interview_name).root_interview_name
        for interview in self.interviews:
            if interview.root_interview_name == root_interview_name:
                interview.key.delete()
        self.__init__(self.project)

    def get_closest_ancestor_interview_with_content(self, interview_name):
        for interview in self.interviews:
            if interview.child_interview_names:
                child_interview_names = interview.child_interview_names.split("|")
                if interview_name in child_interview_names:
                    if interview.content:
                        return interview
                    return self.get_closest_ancestor_interview_with_content(interview.name)

    def get_first_child_interview_with_content(self, interview_name):
        interview = self.get_interview_by_name(interview_name)
        if interview and interview.child_interview_names:
            child_interview_names = interview.child_interview_names.split("|")
            return self.get_first_interview_with_content(child_interview_names[0].strip())

    def get_first_interview_with_content(self, root_interview_name):
        interview = self.get_interview_by_name(root_interview_name)
        while interview and not interview.content:
            if interview.child_interview_names:
                child_interview_names = interview.child_interview_names.split("|")
                interview = self.get_interview_by_name(child_interview_names[0].strip())
        return interview

    def get_dependent_interviews(self, i1):
        re1 = interview_name_pattern.match(i1.name)
        n1 = re1.group(1) if re1 else i1.name
        dependent_interviews = list()
        for i2 in self.interviews:
            if i2.prereq_interview_names:
                for prereq_interview_name in i2.prereq_interview_names:
                    re2 = interview_name_pattern.match(prereq_interview_name)
                    n2 = re2.group(1) if re2 else prereq_interview_name
                    if n1 == n2:
                        # If either of the interviews doesn't have an assigned index, or they they both do
                        # and the assigned indexes are the same, add i2 to the list of dependent interviews
                        try:
                            if int(i1.assigned_index) != int(i2.assigned_index):
                                continue
                        except:
                            pass
                        dependent_interviews.append(i2)
        return dependent_interviews

    def get_interview_by_id(self, interview_id):
        for interview in self.interviews:
            if interview.key.id() == interview_id:
                return interview

    def get_interview_by_name(self, interview_name):
        for interview in self.interviews:
            if interview.name == interview_name:
                return interview

    def get_names_by_dependency(self):
        # Create name_entries as a dictionary:
        # -- The key of each entry is an interview name.
        # -- The value of each entry is a set containing the names of all prerequisite interviews.
        name_entries = dict()
        for interview in self.interviews:
            match = interview_basename_pattern1.match(interview.name)
            if not match:
                match = interview_basename_pattern2.match(interview.name)
            if match:
                name = match.group(2)
                if name in name_entries:
                    name_entry = name_entries[name]
                else:
                    name_entry = set()
                    name_entries[name] = name_entry
                for prereq_name in interview.prereq_interview_names:
                    match = interview_basename_pattern1.match(prereq_name)
                    if not match:
                        match = interview_basename_pattern2.match(prereq_name)
                    if match:
                        prereq_basename = match.group(2)
                        if prereq_basename != name:
                            name_entry.add(prereq_basename)
        # Add entries to the list of names where all prereqs are already on the list
        names = list()
        any_changes = True
        while any_changes:
            any_changes = False
            for name, name_entry in name_entries.iteritems():
                if name_entry:
                    prereq_missing = False
                    for prereq_name in name_entry:
                        if prereq_name not in names:
                            prereq_missing = True
                            break
                    if not prereq_missing:
                        names.append(name)
                        del name_entries[name]
                        any_changes = True
                        break
                else:
                    names.append(name)
                    del name_entries[name]
                    any_changes = True
                    break
        # Add any entries for prereqs not met
        for name in name_entries.keys():
            names.append(name)
        return names

    def get_next_name(self, current_name):
        current_interview = self.get_interview_by_name(current_name)
        if current_interview:
            return self.get_next_name_in_child(current_interview.root_interview_name, current_name)

    def get_next_name_in_child(self, interview_name, current_name):
        interview = self.get_interview_by_name(interview_name)
        if interview and interview.child_interview_names and len(interview.child_interview_names):
            child_interview_names = interview.child_interview_names.split("|")
            try:
                index = child_interview_names.index(current_name)
                return child_interview_names[index + 1] if index < (len(child_interview_names) - 1) else None
            except:
                for child_name in child_interview_names:
                    self.get_next_name_in_child(child_name, current_name)

    def get_parent_interview(self, child_interview):
        for interview in self.interviews:
            if interview.child_interview_names:
                if child_interview.name in interview.child_interview_names.split("|"):
                    return interview

    def get_prereq_interviews(self, i1):
        prereq_interviews = list()
        for prereq_interview_name in i1.prereq_interview_names:
            re1 = interview_name_pattern.match(prereq_interview_name)
            n1 = re1.group(1) if re1 else prereq_interview_name
            for i2 in self.interviews:
                re2 = interview_name_pattern.match(i2.name)
                n2 = re2.group(1) if re2 else i2.name
                if n1 == n2:
                    # If either of the interviews doesn't have an assigned index, or they they both do
                    # and the assigned indexes are the same, check whether the prereq is complete
                    try:
                        if int(i1.assigned_index) != int(i2.assigned_index):
                            continue
                    except:
                        pass
                    prereq_interviews.append(i2)
        return prereq_interviews

    def get_previous_name(self, current_name):
        current_interview = self.get_interview_by_name(current_name)
        if current_interview:
            return self.get_previous_name_in_child(current_interview.root_interview_name,
                                                   current_name)

    def get_previous_name_in_child(self, interview_name, current_name):
        interview = self.get_interview_by_name(interview_name)
        if interview and interview.child_interview_names and len(interview.child_interview_names):
            child_interview_names = interview.child_interview_names.split("|")
            try:
                index = child_interview_names.index(current_name)
                return child_interview_names[index - 1] if index else None
            except:
                for child_name in child_interview_names:
                    self.get_previous_name_in_child(child_name, current_name)

    def get_root_interview_names(self):
        names = list()
        for interview in self.interviews: # Note that these are sorted by dependency
            if interview.root_interview_name not in names:
                names.append(interview.root_interview_name)
        return names

    def set_bookmark(self, interview_name):
        interview = self.get_interview_by_name(interview_name)
        dao.set_bookmark(self.get_interview_by_name(interview.root_interview_name),
                         self.get_interview_by_name(interview_name))

    def sort_interviews_by_dependency(self):
        names_by_dependency = self.get_names_by_dependency()
        sorted_interviews = list()
        for name in names_by_dependency:
            for interview in self.interviews:
                match = interview_basename_pattern1.match(interview.name)
                if not match:
                    match = interview_basename_pattern2.match(interview.name)
                test_name = match.group(2) if match else name # else-condition should never happen
                if test_name == name:
                    sorted_interviews.append(interview)
        self.interviews = sorted_interviews
