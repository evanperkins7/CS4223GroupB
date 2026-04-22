from openpilot.selfdrive.test.process_replay.process_replay import CONFIGS
from openpilot.selfdrive.test.process_replay.test_processes import EXCLUDED_PROCS, segments


REQUIRED_CAR_BRANDS = {"HYUNDAI", "TOYOTA", "HONDA", "TESLA"}
FULL_SEGMENT_PROCS = {"card", "controlsd", "lagd"}


def _eligible_segments_for_proc(proc_name: str) -> list[str]:
  if proc_name in FULL_SEGMENT_PROCS:
    return [segment for _, segment in segments]

  return [segment for car_brand, segment in segments if car_brand in {"HYUNDAI", "TOYOTA"}]


def test_selfdrived_is_covered_by_process_replay():
  proc_names = {cfg.proc_name for cfg in CONFIGS}

  assert "selfdrived" in proc_names
  assert "selfdrived" not in EXCLUDED_PROCS


def test_no_duplicate_process_config_names():
  proc_names = [cfg.proc_name for cfg in CONFIGS]

  assert len(proc_names) == len(set(proc_names))


def test_process_configs_have_required_endpoints():
  for cfg in CONFIGS:
    assert len(cfg.pubs) > 0
    assert len(cfg.subs) > 0


def test_required_car_brands_present_in_segment_list():
  cars_in_segments = {car for car, _ in segments}

  missing = REQUIRED_CAR_BRANDS - cars_in_segments
  assert not missing, f"Missing required car segment coverage: {sorted(missing)}"


def test_nonexcluded_processes_have_segment_coverage():
  for cfg in CONFIGS:
    if cfg.proc_name in EXCLUDED_PROCS:
      continue

    eligible = _eligible_segments_for_proc(cfg.proc_name)
    assert len(eligible) > 0, f"No eligible replay segments for process: {cfg.proc_name}"


# Review 3 Test Cases
def test_full_segment_processes_exist_in_configs():
  proc_names = {cfg.proc_name for cfg in CONFIGS}
  missing = FULL_SEGMENT_PROCS - proc_names

  assert not missing, f"Missing expected full-segment process configs: {sorted(missing)}"


def test_segments_have_unique_entries():
  assert len(segments) == len(set(segments)), "Duplicate segment entries found"
