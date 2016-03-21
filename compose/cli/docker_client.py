from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import os

from docker import Client
from docker.errors import TLSParameterError
from docker.tls import TLSConfig
from docker.utils import kwargs_from_env
from requests.utils import urlparse

from ..const import HTTP_TIMEOUT
from .errors import UserError

log = logging.getLogger(__name__)


def tls_config_from_options(options):
    tls = options.get('--tls', False)
    ca_cert = options.get('--tlscacert')
    cert = options.get('--tlscert')
    key = options.get('--tlskey')
    verify = options.get('--tlsverify')
    hostname = urlparse(options.get('--host', '')).hostname

    advanced_opts = any([ca_cert, cert, key, verify])

    if tls is True and not advanced_opts:
        return True
    elif advanced_opts:
        client_cert = None
        if cert or key:
            client_cert = (cert, key)
        return TLSConfig(
            client_cert=client_cert, verify=verify, ca_cert=ca_cert,
            assert_hostname=(
                hostname or not options.get('--skip-hostname-check', False)
            )
        )
    else:
        return None


def docker_client(version=None, tls_config=None, host=None):
    """
    Returns a docker-py client configured using environment variables
    according to the same logic as the official Docker client.
    """
    if 'DOCKER_CLIENT_TIMEOUT' in os.environ:
        log.warn("The DOCKER_CLIENT_TIMEOUT environment variable is deprecated.  "
                 "Please use COMPOSE_HTTP_TIMEOUT instead.")

    try:
        kwargs = kwargs_from_env(assert_hostname=False)
    except TLSParameterError:
        raise UserError(
            "TLS configuration is invalid - make sure your DOCKER_TLS_VERIFY "
            "and DOCKER_CERT_PATH are set correctly.\n"
            "You might need to run `eval \"$(docker-machine env default)\"`")

    if host:
        kwargs['base_url'] = host
    if tls_config:
        kwargs['tls'] = tls_config

    if version:
        kwargs['version'] = version

    kwargs['timeout'] = HTTP_TIMEOUT

    return Client(**kwargs)
