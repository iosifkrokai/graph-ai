"""Output node handler."""

from enums import NodeType, OutputNodeFormat, PortType, ValidatorType
from nodes.base import NodeExecutionContext
from nodes.definition import NodeDefinition, NodeHandlerDeps
from schemas import (
    NodeFieldSpec,
    NodeFieldUI,
    NodeFieldWidget,
    NodeGraphSpec,
)


class OutputNodeHandler:
    """Handler for output nodes."""

    async def execute(self, context: NodeExecutionContext) -> str:
        """Join upstream values into final output."""
        return "\n".join(context.parent_values)


def _build_handler(deps: NodeHandlerDeps) -> OutputNodeHandler:
    """Build an output node handler."""
    del deps
    return OutputNodeHandler()


DEFINITION = NodeDefinition(
    type=NodeType.OUTPUT,
    label="Output",
    icon_key="output",
    graph=NodeGraphSpec(
        has_input=True,
        has_output=False,
        input_port=PortType.TEXT,
    ),
    fields=(
        NodeFieldSpec(
            name="label",
            required=True,
            validators={ValidatorType.MIN_LENGTH.value: 1},
            ui=NodeFieldUI(
                widget=NodeFieldWidget.TEXT,
                label="Label",
                placeholder="Output label",
            ),
            default="Output node",
        ),
        NodeFieldSpec(
            name="format",
            required=True,
            validators={ValidatorType.SELECT.value: [OutputNodeFormat.TXT.value]},
            ui=NodeFieldUI(widget=NodeFieldWidget.SELECT, label="Format"),
            default=OutputNodeFormat.TXT.value,
        ),
    ),
    build_handler=_build_handler,
)
