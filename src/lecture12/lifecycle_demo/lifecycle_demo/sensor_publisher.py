"""Lifecycle sensor publisher node.

Demonstrates the lifecycle state machine by publishing sensor data
only when the node is in the Active state. Resources are allocated
in on_configure and released in on_cleanup.
"""

import rclpy
from rclpy_lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String


class SensorPublisher(LifecycleNode):
    """A lifecycle node that publishes sensor data when active."""

    def __init__(self):
        super().__init__('sensor_publisher')
        self._publisher = None
        self._timer = None
        self._counter = 0

    def on_configure(self, state):
        self.get_logger().info(f'Configuring from: {state.label}')
        self._publisher = self.create_lifecycle_publisher(
            String, 'sensor_data', 10
        )
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state):
        super().on_activate(state)
        self._timer = self.create_timer(1.0, self._publish_sensor_data)
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        super().on_deactivate(state)
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        self._publisher = None
        self._counter = 0
        return TransitionCallbackReturn.SUCCESS

    def _publish_sensor_data(self):
        msg = String(data=f'Reading {self._counter}')
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self._counter += 1
