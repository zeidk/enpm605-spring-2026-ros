"""Entry point for the drive_to_goal_with_recovery executable.

Assembles and runs a behavior tree that drives a ROSbot toward
a goal with a Fallback recovery (Spin) if DriveForward times out.
"""

import rclpy
import py_trees
import py_trees_ros

from bt_demo.goal_not_reached import GoalNotReached
from bt_demo.drive_forward import DriveForward
from bt_demo.spin_in_place import SpinInPlace


def create_tree_with_recovery(goal_x: float, goal_y: float):
    root = py_trees.composites.Sequence(
        name='DriveToGoal', memory=False
    )
    goal_check = GoalNotReached(
        name='GoalNotReached?', goal_x=goal_x, goal_y=goal_y
    )
    recovery = py_trees.composites.Selector(
        name='DriveOrRecover', memory=False
    )
    drive = DriveForward(name='DriveForward', linear_speed=0.2)
    drive_with_timeout = py_trees.decorators.Timeout(
        child=drive,
        name='DriveForward (30 s)',
        duration=30.0,
    )
    spin = SpinInPlace(name='Spin', angular_speed=0.5)
    recovery.add_children([drive_with_timeout, spin])
    root.add_children([goal_check, recovery])
    return root


def main(args=None):
    rclpy.init(args=args)
    root = create_tree_with_recovery(goal_x=2.0, goal_y=0.0)
    tree = py_trees_ros.trees.BehaviourTree(
        root=root, unicode_tree_debug=True
    )
    tree.setup(timeout=15.0)
    tree.tick_tock(period_ms=100)
    rclpy.spin(tree.node)
    tree.shutdown()
    rclpy.shutdown()
