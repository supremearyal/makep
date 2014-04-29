import sys
import re
from string import Template


# regexes to match different parts of
# a makefile
variable_define_regex = re.compile('([a-zA-Z_]+)\s*=\s*(.*)$')
dependency_start_regex = re.compile('([a-zA-Z0-9_.]+)\s*:\s*(.*)$')
dependency_action_regex = re.compile('\t(.*)$')
empty_line_regex = re.compile('\s*$')


# exception class when an error is
# encountered parsing a makefile
class ParseErrorException(Exception):
    def __init__(self, line_number):
        self.line_number = line_number

    def __str__(self):
        error_string = 'Error occurred while parsing in line {}'
        return error_string.format(self.line_number)


# returns parsed makefile
#
# return dictionary of variables
# defined, graph of dependencies,
# actions for each target, and
# starting target
def parse_make_file(make_file_text):
    variables = dict()
    graph = dict()
    actions = dict()
    start_target = None
    current_target = None
    current_commands = list()

    for i, line in enumerate(make_file_text.split('\n')):
        variable_match = variable_define_regex.match(line)
        dependency_start_match = dependency_start_regex.match(line)
        dependency_action_match = dependency_action_regex.match(line)
        empty_line_match = empty_line_regex.match(line)

        parsing_dependencies = current_target is not None and \
                               dependency_action_match is not None

        if variable_match is not None:
            if current_target is not None:
                actions[current_target] = current_commands
            current_target = None
            current_commands = list()

            variable, definition = variable_match.groups()
            variables[variable] = definition
        elif dependency_start_match is not None:
            if current_target is not None:
                actions[current_target] = current_commands

            child, parents = dependency_start_match.groups()
            current_target = child
            current_commands = list()

            if start_target is None:
                start_target = child

            for parent in parents.split():
                if child not in graph:
                    graph[child] = list()
                graph[child].append(parent)
        elif parsing_dependencies:
            command, = dependency_action_match.groups()
            current_commands.append(command)
        elif empty_line_match is not None:
            if current_target is not None:
                actions[current_target] = current_commands
            current_target = None
            current_commands = list()
        else:
            raise ParseErrorException(i + 1)

    return variables, start_target, graph, actions


# perform dfs on graph using start_node
# note: not all nodes may get visited
#
# return topologically sorted actions
def depth_first_search(graph, start_node):
    nodes = graph.keys()
    visited = set()
    ordered_actions = []

    def depth_first_search_visit(node):
        if node in graph:
            for neighbor in graph[node]:
                if neighbor not in visited:
                    depth_first_search_visit(neighbor)
        visited.add(node)
        ordered_actions.append(node)

    depth_first_search_visit(start_node)

    return ordered_actions


# dummy function for topological sort
def topological_sort(graph, start_node):
    return depth_first_search(graph, start_node)


# substitute variables in text
def subsitute_variables(text, variables):
    template_text = re.sub(r'\$\(([a-zA-Z_]+)\)', r'$\1', text)
    return Template(template_text).substitute(variables)


def main():
    argc = len(sys.argv)
    if argc > 2:
        print('Usage: ./makep.py target')
        return

    make_file_path = 'makefile'
    with open(make_file_path) as make_file:
        variables, start_node, graph, actions = parse_make_file(make_file.read())
        if argc == 2:
            start_node = sys.argv[1]
        action_nodes = topological_sort(graph, start_node)
        for node in action_nodes:
            if node in actions:
                commands = '\n'.join(actions[node])
                if commands != '':
                    print(subsitute_variables(commands, variables))


if __name__ == "__main__":
    main()
