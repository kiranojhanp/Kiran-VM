"""
Helpers for pyinfra deploy files.
"""

from pyinfra.operations import files


def tpl(name, src, dest, mode=None, user=None, group=None, _sudo=True):
    """
    Thin wrapper around files.template(). Templates access variables via
    {{ host.data.var_name }} — pyinfra injects host/state/inventory automatically.
    """
    kwargs = dict(src=src, dest=dest, _sudo=_sudo)
    if mode is not None:
        kwargs["mode"] = mode
    if user is not None:
        kwargs["user"] = user
    if group is not None:
        kwargs["group"] = group

    files.template(name=name, **kwargs)
