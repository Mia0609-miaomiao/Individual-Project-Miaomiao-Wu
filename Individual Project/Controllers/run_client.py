# run_client.py
"""Image processing client - Supports interactive selection operations"""

import sys
from client.client import ImageProcessorClient


SERVER = "42.51.39.84"
PORT = 50051

MENU = """
========== Image processing operation ==========
1. rotate    - 旋转
2. resize    - 缩放
3. flip      - 翻转
4. grayscale - 灰度
5. all       - 全部执行 (旋转+缩放+翻转+灰度)
0. Complete the selection and start processing.   -完成选择，开始处理
==================================
"""


def ask_operations():
    """Interactive selection operation"""
    operations = []
    print(MENU)

    while True:
        choice = input("Select operation (enter number): ").strip()

        if choice == "0":
            if not operations:
                print("  Select at least one operation!")
                continue
            break

        elif choice == "1":
            angle = input("  Rotation angle (default 90): ").strip()
            angle = float(angle) if angle else 90
            operations.append({"type": "rotate", "angle": angle})
            print(f"  ->added: rotate {angle}°")

        elif choice == "2":
            w = input("  Height: ").strip()
            h = input("  Width: ").strip()
            if not w or not h:
                print("  Width and height cannot be empty!")
                continue
            operations.append({"type": "resize", "width": int(w), "height": int(h)})
            print(f"  -> added: resize {w}x{h}")

        elif choice == "3":
            d = input("  Direction: h = Horizontal, v = Vertical (default: h): ").strip().lower()
            direction = "vertical" if d == "v" else "horizontal"
            operations.append({"type": "flip", "direction": direction})
            print(f"  -> added: flip {direction}")

        elif choice == "4":
            operations.append({"type": "grayscale"})
            print("  -> added: grayscale")

        elif choice == "5":
            operations = [
                {"type": "rotate", "angle": 90},
                {"type": "resize", "width": 640, "height": 480},
                {"type": "flip", "direction": "horizontal"},
                {"type": "grayscale"},
            ]
            print("  -> All operations have been added.")
            break

        else:
            print("  Invalid input. Please enter a number between 0 and 5.")

    return operations


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Use: python run_client.py <image path> [Server] [Port]")
        print("Example: python run_client.py test.png")
        sys.exit(0)

    image_path = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else SERVER
    port = int(sys.argv[3]) if len(sys.argv) > 3 else PORT

    # 选择操作
    operations = ask_operations()

    # 是否生成缩略图
    thumb_input = input("\nGenerate thumbnail? (y/n, Default y): ").strip().lower()
    generate_thumbnail = thumb_input != "n"

    print(f"\nProcessing... -> {host}:{port}")

    client = ImageProcessorClient(host, port)
    try:
        result = client.process_image(
            image_path,
            operations=operations,
            generate_thumbnail=generate_thumbnail,
            thumbnail_size=(128, 128),
        )

        if result["success"]:
            with open("processed_output.png", "wb") as f:
                f.write(result["image"])
            print(f"figure out -> processed_output.png ({len(result['image'])} bytes)")

            if result["thumbnail"]:
                with open("thumbnail_output.png", "wb") as f:
                    f.write(result["thumbnail"])
                print(f"THUMBNBIL   -> thumbnail_output.png ({len(result['thumbnail'])} bytes)")
        else:
            print(f"Failure in handling: {result['error']}")
            sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()

