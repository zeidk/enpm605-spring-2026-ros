"""Combined mapping and navigation launcher.

One file, three modes selected via the `mode` launch argument:

  - mode:=mapping              SLAM Toolbox only (build a map, no autonomous nav)
  - mode:=navigation           Nav2 + AMCL on a previously saved map
  - mode:=explore   SLAM Toolbox + Nav2 (navigate while mapping)

Examples:
  ros2 launch nav_demo map_nav.launch.py mode:=mapping
  ros2 launch nav_demo map_nav.launch.py mode:=navigation map:=/path/to/map.yaml
  ros2 launch nav_demo map_nav.launch.py mode:=navigation goal_source:=waypoints
  ros2 launch nav_demo map_nav.launch.py mode:=explore goal_source:=single_goal
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = get_package_share_directory("nav_demo")

    # ------------------------------------------------------------------
    # Launch arguments
    # ------------------------------------------------------------------
    mode_arg = DeclareLaunchArgument(
        "mode",
        default_value="explore",
        choices=["mapping", "navigation", "explore"],
        description=(
            "Which stack to launch: "
            "'mapping' (SLAM only), "
            "'navigation' (Nav2 + AMCL on saved map), "
            "'explore' (SLAM + Nav2)."
        ),
    )

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock.",
    )

    # Resolve default map path eagerly so it propagates cleanly into
    # nav2_bringup's localization_launch.py (PathJoinSubstitution defaults
    # don't always survive IncludeLaunchDescription).
    default_map_path = os.path.join(pkg_share, "maps", "husarion_world.yaml")
    map_arg = DeclareLaunchArgument(
        "map",
        default_value=default_map_path,
        description="Full path to map yaml (only used when mode:=navigation).",
    )

    rviz_arg = DeclareLaunchArgument(
        "rviz",
        default_value="true",
        description="Start RViz with the package's nav2 view.",
    )

    goal_source_arg = DeclareLaunchArgument(
        "goal_source",
        default_value="manual",
        choices=["single_goal", "waypoints", "manual"],
        description=(
            "How navigation goals are issued (only applies when Nav2 is running): "
            "'single_goal' / 'waypoints' run the navigation_node_exe demo node; "
            "'manual' skips it so you can click goals in RViz."
        ),
    )

    # ------------------------------------------------------------------
    # Shared paths
    # ------------------------------------------------------------------
    slam_params = PathJoinSubstitution(
        [FindPackageShare("nav_demo"), "config", "mapper_params_online_async.yaml"]
    )
    nav2_params = PathJoinSubstitution(
        [FindPackageShare("nav_demo"), "config", "nav2_params.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("nav_demo"), "rviz", "nav2.rviz"]
    )

    # ------------------------------------------------------------------
    # Mode predicates
    # ------------------------------------------------------------------
    mode = LaunchConfiguration("mode")

    uses_slam = IfCondition(
        PythonExpression(["'", mode, "' in ['mapping', 'explore']"])
    )
    uses_amcl = IfCondition(
        PythonExpression(["'", mode, "' == 'navigation'"])
    )
    uses_nav2 = IfCondition(
        PythonExpression(["'", mode, "' in ['navigation', 'explore']"])
    )
    run_demo_node = IfCondition(
        PythonExpression([
            "'", LaunchConfiguration("goal_source"), "' != 'manual' and '",
            mode, "' in ['navigation', 'explore']",
        ])
    )

    # ------------------------------------------------------------------
    # Conditional groups
    # ------------------------------------------------------------------
    slam_group = GroupAction(
        condition=uses_slam,
        actions=[
            LogInfo(msg="[map_nav] starting SLAM Toolbox"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("slam_toolbox"),
                        "launch",
                        "online_async_launch.py",
                    ])
                ]),
                launch_arguments={
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "slam_params_file": slam_params,
                }.items(),
            ),
        ],
    )

    amcl_group = GroupAction(
        condition=uses_amcl,
        actions=[
            LogInfo(msg=["[map_nav] starting Nav2 localization (AMCL) on map: ",
                         LaunchConfiguration("map")]),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("nav2_bringup"),
                        "launch",
                        "localization_launch.py",
                    ])
                ]),
                launch_arguments={
                    "map": LaunchConfiguration("map"),
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "params_file": nav2_params,
                    "autostart": "true",
                }.items(),
            ),
        ],
    )

    nav2_group = GroupAction(
        condition=uses_nav2,
        actions=[
            LogInfo(msg="[map_nav] starting Nav2 navigation stack"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("nav2_bringup"),
                        "launch",
                        "navigation_launch.py",
                    ])
                ]),
                launch_arguments={
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "autostart": "true",
                    "params_file": nav2_params,
                }.items(),
            ),
        ],
    )

    rviz_group = GroupAction(
        condition=IfCondition(LaunchConfiguration("rviz")),
        actions=[
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=["-d", rviz_config],
                parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
                output="screen",
            ),
        ],
    )

    demo_node = Node(
        package="nav_demo",
        executable="navigation_node_exe",
        name="navigation_node",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "mode": LaunchConfiguration("goal_source"),
        }],
        condition=run_demo_node,
    )

    return LaunchDescription([
        mode_arg,
        use_sim_time_arg,
        map_arg,
        rviz_arg,
        goal_source_arg,
        LogInfo(msg=["[map_nav] mode = ", mode]),
        slam_group,
        amcl_group,
        nav2_group,
        rviz_group,
        demo_node,
    ])
