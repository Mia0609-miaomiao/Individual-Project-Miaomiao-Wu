# server/operations.py
"""Image processing operation module - Each operation receives a PIL Image and returns a new PIL Image"""

from PIL import Image, ImageOps


def rotate(image: Image.Image, angle: float) -> Image.Image:
    """Rotate the image while maintaining the complete content. Fill the background with white (the fill color will be dynamically selected based on the image mode)"""
    fill = _get_white_fillcolor(image.mode)
    return image.rotate(angle, expand=True, fillcolor=fill)


def _get_white_fillcolor(mode: str):
    """Return the corresponding white fill value based on the image mode"""
    if mode == "L":
        return 255
    if mode == "RGBA":
        return (255, 255, 255, 255)
    return (255, 255, 255)


def resize(image: Image.Image, width: int, height: int) -> Image.Image:
    """Adjust the size of the image"""
    if width <= 0 or height <= 0:
        raise ValueError(f"resize Invalid size: width={width}, height={height}")
    return image.resize((width, height), Image.LANCZOS)


def flip(image: Image.Image, direction: int) -> Image.Image:
    """Flip the image: 0 = horizontal, 1 = vertical"""
    if direction == 0:
        return ImageOps.mirror(image)
    elif direction == 1:
        return ImageOps.flip(image)
    else:
        raise ValueError(f"flip Invalid direction: {direction}")


def grayscale(image: Image.Image) -> Image.Image:
    """Convert to grayscale image"""
    return ImageOps.grayscale(image)


def generate_thumbnail(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Generate thumbnails while maintaining the aspect ratio."""
    if max_width <= 0 or max_height <= 0:
        raise ValueError(f"thumbnail Invalid size: max_width={max_width}, max_height={max_height}")
    thumb = image.copy()
    thumb.thumbnail((max_width, max_height), Image.LANCZOS)
    return thumb
