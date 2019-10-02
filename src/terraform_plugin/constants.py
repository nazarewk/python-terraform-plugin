import os

ProviderPluginName = "provider"
ProvisionerPluginName = "provisioner"
CoreProtocolVersion = 1
DefaultProtocolVersion = 5
PluginProtocolVersionKey = 'PLUGIN_PROTOCOL_VERSIONS'
PluginCertKey = 'PLUGIN_CLIENT_CERT'
MagicCookieKey = "TF_PLUGIN_MAGIC_COOKIE"
MagicCookieValue = "d602bf8f470bc67ca7faa0386276bbdd4330efaf76d1a219cb4d6991ca9872b2"

ONE_DAY_IN_SECONDS = 60 * 60 * 24


def get_protocol_version():
    versions = sorted(filter(bool, os.getenv(PluginProtocolVersionKey, '').split()), reverse=True)
    for version in versions:
        try:
            int(version)
        except ValueError:
            continue
        return version
    return DefaultProtocolVersion
