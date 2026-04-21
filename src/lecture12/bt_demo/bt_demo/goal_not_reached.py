"""Condition node: GoalNotReached.

Reads the robot's (x, y) position from /odometry/filtered.
Returns SUCCESS if the robot has not yet reached the goal,
FAILURE otherwise. Never returns RUNNING (condition node).
"""

import math

import py_trees
from nav_msgs.msg import Odometry


class GoalNotReached(py_trees.behaviour.Behaviour):
    """Condition that checks whether the robot is still far from the goal."""

    def __init__(self, name, goal_x, goal_y, tolerance=0.3):
        super().__init__(name=name)
        self._goal_x = goal_x
        self._goal_y = goal_y
        self._tolerance = tolerance
        self._robot_x = 0.0
        self._robot_y = 0.0
        self._node = None

    def setup(self, **kwargs):
        self._node = kwargs['node']
        self._sub = self._node.create_subscription(
            Odometry, '/odometry/filtered',
            self._odom_callback, 10
        )

    def _odom_callback(self, msg):
        self._robot_x = msg.pose.pose.position.x
        self._robot_y = msg.pose.pose.position.y

    def update(self):
        dist = math.sqrt(
            (self._goal_x - self._robot_x) ** 2
            + (self._goal_y - self._robot_y) ** 2
        )
        if dist > self._tolerance:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
