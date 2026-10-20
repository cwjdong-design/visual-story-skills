import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "skills/visual-story-production/scripts/validate_project.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        shutil.copytree(ROOT / "examples/comic-umbrella", self.project)

    def read(self, name):
        return json.loads((self.project / name).read_text(encoding="utf-8"))

    def write(self, name, data):
        (self.project / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def invalid(self, expected):
        result = MOD.validate(self.project)
        self.assertFalse(result["ok"], result)
        self.assertTrue(any(expected in e for e in result["errors"]), result)

    def test_comic_example(self):
        self.assertTrue(MOD.validate(self.project)["ok"])

    def test_short_drama_example(self):
        self.assertTrue(MOD.validate(ROOT / "examples/short-drama-umbrella")["ok"])

    def test_draft_template_has_no_fake_completion(self):
        result = MOD.validate(ROOT / "skills/visual-story-production/assets/project-template")
        self.assertTrue(result["ok"], result)
        self.assertTrue(any("unfinished" in n for n in result["warnings"]))

    def test_duplicate_shot(self):
        doc = self.read("shots.json")
        doc["shots"][1]["id"] = doc["shots"][0]["id"]
        self.write("shots.json", doc)
        self.invalid("duplicate id")

    def test_non_verbatim_source(self):
        doc = self.read("shots.json")
        doc["shots"][0]["sourceQuote"] = "This never happened in the source."
        self.write("shots.json", doc)
        self.invalid("verbatim")

    def test_stale_story(self):
        doc = self.read("project.json")
        doc["story"]["revision"] = 2
        self.write("project.json", doc)
        self.invalid("stale story")

    def test_stale_production(self):
        doc = self.read("shots.json")
        doc["productionRevision"] = 2
        self.write("shots.json", doc)
        self.invalid("stale production")

    def test_approved_cannot_depend_on_draft(self):
        doc = self.read("project.json")
        doc["production"]["status"] = "draft"
        self.write("project.json", doc)
        self.invalid("approved shots require")

    def test_unknown_look(self):
        doc = self.read("shots.json")
        doc["shots"][0]["visualTargets"][0]["lookId"] = "NOT_FOUND"
        self.write("shots.json", doc)
        self.invalid("unknown lookId")

    def test_unknown_state(self):
        doc = self.read("shots.json")
        doc["shots"][0]["visualTargets"][0]["stateId"] = "NOT_FOUND"
        self.write("shots.json", doc)
        self.invalid("unknown stateId")

    def test_state_disallows_look(self):
        doc = self.read("production.json")
        doc["assets"][0]["looks"].append({"id":"L02", "description":"second look", "sources":[{"kind":"design","note":"test"}]})
        self.write("production.json", doc)
        shots = self.read("shots.json")
        shots["shots"][0]["visualTargets"][0]["lookId"] = "L02"
        self.write("shots.json", shots)
        self.invalid("look not allowed")

    def test_state_phase_restriction(self):
        doc = self.read("production.json")
        doc["phases"].append({"id":"OTHER", "name":"other", "kind":"story", "sourceQuote":doc["phases"][0]["sourceQuote"]})
        doc["assets"][0]["states"][0]["phaseIds"] = ["OTHER"]
        self.write("production.json", doc)
        self.invalid("does not apply")

    def test_depiction_phase_is_not_onsite(self):
        doc = self.read("production.json")
        doc["phases"][0]["kind"] = "depiction"
        self.write("production.json", doc)
        self.invalid("onsite phaseId")

    def test_text_only_not_visible(self):
        doc = self.read("production.json")
        doc["assets"][0].update(visibility="text-only", looks=[], states=[])
        self.write("production.json", doc)
        self.invalid("text-only asset used")

    def test_visible_target_in_asset_ids(self):
        doc = self.read("shots.json")
        doc["shots"][0]["assetIds"].remove("CHAR_LIN")
        self.write("shots.json", doc)
        self.invalid("absent from assetIds")

    def test_duplicate_visible_target(self):
        doc = self.read("shots.json")
        doc["shots"][0]["visualTargets"].append(copy.deepcopy(doc["shots"][0]["visualTargets"][0]))
        self.write("shots.json", doc)
        self.invalid("duplicate onsite")

    def test_design_requires_reason(self):
        doc = self.read("production.json")
        doc["assets"][0]["looks"][0]["sources"] = [{"kind":"design","note":""}]
        self.write("production.json", doc)
        self.invalid("design requires")

    def test_content_clear_requires_evidence(self):
        doc = self.read("production.json")
        state = doc["assets"][2]["states"][0]
        state["depictedSubjects"] = []
        state["sources"] = [{"kind":"design","note":"not event evidence"}]
        self.write("production.json", doc)
        self.invalid("depiction override requires contentChange")

    def test_approved_empty_shots(self):
        doc = self.read("shots.json")
        doc["shots"] = []
        self.write("shots.json", doc)
        self.invalid("approved shot list cannot be empty")

    def test_panel_count(self):
        doc = self.read("project.json")
        doc["target"]["panelCount"] = 4
        self.write("project.json", doc)
        self.invalid("shot count differs")

    def test_video_duration_total(self):
        self.project = Path(self.tmp.name) / "drama"
        shutil.copytree(ROOT / "examples/short-drama-umbrella", self.project)
        doc = self.read("shots.json")
        doc["shots"][0]["durationSeconds"] += 1
        self.write("shots.json", doc)
        self.invalid("do not sum")

    def test_video_motion_required(self):
        self.project = Path(self.tmp.name) / "drama"
        shutil.copytree(ROOT / "examples/short-drama-umbrella", self.project)
        doc = self.read("shots.json")
        doc["shots"][0]["motion"] = ""
        self.write("shots.json", doc)
        self.invalid("requires motion")

    def test_path_escape(self):
        doc = self.read("project.json")
        doc["story"]["path"] = "../outside.md"
        self.write("project.json", doc)
        self.invalid("escapes project")

    def test_windows_absolute_path_rejected_on_any_os(self):
        doc = self.read("project.json")
        doc["story"]["path"] = "C:/private/story.md"
        self.write("project.json", doc)
        self.invalid("paths are not portable")

    def test_invalid_json_root(self):
        self.write("production.json", [])
        self.invalid("expected object")

    def test_invalid_nested_types_do_not_crash(self):
        doc = self.read("shots.json")
        doc["shots"][0]["assetIds"] = [{}]
        doc["shots"][0]["visualTargets"] = [None, {"assetId":[],"lookId":{},"stateId":[]}]
        self.write("shots.json", doc)
        self.invalid("expected object")

    def run_record(self, **kwargs):
        rec = {"id":"RUN01", "shotIds":["SH01"], "shotRevision":1, "platform":"test-only", "externalId":None,"attempt":1,"retryOf":None,"state":"unknown","outputPaths":[]}
        rec.update(kwargs)
        return rec

    def test_unknown_retry_blocked(self):
        self.write("runs.json", {"records":[self.run_record(),self.run_record(id="RUN02",attempt=2,retryOf="RUN01",state="planned")]})
        self.invalid("cannot retry an unresolved")

    def test_failed_retry_retains_history(self):
        self.write("runs.json", {"records":[self.run_record(state="failed"),self.run_record(id="RUN02",attempt=2,retryOf="RUN01",state="planned")]})
        result = MOD.validate(self.project)
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(self.read("runs.json")["records"]),2)

    def test_retry_must_increment(self):
        self.write("runs.json", {"records":[self.run_record(state="failed"),self.run_record(id="RUN02",attempt=3,retryOf="RUN01",state="planned")]})
        self.invalid("increment predecessor")

    def test_retry_must_target_same_shots(self):
        self.write("runs.json", {"records":[self.run_record(state="failed"),self.run_record(id="RUN02",shotIds=["SH02"],attempt=2,retryOf="RUN01",state="planned")]})
        self.invalid("same shot revision")

    def test_no_fabricated_success(self):
        self.write("runs.json", {"records":[self.run_record(state="succeeded")]})
        self.invalid("succeeded needs")

    def test_missing_local_media(self):
        self.write("runs.json", {"records":[self.run_record(state="succeeded",outputPaths=["media/not-created.png"])]})
        self.invalid("output does not exist")

    def test_historical_result_not_lost(self):
        self.write("runs.json", {"records":[self.run_record(shotRevision=2,state="failed",shotIds=["OLD_SHOT"])]})
        result = MOD.validate(self.project)
        self.assertTrue(result["ok"], result)
        self.assertTrue(any("historical" in w for w in result["warnings"]))

    def test_bad_task_state_reports_error_not_exception(self):
        self.write("runs.json", {"records":[self.run_record(state={})]})
        self.invalid("invalid state")

    def test_cli_json_and_exit_code(self):
        command = [sys.executable,str(ROOT / "skills/visual-story-production/scripts/validate_project.py"),str(self.project),"--json"]
        result = subprocess.run(command,capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.write("shots.json",{})
        failed = subprocess.run(command,capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(failed.returncode,1)
        self.assertFalse(json.loads(failed.stdout)["ok"])
