from pkg_resources import resource_string

from aiorequests.api import (head, get, post, put, patch, delete, request,
                             options)
from aiorequests.content import collect, content, text_content, json_content

__all__ = ['head', 'get', 'post', 'put', 'patch', 'delete', 'request', 'options'
           'collect', 'content', 'text_content', 'json_content']

__version__ = resource_string(__name__, "_version").strip()
