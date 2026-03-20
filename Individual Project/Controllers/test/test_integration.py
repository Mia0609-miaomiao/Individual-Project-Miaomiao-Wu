# tests/test_integration.py
"""Integration testing - Complete gRPC client-server interaction"""

import io
import time
import unittest
import threading
from concurrent import futures

import grpc
from PIL import Image

from proto import image_processing_pb2 as pb2
from proto import image_processing_pb2_grpc as pb2_grpc
from server.grpc_server import ImageProcessorServicer


def _create_test_image_bytes(width=100, height=80, fmt="PNG"):
    """Create the bytes of the test image"""
    img = Image.new("RGB", (width, height), "blue")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class TestIntegration(unittest.TestCase):
    """gRPC integration test"""

    @classmethod
    def setUpClass(cls):
        cls.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=2),
            options=[
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ],
        )
        pb2_grpc.add_ImageProcessorServicer_to_server(
            ImageProcessorServicer(), cls.server
        )
        cls.port = cls.server.add_insecure_port("[::]:0")
        cls.server.start()

        cls.channel = grpc.insecure_channel(
            f"localhost:{cls.port}",
            options=[
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ],
        )
        cls.stub = pb2_grpc.ImageProcessorStub(cls.channel)

    @classmethod
    def tearDownClass(cls):
        cls.channel.close()
        cls.server.stop(grace=0)

    def test_rotate_operation(self):
        image_data = _create_test_image_bytes(100, 80)
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[
                pb2.Operation(
                    type=pb2.ROTATE,
                    rotate_params=pb2.RotateParams(angle=90),
                )
            ],
        )
        response = self.stub.ProcessImage(request)

        self.assertTrue(response.success)
        self.assertGreater(len(response.processed_image), 0)
        result_img = Image.open(io.BytesIO(response.processed_image))
        self.assertEqual(result_img.size, (80, 100))

    def test_resize_operation(self):
        image_data = _create_test_image_bytes(100, 80)
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[
                pb2.Operation(
                    type=pb2.RESIZE,
                    resize_params=pb2.ResizeParams(width=200, height=150),
                )
            ],
        )
        response = self.stub.ProcessImage(request)

        self.assertTrue(response.success)
        result_img = Image.open(io.BytesIO(response.processed_image))
        self.assertEqual(result_img.size, (200, 150))

    def test_flip_operation(self):
        image_data = _create_test_image_bytes()
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[
                pb2.Operation(
                    type=pb2.FLIP,
                    flip_params=pb2.FlipParams(direction=pb2.HORIZONTAL),
                )
            ],
        )
        response = self.stub.ProcessImage(request)
        self.assertTrue(response.success)
        self.assertGreater(len(response.processed_image), 0)

    def test_grayscale_operation(self):
        image_data = _create_test_image_bytes()
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[pb2.Operation(type=pb2.GRAYSCALE)],
        )
        response = self.stub.ProcessImage(request)
        self.assertTrue(response.success)

    def test_pipeline_multiple_operations(self):
        """Pipeline for testing multiple operations"""
        image_data = _create_test_image_bytes(200, 150)
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[
                pb2.Operation(
                    type=pb2.RESIZE,
                    resize_params=pb2.ResizeParams(width=100, height=75),
                ),
                pb2.Operation(
                    type=pb2.ROTATE,
                    rotate_params=pb2.RotateParams(angle=90),
                ),
                pb2.Operation(type=pb2.GRAYSCALE),
                pb2.Operation(
                    type=pb2.FLIP,
                    flip_params=pb2.FlipParams(direction=pb2.VERTICAL),
                ),
            ],
        )
        response = self.stub.ProcessImage(request)

        self.assertTrue(response.success)
        result_img = Image.open(io.BytesIO(response.processed_image))
        self.assertEqual(result_img.size, (75, 100))

    def test_thumbnail_generation(self):
        """Test thumbnail generation"""
        image_data = _create_test_image_bytes(400, 300)
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[pb2.Operation(type=pb2.GRAYSCALE)],
            generate_thumbnail=True,
            thumbnail_params=pb2.ThumbnailParams(max_width=64, max_height=64),
        )
        response = self.stub.ProcessImage(request)

        self.assertTrue(response.success)
        self.assertGreater(len(response.thumbnail), 0)
        thumb = Image.open(io.BytesIO(response.thumbnail))
        self.assertLessEqual(thumb.size[0], 64)
        self.assertLessEqual(thumb.size[1], 64)

    def test_empty_operations_returns_error(self):
        image_data = _create_test_image_bytes()
        request = pb2.ImageRequest(image_data=image_data, operations=[])
        response = self.stub.ProcessImage(request)

        self.assertFalse(response.success)
        self.assertIn("Not null", response.error_message)

    def test_empty_image_returns_error(self):
        request = pb2.ImageRequest(
            image_data=b"",
            operations=[pb2.Operation(type=pb2.GRAYSCALE)],
        )
        response = self.stub.ProcessImage(request)

        self.assertFalse(response.success)
        self.assertIn("Not null", response.error_message)

    def test_invalid_resize_returns_error(self):
        image_data = _create_test_image_bytes()
        request = pb2.ImageRequest(
            image_data=image_data,
            operations=[
                pb2.Operation(
                    type=pb2.RESIZE,
                    resize_params=pb2.ResizeParams(width=0, height=100),
                )
            ],
        )
        response = self.stub.ProcessImage(request)
        self.assertFalse(response.success)


if __name__ == "__main__":
    unittest.main()
