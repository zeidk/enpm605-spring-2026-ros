"""Action node: SpinInPlace (proportional controller).

This module defines a py_trees behaviour node that rotates a robot in
place toward a desired yaw angle using a single-gain proportional
controller:

- **k_yaw** scales the yaw error (difference between the desired and
  current heading) into an angular velocity.  The robot decelerates
  smoothly as it approaches the target heading.

The angular velocity is clamped to a configurable maximum to protect the
hardware.  No linear velocity is published, so the robot pivots around
its own centre.

Lifecycle:
    - **setup**: Acquires a reference to the ROS 2 node, creates the
      ``/cmd_vel`` publisher and the ``/odometry/filtered`` subscriber.
    - **update**: Reads the latest odometry, computes a proportional
      angular velocity, publishes a ``TwistStamped``, and returns
      ``RUNNING``.  The node never returns ``SUCCESS`` on its own — the
      parent tree is responsible for deciding when to stop spinning.
    - **terminate**: Publishes a zero-velocity stop command.
"""

import math

# py_trees provides the behaviour-tree framework (nodes, status codes, etc.)
import py_trees

# TwistStamped carries linear + angular velocity with a header (stamp + frame)
from geometry_msgs.msg import TwistStamped

# Odometry messages carry the robot's pose and velocity from sensor fusion
from nav_msgs.msg import Odometry


class SpinInPlace(py_trees.behaviour.Behaviour):
    """Behaviour-tree action that rotates toward a target yaw using P-control.

    On every tick the node computes a proportional angular velocity based
    on the yaw error between the robot's current heading and the target
    heading, publishes the command (with zero linear velocity), and
    returns ``RUNNING``.

    Attributes:
        _goal_yaw (float): Desired heading in radians.
        _k_yaw (float): Proportional gain for yaw error → angular velocity.
        _max_angular (float): Maximum angular speed clamp (rad/s).
        _robot_yaw (float): Latest yaw angle from odometry (rad).
        _odom_received (bool): True once at least one odometry message
            has been processed.
        _publisher (rclpy.publisher.Publisher | None): ``/cmd_vel`` publisher.
        _node (rclpy.node.Node | None): Owning ROS 2 node.
    """

    def __init__(
        self,
        name,
        goal_yaw=0.0,
        k_yaw=0.8,
        yaw_tolerance=0.05,
        max_angular=1.0,
    ):
        """Initialize the SpinInPlace behaviour.

        Args:
            name (str): Human-readable name for tree logs / visualisation.
            goal_yaw (float): Target heading in radians.  Defaults to 0.0.
            k_yaw (float): Proportional gain mapping yaw error to angular
                speed.  Defaults to 0.8.
            yaw_tolerance (float): Yaw error (rad) below which the target
                heading is considered reached.  Defaults to 0.05.
            max_angular (float): Angular velocity clamp (rad/s).  Defaults
                to 1.0.
        """
        super().__init__(name=name)

        # Target heading (radians)
        self._goal_yaw = goal_yaw

        # Proportional gain for yaw control
        self._k_yaw = k_yaw

        # Tolerance for considering the target heading reached
        self._yaw_tolerance = yaw_tolerance

        # Angular velocity clamp
        self._max_angular = max_angular

        # Robot state — updated asynchronously by the odometry callback
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

        # Subscribe to filtered odometry for yaw feedback
        self._sub = self._node.create_subscription(
            Odometry, '/odometry/filtered',
            self._odom_callback, 10
        )

    def _odom_callback(self, msg):
        """Cache the robot's latest yaw from odometry.

        Args:
            msg (nav_msgs.msg.Odometry): Incoming odometry message.
        """
        # Extract yaw from the orientation quaternion using the standard
        # atan2 formula (avoids an external dependency like scipy)
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self._robot_yaw = math.atan2(siny_cosp, cosy_cosp)

        self._odom_received = True

    def update(self):
        """Compute and publish a proportional angular velocity command.

        Calculates the shortest-path yaw error between the robot's
        current heading and the target heading.  If the error is within
        ``_yaw_tolerance``, publishes a stop command and returns
        ``SUCCESS``.  Otherwise applies the proportional gain, clamps
        the result, publishes, and returns ``RUNNING``.

        If no odometry has been received yet, publishes a zero-velocity
        command as a safety measure.

        Returns:
            py_trees.common.Status.SUCCESS: Target heading reached
                (within tolerance).
            py_trees.common.Status.RUNNING: Still rotating toward the
                target heading.
        """
        msg = TwistStamped()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        if self._odom_received:
            # Shortest-path yaw error wrapped to [-pi, pi]
            yaw_error = math.atan2(
                math.sin(self._goal_yaw - self._robot_yaw),
                math.cos(self._goal_yaw - self._robot_yaw),
            )

            # If within tolerance, stop and report success
            if abs(yaw_error) < self._yaw_tolerance:
                self._publisher.publish(msg)  # zero-velocity stop
                return py_trees.common.Status.SUCCESS

            # Proportional control with clamping
            msg.twist.angular.z = max(
                -self._max_angular,
                min(self._max_angular, self._k_yaw * yaw_error),
            )

        # If no odom yet, angular.z remains 0.0 (safe stop);
        # linear components stay 0.0 so the robot only rotates
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
