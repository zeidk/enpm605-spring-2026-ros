"""Action node: DriveForward (proportional controller).

This module defines a py_trees behaviour node that steers a robot toward
a goal (x, y) position using a two-gain proportional controller:

- **k_rho** scales the Euclidean distance to the goal into a linear
  velocity (the farther the robot is, the faster it drives).
- **k_alpha** scales the heading error (angle between the robot's
  current heading and the direction to the goal) into an angular
  velocity so the robot curves toward the goal rather than driving
  in a straight line.

Both velocities are clamped to configurable maximums to protect the
hardware.

Lifecycle:
    - **setup**: Acquires a reference to the ROS 2 node, creates the
      ``/cmd_vel`` publisher and the ``/odometry/filtered`` subscriber.
    - **update**: Reads the latest odometry, computes proportional
      velocities, publishes a ``TwistStamped``, and returns ``RUNNING``.
      The node never returns ``SUCCESS`` on its own — it relies on the
      ``GoalNotReached`` condition in the parent Sequence to stop the
      tree once the goal is within tolerance.
    - **terminate**: Publishes a zero-velocity stop command.
"""

import math

# py_trees provides the behaviour-tree framework (nodes, status codes, etc.)
import py_trees

# TwistStamped carries linear + angular velocity with a header (stamp + frame)
from geometry_msgs.msg import TwistStamped

# Odometry messages carry the robot's pose and velocity from sensor fusion
from nav_msgs.msg import Odometry


class DriveForward(py_trees.behaviour.Behaviour):
    """Behaviour-tree action that drives toward a goal using P-control.

    On every tick the node computes proportional linear and angular
    velocities based on the distance and heading error to the goal,
    publishes the command, and returns ``RUNNING``.  The parent tree
    (typically a Sequence gated by ``GoalNotReached``) is responsible
    for terminating this behaviour once the goal is reached.

    Attributes:
        _goal_x (float): Target x-coordinate in the odometry frame (m).
        _goal_y (float): Target y-coordinate in the odometry frame (m).
        _k_rho (float): Proportional gain for distance → linear velocity.
        _k_alpha (float): Proportional gain for heading error → angular
            velocity.
        _max_linear (float): Maximum linear speed clamp (m/s).
        _max_angular (float): Maximum angular speed clamp (rad/s).
        _robot_x (float): Latest x-position from odometry.
        _robot_y (float): Latest y-position from odometry.
        _robot_yaw (float): Latest yaw angle from odometry (rad).
        _odom_received (bool): True once at least one odometry message
            has been processed.
        _publisher (rclpy.publisher.Publisher | None): ``/cmd_vel`` publisher.
        _node (rclpy.node.Node | None): Owning ROS 2 node.
    """

    def __init__(
        self,
        name,
        goal_x=0.0,
        goal_y=0.0,
        k_rho=0.4,
        k_alpha=0.8,
        max_linear=0.5,
        max_angular=1.0,
    ):
        """Initialize the DriveForward behaviour.

        Args:
            name (str): Human-readable name for tree logs / visualisation.
            goal_x (float): Target x-coordinate (metres).
            goal_y (float): Target y-coordinate (metres).
            k_rho (float): Proportional gain mapping distance to linear
                speed.  Defaults to 0.4.
            k_alpha (float): Proportional gain mapping heading error to
                angular speed.  Defaults to 0.8.
            max_linear (float): Linear velocity clamp (m/s).  Defaults
                to 0.5.
            max_angular (float): Angular velocity clamp (rad/s).  Defaults
                to 1.0.
        """
        super().__init__(name=name)

        # Goal position in the odometry frame
        self._goal_x = goal_x
        self._goal_y = goal_y

        # Proportional gains
        self._k_rho = k_rho
        self._k_alpha = k_alpha

        # Velocity clamps to protect the hardware
        self._max_linear = max_linear
        self._max_angular = max_angular

        # Robot state — updated asynchronously by the odometry callback
        self._robot_x = 0.0
        self._robot_y = 0.0
        self._robot_yaw = 0.0
        self._odom_received = False

        # ROS resources created during setup()
        self._publisher = None
        self._node = None
        self._sub = None

    def setup(self, **kwargs):
        """One-time initialisation: create the publisher and subscriber.

        Args:
            **kwargs: Must contain ``'node'`` (the owning
                ``rclpy.node.Node``).

        Raises:
            KeyError: If ``'node'`` is missing from *kwargs*.
        """
        self._node = kwargs['node']

        # Publisher for velocity commands
        self._publisher = self._node.create_publisher(
            TwistStamped, '/cmd_vel', 10
        )

        # Subscribe to filtered odometry for pose feedback
        self._sub = self._node.create_subscription(
            Odometry, '/odometry/filtered',
            self._odom_callback, 10
        )

    def _odom_callback(self, msg):
        """Cache the robot's latest pose from odometry.

        Args:
            msg (nav_msgs.msg.Odometry): Incoming odometry message.
        """
        self._robot_x = msg.pose.pose.position.x
        self._robot_y = msg.pose.pose.position.y

        # Extract yaw from the orientation quaternion using the standard
        # atan2 formula (avoids an external dependency like scipy)
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self._robot_yaw = math.atan2(siny_cosp, cosy_cosp)

        self._odom_received = True

    def update(self):
        """Compute and publish a proportional velocity command.

        Calculates the Euclidean distance (rho) and the heading error
        (alpha) between the robot and the goal, applies proportional
        gains, clamps the results, and publishes the command.

        If no odometry has been received yet, publishes a zero-velocity
        command as a safety measure.

        Returns:
            py_trees.common.Status.RUNNING: Always — the parent tree
                decides when to stop.
        """
        msg = TwistStamped()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        if self._odom_received:
            # Distance to goal
            dx = self._goal_x - self._robot_x
            dy = self._goal_y - self._robot_y
            rho = math.sqrt(dx ** 2 + dy ** 2)

            # Heading error: angle from the robot's heading to the goal
            angle_to_goal = math.atan2(dy, dx)
            alpha = math.atan2(
                math.sin(angle_to_goal - self._robot_yaw),
                math.cos(angle_to_goal - self._robot_yaw),
            )

            # Proportional control with clamping
            msg.twist.linear.x = max(
                -self._max_linear,
                min(self._max_linear, self._k_rho * rho),
            )
            msg.twist.angular.z = max(
                -self._max_angular,
                min(self._max_angular, self._k_alpha * alpha),
            )

        # If no odom yet, linear.x and angular.z remain 0.0 (safe stop)
        self._publisher.publish(msg)
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        """Publish a zero-velocity stop command.

        Args:
            new_status (py_trees.common.Status): The status being
                transitioned to.
        """
        stop = TwistStamped()
        stop.header.stamp = self._node.get_clock().now().to_msg()
        stop.header.frame_id = 'base_link'
        if self._publisher is not None:
            self._publisher.publish(stop)
