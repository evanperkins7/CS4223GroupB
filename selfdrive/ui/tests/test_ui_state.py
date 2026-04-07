import pytest

from cereal import log
from openpilot.selfdrive.ui.ui_state import UIStatus, ui_state

State = log.SelfdriveState.OpenpilotState


class FakeSelfdriveState:
  def __init__(self, enabled=False, state=State.disabled):
    self.enabled = enabled
    self.state = state


class FakeSubMaster:
  def __init__(self, selfdrive_state, updated=True, frame=10):
    self._msgs = {"selfdriveState": selfdrive_state}
    self.updated = {"selfdriveState": updated}
    self.frame = frame

  def __getitem__(self, key):
    return self._msgs[key]


@pytest.fixture(autouse=True)
def restore_ui_state():
  snapshot = {
    "sm": ui_state.sm,
    "status": ui_state.status,
    "started": ui_state.started,
    "started_frame": ui_state.started_frame,
    "started_time": ui_state.started_time,
    "_engaged_prev": ui_state._engaged_prev,
    "_started_prev": ui_state._started_prev,
    "_offroad_transition_callbacks": ui_state._offroad_transition_callbacks,
    "_engaged_transition_callbacks": ui_state._engaged_transition_callbacks,
  }
  yield
  for k, v in snapshot.items():
    setattr(ui_state, k, v)


@pytest.mark.parametrize("ss_state", [State.preEnabled, State.overriding])
def test_ui_status_override_states(ss_state):
  ui_state.started = True
  ui_state._started_prev = True
  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=True, state=ss_state), updated=True)

  ui_state._update_status()

  assert ui_state.status == UIStatus.OVERRIDE


def test_ui_status_engaged_and_disengaged_states():
  ui_state.started = True
  ui_state._started_prev = True

  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=True, state=State.enabled), updated=True)
  ui_state._update_status()
  assert ui_state.status == UIStatus.ENGAGED

  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=False, state=State.disabled), updated=True)
  ui_state._update_status()
  assert ui_state.status == UIStatus.DISENGAGED


def test_engaged_transition_callback_fires_on_edges_only():
  callback_count = 0

  def callback():
    nonlocal callback_count
    callback_count += 1

  ui_state._engaged_transition_callbacks = [callback]
  ui_state.started = True
  ui_state._started_prev = True
  ui_state._engaged_prev = False

  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=True, state=State.enabled), updated=True)
  ui_state._update_status()
  assert callback_count == 1

  ui_state._update_status()
  assert callback_count == 1

  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=False, state=State.disabled), updated=True)
  ui_state._update_status()
  assert callback_count == 2


def test_offroad_transition_callback_fires_on_started_toggle():
  callback_count = 0

  def callback():
    nonlocal callback_count
    callback_count += 1

  ui_state._offroad_transition_callbacks = [callback]
  ui_state._started_prev = True
  ui_state.started = False
  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=False, state=State.disabled), updated=True, frame=25)

  ui_state._update_status()

  assert callback_count == 1


def test_onroad_transition_sets_started_metadata(monkeypatch):
  now = 123.45
  monkeypatch.setattr("openpilot.selfdrive.ui.ui_state.time.monotonic", lambda: now)

  ui_state.started = True
  ui_state._started_prev = False
  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=True, state=State.enabled), updated=True, frame=42)

  ui_state._update_status()

  assert ui_state.status == UIStatus.DISENGAGED
  assert ui_state.started_frame == 42
  assert ui_state.started_time == now


def test_offroad_transition_callback_runs_on_first_frame_even_without_toggle():
  callback_count = 0

  def callback():
    nonlocal callback_count
    callback_count += 1

  ui_state._offroad_transition_callbacks = [callback]
  ui_state._started_prev = False
  ui_state.started = False
  ui_state.sm = FakeSubMaster(FakeSelfdriveState(enabled=False, state=State.disabled), updated=False, frame=1)

  ui_state._update_status()

  assert callback_count == 1
