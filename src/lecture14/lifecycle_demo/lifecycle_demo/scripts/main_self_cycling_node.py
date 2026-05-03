"""Entry point for the self_cycling_node executable."""

import rclpy
from lifecycle_demo.self_cycling_node import SelfCyclingNode


def main(args=None):
    rclpy.init(args=args)
    node = SelfCyclingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT) detected")
    finally:
        node.destroy_node()
        rclpy.shutdown()
