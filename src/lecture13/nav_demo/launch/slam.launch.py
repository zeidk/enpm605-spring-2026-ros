from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
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

    # Parameter files
    default_slam_params_path = PathJoinSubstitution(
        [
            FindPackageShare("nav_demo"),
            "config",
            "mapper_params_online_async.yaml",
        ]
    )

    nav2_file_path = PathJoinSubstitution(
        [FindPackageShare("nav_demo"), "config", "nav2_params.yaml"]
    )


    # 1. SLAM Toolbox launch - before Nav2
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
            "use_sim_time": LaunchConfiguration('use_sim_time'),
            "slam_params_file": default_slam_params_path,
        }.items()
    )
    
    # 2. Nav2 launch - REMOVED map parameter for SLAM mode
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("nav2_bringup"),
                        "launch",
                        "navigation_launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": LaunchConfiguration('use_sim_time'),
            "autostart": "true",
            "params_file": nav2_file_path,
            # Removed map parameter to work with SLAM
        }.items(),
    )
    
    # 4. RViz with navigation configuration
    rviz_config_path = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "rviz", "nav2_default_view.rviz"]
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )
    
    # 5. Your navigation demo node
    navigation_demo_node = Node(
        package='nav_demo',
        executable='navigation_node',
        name='navigation_node',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )

    # Add the launch arguments first
    ld.add_action(use_sim_time_arg)
    
    # Add actions in correct order
    ld.add_action(slam_toolbox_launch)  # SLAM first
    ld.add_action(nav2_launch)          # Nav2 second
    ld.add_action(rviz_node)            # RViz third
    # ld.add_action(navigation_demo_node) # Your node last
    
    # Return the LaunchDescription object
    return ld