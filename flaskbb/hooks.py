from flask.ext.plugins import HookManager

hooks = HookManager()

hooks.new("beforeIndex")
hooks.new("afterIndex")
hooks.new("beforeBreadcrumb")
hooks.new("afterBreadcrumb")
