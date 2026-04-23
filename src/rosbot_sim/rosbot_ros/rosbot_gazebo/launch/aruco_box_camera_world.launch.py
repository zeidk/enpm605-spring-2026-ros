"""
Launch the ROSbot Gazebo simulation with aruco_box_camera_world.sdf and
bridge the overhead camera image/camera_info topics to ROS.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    gz_world = os.path.join(
        get_package_share_directory("husarion_gz_worlds"),
        "worlds",
        "aruco_box_camera_world.sdf",
    )

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

    # Bridge the Gazebo camera topic(s) to ROS 2.
    # GZ topic "overhead_camera/image_raw" -> ROS topic "/overhead_camera/image_raw"
    # GZ topic "overhead_camera/camera_info" -> ROS topic "/overhead_camera/camera_info"
    camera_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="overhead_camera_bridge",
        arguments=[
            "/overhead_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/overhead_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            simulation,
            camera_bridge,
        ]
    )
