"""Entry point for the ``drive_to_goal_with_recovery`` executable.

This script assembles and runs a py_trees behaviour tree that drives a
ROSbot toward a configurable (x, y) goal position **with** a recovery
mechanism: if the DriveForward action runs longer than a configurable
timeout without the goal being reached, a Timeout decorator forces it
to fail and a Selector (fallback) node activates a SpinInPlace recovery
action instead.

All tuneable values are exposed as ROS 2 parameters so the behaviour
can be changed at launch time without modifying code.

Tree structure::

    Sequence (DriveToGoal, memory=False)
    ├── GoalNotReached?              — condition
    └── Selector (DriveOrRecover, memory=False)
        ├── Timeout
        │   └── DriveForward         — action
        └── Spin                     — recovery action

Tick-by-tick behaviour:
    1. The **Sequence** first ticks GoalNotReached?.  If the robot is
       within tolerance the condition returns FAILURE and the whole
       Sequence fails — the robot stops.
    2. If the goal is still far away (SUCCESS), the Sequence ticks the
       **Selector**.  The Selector tries DriveForward (wrapped in a
       Timeout) first.
    3. While the timeout has not expired, DriveForward returns RUNNING
       and the robot drives straight.
    4. If the timeout elapses without the goal being reached, the
       decorator forces FAILURE.  The Selector then falls back to the
       **Spin** action, which rotates the robot in place (e.g., to
       reorient before the next attempt).

ROS 2 Parameters:
    goal_x (double, default 2.0): Target x-coordinate (metres).
    goal_y (double, default 0.0): Target y-coordinate (metres).
    goal_yaw (double, default 0.0): Target heading for spin recovery (rad).
    tolerance (double, default 0.3): Distance (m) to consider the goal
        reached.
    k_rho (double, default 0.4): Gain for distance → linear velocity.
    k_alpha (double, default 0.8): Gain for heading error → angular velocity.
    k_yaw (double, default 0.8): Gain for yaw error → spin angular velocity.
    timeout_duration (double, default 30.0): Seconds before DriveForward
        is considered stuck and the recovery spin activates.

Usage examples (after building the workspace)::

    # Default — P-control drive to (2, 0), 30 s timeout:
    ros2 run bt_demo drive_to_goal_with_recovery_exe

    # Reach a nearby goal quickly (higher gain):
    ros2 run bt_demo drive_to_goal_with_recovery_exe --ros-args \\
        -p goal_x:=1.0 -p goal_y:=0.0 -p k_rho:=0.8

    # Force the robot to spin immediately (tiny timeout):
    ros2 run bt_demo drive_to_goal_with_recovery_exe --ros-args \\
        -p goal_x:=100.0 -p timeout_duration:=0.1
"""

# rclpy is the ROS 2 Python client library — needed to initialise the
# ROS context and spin the executor
import rclpy
from rclpy.node import Node

# py_trees provides the core behaviour-tree composites, decorators, and
# status codes
import py_trees

# py_trees_ros wraps a py_trees tree inside a ROS 2 node so that
# behaviours can use ROS publishers, subscribers, and services
import py_trees_ros

# Custom behaviour nodes defined in the bt_demo package
from bt_demo.goal_not_reached import GoalNotReached
from bt_demo.drive_forward import DriveForward
from bt_demo.spin_in_place import SpinInPlace


def create_tree_with_recovery(
    goal_x: float,
    goal_y: float,
    goal_yaw: float,
    tolerance: float,
    k_rho: float,
    k_alpha: float,
    k_yaw: float,
    timeout_duration: float,
):
    """Build the behaviour tree for driving to a goal with recovery.

    The tree uses a Selector (fallback) to attempt driving first and,
    if that times out, fall back to spinning in place as a recovery
    behaviour.

    Args:
        goal_x (float): Target x-coordinate in the odometry frame (metres).
        goal_y (float): Target y-coordinate in the odometry frame (metres).
        goal_yaw (float): Target heading for the spin recovery (radians).
        tolerance (float): Distance (m) within which the goal is
            considered reached.
        k_rho (float): Proportional gain for distance → linear velocity.
        k_alpha (float): Proportional gain for heading error → angular
            velocity.
        k_yaw (float): Proportional gain for yaw error → spin angular
            velocity.
        timeout_duration (float): Seconds before DriveForward is forced
            to fail and recovery kicks in.

    Returns:
        py_trees.behaviour.Behaviour: The root node of the assembled
        behaviour tree, ready to be wrapped in a
        ``py_trees_ros.trees.BehaviourTree``.
    """
    # Root Sequence — ticks children left-to-right and succeeds only if
    # ALL children succeed.  memory=False makes it reactive: every child
    # is re-evaluated from scratch on each tick.
    root = py_trees.composites.Sequence(
        name='DriveToGoal', memory=False
    )

    # Condition node: returns SUCCESS while the robot is farther than
    # `tolerance` from the goal, FAILURE otherwise
    goal_check = GoalNotReached(
        name='GoalNotReached?',
        goal_x=goal_x,
        goal_y=goal_y,
        tolerance=tolerance,
    )

    # Selector (fallback) node: tries children left-to-right and succeeds
    # as soon as ANY child succeeds (or returns RUNNING).  memory=True
    # means that once DriveForward fails (timeout), the Selector stays
    # on the Spin child until Spin returns SUCCESS (target yaw reached).
    # Only then does the Selector complete and reset, giving DriveForward
    # a fresh attempt with a new timeout on the next tick.
    recovery = py_trees.composites.Selector(
        name='DriveOrRecover', memory=True
    )

    # Primary action: P-control drive toward the goal using k_rho and
    # k_alpha gains.  Always returns RUNNING.
    drive = DriveForward(
        name='DriveForward',
        goal_x=goal_x,
        goal_y=goal_y,
        k_rho=k_rho,
        k_alpha=k_alpha,
    )

    # Wrap the drive action in a Timeout decorator.  If DriveForward
    # returns RUNNING for longer than timeout_duration seconds, the
    # decorator forces a FAILURE status, which causes the Selector to
    # try the next child (the recovery spin).
    drive_with_timeout = py_trees.decorators.Timeout(
        child=drive,
        name=f'DriveForward ({timeout_duration} s)',
        duration=timeout_duration,
    )

    # Recovery action: P-control spin toward goal_yaw using k_yaw gain.
    # Only reached if the Timeout on DriveForward expires.
    spin = SpinInPlace(name='Spin', goal_yaw=goal_yaw, k_yaw=k_yaw)

    # Assemble the Selector: try driving first, fall back to spinning
    recovery.add_children([drive_with_timeout, spin])

    # Assemble the root Sequence: check goal condition, then attempt
    # drive-or-recover
    root.add_children([goal_check, recovery])
    return root


