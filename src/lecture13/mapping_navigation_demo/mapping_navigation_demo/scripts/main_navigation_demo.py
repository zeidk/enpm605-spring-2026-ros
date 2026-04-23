"""Entry point for the navigation demo node."""

import rclpy
from mapping_navigation_demo.navigation_demo_interface import NavigationDemoInterface


def main(args=None):
    rclpy.init(args=args)
    node = NavigationDemoInterface("navigation_node")
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT) detected")
    finally:
        node.destroy_node()
        rclpy.shutdown()
