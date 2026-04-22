from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    front_camera = Node(
        package="remapping_demo",
        executable="camera_demo",
        name="front_camera",
        remappings=[
            ("image_raw", "/sensors/front/image"),
        ],
        output="screen",
    )
    rear_camera = Node(
        package="remapping_demo",
        executable="camera_demo",
        name="rear_camera",
        remappings=[
            ("image_raw", "/sensors/rear/image"),
        ],
        output="screen",
    )
    front_image_processor = Node(
        package="remapping_demo",
        executable="image_processor",
        name="front_camera_processor",
        remappings=[
            ("camera/image", "/sensors/front/image"),
        ],
        output="screen",
    )
    rear_image_processor = Node(
        package="remapping_demo",
        executable="image_processor",
        name="rear_camera_processor",
        remappings=[
            ("camera/image", "/sensors/rear/image"),
        ],
        output="screen",
    )
    return LaunchDescription(
        [front_camera, rear_camera, front_image_processor, rear_image_processor]
    )