def main(args=None):
    """ROS 2 entry point — initialise, run the tree, then clean up.

    Creates a temporary ROS 2 node to declare and read parameters, then
    builds the behaviour tree with those values, wraps it in a
    ``py_trees_ros.trees.BehaviourTree``, and spins until shutdown.

    Args:
        args (list[str] | None): Command-line arguments forwarded to
            ``rclpy.init()``.  Defaults to ``None`` (use sys.argv).
    """
    # Initialise the ROS 2 client library (creates the global context)
    rclpy.init(args=args)

    # Create a temporary node solely to declare and read parameters.
    # This node is destroyed after parameter values are captured.
    param_node = Node('bt_params')
    param_node.declare_parameter('goal_x', 2.0)
    param_node.declare_parameter('goal_y', 0.0)
    param_node.declare_parameter('goal_yaw', 0.0)
    param_node.declare_parameter('tolerance', 0.3)
    param_node.declare_parameter('k_rho', 0.4)
    param_node.declare_parameter('k_alpha', 0.8)
    param_node.declare_parameter('k_yaw', 0.8)
    param_node.declare_parameter('timeout_duration', 30.0)

    # Read the parameter values (may have been overridden via --ros-args)
    goal_x = param_node.get_parameter('goal_x').get_parameter_value().double_value
    goal_y = param_node.get_parameter('goal_y').get_parameter_value().double_value
    goal_yaw = param_node.get_parameter('goal_yaw').get_parameter_value().double_value
    tolerance = param_node.get_parameter('tolerance').get_parameter_value().double_value
    k_rho = param_node.get_parameter('k_rho').get_parameter_value().double_value
    k_alpha = param_node.get_parameter('k_alpha').get_parameter_value().double_value
    k_yaw = param_node.get_parameter('k_yaw').get_parameter_value().double_value
    timeout_duration = param_node.get_parameter('timeout_duration').get_parameter_value().double_value

    # Destroy the temporary parameter node — the BehaviourTree will
    # create its own internal node for ROS communication
    param_node.destroy_node()

    # Build the behaviour tree using the parameter values
    root = create_tree_with_recovery(
        goal_x=goal_x,
        goal_y=goal_y,
        goal_yaw=goal_yaw,
        tolerance=tolerance,
        k_rho=k_rho,
        k_alpha=k_alpha,
        k_yaw=k_yaw,
        timeout_duration=timeout_duration,
    )

    # Wrap the pure py_trees tree in a ROS 2-aware tree that manages its
    # own node internally.  unicode_tree_debug=True prints an ASCII tree
    # to the console on every tick for easy debugging.
    tree = py_trees_ros.trees.BehaviourTree(
        root=root, unicode_tree_debug=True
    )

    # Call setup() on every behaviour in the tree, passing the internal
    # ROS 2 node so behaviours can create publishers / subscribers.
    # The 15-second timeout guards against hanging setup calls.
    tree.setup(timeout=15.0)

    # Start a periodic timer that ticks the tree every 100 ms (10 Hz)
    tree.tick_tock(period_ms=100)

    # Hand control to the ROS 2 executor — this blocks until the node is
    # shut down (e.g., Ctrl-C)
    rclpy.spin(tree.node)

    # Orderly shutdown: tear down the tree (terminates active behaviours)
    # and then shut down the ROS 2 context
    tree.shutdown()
    rclpy.shutdown()
