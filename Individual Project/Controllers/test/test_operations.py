# tests/test_operations.py
"""Image operation unit test"""

import unittest
from PIL import Image
from server.operations import rotate, resize, flip, grayscale, generate_thumbnail


def _create_test_image(width=100, height=80, color="red"):
    """Create test images"""
    return Image.new("RGB", (width, height), color)


class TestRotate(unittest.TestCase):
    def test_rotate_90(self):
        img = _create_test_image(100, 80)
        result = rotate(img, 90)
        self.assertEqual(result.size, (80, 100))

    def test_rotate_180(self):
        img = _create_test_image(100, 80)
        result = rotate(img, 180)
        self.assertEqual(result.size, (100, 80))

    def test_rotate_returns_new_image(self):
        img = _create_test_image()
        result = rotate(img, 45)
        self.assertIsNot(result, img)

    def test_rotate_after_grayscale(self):
        """Grayscale followed by rotation does not report any errors and maintains the correct size."""
        img = _create_test_image(100, 80)
        gray = grayscale(img)
        result = rotate(gray, 90)
        self.assertEqual(result.size, (80, 100))
        self.assertEqual(result.mode, "L")


class TestResize(unittest.TestCase):
    def test_resize_basic(self):
        img = _create_test_image(100, 80)
        result = resize(img, 200, 150)
        self.assertEqual(result.size, (200, 150))

    def test_resize_invalid_dimensions(self):
        img = _create_test_image()
        with self.assertRaises(ValueError):
            resize(img, 0, 100)

    def test_resize_returns_new_image(self):
        img = _create_test_image()
        result = resize(img, 50, 50)
        self.assertIsNot(result, img)


class TestFlip(unittest.TestCase):
    def test_flip_horizontal(self):
        img = _create_test_image()
        result = flip(img, 0)
        self.assertEqual(result.size, img.size)

    def test_flip_vertical(self):
        img = _create_test_image()
        result = flip(img, 1)
        self.assertEqual(result.size, img.size)

    def test_flip_invalid_direction(self):
        img = _create_test_image()
        with self.assertRaises(ValueError):
            flip(img, 99)


class TestGrayscale(unittest.TestCase):
    def test_grayscale_converts_mode(self):
        img = _create_test_image()
        result = grayscale(img)
        self.assertEqual(result.mode, "L")

    def test_grayscale_preserves_size(self):
        img = _create_test_image(100, 80)
        result = grayscale(img)
        self.assertEqual(result.size, (100, 80))


class TestThumbnail(unittest.TestCase):
    def test_thumbnail_respects_max_size(self):
        img = _create_test_image(400, 300)
        result = generate_thumbnail(img, 100, 100)
        self.assertLessEqual(result.size[0], 100)
        self.assertLessEqual(result.size[1], 100)

    def test_thumbnail_preserves_aspect_ratio(self):
        img = _create_test_image(400, 200)
        result = generate_thumbnail(img, 100, 100)
        ratio = result.size[0] / result.size[1]
        self.assertAlmostEqual(ratio, 2.0, places=1)

    def test_thumbnail_invalid_size(self):
        img = _create_test_image()
        with self.assertRaises(ValueError):
            generate_thumbnail(img, 0, 100)

    def test_thumbnail_does_not_modify_original(self):
        img = _create_test_image(400, 300)
        original_size = img.size
        generate_thumbnail(img, 100, 100)
        self.assertEqual(img.size, original_size)


if __name__ == "__main__":
    unittest.main()
