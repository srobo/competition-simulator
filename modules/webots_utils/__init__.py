"""
General utilities which wrap Webots' APIs.

These are separate to avoid forcing a dependency on Webots within consumers of
our `controller_utils`.
"""

from controller import Node, Supervisor


def node_from_def(supervisor: Supervisor, name: str) -> Node:
    node = supervisor.getFromDef(name)
    if node is None:
        raise ValueError(f"Unable to fetch node {name!r} from Webots")
    return node
