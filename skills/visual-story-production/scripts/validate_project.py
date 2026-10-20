#!/usr/bin/env python3
"""Read-only, offline integrity checks for visual-story-production projects."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys


def validate(root):
    root = Path(root).resolve()
    errors, warnings = [], []

    def error(where, message):
        errors.append(f"{where}: {message}")

    def obj(value, where):
        if not isinstance(value, dict):
            error(where, "expected object")
            return {}
        return value

    def array(value, where):
        if not isinstance(value, list):
            error(where, "expected array")
            return []
        return value

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def integer(value, minimum=1):
        return type(value) is int and value >= minimum

    def number(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0

    def path_in_project(value, where):
        if not text(value):
            error(where, "expected non-empty relative path")
            return None
        # Reject Windows paths even when running on Unix, and vice versa.
        if "\\" in value or ":" in value or Path(value).is_absolute():
            error(where, "absolute/Windows-style paths are not portable")
            return None
        path = (root / value).resolve()
        if not path.is_relative_to(root):
            error(where, "path escapes project directory")
            return None
        return path

    def read_json(value, where):
        path = path_in_project(value, where)
        if path is None:
            return {}
        try:
            return obj(json.loads(path.read_text(encoding="utf-8-sig")), where)
        except (OSError, ValueError, UnicodeError) as exc:
            error(where, f"cannot read JSON ({type(exc).__name__})")
            return {}

    project = read_json("project.json", "project")
    if type(project.get("schemaVersion")) is not int or project.get("schemaVersion") != 1:
        error("project.schemaVersion", "expected 1")
    for name in ("projectId", "title"):
        if not text(project.get(name)):
            error(f"project.{name}", "required")
    if not integer(project.get("revision")):
        error("project.revision", "expected positive integer")
    medium = project.get("medium")
    if medium not in ("comic", "short-drama"):
        error("project.medium", "expected comic or short-drama")
    refs = {}
    for name in ("story", "production", "shots"):
        ref = obj(project.get(name), f"project.{name}")
        refs[name] = ref
        if not integer(ref.get("revision")):
            error(f"project.{name}.revision", "expected positive integer")
        if ref.get("status") not in ("draft", "approved", "stale"):
            error(f"project.{name}.status", "expected draft/approved/stale")
        elif ref["status"] != "approved":
            warnings.append(f"{name} is {ref['status']}; not an approved executable artifact")
    spath = path_in_project(refs["story"].get("path"), "story.path")
    story = ""
    if spath:
        try:
            story = spath.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            error("story", f"cannot read text ({type(exc).__name__})")
    if not story.strip():
        error("story", "empty or unavailable story")
    production = read_json(refs["production"].get("path"), "production")
    shots_doc = read_json(refs["shots"].get("path"), "shots")
    runs_doc = read_json("runs.json", "runs")
    for name, doc in (("production", production), ("shots", shots_doc)):
        if not integer(doc.get("revision")) or doc.get("revision") != refs[name].get("revision"):
            error(name + ".revision", "does not match project index")
        if doc.get("storyRevision") != refs["story"].get("revision"):
            error(name + ".storyRevision", "stale story dependency")
    if shots_doc.get("productionRevision") != refs["production"].get("revision"):
        error("shots.productionRevision", "stale production dependency")
    if refs["production"].get("status") == "approved" and refs["story"].get("status") != "approved":
        error("production", "approved production requires approved story")
    if refs["shots"].get("status") == "approved" and refs["production"].get("status") != "approved":
        error("shots", "approved shots require approved production")
    if not text(production.get("style")):
        error("production.style", "required")
    authorization = obj(project.get("authorization"), "authorization")
    for key in ("generationAllowed", "publicationAllowed"):
        if type(authorization.get(key)) is not bool:
            error("authorization." + key, "expected boolean")
    if not integer(authorization.get("maxAttemptsPerShot")):
        error("authorization.maxAttemptsPerShot", "expected positive integer")

    def quote(value, where):
        if not text(value) or value not in story:
            error(where, "must be a non-empty verbatim span of current story")

    def sources(value, where):
        items = array(value, where)
        if not items:
            error(where, "at least one provenance entry required")
        for index, raw in enumerate(items):
            src = obj(raw, f"{where}[{index}]")
            if src.get("kind") == "story":
                quote(src.get("quote"), where + ".quote")
            elif src.get("kind") == "design":
                if not text(src.get("note")):
                    error(where + ".note", "design requires a reason")
            else:
                error(where, "source kind must be story/design")
        return items

    def index_by_id(value, where):
        indexed = {}
        for index, raw in enumerate(array(value, where)):
            item = obj(raw, f"{where}[{index}]")
            key = item.get("id")
            if not text(key):
                error(where, "id must be non-empty string")
                continue
            if key in indexed:
                error(where, f"duplicate id {key}")
            indexed[key] = item
        return indexed

    phases = index_by_id(production.get("phases"), "phases")
    for key, phase in phases.items():
        if phase.get("kind") not in ("story", "depiction"):
            error("phases." + key, "expected story/depiction kind")
        if not text(phase.get("name")):
            error("phases." + key, "name required")
        quote(phase.get("sourceQuote"), "phases." + key + ".sourceQuote")
    assets = index_by_id(production.get("assets"), "assets")
    looks, states = {}, {}
    for key, asset in assets.items():
        where = "assets." + key
        if asset.get("kind") not in ("character", "scene", "prop"):
            error(where, "invalid asset kind")
        if asset.get("visibility") not in ("visible", "text-only"):
            error(where, "invalid visibility")
        for field in ("name", "description"):
            if not text(asset.get(field)):
                error(where + "." + field, "required")
        sources(asset.get("sources"), where + ".sources")
        looks[key] = index_by_id(asset.get("looks"), where + ".looks")
        states[key] = index_by_id(asset.get("states"), where + ".states")
        if asset.get("visibility") == "visible" and (not looks[key] or not states[key]):
            error(where, "visible assets need looks and states")
        if asset.get("visibility") == "text-only" and (looks[key] or states[key]):
            error(where, "text-only assets must not carry looks/states")
        for lid, look in looks[key].items():
            if not text(look.get("description")):
                error(where + ".looks." + lid, "description required")
            sources(look.get("sources"), where + ".looks." + lid + ".sources")
        for sid, state in states[key].items():
            sw = where + ".states." + sid
            if not text(state.get("description")):
                error(sw, "description required")
            state_sources = sources(state.get("sources"), sw + ".sources")
            allowed = array(state.get("allowedLookIds"), sw + ".allowedLookIds")
            if not allowed:
                error(sw, "state requires an allowed look")
            for lid in allowed:
                if not isinstance(lid, str) or lid not in looks[key]:
                    error(sw, "unknown allowed look")
            for pid in array(state.get("phaseIds"), sw + ".phaseIds"):
                if not isinstance(pid, str) or pid not in phases:
                    error(sw, "unknown phase")
            if "depictedSubjects" in state:
                if not text(state.get("contentChange")):
                    error(sw, "depiction override requires contentChange")
                if not any(isinstance(s, dict) and s.get("kind") == "story" for s in state_sources):
                    error(sw, "depiction override needs story provenance")

    def check_target(raw, where, phase_id=None, depiction=False):
        target = obj(raw, where)
        aid, lid, sid = (target.get(k) for k in ("assetId", "lookId", "stateId"))
        if not isinstance(aid, str) or aid not in assets:
            error(where, "unknown assetId")
            return None
        if assets[aid].get("visibility") != "visible":
            error(where, "text-only asset used as visible target")
        if not isinstance(lid, str) or lid not in looks[aid]:
            error(where, "unknown lookId")
        if not isinstance(sid, str) or sid not in states[aid]:
            error(where, "unknown stateId")
        else:
            state = states[aid][sid]
            allowed = state.get("allowedLookIds", [])
            if isinstance(allowed, list) and lid not in allowed:
                error(where, "look not allowed by state")
            restricted = state.get("phaseIds", [])
            if isinstance(restricted, list) and restricted and phase_id not in restricted:
                error(where, "state does not apply to selected phase")
        if depiction and assets[aid].get("kind") != "character":
            error(where, "depicted subject must be a character")
        return aid

    for aid, asset in assets.items():
        holders = [("assets." + aid, asset)] + [("assets." + aid + ".states." + sid, s) for sid, s in states[aid].items()]
        for where, holder in holders:
            if "depictedSubjects" not in holder:
                continue
            if asset.get("kind") != "prop":
                error(where, "only props may contain depictedSubjects")
            for raw in array(holder["depictedSubjects"], where + ".depictedSubjects"):
                item = obj(raw, where + ".depictedSubjects")
                pid = item.get("depictionPhaseId")
                if not isinstance(pid, str) or pid not in phases or phases[pid].get("kind") != "depiction":
                    error(where, "invalid depictionPhaseId")
                check_target(item, where + ".depictedSubjects", pid, depiction=True)

    shots = index_by_id(shots_doc.get("shots"), "shots")
    if not shots:
        if refs["shots"].get("status") == "approved":
            error("shots", "approved shot list cannot be empty")
        else:
            warnings.append("No shots yet; this is an unfinished planning project")
    total_duration = 0
    for key, shot in shots.items():
        where = "shots." + key
        pid = shot.get("phaseId")
        if not isinstance(pid, str) or pid not in phases or phases[pid].get("kind") != "story":
            error(where, "onsite phaseId must refer to story phase")
        for field in ("beat", "instant"):
            if not text(shot.get(field)):
                error(where + "." + field, "required")
        quote(shot.get("sourceQuote"), where + ".sourceQuote")
        ids = array(shot.get("assetIds"), where + ".assetIds")
        if len([i for i in ids if isinstance(i, str)]) != len(ids) or len(set(i for i in ids if isinstance(i, str))) != len(ids):
            error(where, "assetIds must be unique strings")
        for aid in ids:
            if not isinstance(aid, str) or aid not in assets:
                error(where, "assetIds contains unknown asset")
        visible = []
        for raw in array(shot.get("visualTargets"), where + ".visualTargets"):
            aid = check_target(raw, where + ".visualTargets", pid)
            if aid is not None:
                if aid not in ids:
                    error(where, "visible target absent from assetIds")
                visible.append(aid)
        if len(visible) != len(set(visible)):
            error(where, "duplicate onsite visible target")
        for raw in array(shot.get("textBlocks"), where + ".textBlocks"):
            block = obj(raw, where + ".textBlocks")
            if block.get("type") not in ("dialogue", "narration", "caption", "screen"):
                error(where, "invalid text block type")
            for field in ("text", "carrier"):
                if not text(block.get(field)):
                    error(where, "text block needs " + field)
            speaker = block.get("speakerId")
            if speaker is not None:
                if not isinstance(speaker, str) or speaker not in assets or assets[speaker].get("kind") != "character":
                    error(where, "unknown/non-character speaker")
                elif speaker not in ids:
                    error(where, "speaker absent from assetIds")
        if medium == "short-drama":
            duration = shot.get("durationSeconds")
            if not number(duration):
                error(where, "short-drama requires positive finite durationSeconds")
            else:
                total_duration += duration
            if not text(shot.get("motion")):
                error(where, "short-drama requires motion")
            array(shot.get("audio"), where + ".audio")
        elif shot.get("durationSeconds") is not None:
            error(where, "comic panel must not specify video duration")
    target = obj(project.get("target"), "target")
    count = target.get("panelCount")
    duration = target.get("durationSeconds")
    if count is not None and (not integer(count) or medium != "comic"):
        error("target.panelCount", "requires comic and positive integer")
    elif integer(count) and shots and count != len(shots):
        error("target.panelCount", "shot count differs from requested panel count")
    if duration is not None and (not number(duration) or medium != "short-drama"):
        error("target.durationSeconds", "requires short-drama and positive duration")
    elif number(duration) and shots and abs(duration - total_duration) > 0.01:
        error("target.durationSeconds", "shot durations do not sum to target (tolerance 0.01s)")

    runs = index_by_id(runs_doc.get("records"), "runs.records")
    allowed_states = ("planned", "submitted", "running", "succeeded", "failed", "unknown", "cancelled")
    for key, run in runs.items():
        where = "runs." + key
        shot_ids = array(run.get("shotIds"), where + ".shotIds")
        if not shot_ids:
            error(where, "shotIds must not be empty")
        revision = run.get("shotRevision")
        if not integer(revision):
            error(where, "shotRevision must be positive integer")
        elif revision == shots_doc.get("revision"):
            for sid in shot_ids:
                if not isinstance(sid, str) or sid not in shots:
                    error(where, "unknown shot for current revision")
        else:
            warnings.append(where + ": historical shot revision; cannot approve current shots")
        if run.get("state") not in allowed_states:
            error(where, "invalid state")
        attempt = run.get("attempt")
        if not integer(attempt):
            error(where, "attempt must be positive integer")
        elif integer(authorization.get("maxAttemptsPerShot")) and attempt > authorization["maxAttemptsPerShot"]:
            warnings.append(where + ": attempt exceeds currently recorded limit; reconcile authorization/history")
        if not text(run.get("platform")):
            error(where, "platform required")
        prior_id = run.get("retryOf")
        if prior_id is not None:
            prior = runs.get(prior_id) if isinstance(prior_id, str) else None
            if prior is None or prior_id == key:
                error(where, "invalid retryOf")
            elif prior.get("state") in ("unknown", "submitted", "running", "planned"):
                error(where, "cannot retry an unresolved attempt")
            elif not integer(prior.get("attempt")) or not integer(attempt) or attempt != prior["attempt"] + 1:
                error(where, "retry attempt must increment predecessor by one")
            elif prior.get("shotRevision") != revision or prior.get("shotIds") != shot_ids:
                error(where, "retry must target same shot revision and shotIds")
        elif integer(attempt) and attempt != 1:
            error(where, "attempt > 1 needs retryOf")
        existing_outputs = []
        for value in array(run.get("outputPaths"), where + ".outputPaths"):
            path = path_in_project(value, where + ".outputPaths")
            if path and not path.is_file():
                error(where, "recorded local output does not exist")
            elif path:
                existing_outputs.append(path)
        if run.get("state") == "succeeded" and not text(run.get("externalId")) and not existing_outputs:
            error(where, "succeeded needs external task identity or real local output; not proof of quality")
    if not runs:
        warnings.append("No generation records; no media completion is asserted")
    warnings.append("Integrity checks do not verify real approval, narrative/visual quality, billing or platform capability")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        result = validate(args.project)
    except (OSError, ValueError, RecursionError) as exc:
        result = {"ok": False, "errors": ["Cannot inspect project (" + type(exc).__name__ + ")"], "warnings": []}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS" if result["ok"] else "FAIL")
        for item in result["errors"]:
            print("ERROR: " + item)
        for item in result["warnings"]:
            print("NOTE: " + item)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
