"""Navigate action client node.

This module demonstrates how to create a ROS 2 action client using
a custom action interface (Navigate). This is a text-based demo -- no
robot or simulator is needed. The client sends simulated navigation
goals and handles feedback and results via callbacks.
"""

from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.node import Node

from custom_interfaces.action import Navigate


class NavigateClient(Node):
    """An action client node that sends navigation goals."""

    def __init__(self, node_name: str) -> None:
        """Initialize the Navigate action client.

        Args:
            node_name: Name to register this node with in the ROS 2 graph.
        """
        super().__init__(node_name)
        self._action_client = ActionClient(
            self,  # the current node
            Navigate,  # the action type
            "navigate",  # the action name
        )

        self._goal_handle = None
        self._feedback_count = 0
        self._canceling = False

        self.declare_parameter("cancel_and_resend", False)
        self._cancel_and_resend = (
            self.get_parameter("cancel_and_resend").get_parameter_value().bool_value
        )
        

        # Send a hardcoded goal
        self.send_goal(5.0, 3.0, 1.0)

    def send_goal(self, x: float, y: float, max_speed: float) -> None:
        """Send a navigation goal to the action server.

        Waits for the server to become available, then sends the goal
        with feedback and result callbacks.

        Args:
            x: Target x position.
            y: Target y position.
            max_speed: Maximum allowed speed for the navigation.
        """
        self._feedback_count = 0
        self._canceling = False
        self.get_logger().info("Waiting for action server...")
        self._action_client.wait_for_server()

        goal_msg = Navigate.Goal()
        goal_msg.target_pose.position.x = x
        goal_msg.target_pose.position.y = y
        goal_msg.max_speed = max_speed

        self.get_logger().info(
            f"Sending goal: ({x}, {y}), max_speed={max_speed}"
        )
        
        # send the goal asynchronously
        future = self._action_client.send_goal_async(
            goal_msg, # the goal
            feedback_callback=self._feedback_callback # process server feedback
        )
        
        # process server goal response
        future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future) -> None:
        """Handle the goal response from the server.

        If the goal is accepted, requests the result asynchronously.

        Args:
            future: The future containing the goal handle.
        """
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected.")
            return

        # Log confirmation that the server accepted the goal
        self.get_logger().info("Goal accepted.")

        # Store the goal handle so other callbacks (e.g. feedback) can cancel the goal
        self._goal_handle = goal_handle

        # Request the final result asynchronously and register a callback for when it arrives
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg) -> None:
        """Handle feedback from the action server.

        If cancel_and_resend is True, cancels the goal after 5 feedback
        messages and sends a new goal.

        Args:
            feedback_msg: The feedback message containing navigation progress.
        """
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f"Feedback: {feedback.percent_complete:.0f}% complete, "
            f"{feedback.distance_remaining:.1f} remaining"
        )

        self._feedback_count += 1
        if (
            self._cancel_and_resend
            and not self._canceling
            and self._feedback_count == 5
            and self._goal_handle is not None
        ):
            self._canceling = True
            self.get_logger().info("Canceling goal after 5 feedback messages...")
            cancel_future = self._goal_handle.cancel_goal_async()
            cancel_future.add_done_callback(self._cancel_done_callback)

    def _cancel_done_callback(self, future) -> None:
        """Handle the cancel response.

        The new goal is sent from _result_callback once the canceled
        result is received, to avoid racing with the result future.

        Args:
            future: The future containing the cancel response.
        """
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info("Cancel accepted by server.")
        else:
            self.get_logger().warn("Cancel request was rejected.")
            self._canceling = False

    def _result_callback(self, future) -> None:
        """Handle the final result from the action server.

        If the goal was canceled and cancel_and_resend is active,
        sends a new goal.

        Args:
            future: The future containing the action result.
        """
        result = future.result().result
        status = future.result().status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(
                f"Navigation succeeded! "
                f"Total distance: {result.total_distance:.1f}, "
                f"Elapsed time: {result.elapsed_time:.1f}s"
            )
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info("Goal was canceled.")
            if self._canceling:
                self._canceling = False
                self._cancel_and_resend = False
                self.get_logger().info("Sending new goal...")
                self.send_goal(8.0, 6.0, 1.0)
        else:
            self.get_logger().warn(f"Navigation failed with status: {status}")
