"""Self-cycling lifecycle node.

Demonstrates programmatic state transitions by calling its own
change_state service on a timer, cycling through the full lifecycle:
Unconfigured -> Inactive -> Active -> Inactive -> Unconfigured -> ...
"""

from lifecycle_msgs.srv import ChangeState
from lifecycle_msgs.msg import Transition
from rclpy_lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String


class SelfCyclingNode(LifecycleNode):
    """A lifecycle node that cycles through all states automatically."""

    _CYCLE = [
        Transition.TRANSITION_CONFIGURE,
        Transition.TRANSITION_ACTIVATE,
        Transition.TRANSITION_DEACTIVATE,
        Transition.TRANSITION_CLEANUP,
    ]

    def __init__(self):
        super().__init__('self_cycling_node')
        self._publisher = None
        self._pub_timer = None
        self._step = 0
        self._cli = self.create_client(
            ChangeState,
            '/self_cycling_node/change_state',
        )
        self._cycle_timer = self.create_timer(5.0, self._advance_state)
        self.get_logger().info('Node created. Cycling starts in 5 s.')

    def _advance_state(self):
        if not self._cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('change_state service not available')
            return

        transition_id = self._CYCLE[self._step % len(self._CYCLE)]
        req = ChangeState.Request()
        req.transition.id = transition_id

        future = self._cli.call_async(req)
        future.add_done_callback(self._on_change_state_done)

        self._step += 1

    def _on_change_state_done(self, future):
        result = future.result()
        if result is not None and result.success:
            self.get_logger().info('Transition succeeded.')
        else:
            self.get_logger().error('Transition failed.')

    def on_configure(self, state):
        self._publisher = self.create_lifecycle_publisher(
            String, 'sensor_data', 10
        )
        self.get_logger().info('Configured: publisher created.')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state):
        super().on_activate(state)
        self._pub_timer = self.create_timer(1.0, self._publish)
        self.get_logger().info('Active: publishing started.')
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        if self._pub_timer is not None:
            self._pub_timer.cancel()
            self._pub_timer = None
        super().on_deactivate(state)
        self.get_logger().info('Inactive: publishing stopped.')
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        self._publisher = None
        self.get_logger().info('Unconfigured: resources released.')
        return TransitionCallbackReturn.SUCCESS

    def _publish(self):
        msg = String(data=f'Cycling data')
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
