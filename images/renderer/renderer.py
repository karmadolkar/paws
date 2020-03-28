from werkzeug.wrappers import Request, Response
from nbconvert.exporters import HTMLExporter

import os
import markdown
import docutils.core

BASE_PATH = os.environ['BASE_PATH']
URL_PREFIX = os.environ['URL_PREFIX']


def get_extension(path, format):
    """
    Return the extension of the path, if any
    """
    splits = path.split('.')
    if len(splits) == 1:
        # This means there's no two parts - so either no ., or nothing before
        # or after the .. Easier to handle by just saying we found no extensions.
        return ''
    return splits[-1]


def render_ipynb(full_path, format):
    """
    Render a given ipynb file
    """
    exporter = HTMLExporter()
    with open(full_path, encoding='utf-8') as file_handle:
        html, res = exporter.from_file(file_handle)
    return Response(html, mimetype='text/html')

def render_md(full_path, format):
    """
    Render a given .md file
    """
    md = markdown.markdownFromFile(filename)
    rmd = md.convert()
    return rmd

def render_rst(full_path, format):
    """
    Render a given .rst file
    """
    docutils.core.publish_file(source_path=full_path, destination path="output.html", writer_name="html")
    html = open("output.html").read()
    return html

# Map of extensions to functions to call for handling them
handlers = {
    'ipynb': render_ipynb,
    'md' : render_md,
    'rst' : render_rst
}


@Request.application
def application(request):
    file_path = request.path.lstrip(URL_PREFIX) 
    full_path = os.path.join(BASE_PATH, file_path)
    # Protect against path traversal attacks, if they make it this far.
    if not full_path.startswith(BASE_PATH):
        # DANGER!
        return Response("Suspicious url", status=403)
    format = request.args.get('format', None)
    if format == 'raw':
        # Let nginx serve raw files
        accel_path = os.path.join('/accelredir/', file_path)
        return Response('', headers={'X-Accel-Redirect': accel_path})

    try:
        extension = get_extension(full_path, format)
        if extension and extension in handlers:
            return handlers[extension](full_path, format)
        else:
            return Response("No handlers for format %s" % extension, status=400)
    except FileNotFoundError:
        return Response("Not found", status=404)
    return Response(full_path)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 4000, application)