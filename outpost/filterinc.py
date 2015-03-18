# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import os
import gzip

from StringIO import StringIO

from pyramid.renderers import render
from pyramid.response import Response

from outpost import filtermanager

def template(response, request, settings, url):
    """
    Templating filter
    -----------------
    Calls a template with the file or proxy response as the value.
    The template itself is loaded as a pyramid renderer baased on the template path.
    You can use any pyramid template engine as long as it is included by calling
    `config.include()` during startup.

    The template path can be an asset spec path e.g. `myproject:templates/tmpl.pt` or
    absolute path or a relative path starting with `./` or `../`.

    The template is called with `content` and `response` attributes in the templates
    namespace. Also the original request is passed as `request`.

    Settings ::

        template: the template path
        values: additional values passed to the templates namespace

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.template",
           "apply_to": "proxy",
           "content_type": "text/html",
           "path": "\.html",
           "settings": {"template": "../templates/main.pt", "values": {}},
           "name": "HTML filter example"}
          ]

    """
    tmpl = settings.get("template")
    if not tmpl:
        return response
    # extend relative path
    wd = os.getcwd()+os.sep
    if tmpl.startswith("."+os.sep):
        tmpl = wd + tmpl[2:]
    elif tmpl.startswith(".."+os.sep):
        tmpl = wd + tmpl
        tmpl = os.path.normpath(tmpl)
    elif tmpl.find(":") == -1 and not tmpl.startswith(os.sep):
        tmpl = wd + tmpl
    if not tmpl:
        return response
    values = {"content": response.unicode_body, "response": response}
    v2 = settings.get("values")
    if v2 and isinstance(v2, dict):
        values.update(v2)
    response.unicode_body = render(tmpl, values, request=request)
    return response


def replacestr(response, request, settings, url):
    """
    Simple string replacer
    ----------------------
    Search and replace strings in the responses body.

    Settings

    replacestr: one or a list of strings to be replaced ::

        {"str": "old", "new": "new"}

    or ::

        [{"str": "old", "new": "new"}, {"str": "also", "new": "new"}]

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.replacestr",
           "apply_to": "file",
           "path": "\.html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}
          ]

    """
    if not settings:
        return response
    # process
    if not isinstance(settings, (list,tuple)):
        settings = (settings,)
    for repl in settings:
        response.unicode_body = response.unicode_body.replace(repl["str"], repl["new"])
    return response


def rewrite_urls(response, request, settings, url):
    """
    Rewirite proxied urls
    ----------------------
    Search and replace urls based on proxy server host and backend host.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.rewrite_urls",
           "apply_to": "proxy",
           "path": "\.html",
           "settings": {},
           "name": "rewrite_urls"}
          ]

    """
    if not url:
        return response
    # rewrite urls
    response.unicode_body = url.rewriteUrls(response.unicode_body)
    return response


def compress(response, request, settings, url):
    """
    Compress response body
    ----------------------
    Compress the resposne with gzip on the fly.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.compress",
           "apply_to": "proxy",
           "content_type": "text/",
           "settings": {},
           "name": "compress"}
          ]

    """
    response.content_encoding = "gzip"
    response.accept_ranges = "bytes"
    response.content_length = len(response.body)
    # compress
    zipped = StringIO()
    gz = gzip.GzipFile(fileobj=zipped, mode="wb")
    gz.write(response.body)
    gz.close()

    zipped.seek(0)
    response.body = zipped.read()
    zipped.close()
    return response


def addHeader(response, request, settings, url):
    """
    Add a http header
    ----------------------
    Compress the resposne with gzip on the fly.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.addHeader",
           "apply_to": "proxy",
           "content_type": "text/html",
           "settings": {"name": "Cache-Control", "value": "no-cache"},
           "name": "add header"}
          ]

    """
    name = str(settings.get("name"))
    value = str(settings.get("value"))
    if name:
        if name in response.headers:
            del response.headers[name]

        response.headers[name] = value
    return response


__file_cache__ = {}

def cache_write(response, request, settings, url):
    """
    Write response to cache
    -----------------------
    A simple ignorant python module level memory cache.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.cache_write",
           "hook": "post",
           "apply_to": "proxy",
           "content_type": "text/",
           "settings": {},
           "name": "cache-write"}
          ]

    """
    # do not cache responses loaded from cache
    if request.environ.get('cache-hit'):
        return response

    global __file_cache__
    # todo handle request type if response is none
    __file_cache__[str(url)] = (response.body, response.status_code, response.headers)
    return response

def cache_read(response, request, settings, url):
    """
    Read response from cache
    -----------------------
    A simple ignorant python module level memory cache.

    Set `abort=true` to finish proxy response if found in cache.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.cache_read",
           "hook": "pre",
           "apply_to": "proxy",
           "content_type": "text/",
           "settings": {"abort": false},
           "name": "cache-read"}
          ]

    """
    global __file_cache__
    if not str(url) in __file_cache__:
        return None
    body, status_code, headers = __file_cache__[str(url)]
    response = Response(body=body, status=status_code)
    response.headers.update(headers)
    request.environ['cache-hit'] = True
    # todo handle request type if cached
    #alsoProvides(response, filtermanager.IProxyRequest)
    if settings.get("abort")==True:
        raise filtermanager.ResponseFinished(response=response)
    return response


# quick and dirty string filter callables

def appendhead(response, request, settings, url):
    htmlfile = settings.get("appendhead")
    if not htmlfile:
        return response
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return response
    # process
    response.body = response.body.replace("</head>", data+"</head>")
    return response


def appendbody(response, request, settings, url):
    htmlfile = settings.get("appendbody")
    if not htmlfile:
        return response
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return response
    # process
    response.body = response.body.replace("</body>", data+"</body>")
    return response


