"""Entry point for the image_processor executable."""

import rclpy
from remapping_demo.image_processor import ImageProcessor


def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor("image_processor")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt as e:
        print(f"Exception: {type(e).__name__}")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
