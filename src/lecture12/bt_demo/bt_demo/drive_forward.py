"""Action node: DriveForward.

Publishes a fixed forward velocity on /cmd_vel.
Returns RUNNING while driving. Sends a zero-velocity
stop command when terminated.
"""

import py_trees
from geometry_msgs.msg import TwistStamped


class DriveForward(py_trees.behaviour.Behaviour):
    """Action that drives the robot forward at a constant speed."""

    def __init__(self, name, linear_speed=0.2):
        super().__init__(name=name)
        self._linear_speed = linear_speed
        self._publisher = None
        self._node = None

    def setup(self, **kwargs):
        self._node = kwargs['node']
        self._publisher = self._node.create_publisher(
            TwistStamped, '/cmd_vel', 10
        )

    def update(self):
        msg = TwistStamped()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = self._linear_speed
        self._publisher.publish(msg)
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        stop = TwistStamped()
        stop.header.stamp = self._node.get_clock().now().to_msg()
        stop.header.frame_id = 'base_link'
        if self._publisher is not None:
            self._publisher.publish(stop)
