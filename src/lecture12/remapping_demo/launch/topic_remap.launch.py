from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    front_camera = Node(
        package='remapping_demo',
        executable='camera_node',
        name='front_camera',
        remappings=[
            ('image_raw', '/sensors/front/image'),
        ],
        output='screen',
    )
    image_processor = Node(
        package='remapping_demo',
        executable='image_processor',
        remappings=[
            ('camera/image', '/sensors/front/image'),
        ],
        output='screen',
    )
    return LaunchDescription([front_camera, image_processor])
