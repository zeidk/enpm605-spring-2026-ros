"""Image processor node for remapping demonstration.

Subscribes on the relative topic 'camera/image'.
This name is intentionally different from the camera_node's 'image_raw'
topic to demonstrate the need for topic remapping.
"""

from rclpy.node import Node
from std_msgs.msg import String


class ImageProcessor(Node):
    """Simulated image processor that subscribes on 'camera/image'."""

    def __init__(self, node_name: str) -> None:
        super().__init__(node_name)
        self._subscription = self.create_subscription(
            String, "camera/image", self._callback, 10
        )
        self.get_logger().info(
            f"ImageProcessor started. Subscribing on "
            f"'{self._subscription.topic_name}'"
        )

    def _callback(self, msg: String) -> None:
        """Process the received image data."""
        self.get_logger().info(f"Received: {msg.data}")
