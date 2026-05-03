"""Self-cycling lifecycle node.

Demonstrates programmatic state transitions by calling its own
``change_state`` service on a timer, cycling through the full lifecycle:
Unconfigured -> Inactive -> Active -> Inactive -> Unconfigured -> ...

Unlike a typical lifecycle node driven by an external supervisor
(e.g. the ``ros2 lifecycle`` CLI), this node triggers its own
transitions to illustrate the state machine end-to-end in a single
process.
"""

from lifecycle_msgs.srv import ChangeState
from lifecycle_msgs.msg import Transition
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String


class SelfCyclingNode(LifecycleNode):
    """A lifecycle node that cycles through all states automatically.

    On a fixed interval the node issues the next transition in the
    sequence ``configure -> activate -> deactivate -> cleanup`` against
    its own ``change_state`` service. A ``std_msgs/String`` publisher on
    ``sensor_data`` is created in ``on_configure`` and only emits
    messages while the node is in the Active state.

    Attributes:
        _CYCLE (list[int]): Ordered transition IDs applied in round-robin.
        _publisher: Lifecycle publisher created in ``on_configure``.
        _timer: Timer driving the publish callback while active.
        _counter (int): Sequence number embedded in each message; reset
            to 0 on cleanup so a fresh configure starts from zero.
        _step (int): Index into ``_CYCLE`` for the next transition.
        _cli: Async client for this node's ``change_state`` service.
        _cycle_timer: Timer that periodically requests the next transition.
    """

    _CYCLE = [
        Transition.TRANSITION_CONFIGURE,
        Transition.TRANSITION_ACTIVATE,
        Transition.TRANSITION_DEACTIVATE,
        Transition.TRANSITION_CLEANUP,
    ]

    def __init__(self):
        """Initialize the node, service client, and cycling timer.

        Creates the ``change_state`` client targeting this node's own
        lifecycle service and starts a 5-second timer that advances the
        state machine. No lifecycle resources (publisher, publish timer)
        are created here; those are allocated in ``on_configure``.
        """
        super().__init__('self_cycling_node')
        self._publisher = None
        self._timer = None
        self._counter = 0
        self._step = 0
        self._cli = self.create_client(
            ChangeState,
            f'/{self.get_name()}/change_state',
        )
        self._cycle_timer = self.create_timer(5.0, self._advance_state)
        # print the current state of this node (retrieve the node name and its state dynamically)
        self.get_logger().info(f'Node {self.get_name()} started in state: {self._state_machine.current_state[1]}')

    def _advance_state(self):
        """Request the next transition from this node's lifecycle service.

        Picks the next transition ID from ``_CYCLE`` (wrapping around),
        sends it asynchronously, and registers a completion callback.
        If the service is unavailable within 1 second the attempt is
        skipped and retried on the next timer tick.
        """
        if not self._cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('change_state service not available')
            return

        transition_id = self._CYCLE[self._step % len(self._CYCLE)]
        req = ChangeState.Request()
        req.transition.id = transition_id

        previous_state = self._state_machine.current_state[1]
        future = self._cli.call_async(req)
        future.add_done_callback(
            lambda f: self._on_change_state_done(f, previous_state)
        )

        self._step += 1

    def _on_change_state_done(self, future, previous_state):
        """Log the outcome of an asynchronous ``change_state`` call.

        Args:
            future: Future returned by ``call_async``. Its result holds
                the ``ChangeState.Response`` whose ``success`` flag
                indicates whether the transition was accepted.
            previous_state: Lifecycle state label captured just before
                the transition request was sent.
        """
        result = future.result()
        current_state = self._state_machine.current_state[1]
        if result is not None and result.success:
            self.get_logger().info(
                f'Transition succeeded: {previous_state} -> {current_state}'
            )
        else:
            self.get_logger().error(
                f'Transition failed from {previous_state}. Current state: {current_state}'
            )

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
