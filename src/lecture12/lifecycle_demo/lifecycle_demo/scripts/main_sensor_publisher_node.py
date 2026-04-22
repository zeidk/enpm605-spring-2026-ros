"""Entry point for the sensor_publisher executable."""

import rclpy
from lifecycle_demo.sensor_publisher_node import SensorPublisher


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(SensorPublisher())
    rclpy.shutdown()
