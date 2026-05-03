"""Lifecycle sensor publisher node.

Demonstrates the managed-node lifecycle by publishing sensor data
only while the node is in the Active state. The publisher is
allocated in ``on_configure`` and released in ``on_cleanup``; the
publish timer is created in ``on_activate`` and cancelled in
``on_deactivate``.

Transitions are driven externally (e.g. via the ``ros2 lifecycle``
CLI or a supervisor node), making this a good counterpart to the
self-cycling example that drives its own transitions.
"""

from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String


class SensorPublisher(LifecycleNode):
    """A lifecycle node that publishes sensor data when active.

    Publishes ``std_msgs/String`` messages on the ``sensor_data`` topic
    at 1 Hz while Active. The payload carries a monotonically
    increasing reading counter so consumers can detect gaps caused by
    deactivation.

    Attributes:
        _publisher: Lifecycle publisher created in ``on_configure``.
        _timer: Timer driving the publish callback while active.
        _counter (int): Sequence number embedded in each message; reset
            to 0 on cleanup so a fresh configure starts from zero.
    """

    def __init__(self):
        """Initialize the node without allocating lifecycle resources.

        Only base-class setup runs here; the publisher and timer are
        created during the ``configure`` and ``activate`` transitions
        so the node starts in the Unconfigured state with no active
        ROS resources.
        """
        super().__init__('sensor_publisher')
        self._publisher = None
        self._timer = None
        self._counter = 0
        self.get_logger().info(f'Node {self.get_name()} started in state: {self._state_machine.current_state[1]}')
        

    def on_configure(self, state):
        """Allocate the lifecycle publisher when entering Inactive.

        Creates the ``sensor_data`` publisher. The publisher exists but
        does not emit messages until the node is activated.

        Args:
            state: Previous lifecycle state (provided by the framework);
                its ``label`` is logged for traceability.

        Returns:
            TransitionCallbackReturn.SUCCESS on successful configuration.
        """
        self.get_logger().info(f'Configuring from: {state.label}')
        try:
            self._publisher = self.create_lifecycle_publisher(String, 'sensor_data', 10)
        except Exception as e:
            self.get_logger().error(f'Configuration failed: {e}')
            return TransitionCallbackReturn.FAILURE
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state):
        """Start publishing when entering the Active state.

        Delegates to the base class to activate the lifecycle publisher,
        then starts a 1 Hz timer that drives ``_publish_sensor_data``.

        Args:
            state: Previous lifecycle state (provided by the framework).

        Returns:
            TransitionCallbackReturn.SUCCESS once the timer is started.
        """
        super().on_activate(state)
        self._timer = self.create_timer(1.0, self._publish_sensor_data)
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        """Stop publishing when leaving the Active state.

        Cancels and drops the publish timer and defers to the base class
        to deactivate the lifecycle publisher. The publisher itself is
        retained so the node can be reactivated without reconfiguring.

        Args:
            state: Previous lifecycle state (provided by the framework).

        Returns:
            TransitionCallbackReturn.SUCCESS after the timer is stopped.
        """
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        super().on_deactivate(state)
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        """Release resources when returning to Unconfigured.

        Drops the lifecycle publisher and resets the reading counter so
        the next ``on_configure`` call starts from a clean slate.

        Args:
            state: Previous lifecycle state (provided by the framework).

        Returns:
            TransitionCallbackReturn.SUCCESS once resources are released.
        """
        self._publisher = None
        self._counter = 0
        return TransitionCallbackReturn.SUCCESS

    def _publish_sensor_data(self):
        """Publish the next reading and advance the sequence counter."""
        msg = String(data=f'Reading {self._counter}')
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self._counter += 1
