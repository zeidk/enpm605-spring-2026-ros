from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    ExecuteProcess,
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Create a LaunchDescription object
    ld = LaunchDescription()

    default_slam_params_path = PathJoinSubstitution(
        [
            FindPackageShare("mapping_navigation_demo"),
            "config",
            "mapper_params_online_async.yaml",
        ]
    )

    # Declare a launch argument to enable or disable SLAM Toolbox
    enable_slam_toolbox_arg = DeclareLaunchArgument(
        "enable_slam_toolbox", default_value="true", description="Enable SLAM Toolbox"
    )

    # SLAM Toolbox launch - improved version
    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("slam_toolbox"),
                        "launch",
                        "online_async_launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "true",
            "slam_params_file": default_slam_params_path,
        }.items(),
        condition=IfCondition(LaunchConfiguration("enable_slam_toolbox")),
    )

    # Add the launch arguments and groups to the LaunchDescription
    ld.add_action(enable_slam_toolbox_arg)
    ld.add_action(slam_toolbox_launch)

    # Return the LaunchDescription object
    return ld
