"""Node-related enums."""

from enum import StrEnum, auto


class NodeType(StrEnum):
    """Supported node types in a workflow graph."""

    INPUT = auto()
    LLM = auto()
    WEB_SEARCH = auto()
    OUTPUT = auto()


class PortType(StrEnum):
    """Data type carried by a node input/output port."""

    TEXT = auto()
    JSON = auto()
    FILE = auto()
    LIST = auto()


class InputNodeFormat(StrEnum):
    """Supported input node formats."""

    TXT = auto()


class OutputNodeFormat(StrEnum):
    """Supported output node formats."""

    TXT = auto()
