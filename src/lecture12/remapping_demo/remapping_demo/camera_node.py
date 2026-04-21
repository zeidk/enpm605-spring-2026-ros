"""Camera node for remapping demonstration.

Publishes sensor data on the relative topic 'image_raw'.
This topic can be remapped at launch time to any other name
(e.g., /sensors/front/image) without modifying this code.
"""

from rclpy.node import Node
from std_msgs.msg import String


class CameraNode(Node):
    """Simulated camera node that publishes on a relative topic."""

    def __init__(self, node_name: str) -> None:
        super().__init__(node_name)
        # Use a relative topic name so remapping and namespaces apply
        self._publisher = self.create_publisher(String, "image_raw", 10)
        self._timer = self.create_timer(1.0, self._timer_callback)
        self._frame_id = 0
        self.get_logger().info(
            f"CameraNode started. Publishing on "
            f"'{self._publisher.topic_name}'"
        )

    def _timer_callback(self) -> None:
        """Publish a simulated image frame."""
        msg = String()
        msg.data = (
            f"[{self.get_fully_qualified_name()}] "
            f"frame_{self._frame_id}"
        )
        self._publisher.publish(msg)
        self.get_logger().info(
            f"Published frame {self._frame_id} on "
            f"'{self._publisher.topic_name}'"
        )
        self._frame_id += 1
