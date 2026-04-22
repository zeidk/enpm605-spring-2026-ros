"""Launch file for the drive_to_goal_with_recovery behaviour tree node.

Launches the ``drive_to_goal_with_recovery_exe`` executable with
configurable parameters exposed as launch arguments.

Usage::

    ros2 launch bt_demo drive_to_goal_with_recovery.launch.py
    ros2 launch bt_demo drive_to_goal_with_recovery.launch.py goal_x:=3.0 timeout_duration:=10.0
    ros2 launch bt_demo drive_to_goal_with_recovery.launch.py goal_x:=100.0 timeout_duration:=0.1 goal_yaw:=1.57
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate the launch description with all configurable arguments."""

    # Declare launch arguments with defaults matching the node's defaults
    goal_x_arg = DeclareLaunchArgument(
        'goal_x', default_value='2.0',
        description='Target x-coordinate in the odometry frame (metres)'
    )
    goal_y_arg = DeclareLaunchArgument(
        'goal_y', default_value='0.0',
        description='Target y-coordinate in the odometry frame (metres)'
    )
    goal_yaw_arg = DeclareLaunchArgument(
        'goal_yaw', default_value='0.0',
        description='Target heading for spin recovery (radians)'
    )
    tolerance_arg = DeclareLaunchArgument(
        'tolerance', default_value='0.3',
        description='Distance (m) to consider the goal reached'
    )
    k_rho_arg = DeclareLaunchArgument(
        'k_rho', default_value='0.4',
        description='Proportional gain: distance to linear velocity'
    )
    k_alpha_arg = DeclareLaunchArgument(
        'k_alpha', default_value='0.8',
        description='Proportional gain: heading error to angular velocity'
    )
    k_yaw_arg = DeclareLaunchArgument(
        'k_yaw', default_value='0.8',
        description='Proportional gain: yaw error to spin angular velocity'
    )
    timeout_duration_arg = DeclareLaunchArgument(
        'timeout_duration', default_value='30.0',
        description='Seconds before DriveForward times out and recovery spin activates'
    )

    # Node configuration
    drive_with_recovery_node = Node(
        package='bt_demo',
        executable='drive_to_goal_exe',
        name='drive_to_goal_with_recovery',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'goal_x': LaunchConfiguration('goal_x'),
            'goal_y': LaunchConfiguration('goal_y'),
            'goal_yaw': LaunchConfiguration('goal_yaw'),
            'tolerance': LaunchConfiguration('tolerance'),
            'k_rho': LaunchConfiguration('k_rho'),
            'k_alpha': LaunchConfiguration('k_alpha'),
            'k_yaw': LaunchConfiguration('k_yaw'),
            'timeout_duration': LaunchConfiguration('timeout_duration'),
        }],
    )

    return LaunchDescription([
        goal_x_arg,
        goal_y_arg,
        goal_yaw_arg,
        tolerance_arg,
        k_rho_arg,
        k_alpha_arg,
        k_yaw_arg,
        timeout_duration_arg,
        drive_with_recovery_node,
    ])
