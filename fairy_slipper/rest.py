# Copyright (c) 2015 Russell Sim <russell.sim@gmail.com>
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""

"""
import logging

from docutils import writers, nodes
from docutils.writers import html4css1
from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive

logger = logging.getLogger(__name__)


MIME_MAP = {
    'json': 'application/json',
    'txt': 'text/plain',
    'xml': 'application/xml',
}


def search_node_parents(node, node_name):
    parent = node
    while parent.parent:
        if parent.tagname == node_name:
            return node
        parent = parent.parent
    if parent.tagname == node_name:
        return node


class JSONTranslator(nodes.GenericNodeVisitor):
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.output = {}
        self.node_stack = []
        self.node_stack.append(self.output)
        self.current_node_name = None

    def search_stack_for(self, tag_name):
        for node in self.node_stack:
            # Skip any list elements, this is a hack, but it' works
            # for now.
            if isinstance(node, (list, str, unicode)):
                continue
            if tag_name in node.keys():
                return node

    def default_visit(self, node):
        """Default node visit method."""
        self.current_node_name = node.__class__.__name__
        if hasattr(node, 'children') and node.children:
            new_node = {}
            try:
                self.node_stack[-1][self.current_node_name] = new_node
            except:
                import pdb; pdb.set_trace()  # FIXME
            self.node_stack.append(new_node)

    def default_departure(self, node):
        """Default node depart method."""
        self.node_stack.pop()

    def visit_Text(self, node):
        # Skip if in a field, it will have special parsing.
        if self.search_stack_for('field_list') \
           or search_node_parents(node, 'resource_url') \
           or search_node_parents(node, 'resource_method') \
           or search_node_parents(node, 'resource_summary'):
            return
        if isinstance(self.node_stack[-1], list):
            self.node_stack[-1].append(node.astext())
        else:
            self.node_stack[-1] += node.astext()

    def depart_Text(self, node):
        pass

    def visit_literal(self, node):
        literal = '`%s` ' % node.astext()
        if isinstance(self.node_stack[-1], list):
            self.node_stack[-1].append(literal)
        else:
            self.node_stack[-1] += node.astext()

    def depart_literal(self, node):
        pass

    def visit_title(self, node):
        self.current_node_name = node.__class__.__name__
        if self.current_node_name not in self.node_stack[-1]:
            new_node = []
            self.node_stack[-1][self.current_node_name] = new_node
            self.node_stack.append(new_node)

    def depart_title(self, node):
        self.node_stack.pop()

    def visit_paragraph(self, node):
        if isinstance(self.node_stack[-1], list):
            return

        self.current_node_name = node.__class__.__name__
        if self.current_node_name not in self.node_stack[-1]:
            new_node = []
            self.node_stack[-1][self.current_node_name] = new_node
            self.node_stack.append(new_node)
        else:
            self.node_stack.append(self.node_stack[-1][self.current_node_name])

    def depart_paragraph(self, node):
        if isinstance(self.node_stack[-1], list):
            self.node_stack.pop()
        paragraph = ''.join(self.node_stack[-1]['paragraph'])
        paragraph = paragraph.replace('\n', ' ')
        print repr(paragraph)
        del self.node_stack[-1]['paragraph']
        self.node_stack[-1]['description'] = '\n\n'.join(
            [self.node_stack[-1]['description'],
             paragraph])

    def visit_line_block(self, node):
        if isinstance(self.node_stack[-1], list):
            return

        self.current_node_name = node.__class__.__name__
        if self.current_node_name not in self.node_stack[-1]:
            new_node = []
            self.node_stack[-1][self.current_node_name] = new_node
            self.node_stack.append(new_node)
        else:
            self.node_stack.append(self.node_stack[-1][self.current_node_name])

    def depart_line_block(self, node):
        if isinstance(self.node_stack[-1], list):
            self.node_stack.pop()

    def visit_resource(self, node):
        if 'paths' not in self.node_stack[-1]:
            self.node_stack[-1]['paths'] = {}
        self.node_stack.append(self.node_stack[-1]['paths'])

    def depart_resource(self, node):
        self.node_stack.pop()
        self.node_stack.pop()

    def visit_resource_url(self, node):
        url_path = node.astext()
        if url_path not in self.node_stack[-1]:
            self.node_stack[-1][url_path] = []
        new_node = {'responses': {},
                    'parameters': [],
                    'description': '',
                    'tags': []}
        self.node_stack[-1][url_path].append(new_node)
        self.node_stack.append(new_node)

    def depart_resource_url(self, node):
        pass

    def visit_resource_summary(self, node):
        summary = node.astext()
        self.node_stack[-1]['summary'] = summary
        node.clear()

    def depart_resource_summary(self, node):
        pass

    def visit_resource_method(self, node):
        method = node.astext()
        self.node_stack[-1]['method'] = method
        node.clear()

    def depart_resource_method(self, node):
        pass

    def visit_field_list(self, node):
        pass

    def depart_field_list(self, node):
        pass

    def visit_field(self, node):
        name = node.attributes['names'][0]
        resource = self.node_stack[-1]
        new_response = {'description': ''}
        if name == 'statuscode':
            responses = resource['responses']
            status_code = node[0].astext()
            description = node[1].astext()
            if status_code not in responses:
                responses[status_code] = new_response
            responses[status_code]['description'] = description
        elif name == 'responseexample':
            responses = resource['responses']
            status_code = node[0].astext()
            filepath = node[1].astext()
            if status_code not in responses:
                responses[status_code] = new_response
            ext = filepath.rsplit('.', 1)[1]
            mimetype = MIME_MAP[ext]
            if 'examples' not in responses[status_code]:
                responses[status_code]['examples'] = {}
            responses[status_code]['examples'][mimetype] = {'$ref': filepath}
        elif name == 'requestexample':
            status_code = node[0].astext()
            filepath = node[1].astext()
            ext = filepath.rsplit('.', 1)[1]
            mimetype = MIME_MAP[ext]
            if 'examples' not in resource:
                resource['examples'] = {}
            resource['examples'][mimetype] = {'$ref': filepath}
        elif name == 'requestschema':
            filepath = node[1].astext()
            resource['parameters'].append(
                {'name': 'body',
                 'in': 'body',
                 'required': True,
                 'schema': {'$ref': filepath}})
        elif name == 'parameter':
            param_name = node[1].astext()
            resource['parameters'].append(
                {'name': param_name,
                 'in': 'path',
                 'type': 'string',
                 'required': True})
        elif name == 'query':
            param_name = node[1].astext()
            resource['parameters'].append(
                {'name': param_name,
                 'in': 'query',
                 'type': 'string',
                 'required': False})
        elif name == 'tag':
            tag = node[1].astext()
            resource['tags'].append(tag)

        node.clear()

    def depart_field(self, node):
        pass

    def visit_field_name(self, node):
        self.node_stack[-1]['name'] = node.astext()

    def depart_field_name(self, node):
        pass

    def visit_field_body(self, node):
        self.node_stack[-1]['type'] = node.astext()

    def depart_field_body(self, node):
        pass

    def visit_field_type(self, node):
        self.node_stack[-1]['type'] = node.astext()

    def depart_field_type(self, node):
        pass


class JSONWriter(writers.Writer):

    supported = ('json',)
    """Formats this writer supports."""

    settings_spec = (
        '"Docutils JSON" Writer Options',
        None,
        [])

    config_section = 'docutils_json writer'
    config_section_dependencies = ('writers',)

    output = None

    def __init__(self):
        writers.Writer.__init__(self)
        self.translator_class = JSONTranslator

    def translate(self):
        self.visitor = visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.output


class field_type(nodes.Part, nodes.TextElement):
    pass


class resource(nodes.Inline, nodes.TextElement):
    pass


class resource_url(nodes.Admonition, nodes.TextElement):
    pass


class resource_summary(nodes.Admonition, nodes.TextElement):
    pass


class resource_method(nodes.Admonition, nodes.TextElement):
    pass


class Field(object):
    def __init__(self, name, names=(), label=None,
                 has_arg=True, rolename=None):
        self.name = name
        self.names = names
        self.label = label
        self.has_arg = has_arg
        self.rolename = rolename

    @classmethod
    def transform(cls, node):
        node.attributes['names'].append(node[0].astext())


class TypedField(Field):
    def __init__(self, name, names=(), label=None,
                 has_arg=True, rolename=None,
                 typerolename='', typenames=()):
        super(TypedField, self).__init__(
            name=name,
            names=names,
            label=label,
            has_arg=has_arg,
            rolename=rolename)
        self.typerolename = typerolename
        self.typenames = typenames

    @classmethod
    def transform(cls, node):
        split = node[0].rawsource.split(None, 2)
        type = None
        if len(split) == 3:
            name, type, value = split
        elif len(split) == 2:
            name, value = split
        else:
            raise Exception('Too Few arguments.')
        node.attributes['names'].append(name)
        if type:
            node.insert(1, field_type(type))
        node[0].replace_self(nodes.field_name(value, value))


class GroupedField(Field):

    @classmethod
    def transform(cls, node):
        name, value = node[0].rawsource.split(None, 1)
        node.attributes['names'].append(name)
        node[0].replace_self(nodes.field_name(value, value))


class Resource(Directive):

    method = None

    required_arguments = 0
    optional_arguments = 0
    has_content = True
    final_argument_whitespace = True

    doc_field_types = [
        TypedField('parameter', label='Parameters',
                   names=('param', 'parameter', 'arg', 'argument'),
                   typerolename='obj', typenames=('paramtype', 'type')),
        TypedField('jsonparameter', label='JSON Parameters',
                   names=('jsonparameter', 'jsonparam', 'json'),
                   typerolename='obj', typenames=('jsonparamtype', 'jsontype')),
        TypedField('requestjsonobject', label='Request JSON Object',
                   names=('reqjsonobj', 'reqjson', '<jsonobj', '<json'),
                   typerolename='obj', typenames=('reqjsonobj', '<jsonobj')),
        TypedField('requestjsonarray', label='Request JSON Array of Objects',
                   names=('reqjsonarr', '<jsonarr'),
                   typerolename='obj',
                   typenames=('reqjsonarrtype', '<jsonarrtype')),
        TypedField('responsejsonobject', label='Response JSON Object',
                   names=('resjsonobj', 'resjson', '>jsonobj', '>json'),
                   typerolename='obj', typenames=('resjsonobj', '>jsonobj')),
        TypedField('responsejsonarray', label='Response JSON Array of Objects',
                   names=('resjsonarr', '>jsonarr'),
                   typerolename='obj',
                   typenames=('resjsonarrtype', '>jsonarrtype')),
        TypedField('queryparameter', label='Query Parameters',
                   names=('queryparameter', 'queryparam', 'qparam', 'query'),
                   typerolename='obj',
                   typenames=('queryparamtype', 'querytype', 'qtype')),
        GroupedField('formparameter', label='Form Parameters',
                     names=('formparameter', 'formparam', 'fparam', 'form')),
        GroupedField('requestheader', label='Request Headers',
                     rolename='header',
                     names=('<header', 'reqheader', 'requestheader')),
        GroupedField('responseheader', label='Response Headers',
                     rolename='header',
                     names=('>header', 'resheader', 'responseheader')),
        GroupedField('statuscode', label='Status Codes',
                     rolename='statuscode',
                     names=('statuscode', 'status', 'code')),

        # Swagger Extensions
        GroupedField('responseexample', label='Response Example',
                     rolename='responseexample',
                     names=('swagger-response', 'responseexample')),
        Field('requestexample', label='Request Example',
              rolename='requestexample',
              names=('swagger-request', 'requestexample')),
        Field('requestschema', label='Request Schema',
              rolename='requestschema',
              names=('swagger-schema', 'requestschema')),
        Field('tag',
              label='Swagger Tag',
              rolename='tag',
              names=('swagger-tag', 'tag'))
    ]

    option_spec = {
        'synopsis': lambda x: x,
    }

    def transform_fields(self):
        return {name: f
                for f in self.doc_field_types
                for name in f.names}

    def run(self):
        node = nodes.line_block()
        node = resource()
        self.state.nested_parse(self.content, self.content_offset, node)
        fields = self.transform_fields()

        if node[0].tagname == 'system_message':
            logger.error(node[0].astext())
            node.remove(node[0])
        # This is the first line of the definition.
        url = node[0].astext()
        node[0].replace_self(resource_url(url, url))

        # Method
        node.insert(1, resource_method(self.method, self.method))

        # Summary
        summary = self.options.get('synopsis', '')
        node.insert(1, resource_summary(summary, summary))

        # Generate field lists
        for child in node:
            if isinstance(child, nodes.field_list):
                for field in child:
                    name = field[0].rawsource.split(None, 1)[0]
                    fields[name].transform(field)
        return [node]


class HTTPGet(Resource):

    method = 'get'


class HTTPPost(Resource):

    method = 'post'


class HTTPPut(Resource):

    method = 'put'


class HTTPPatch(Resource):

    method = 'patch'


class HTTPOptions(Resource):

    method = 'options'


class HTTPHead(Resource):

    method = 'head'


class HTTPDelete(Resource):

    method = 'delete'


directives.register_directive('http:get', HTTPGet)
directives.register_directive('http:post', HTTPPost)
directives.register_directive('http:put', HTTPPut)
directives.register_directive('http:patch', HTTPPatch)
directives.register_directive('http:options', HTTPOptions)
directives.register_directive('http:head', HTTPHead)
directives.register_directive('http:delete', HTTPDelete)
