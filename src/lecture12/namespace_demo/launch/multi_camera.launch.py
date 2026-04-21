from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    front_camera = Node(
        package='namespace_demo',
        executable='camera_node',
        namespace='front',
        output='screen',
    )
    rear_camera = Node(
        package='namespace_demo',
        executable='camera_node',
        namespace='rear',
        output='screen',
    )
    return LaunchDescription([front_camera, rear_camera])
