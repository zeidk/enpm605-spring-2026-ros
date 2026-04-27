"""Entry point for the navigation demo node."""

import rclpy
from nav_demo.navigation_demo import NavigationDemo


def main(args=None):
    rclpy.init(args=args)
    node = NavigationDemo("navigation_node")
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT) detected")
    finally:
        node.destroy_node()
        rclpy.shutdown()
