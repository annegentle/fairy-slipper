# Copyright (c) 2015 Russell Sim <russell.sim@gmail.com>
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

from unittest import TestCase
import docutils.core

from fairy_slipper import rest
from fairy_slipper.rest import JSONWriter


def minimal_method_json(consumes=[],
                        description='',
                        method='get',
                        parameters=[],
                        produces=[],
                        responses={},
                        summary='',
                        tags=[],
                        title=''):
    return dict(consumes=consumes,
                description=description,
                method=method,
                parameters=parameters,
                produces=produces,
                responses=responses,
                summary=summary,
                tags=tags,
                title=title)


class TestReSTMethod(TestCase):

    def test_no_path(self):
        rst = """
.. http:get::

"""
        json = rest.publish_string(rst)

        assert json == {'paths': {}, 'tags': []}

    def test_path_with_body(self):
        rst = """
.. http:get:: /path

   body

"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path': [
                            minimal_method_json(description='body\n\n')]},
                        'tags': []}

    def test_minimal(self):
        rst = """
.. http:%s:: /path

"""
        for method in ['get', 'post', 'put', 'patch',
                       'options', 'head', 'delete', 'copy']:
            json = docutils.core.publish_string(
                rst % method, writer=JSONWriter())

            assert json == {'paths':
                            {'/path': [
                                minimal_method_json(method=method)]},
                            'tags': []}

    def test_body_literal(self):
        rst = """
.. http:get:: /path

   literal block::

      banana
      1
      2
      3

"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(description='''literal block:

```
banana
1
2
3
```
''')]},
                        'tags': []}

    def test_body_ul(self):
        rst = """
.. http:get:: /path

   Some normal body text

   - the first item
   - the second item

"""

        markdown = '''Some normal body text


 * the first item


 * the second item

'''
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(description=markdown)]},
                        'tags': []}

    def test_synopsis(self):
        rst = """
.. http:get:: /path
   :synopsis: Some description of the operation
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             summary='Some description of the operation')]},
                        'tags': []}

    def test_title(self):
        rst = """
.. http:get:: /path
   :title: Path Thing
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(title='Path Thing')]},
                        'tags': []}

    def test_method_tags(self):
        rst = """
.. http:get:: /path

   :tag: cool-tag
   :tag: cool-tag1
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             tags=['cool-tag', 'cool-tag1'])]},
                        'tags': []}

    def test_produces(self):
        rst = """
.. http:get:: /path

   :produces: application/json
   :produces: text/plain
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             produces=['application/json',
                                       'text/plain'])]},
                        'tags': []}

    def test_accepts(self):
        rst = """
.. http:get:: /path

   :accepts: application/json
   :accepts: text/plain
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             consumes=['application/json',
                                       'text/plain'])]},
                        'tags': []}

    def test_parameter(self):
        rst = """
.. http:get:: /path

   :parameter thing: A parameter something.
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             parameters=[{
                                 'description': u'A parameter something.',
                                 'in': 'path',
                                 'name': u'thing',
                                 'required': True,
                                 'type': 'string'}])]},
                        'tags': []}

    def test_response_example(self):
        rst = """
.. http:get:: /path

   :responseexample 200: example.json
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             responses={'200':
                                        {'description': '',
                                         'examples':
                                         {'application/json':
                                          {'$ref':
                                           'example.json'}}}})]},
                        'tags': []}

    def test_statuscode(self):
        rst = """
.. http:get:: /path

   :statuscode 200: Success! Yeah!
"""
        json = rest.publish_string(rst)

        assert json == {'paths':
                        {'/path':
                         [minimal_method_json(
                             responses={'200':
                                        {'description': 'Success! Yeah!'}})]},
                        'tags': []}


class TestReSTTag(TestCase):

    def test_synopsis(self):
        rst = """
.. swagger:tag:: my-tag
   :synopsis: Interesting things!
"""
        json = rest.publish_string(rst)
        assert json == {'paths': {},
                        'tags': [{'name': 'my-tag',
                                  'description': '',
                                  'summary': 'Interesting things!'}]}

    def test_description(self):
        rst = """
.. swagger:tag:: my-tag

   body
"""
        json = rest.publish_string(rst)
        assert json == {'paths': {},
                        'tags': [{'name': 'my-tag',
                                  'description': 'body\n\n',
                                  'summary': ''}]}
