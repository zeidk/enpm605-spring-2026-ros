"""Entry point for the drive_to_goal executable.

Assembles and runs a behavior tree that drives a ROSbot
toward a goal position, stopping when the goal is reached.
"""

import rclpy
import py_trees
import py_trees_ros

from bt_demo.goal_not_reached import GoalNotReached
from bt_demo.drive_forward import DriveForward


def create_tree(goal_x: float, goal_y: float):
    root = py_trees.composites.Sequence(
        name='DriveToGoal', memory=False
    )
    goal_check = GoalNotReached(
        name='GoalNotReached?', goal_x=goal_x, goal_y=goal_y
    )
    drive = DriveForward(name='DriveForward', linear_speed=0.2)
    root.add_children([goal_check, drive])
    return root


def main(args=None):
    rclpy.init(args=args)
    root = create_tree(goal_x=2.0, goal_y=0.0)
    tree = py_trees_ros.trees.BehaviourTree(
        root=root, unicode_tree_debug=True
    )
    tree.setup(timeout=15.0)
    tree.tick_tock(period_ms=100)
    rclpy.spin(tree.node)
    tree.shutdown()
    rclpy.shutdown()
