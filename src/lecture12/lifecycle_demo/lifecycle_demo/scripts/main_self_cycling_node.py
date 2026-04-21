"""Entry point for the self_cycling_node executable."""

import rclpy
from lifecycle_demo.self_cycling_node import SelfCyclingNode


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(SelfCyclingNode())
    rclpy.shutdown()
