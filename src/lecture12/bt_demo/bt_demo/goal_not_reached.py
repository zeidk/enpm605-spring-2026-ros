"""Condition node: GoalNotReached.

This module defines a py_trees **condition** behaviour that monitors the
robot's current position via the ``/odometry/filtered`` topic and checks
whether the robot has reached a specified (x, y) goal within a given
tolerance.

Condition-node contract:
    - Returns ``SUCCESS`` when the condition is **true** (the robot has
      *not* yet reached the goal), allowing sibling action nodes to
      continue executing.
    - Returns ``FAILURE`` when the condition is **false** (the robot *is*
      within tolerance of the goal), which typically causes the parent
      sequence to stop ticking its remaining children.
    - **Never** returns ``RUNNING`` — condition nodes must give an
      instantaneous yes/no answer on every tick.
"""

# math.sqrt is used for Euclidean distance calculation
import math

# py_trees provides the behaviour-tree framework (nodes, status codes, etc.)
import py_trees

# Odometry messages carry the robot's pose (position + orientation) and
# velocity, as estimated by the sensor-fusion / EKF pipeline
from nav_msgs.msg import Odometry


class GoalNotReached(py_trees.behaviour.Behaviour):
    """Condition behaviour that succeeds while the robot is far from the goal.

    This node subscribes to ``/odometry/filtered`` to track the robot's
    (x, y) position.  On every tick it computes the Euclidean distance
    between the robot and the goal and returns ``SUCCESS`` if the robot
    still needs to travel, or ``FAILURE`` once it is within tolerance.

    In a typical behaviour tree this condition is placed as the first
    child of a **Sequence** node, followed by a driving action.  The
    sequence re-checks this condition every tick and only allows the
    driving action to run while the goal has not been reached.

    Attributes:
        _goal_x (float): Target x-coordinate in the odometry frame.
        _goal_y (float): Target y-coordinate in the odometry frame.
        _tolerance (float): Distance (m) at which the goal is considered
            reached.
        _robot_x (float): Latest x-position received from odometry.
        _robot_y (float): Latest y-position received from odometry.
        _node (rclpy.node.Node | None): Reference to the owning ROS 2
            node, injected during ``setup()``.
        _sub (rclpy.subscription.Subscription): Odometry subscription,
            created during ``setup()``.
    """

    def __init__(self, name, goal_x, goal_y, tolerance=0.3):
        """Initialize the GoalNotReached condition.

        Args:
            name (str): Human-readable name shown in behaviour-tree logs
                and visualisations.
            goal_x (float): Target x-coordinate in the odometry frame
                (metres).
            goal_y (float): Target y-coordinate in the odometry frame
                (metres).
            tolerance (float, optional): How close (in metres) the robot
                must be to the goal for it to count as "reached".
                Defaults to 0.3 m.
        """
        # Delegate to the base Behaviour class (registers the name, sets
        # the initial status to INVALID, etc.)
        super().__init__(name=name)

        # Store the goal coordinates and arrival tolerance
        self._goal_x = goal_x
        self._goal_y = goal_y
        self._tolerance = tolerance

        # Initialise the robot position to the origin; will be updated
        # continuously by the odometry callback once setup() runs
        self._robot_x = 0.0
        self._robot_y = 0.0

        # The ROS 2 node reference is not available until setup()
        self._node = None

    def setup(self, **kwargs):
        """One-time initialisation called before the first tick.

        Creates a subscription to ``/odometry/filtered`` so the node
        can track the robot's position asynchronously between ticks.

        Args:
            **kwargs: Must contain a ``'node'`` key whose value is the
                ``rclpy.node.Node`` instance driving the behaviour tree.

        Raises:
            KeyError: If ``'node'`` is not present in *kwargs*.
        """
        # Retrieve the ROS 2 node that owns this behaviour tree
        self._node = kwargs['node']

        # Subscribe to the filtered odometry topic (output of an EKF or
        # similar sensor-fusion node).  The callback caches the latest
        # position so update() can use it without blocking.
        self._sub = self._node.create_subscription(
            Odometry, '/odometry/filtered',
            self._odom_callback, 10
        )

    def _odom_callback(self, msg):
        """Cache the robot's latest (x, y) position from odometry.

        This callback runs asynchronously on the ROS 2 executor thread
        whenever a new ``Odometry`` message arrives.  It extracts only
        the x and y components of the pose — orientation and velocity
        are not needed for the distance check.

        Args:
            msg (nav_msgs.msg.Odometry): Incoming odometry message.
        """
        # Extract the 2-D position from the full 6-DOF pose
        self._robot_x = msg.pose.pose.position.x
        self._robot_y = msg.pose.pose.position.y

    def update(self):
        """Called on every behaviour-tree tick while this node is active.

        Computes the Euclidean distance between the robot's last-known
        position and the goal.  If the distance exceeds the tolerance
        the condition is "true" (goal not reached → ``SUCCESS``);
        otherwise the condition is "false" (goal reached → ``FAILURE``).

        Returns:
            py_trees.common.Status.SUCCESS: The robot is still farther
                than ``_tolerance`` from the goal — keep driving.
            py_trees.common.Status.FAILURE: The robot is within
                ``_tolerance`` of the goal — stop driving.
        """
        # Compute straight-line (Euclidean) distance in the x-y plane
        dist = math.sqrt(
            (self._goal_x - self._robot_x) ** 2
            + (self._goal_y - self._robot_y) ** 2
        )

        # If still far from the goal, return SUCCESS so the parent
        # sequence continues ticking the driving action
        if dist > self._tolerance:
            return py_trees.common.Status.SUCCESS

        # Goal reached — return FAILURE to signal the parent sequence
        # that the driving action should no longer execute
        return py_trees.common.Status.FAILURE
