# client/client.py
"""gRPC image processing client"""

import io
import sys
import logging
from pathlib import Path

import grpc
from PIL import Image

from proto import image_processing_pb2 as pb2
from proto import image_processing_pb2_grpc as pb2_grpc

logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE = 50 * 1024 * 1024  # 50MB


class ImageProcessorClient:
    """Image processing gRPC client"""

    def __init__(self, host: str = "localhost", port: int = 50051):
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(
            self.target,
            options=[
                ("grpc.max_receive_message_length", MAX_MESSAGE_SIZE),
                ("grpc.max_send_message_length", MAX_MESSAGE_SIZE),
            ],
        )
        self.stub = pb2_grpc.ImageProcessorStub(self.channel)

    def process_image(
        self,
        image_path: str,
        operations: list[dict],
        generate_thumbnail: bool = False,
        thumbnail_size: tuple[int, int] = (128, 128),
    ) -> dict:
        """
        Send a request for image processing。

        Args:
            image_path: Image file path
            operations: Operation list, for example:
                [
                    {"type": "rotate", "angle": 90},
                    {"type": "resize", "width": 800, "height": 600},
                    {"type": "flip", "direction": "horizontal"},
                    {"type": "grayscale"},
                ]
            generate_thumbnail: Should a thumbnail be generated?
            thumbnail_size: Maximum size of thumbnail image (width, height)

        Returns:
            dict: {"success": bool, "image": bytes, "thumbnail": bytes, "error": str}
        """
        image_data = Path(image_path).read_bytes()
        proto_ops = [self._build_operation(op) for op in operations]

        thumbnail_params = pb2.ThumbnailParams(
            max_width=thumbnail_size[0],
            max_height=thumbnail_size[1],
        )

        request = pb2.ImageRequest(
            image_data=image_data,
            operations=proto_ops,
            generate_thumbnail=generate_thumbnail,
            thumbnail_params=thumbnail_params,
        )

        logger.info(
            "RTS: image=%s (%d bytes), ops=%d, thumbnail=%s",
            image_path,
            len(image_data),
            len(proto_ops),
            generate_thumbnail,
        )

        response = self.stub.ProcessImage(request)

        return {
            "success": response.success,
            "image": response.processed_image,
            "thumbnail": response.thumbnail,
            "mime_type": response.mime_type,
            "error": response.error_message,
        }

    def _build_operation(self, op: dict) -> pb2.Operation:
        """Convert the dict to proto Operation"""
        op_type = op["type"].lower()

        if op_type == "rotate":
            return pb2.Operation(
                type=pb2.ROTATE,
                rotate_params=pb2.RotateParams(angle=op.get("angle", 90)),
            )
        elif op_type == "resize":
            return pb2.Operation(
                type=pb2.RESIZE,
                resize_params=pb2.ResizeParams(
                    width=op["width"],
                    height=op["height"],
                ),
            )
        elif op_type == "flip":
            direction_map = {"horizontal": pb2.HORIZONTAL, "vertical": pb2.VERTICAL}
            direction = direction_map.get(op.get("direction", "horizontal"), pb2.HORIZONTAL)
            return pb2.Operation(
                type=pb2.FLIP,
                flip_params=pb2.FlipParams(direction=direction),
            )
        elif op_type == "grayscale":
            return pb2.Operation(type=pb2.GRAYSCALE)
        else:
            raise ValueError(f"Unsupported operation type: {op_type}")

    def close(self):
        """Close"""
        self.channel.close()


def demo(host: str, port: int, image_path: str):
    """Demo of Client Usage"""
    client = ImageProcessorClient(host, port)

    operations = [
        {"type": "rotate", "angle": 90},
        {"type": "resize", "width": 640, "height": 480},
        {"type": "flip", "direction": "horizontal"},
        {"type": "grayscale"},
    ]

    try:
        result = client.process_image(
            image_path,
            operations=operations,
            generate_thumbnail=True,
            thumbnail_size=(128, 128),
        )

        if result["success"]:
            output_dir = Path(image_path).parent
            output_path = output_dir / "processed_output.png"
            output_path.write_bytes(result["image"])
            print(f"Processing completed successfully! Output: {output_path} ({len(result['image'])} bytes)")

            if result["thumbnail"]:
                thumb_path = output_dir / "thumbnail_output.png"
                thumb_path.write_bytes(result["thumbnail"])
                print(f"THUMBNBIL: {thumb_path} ({len(result['thumbnail'])} bytes)")
        else:
            print(f"Failure in handling: {result['error']}")

    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("usage: python -m client.client <image_path> [host] [port]")
        print("give a typical example: python -m client.client test.png localhost 50051")
        sys.exit(1)

    img_path = sys.argv[1]
    target_host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    target_port = int(sys.argv[3]) if len(sys.argv) > 3 else 50051

    demo(target_host, target_port, img_path)
