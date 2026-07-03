"""Input node handler."""

from enums import InputNodeFormat, NodeType, PortType, ValidatorType
from nodes.base import NodeExecutionContext
from nodes.definition import NodeDefinition, NodeHandlerDeps
from schemas import (
    NodeFieldSpec,
    NodeFieldUI,
    NodeFieldWidget,
    NodeGraphSpec,
)


class InputNodeHandler:
    """Handler for input nodes."""

    async def execute(self, context: NodeExecutionContext) -> str:
        """Return execution input value."""
        return context.input_value


def _build_handler(deps: NodeHandlerDeps) -> InputNodeHandler:
    """Build an input node handler."""
    del deps
    return InputNodeHandler()


DEFINITION = NodeDefinition(
    type=NodeType.INPUT,
    label="Input",
    icon_key="input",
    graph=NodeGraphSpec(
        has_input=False,
        has_output=True,
        output_port=PortType.TEXT,
    ),
    fields=(
        NodeFieldSpec(
            name="label",
            required=True,
            validators={ValidatorType.MIN_LENGTH.value: 1},
            ui=NodeFieldUI(
                widget=NodeFieldWidget.TEXT,
                label="Label",
                placeholder="Input label",
            ),
            default="Input node",
        ),
        NodeFieldSpec(
            name="format",
            required=True,
            validators={ValidatorType.SELECT.value: [InputNodeFormat.TXT.value]},
            ui=NodeFieldUI(widget=NodeFieldWidget.SELECT, label="Format"),
            default=InputNodeFormat.TXT.value,
        ),
    ),
    build_handler=_build_handler,
)
