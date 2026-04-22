from cereal import log

from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.selfdrived.events import ET, EVENTS, Events, NormalPermanentAlert
from openpilot.selfdrive.selfdrived.state import SOFT_DISABLE_TIME, StateMachine

State = log.SelfdriveState.OpenpilotState


def make_event(event_types):
  EVENTS[0] = {et: NormalPermanentAlert("alert") for et in event_types}
  return 0


class TestStateMachineTransitionsExtended:
  def setup_method(self):
    self.events = Events()
    self.state_machine = StateMachine()
    self.original_event_0 = EVENTS.get(0, {}).copy()

  def teardown_method(self):
    EVENTS[0] = self.original_event_0

  def _update(self, *event_types):
    self.events.clear()
    self.events.add(make_event(event_types))
    return self.state_machine.update(self.events)

  def test_disabled_enable_goes_to_enabled(self):
    self.state_machine.state = State.disabled
    enabled, active = self._update(ET.ENABLE)

    assert self.state_machine.state == State.enabled
    assert enabled is True
    assert active is True

  def test_disabled_enable_with_pre_enable_goes_to_pre_enabled(self):
    self.state_machine.state = State.disabled
    enabled, active = self._update(ET.ENABLE, ET.PRE_ENABLE)

    assert self.state_machine.state == State.preEnabled
    assert enabled is True
    assert active is False

  def test_disabled_enable_with_override_goes_to_overriding(self):
    self.state_machine.state = State.disabled
    enabled, active = self._update(ET.ENABLE, ET.OVERRIDE_LATERAL)

    assert self.state_machine.state == State.overriding
    assert enabled is True
    assert active is True

  def test_pre_enabled_transitions_to_enabled_when_pre_enable_clears(self):
    self.state_machine.state = State.preEnabled
    enabled, active = self._update()

    assert self.state_machine.state == State.enabled
    assert enabled is True
    assert active is True

  def test_soft_disabling_recovers_to_enabled_if_condition_clears(self):
    self.state_machine.state = State.softDisabling
    self.state_machine.soft_disable_timer = int(SOFT_DISABLE_TIME / DT_CTRL)
    enabled, active = self._update()

    assert self.state_machine.state == State.enabled
    assert enabled is True
    assert active is True

  def test_overriding_with_soft_disable_transitions_to_soft_disabling(self):
    self.state_machine.state = State.overriding
    enabled, active = self._update(ET.OVERRIDE_LATERAL, ET.SOFT_DISABLE)

    assert self.state_machine.state == State.softDisabling
    assert self.state_machine.soft_disable_timer == int(SOFT_DISABLE_TIME / DT_CTRL)
    assert enabled is True
    assert active is True

  def test_user_disable_has_priority_over_immediate_disable(self):
    self.state_machine.state = State.enabled
    enabled, active = self._update(ET.USER_DISABLE, ET.IMMEDIATE_DISABLE, ET.SOFT_DISABLE)

    assert self.state_machine.state == State.disabled
    assert enabled is False
    assert active is False
    assert self.state_machine.current_alert_types[-1] == ET.USER_DISABLE

  def test_immediate_disable_takes_priority_over_soft_disable(self):
    self.state_machine.state = State.enabled
    enabled, active = self._update(ET.IMMEDIATE_DISABLE, ET.SOFT_DISABLE)

    assert self.state_machine.state == State.disabled
    assert enabled is False
    assert active is False
    assert self.state_machine.current_alert_types[-1] == ET.IMMEDIATE_DISABLE

  def test_disabled_with_no_entry_stays_disabled(self):
    self.state_machine.state = State.disabled
    enabled, active = self._update(ET.ENABLE, ET.NO_ENTRY)

    assert self.state_machine.state == State.disabled
    assert enabled is False
    assert active is False
    assert ET.NO_ENTRY in self.state_machine.current_alert_types

  # Review 3 Test Cases
  def test_overriding_returns_to_enabled_when_override_clears(self):
    self.state_machine.state = State.overriding
    enabled, active = self._update()

    assert self.state_machine.state == State.enabled
    assert enabled is True
    assert active is True

  def test_disabled_with_pre_enable_without_enable_stays_disabled(self):
    self.state_machine.state = State.disabled
    enabled, active = self._update(ET.PRE_ENABLE)

    assert self.state_machine.state == State.disabled
    assert enabled is False
    assert active is False
