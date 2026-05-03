"""Entry point for the sensor_publisher executable."""

import rclpy
from lifecycle_demo.sensor_publisher_node import SensorPublisher


def main(args=None):
    rclpy.init(args=args)
    node = SensorPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT) detected")
    finally:
        node.destroy_node()
        rclpy.shutdown()