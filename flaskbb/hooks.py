from flask.ext.plugins import HookManager

hooks = HookManager()

hooks.new("tmpl_before_navigation")
hooks.new("tmpl_after_navigation")
