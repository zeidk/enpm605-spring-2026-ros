"""
Launch the ROSbot Gazebo simulation with empty_world.sdf
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource


def generate_launch_description():
    # World file path resolved at launch-file parse time
    gz_world = os.path.join(
        get_package_share_directory("husarion_gz_worlds"),
        "worlds",
        "empty_with_plugins.sdf",
    )

    # Gazebo simulation
    simulation = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("rosbot_gazebo"),
                "launch",
                "simulation.yaml",
            )
        ),
        launch_arguments={"gz_world": gz_world}.items(),
    )


    return LaunchDescription(
        [
            simulation,
        ]
    )
