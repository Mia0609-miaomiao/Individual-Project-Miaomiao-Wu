# server/grpc_server.py
"""gRPC service implementation - Receiving requests, validating parameters, executing pipeline, and returning results"""

import io
import logging
import grpc
from PIL import Image

from proto import image_processing_pb2 as pb2
from proto import image_processing_pb2_grpc as pb2_grpc
from server.pipeline import execute, PipelineError
from server.operations import generate_thumbnail

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB


class ImageProcessorServicer(pb2_grpc.ImageProcessorServicer):
    """gRPC service implementation"""

    def ProcessImage(self, request, context):
        logger.info(
            "Received the request: image_size=%d bytes, operations=%d, thumbnail=%s",
            len(request.image_data),
            len(request.operations),
            request.generate_thumbnail,
        )

        # 1. 验证输入
        error = self._validate_request(request)
        if error:
            logger.warning("Request verification failed: %s", error)
            return pb2.ImageResponse(success=False, error_message=error)

        try:
            # 2. decode image
            image = self._decode_image(request.image_data)
            original_format = image.format or "PNG"
            logger.info("Image decoding successful: size=%s, format=%s", image.size, original_format)

            # 3. 验证操作列表
            error = self._validate_operations(request.operations)
            if error:
                return pb2.ImageResponse(success=False, error_message=error)

            # 4. 执行 pipeline
            processed = execute(image, request.operations)

            # 5. encode 处理后的图片
            processed_bytes, mime_type = self._encode_image(processed, original_format)
            logger.info("图片处理完成: output_size=%d bytes", len(processed_bytes))

            # 6. 生成 thumbnail（可选）
            thumbnail_bytes = b""
            if request.generate_thumbnail:
                max_w = request.thumbnail_params.max_width or 128
                max_h = request.thumbnail_params.max_height or 128
                thumb = generate_thumbnail(processed, max_w, max_h)
                thumbnail_bytes, _ = self._encode_image(thumb, original_format)
                logger.info("Thumbnail generation completed: size=%d bytes", len(thumbnail_bytes))

            # 7. 返回结果
            return pb2.ImageResponse(
                success=True,
                processed_image=processed_bytes,
                thumbnail=thumbnail_bytes,
                mime_type=mime_type,
            )

        except PipelineError as e:
            logger.error("Pipeline execution failed: %s", e)
            return pb2.ImageResponse(success=False, error_message=str(e))

        except Exception as e:
            logger.error("handle an exception: %s", e, exc_info=True)
            return pb2.ImageResponse(success=False, error_message=f"Internal server error: {e}")

    def _validate_request(self, request) -> str:
        """Verify the basic parameters of the request"""
        if not request.image_data:
            return "image_data NOT NULL"
        if len(request.image_data) > MAX_IMAGE_SIZE:
            return f"The size of the image exceeds the limit.: {len(request.image_data)} > {MAX_IMAGE_SIZE}"
        if len(request.operations) == 0:
            return "operations NOT NULL"
        return ""

    def _validate_operations(self, ops) -> str:
        """Verify the parameters of the operation list"""
        for i, op in enumerate(ops):
            if op.type == 1:  # RESIZE
                if op.resize_params.width <= 0 or op.resize_params.height <= 0:
                    return f"operate {i + 1} (resize): The values of width and height must be greater than 0."
        return ""

    def _decode_image(self, image_data: bytes) -> Image.Image:
        """Decode the bytes into a PIL Image"""
        buf = io.BytesIO(image_data)
        image = Image.open(buf)
        image.load()  # Force loading into memory
        return image

    def _encode_image(self, image: Image.Image, fmt: str) -> tuple[bytes, str]:
        """Encode PIL Image as bytes"""
        buf = io.BytesIO()

        # 灰度图转回 RGB 以兼容 JPEG
        if fmt.upper() == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        mime_map = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif"}
        save_format = fmt.upper() if fmt.upper() in mime_map else "PNG"
        mime_type = mime_map.get(save_format, "image/png")

        image.save(buf, format=save_format)
        return buf.getvalue(), mime_type

