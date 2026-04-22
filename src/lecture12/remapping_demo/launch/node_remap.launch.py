from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    front_camera = Node(
        package="remapping_demo",
        executable="camera_demo",
        name="front_camera",
        output="screen",
    )
    rear_camera = Node(
        package="remapping_demo",
        executable="camera_demo",
        name="rear_camera",
        output="screen",
    )

    return LaunchDescription(
        [front_camera, rear_camera]
    )
