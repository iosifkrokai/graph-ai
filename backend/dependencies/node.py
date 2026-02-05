"""Node dependency providers."""

from usecases import NodeUsecase


def get_node_usecase() -> NodeUsecase:
    """Get the node usecase."""
    return NodeUsecase()
