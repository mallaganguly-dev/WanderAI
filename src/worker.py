from flask import Response, request
from jinja2 import BaseLoader, TemplateNotFound
from pyodide.ffi import run_sync
from workers import wsgi

from web import app


def _assets():
    env = request.environ.get("workers.env")
    if env is None:
        raise RuntimeError("Cloudflare ASSETS binding is unavailable")
    return env.ASSETS


class CloudflareTemplateLoader(BaseLoader):
    def get_source(self, environment, template):
        safe_name = template.replace("\\", "/").lstrip("/")
        if ".." in safe_name.split("/"):
            raise TemplateNotFound(template)
        response = run_sync(
            _assets().fetch(f"https://assets.local/templates/{safe_name}")
        )
        if response.status != 200:
            raise TemplateNotFound(template)
        source = run_sync(response.text())
        return source, f"assets://templates/{safe_name}", None


app.jinja_loader = CloudflareTemplateLoader()


def serve_static(filename):
    safe_name = filename.replace("\\", "/").lstrip("/")
    if ".." in safe_name.split("/"):
        return Response("Not found", status=404)
    response = run_sync(
        _assets().fetch(f"https://assets.local/static/{safe_name}")
    )
    body = run_sync(response.bytes())
    return Response(
        body,
        status=response.status,
        headers={
            key: value
            for key, value in response.headers.items()
            if key.lower() not in ("content-length", "transfer-encoding")
        },
    )


# Replace Flask's filesystem-based static handler with the Cloudflare asset handler.
app.view_functions["static"] = serve_static

Default = wsgi.entrypoint(app)
