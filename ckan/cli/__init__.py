# encoding: utf-8

import os

import click
import logging
from logging.config import fileConfig as loggingFileConfig
from configparser import ConfigParser

log = logging.getLogger(__name__)


class CKANConfigLoader(object):
    def __init__(self, filename):
        self.filename = filename = filename.strip()
        self.parser = ConfigParser()
        self.parser.read(filename)

        defaults = {
            'here': os.path.dirname(os.path.abspath(filename)),
            '__file__': os.path.abspath(filename)
        }
        self._update_defaults(defaults)

    def _update_defaults(self, new_defaults, overwrite=True):
        for key, value in new_defaults.iteritems():
            if not overwrite and key in self.parser._defaults:
                continue
            self.parser._defaults[key] = value

    def get_context(self):
        global_conf = self.parser.defaults().copy()
        local_conf = {}
        section = 'app:main'
        options = self.parser.options(section)

        for option in options:
            if option in global_conf:
                continue
            local_conf[option] = self.parser.get(section, option)

        return CKANLoaderContext(global_conf, local_conf).config()


class CKANLoaderContext(object):
    def __init__(self, global_conf, local_conf):
        self.global_conf = global_conf
        self.local_conf = local_conf

    def config(self):
        conf = AttrDict(self.global_conf)
        conf.update(self.local_conf)
        conf.local_conf = self.local_conf
        conf.global_conf = self.global_conf
        conf.context = self
        return conf


class AttrDict(dict):
    """
    A dictionary that can be assigned to.
    """
    pass


def error_shout(exception):
    click.secho(str(exception), fg=u'red', err=True)


click_config_option = click.option(
    u'-c',
    u'--config',
    default=None,
    metavar=u'CONFIG',
    help=u'Config file to use (default: development.ini)'
)


def load_config(ini_path=None):
    if ini_path:
        if ini_path.startswith(u'~'):
            ini_path = os.path.expanduser(ini_path)
        filename = os.path.abspath(ini_path)
        config_source = u'-c parameter'
    elif os.environ.get(u'CKAN_INI'):
        filename = os.environ.get(u'CKAN_INI')
        config_source = u'$CKAN_INI'
    else:
        default_filename = u'development.ini'
        filename = os.path.join(os.getcwd(), default_filename)
        if not os.path.exists(filename):
            # give really clear error message for this common situation
            msg = u'ERROR: You need to specify the CKAN config (.ini) '\
                u'file path.'\
                u'\nUse the --config parameter or set environment ' \
                u'variable CKAN_INI or have {}\nin the current directory.' \
                .format(default_filename)
            exit(msg)

    if not os.path.exists(filename):
        msg = u'Config file not found: %s' % filename
        msg += u'\n(Given by: %s)' % config_source
        exit(msg)

    config_loader = CKANConfigLoader(filename)
    log.info(u'Using configuration file {}'.format(filename))

    return config_loader.get_context()
