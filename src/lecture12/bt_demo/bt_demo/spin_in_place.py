"""Action node: SpinInPlace.

Publishes a fixed angular velocity on /cmd_vel to rotate the robot
in place. Returns RUNNING while spinning. Sends a zero-velocity
stop command when terminated.
"""

import py_trees
from geometry_msgs.msg import TwistStamped


class SpinInPlace(py_trees.behaviour.Behaviour):
    """Action that spins the robot in place at a constant angular speed."""

    def __init__(self, name, angular_speed=0.5):
        super().__init__(name=name)
        self._angular_speed = angular_speed
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
        msg.twist.angular.z = self._angular_speed
        self._publisher.publish(msg)
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        stop = TwistStamped()
        stop.header.stamp = self._node.get_clock().now().to_msg()
        stop.header.frame_id = 'base_link'
        if self._publisher is not None:
            self._publisher.publish(stop)
