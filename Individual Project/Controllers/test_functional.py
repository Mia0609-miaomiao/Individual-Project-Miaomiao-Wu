
# test_functional.py
"""Functional testing - Verify each operation of the remote service individually"""

import io
import sys
from PIL import Image
from client.client import ImageProcessorClient

SERVER = "42.51.39.84"
PORT = 50051

PASSED = 0
FAILED = 0


def check(name, condition, detail=""):
    """Assert and print the result"""
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} — {detail}")


def parse_result(result):
    """Parse the returned image"""
    img = Image.open(io.BytesIO(result["image"]))
    return img


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else SERVER
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT

    print(f"functional test -> {host}:{port}")
    print("=" * 50)

    client = ImageProcessorClient(host, port)

    # ── 1. 单操作: rotate ──
    print("\n1. rotate (rotate 90°)")
    r = client.process_image("test.png", [{"type": "rotate", "angle": 90}])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("Aspect ratio swap", img.size == (300, 400), f"got {img.size}")

    # ── 2. 单操作: resize ──
    print("\n2. resize (resize 200x100)")
    r = client.process_image("test.png", [{"type": "resize", "width": 200, "height": 100}])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("The size is correct.", img.size == (200, 100), f"got {img.size}")

    # ── 3. 单操作: flip horizontal ──
    print("\n3. flip horizontal (flip horizontal)")
    r = client.process_image("test.png", [{"type": "flip", "direction": "horizontal"}])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("unchanged size", img.size == (400, 300), f"got {img.size}")

    # ── 4. 单操作: flip vertical ──
    print("\n4. flip vertical (flip vertical)")
    r = client.process_image("test.png", [{"type": "flip", "direction": "vertical"}])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("unchanged size", img.size == (400, 300), f"got {img.size}")

    # ── 5. 单操作: grayscale ──
    print("\n5. grayscale (grayscale)")
    r = client.process_image("test.png", [{"type": "grayscale"}])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("The mode is grayscale.", img.mode == "L", f"got {img.mode}")
        check("unchanged size", img.size == (400, 300), f"got {img.size}")

    # ── 6. 组合 pipeline ──
    print("\n6. pipeline (grayscale → rotate 90° → resize 100x75)")
    r = client.process_image("test.png", [
        {"type": "grayscale"},
        {"type": "rotate", "angle": 90},
        {"type": "resize", "width": 100, "height": 75},
    ])
    check("Request successful", r["success"], r["error"])
    if r["success"]:
        img = parse_result(r)
        check("Size 100x75", img.size == (100, 75), f"got {img.size}")

    # ── 7. thumbnail 生成 ──
    print("\n7. thumbnail (THUMBNBIL 64x64)")
    r = client.process_image(
        "test.png",
        [{"type": "grayscale"}],
        generate_thumbnail=True,
        thumbnail_size=(64, 64),
    )
    check("Request successful", r["success"], r["error"])
    check("have THUMBNBIL", len(r["thumbnail"]) > 0)
    if r["thumbnail"]:
        thumb = Image.open(io.BytesIO(r["thumbnail"]))
        check("THUMBNBIL ≤ 64px", thumb.size[0] <= 64 and thumb.size[1] <= 64, f"got {thumb.size}")

    # ── 8. 错误处理: 空操作 ──
    print("\n8. Error handling (empty operation list)")
    r = client.process_image("test.png", [{"type": "resize", "width": 0, "height": 100}])
    check("Return failed", not r["success"])
    check("There is an error message.", len(r["error"]) > 0, "error null")

    # ── 汇总 ──
    client.close()
    total = PASSED + FAILED
    print("\n" + "=" * 50)
    print(f"Result: {PASSED}/{total} pass", end="")
    if FAILED:
        print(f", {FAILED} failed")
        sys.exit(1)
    else:
        print(" — All pass!")


if __name__ == "__main__":
    main()
