from functools import wraps

class objname(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        func.obj_name = self.name
        return func

class extends(object):
    def __init__(self, extended):
        self.extended = extended

    def __call__(self, func):
        def new_func(*args, **kwargs):
            d = getattr(args[0].__class__, self.extended)(*args, **kwargs)
            d.update(func(*args, **kwargs))
            return d
        if hasattr(func, 'obj_name'):
            new_func.obj_name = func.obj_name
        return wraps(func)(new_func)

