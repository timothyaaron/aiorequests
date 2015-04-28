import base64


class UnknownAuthConfig(Exception):
    def __init__(self, config):
        super(Exception, self).__init__(
            '{0!r} not of a known type.'.format(config))


def add_basic_auth(agent, username, password):
    creds = base64.b64encode('{0}:{1}'.format(username, password))
    return _RequestHeaderSettingAgent(
        agent,
        Headers({'Authorization': ['Basic {0}'.format(creds)]}))


def add_auth(agent, auth_config):
    if isinstance(auth_config, tuple):
        return add_basic_auth(agent, auth_config[0], auth_config[1])

    raise UnknownAuthConfig(auth_config)
