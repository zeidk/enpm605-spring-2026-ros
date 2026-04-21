import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo
)
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Create a LaunchDescription object
    ld = LaunchDescription()

    # Launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )

    # Resolve map path at Python load time so it passes cleanly into
    # nav2_bringup's localization_launch.py (PathJoinSubstitution defaults
    # don't propagate reliably through IncludeLaunchDescription).
    pkg_share = get_package_share_directory("mapping_navigation_demo")
    default_map_path = os.path.join(pkg_share, "maps", "my_map.yaml")

    map_file_arg = DeclareLaunchArgument(
        "map",
        default_value=default_map_path,
        description="Full path to map yaml file to load"
    )

    # Log the map path for debugging
    log_map_path = LogInfo(
        msg=["Map file path: ", LaunchConfiguration("map")]
    )

    # Parameter files
    nav2_params_path = PathJoinSubstitution(
        [FindPackageShare("mapping_navigation_demo"), "config", "nav2_params.yaml"]
    )

    # 1. Nav2 Localization - AMCL publishes the map->odom transform itself
    #    Do NOT publish a static map->odom transform here; it conflicts with AMCL.
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'localization_launch.py'
            ])
        ]),
        launch_arguments={
            'map': default_map_path,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': nav2_params_path,
            'autostart': 'true'
        }.items(),
    )
    
    # 3. Nav2 Navigation Stack
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            ])
        ]),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': 'true',
            'params_file': nav2_params_path,
        }.items(),
    )
    
    # 4. RViz with navigation configuration
    rviz_config_path = PathJoinSubstitution(
        [FindPackageShare("mapping_navigation_demo"), "rviz", "nav2.rviz"]
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )

    # Add the launch arguments first
    ld.add_action(use_sim_time_arg)
    ld.add_action(map_file_arg)
    ld.add_action(log_map_path)
    
    # Add actions in the correct order
    ld.add_action(localization_launch)  # Using standard localization launch file
    ld.add_action(navigation_launch)
    ld.add_action(rviz_node)
    
    return ld