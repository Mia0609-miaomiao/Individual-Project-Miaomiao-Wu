# server/pipeline.py
"""Pipeline Executor - Executes the list of operations in sequence. The execution stops immediately upon failure at any step."""

import logging
from PIL import Image
from server import operations

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Errors during the execution of the pipeline process"""

    def __init__(self, step: int, operation: str, message: str):
        self.step = step
        self.operation = operation
        super().__init__(f"Step {step} ({operation}): {message}")


def execute(image: Image.Image, ops: list) -> Image.Image:
    """
    Execute the operation list in sequence.

    Args:
        image: Input PIL Image
        ops: Operation list, each element is a proto Operation object

    Returns:
        Processed PIL Image

    Raises:
        PipelineError: An exception is thrown when a certain step fails to execute.
    """
    for i, op in enumerate(ops):
        op_type = op.type
        op_name = _get_operation_name(op_type)
        logger.info("Step %d: executing %s", i + 1, op_name)

        try:
            image = _apply_operation(image, op)
        except Exception as e:
            logger.error("Step %d (%s) failed: %s", i + 1, op_name, e)
            raise PipelineError(i + 1, op_name, str(e)) from e

    return image


def _get_operation_name(op_type: int) -> str:
    """Convert the operation type enumeration to names"""
    names = {0: "rotate", 1: "resize", 2: "flip", 3: "grayscale"}
    return names.get(op_type, f"unknown({op_type})")


def _apply_operation(image: Image.Image, op) -> Image.Image:
    """Perform a single operation"""
    op_type = op.type

    if op_type == 0:  # ROTATE
        angle = op.rotate_params.angle
        if angle == 0:
            return image
        return operations.rotate(image, angle)

    elif op_type == 1:  # RESIZE
        width = op.resize_params.width
        height = op.resize_params.height
        return operations.resize(image, width, height)

    elif op_type == 2:  # FLIP
        direction = op.flip_params.direction
        return operations.flip(image, direction)

    elif op_type == 3:  # GRAYSCALE
        return operations.grayscale(image)

    else:
        raise ValueError(f"Unsupported operation type: {op_type}")
