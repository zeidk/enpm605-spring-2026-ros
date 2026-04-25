from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.parameter import Parameter
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
import tf_transformations


class NavigationDemoInterface(Node):
    """
    Example of a class that uses the BasicNavigator class to navigate the robot.
    """

    def __init__(self, node_name):
        super().__init__(node_name)

        # Since we are using Gazebo, we need to set the use_sim_time parameter to True
        self._sim_time = Parameter("use_sim_time", rclpy.Parameter.Type.BOOL, True)
        self.set_parameters([self._sim_time])

        # TF buffer for looking up the robot's position in the map frame
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        # Navigation mode: "waypoints" or "single_goal"
        self.declare_parameter("mode", "waypoints")
        self._mode = self.get_parameter("mode").get_parameter_value().string_value

        self.get_logger().info(
            f"Navigation demo started (mode={self._mode}), waiting for Nav2..."
        )
        
        # Navigator
        self._navigator = BasicNavigator()
            
        # Create a timer that calls initialize_navigation once after 5 seconds
        self._init_timer = self.create_timer(5.0, self._initialize_navigation_callback)

    def _initialize_navigation_callback(self):
        # Cancel the timer so this only runs once
        self._init_timer.cancel()

        try:
            # Set the initial pose of the robot
            self.localize()

            # Choose navigation mode based on parameter
            if self._mode == "waypoints":
                self.follow_waypoints()
            elif self._mode == "single_goal":
                self.navigate(3.0, -4.0)
            else:
                self.get_logger().error(
                    f"Unknown mode '{self._mode}'. Use 'waypoints' or 'single_goal'."
                )
                return

            self.get_logger().info("Navigation completed successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize navigation: {str(e)}")
            # Try again after a delay by creating a new timer
            self._init_timer = self.create_timer(5.0, self._initialize_navigation_callback)
        
    def localize(self):
        """
        Set the initial pose of the robot.

        Tries to look up the map -> base_link transform (which
        persists across Nav2 restarts as long as Gazebo is running).
        Falls back to the odom -> base_link transform, and finally
        to the origin if neither is available.
        """
        self._initial_pose = PoseStamped()
        self._initial_pose.header.frame_id = "map"
        self._initial_pose.header.stamp = self._navigator.get_clock().now().to_msg()

        pose_set = False

        # Try map -> base_link first (best: gives true map position)
        try:
            tf = self._tf_buffer.lookup_transform(
                "map", "base_link", rclpy.time.Time(), timeout=rclpy.duration.Duration(seconds=2.0)
            )
            self._initial_pose.pose.position.x = tf.transform.translation.x
            self._initial_pose.pose.position.y = tf.transform.translation.y
            self._initial_pose.pose.position.z = tf.transform.translation.z
            self._initial_pose.pose.orientation = tf.transform.rotation
            self.get_logger().info(
                f"Setting initial pose from map->base_link TF: "
                f"({tf.transform.translation.x:.2f}, "
                f"{tf.transform.translation.y:.2f})"
            )
            pose_set = True
        except Exception:
            self.get_logger().info("map->base_link TF not available yet.")

        # Fallback: try odom -> base_link
        if not pose_set:
            try:
                tf = self._tf_buffer.lookup_transform(
                    "odom", "base_link", rclpy.time.Time(), timeout=rclpy.duration.Duration(seconds=2.0)
                )
                self._initial_pose.pose.position.x = tf.transform.translation.x
                self._initial_pose.pose.position.y = tf.transform.translation.y
                self._initial_pose.pose.position.z = tf.transform.translation.z
                self._initial_pose.pose.orientation = tf.transform.rotation
                self.get_logger().info(
                    f"Setting initial pose from odom->base_link TF: "
                    f"({tf.transform.translation.x:.2f}, "
                    f"{tf.transform.translation.y:.2f})"
                )
                pose_set = True
            except Exception:
                self.get_logger().info("odom->base_link TF not available yet.")

        # Last resort: origin
        if not pose_set:
            self._initial_pose.pose.orientation.w = 1.0
            self.get_logger().warn(
                "No TF available, setting initial pose to origin."
            )

        self._navigator.setInitialPose(self._initial_pose)
        
    def navigate(self, x: float, y: float):
        """
        Navigate the robot to the goal (x, y).
        """
        self._navigator.waitUntilNav2Active() # Wait until Nav2 is active
        
        goal = self.create_pose_stamped(x, y, 0.0)
        
        self._navigator.goToPose(goal)
        while not self._navigator.isTaskComplete():
            feedback = self._navigator.getFeedback()
            self.get_logger().info(f"Feedback: {feedback}")
        
        result = self._navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info("Goal succeeded")
        elif result == TaskResult.CANCELED:
            self.get_logger().info("Goal was canceled!")
        elif result == TaskResult.FAILED:
            self.get_logger().info("Goal failed!")
            
    def follow_waypoints(self):
        self._navigator.waitUntilNav2Active()  # Wait until Nav2 is active

        pose1 = self.create_pose_stamped(2.0, 0.0, 0.0)
        pose2 = self.create_pose_stamped(5.0, 1.0, 1.57)
        pose3 = self.create_pose_stamped(-5.42, 11.22, 3.14)
        waypoints = [pose1, pose2, pose3]
        self._navigator.followWaypoints(waypoints)
        
        while not self._navigator.isTaskComplete():
            feedback = self._navigator.getFeedback()
            self.get_logger().info(f"Feedback: {feedback}")

        result = self._navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info("Goal succeeded")
        elif result == TaskResult.CANCELED:
            self.get_logger().info("Goal was canceled!")
        elif result == TaskResult.FAILED:
            self.get_logger().info("Goal failed!")

    def create_pose_stamped(self, x: float, y: float, yaw: float) -> PoseStamped:
        """
        Create a PoseStamped message.
        """
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self._navigator.get_clock().now().to_msg()
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0

        q_x, q_y, q_z, q_w = tf_transformations.quaternion_from_euler(0.0, 0.0, yaw)
        goal.pose.orientation.x = q_x
        goal.pose.orientation.y = q_y
        goal.pose.orientation.z = q_z
        goal.pose.orientation.w = q_w
        return goal