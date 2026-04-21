from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
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
    
    enable_rosbot_gazebo_arg = DeclareLaunchArgument(
        "enable_rosbot_gazebo",
        default_value="true",
        description="Enable the ROSbot Gazebo simulation",
    )
    
    # Set an absolute path for the map file to debug potential issues
    map_yaml_path = PathJoinSubstitution(
        [FindPackageShare("mapping_navigation_demo"), "maps", "husarion_world.yaml"]
    )
    
    map_file_arg = DeclareLaunchArgument(
        "map",
        default_value=map_yaml_path,
        description="Full path to map yaml file to load"
    )

    # Log the map path for debugging
    log_map_path = LogInfo(
        msg=["Map file path: ", LaunchConfiguration("map")]
    )

    # Parameter files
    nav2_file_path = PathJoinSubstitution(
        [FindPackageShare("mapping_navigation_demo"), "config", "nav2_params.yaml"]
    )



    # 2. Standalone Map Server (for better debugging)
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'yaml_filename': LaunchConfiguration('map')},
            {'topic_name': 'map'},
            {'frame_id': 'map'}
        ]
    )
    
    
    # 3. AMCL for localization
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            # Add some basic AMCL parameters - these should be in your nav2_params.yaml normally
            {'alpha1': 0.2},
            {'alpha2': 0.2},
            {'alpha3': 0.2},
            {'alpha4': 0.2},
            {'alpha5': 0.2},
            {'base_frame_id': 'base_link'},
            {'beam_skip_distance': 0.5},
            {'beam_skip_threshold': 0.3},
            {'do_beamskip': False},
            {'global_frame_id': 'map'},
            {'lambda_short': 0.1},
            {'max_beams': 60},
            {'max_particles': 2000},
            {'min_particles': 500},
            {'odom_frame_id': 'odom'},
            {'scan_topic': 'scan_filtered'},
            {'transform_tolerance': 1.0},
            {'update_min_d': 0.2},
            {'update_min_a': 0.2},
            {'z_hit': 0.5},
            {'z_max': 0.05},
            {'z_rand': 0.5},
            {'z_short': 0.05}
        ]
    )
    
    # 4. Lifecycle manager for map_server and amcl
    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'autostart': True},
            {'node_names': ['map_server', 'amcl']}
        ]
    )
    
    # 5. Nav2 Navigation Stack
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
            'params_file': nav2_file_path,
        }.items(),
    )
    
    # 6. RViz with navigation configuration
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

    # Add the launch arguments first
    ld.add_action(use_sim_time_arg)
    ld.add_action(enable_rosbot_gazebo_arg)
    ld.add_action(map_file_arg)
    ld.add_action(log_map_path)

    # Debug map server components individually instead of using localization_launch
    ld.add_action(map_server_node)
    ld.add_action(amcl_node)
    ld.add_action(lifecycle_manager_node)
    
    ld.add_action(navigation_launch)
    ld.add_action(rviz_node)
    
    return ld