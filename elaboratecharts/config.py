def _setup():
    import json
    import re
    from ast import literal_eval
    from os import path, environ
    from warnings import warn

    environ_var = re.compile('ELABORATECHARTS_([A-Z_]+)')

    def relopen(name, *args, **kwargs):
        return open(path.join(path.dirname(__file__), name), *args, **kwargs)

    with relopen('default.json') as default:
        config = json.load(default)
    try:
        with relopen('config.json') as config_fp:
            config.update(json.load(config_fp))
    except IOError:
        warn('user config is missing')

    # Load options from environment and parse them as Python literals
    for key, value in environ.iteritems():
        mo = environ_var.match(key)
        if mo is not None:
            option = mo.group(1).upper()
            try:
                config[option] = literal_eval(value)
            except (ValueError, SyntaxError):
                config[option] = value

    return config

globals().update(_setup())
del _setup
