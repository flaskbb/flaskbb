from flaskbb.utils.helpers import render_template
from flask.views import View


class RenderableView(View):
    def __init__(self, template, view):
        self.template = template
        self.view = view

    def dispatch_request(self, *args, **kwargs):
        view_model = self.view(*args, **kwargs)
        return render_template(self.template, **view_model)
