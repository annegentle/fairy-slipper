import json
import logging
import itertools
from os import path

from pecan import expose, response
from pecan import conf
from webob.exc import status_map
from webob.static import FileIter
import docutils.core

from fairy_slipper.rest import JSONWriter
from fairy_slipper import hooks


logger = logging.getLogger(__name__)


class JSONFileController(object):

    __hooks__ = [hooks.CORSHook()]

    def __init__(self, filepath):
        self.filepath = filepath

    @expose(content_type='text/plain')
    def _default(self):
        if path.exists(self.filepath + '.json'):
            self.filepath = self.filepath + '.json'
        if not path.exists(self.filepath):
            response.status = 404
            return
        f = open(self.filepath, 'rb')
        response.app_iter = FileIter(f)


class DocController(object):

    __hooks__ = [hooks.CORSHook()]

    def __init__(self, service_path, service_info):
        self.service_info = service_info
        base_filepath = path.join(conf.app.api_doc, service_path.rstrip('/'))
        self.api_rst = base_filepath + '.rst'
        self.tags_rst = base_filepath + '-tags.rst'
        self.examples_dir = path.join(base_filepath, 'examples') + path.sep
        if not path.exists(self.api_rst):
            logger.warning("Can't find ReST API doc at %s", self.api_rst)
        if not path.exists(self.tags_rst):
            logger.warning("Can't find ReST TAG doc at %s", self.tags_rst)

    @expose('json')
    def index(self):
        json = docutils.core.publish_file(
            open(self.api_rst),
            writer=JSONWriter())

        return {'info': self.service_info,
                'paths': json['document']['paths']}

    @expose('json')
    def _lookup(self, *components):
        if len(components) != 2 and len(components) != 3:
            return

        if components[0] != 'examples':
            return

        example = components[1]
        filepath = path.join(self.examples_dir, example)
        return JSONFileController(filepath), ['']


class ServicesController(object):

    def __init__(self):
        filepath = path.join(conf.app.api_doc, 'index.json')
        self.services_info = json.load(open(filepath))
        self.url_map = {}
        for key, info in self.services_info.items():
            # Add the path into each element, this is to make
            # consumption by the JS client easier.
            info['url'] = key

            current_map = self.url_map
            previous_map = None
            for part in [k for k in key.split('/') if k]:
                if part not in current_map:
                    current_map[part] = {}
                previous_map = current_map
                current_map = current_map[part]
            else:
                previous_map[part] = DocController(key, info)

    @expose('json')
    def index(self):
        return self.services_info.values()

    @expose('json')
    def _lookup(self, *components):
        url_map = self.url_map
        url_walk = itertools.chain(components)
        for component in url_walk:
            if component in url_map:
                url_map = url_map[component]
            else:
                break
            if isinstance(url_map, DocController):
                return url_map, [u for u in url_walk]


class RootController(object):

    @expose(content_type='text/html')
    def index(self):
        filepath = path.join(conf.app.static_root, 'index.html')
        f = open(filepath, 'rb')
        response.app_iter = FileIter(f)

    @expose('error.html')
    def error(self, status):
        try:
            status = int(status)
        except ValueError:
            status = 0
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)

    doc = ServicesController()
