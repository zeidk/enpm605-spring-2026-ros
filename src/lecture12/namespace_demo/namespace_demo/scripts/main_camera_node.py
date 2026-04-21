"""Entry point for the camera_node executable."""

import rclpy
from namespace_demo.camera_node import CameraNode


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode("camera_node")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt as e:
        print(f"Exception: {type(e).__name__}")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
