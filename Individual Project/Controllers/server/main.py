
# server/main.py
"""Entrance point for starting the gRPC service"""

import sys
import logging
from concurrent import futures

import grpc

from proto import image_processing_pb2_grpc as pb2_grpc
from server.grpc_server import ImageProcessorServicer

logger = logging.getLogger(__name__)

DEFAULT_PORT = 50051
MAX_WORKERS = 10
MAX_MESSAGE_SIZE = 50 * 1024 * 1024  # 50MB


def serve(port: int = DEFAULT_PORT):
    """Start the gRPC service"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=MAX_WORKERS),
        options=[
            ("grpc.max_receive_message_length", MAX_MESSAGE_SIZE),
            ("grpc.max_send_message_length", MAX_MESSAGE_SIZE),
        ],
    )
    pb2_grpc.add_ImageProcessorServicer_to_server(ImageProcessorServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC image processing service has been started: port=%d", port)
    print(f"Server started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Received stop signal, shutting down...")
        server.stop(grace=5)
        logger.info("Service has been stopped.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    serve(port)
