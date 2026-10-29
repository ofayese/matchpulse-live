"""
archive_media_reorganize.py

Autonomous media archiving and reorganization for MatchPulse Live submission.
Moves superseded media to submission/archive/*, support artifacts to submission/final-support,
and verifies byte-for-byte SHA-256 preservation.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = REPO_ROOT / "submission"

EXPECTED_CANDIDATE_NAME = "matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4"
EXPECTED_CANDIDATE_SHA256 = "b89c016d8d0c790ae42b3a761d6ec7f709cfa988159649c4cf0e07eb8906dcbf"

TARGET_DIRS = {
    "archive_videos": SUBMISSION_DIR / "archive" / "videos",
    "archive_audio": SUBMISSION_DIR / "archive" / "audio",
    "archive_manifests": SUBMISSION_DIR / "archive" / "manifests",
    "archive_scripts": SUBMISSION_DIR / "archive" / "scripts",
    "final_support": SUBMISSION_DIR / "final-support",
}

CLASSIFICATIONS = {
    # Approved Active Video
    "matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4": (
        "APPROVED_ACTIVE_VIDEO",
        SUBMISSION_DIR / "matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4",
    ),
    # Approved Support Artifacts
    "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.wav": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.wav",
    ),
    "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.manifest.json": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.manifest.json",
    ),
    "MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json",
    ),
    "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt",
    ),
    "MATCHPULSE_SHOT_LISTS.md": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "MATCHPULSE_SHOT_LISTS.md",
    ),
    "MATCHPULSE_VIDEO_SCRIPTS.md": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "MATCHPULSE_VIDEO_SCRIPTS.md",
    ),
    "MATCHPULSE_PLAYWRIGHT_RECORDING_PLAN.md": (
        "APPROVED_SUPPORT_ARTIFACT",
        TARGET_DIRS["final_support"] / "MATCHPULSE_PLAYWRIGHT_RECORDING_PLAN.md",
    ),
    # Superseded Videos
    "matchpulse-submission-demo-captioned.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-submission-demo-captioned.mp4",
    ),
    "matchpulse-submission-demo.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-submission-demo.mp4",
    ),
    "matchpulse-technical-demo-captioned.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-technical-demo-captioned.mp4",
    ),
    "matchpulse-technical-demo.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-technical-demo.mp4",
    ),
    "matchpulse-submission-hosted-candidate.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-submission-hosted-candidate.mp4",
    ),
    "matchpulse-submission-hosted-kokoro-candidate.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-submission-hosted-kokoro-candidate.mp4",
    ),
    "matchpulse-submission-hosted-kokoro-conversational-candidate.mp4": (
        "SUPERSEDED_VIDEO",
        TARGET_DIRS["archive_videos"] / "matchpulse-submission-hosted-kokoro-conversational-candidate.mp4",
    ),
    # Superseded Audio
    "matchpulse-hosted-narration-kokoro-bf-emma.wav": (
        "SUPERSEDED_AUDIO",
        TARGET_DIRS["archive_audio"] / "matchpulse-hosted-narration-kokoro-bf-emma.wav",
    ),
    "matchpulse-hosted-narration-kokoro-bf-emma-conversational.wav": (
        "SUPERSEDED_AUDIO",
        TARGET_DIRS["archive_audio"] / "matchpulse-hosted-narration-kokoro-bf-emma-conversational.wav",
    ),
    # Superseded Manifests
    "matchpulse-hosted-narration-kokoro-bf-emma.manifest.json": (
        "SUPERSEDED_MANIFEST",
        TARGET_DIRS["archive_manifests"] / "matchpulse-hosted-narration-kokoro-bf-emma.manifest.json",
    ),
    "matchpulse-hosted-narration-kokoro-bf-emma-conversational.manifest.json": (
        "SUPERSEDED_MANIFEST",
        TARGET_DIRS["archive_manifests"] / "matchpulse-hosted-narration-kokoro-bf-emma-conversational.manifest.json",
    ),
    "MATCHPULSE_VIDEO_MANIFEST.json": (
        "SUPERSEDED_MANIFEST",
        TARGET_DIRS["archive_manifests"] / "MATCHPULSE_VIDEO_MANIFEST.json",
    ),
    # Superseded Scripts
    "MATCHPULSE_NARRATION_CONVERSATIONAL.json": (
        "SUPERSEDED_SCRIPT",
        TARGET_DIRS["archive_scripts"] / "MATCHPULSE_NARRATION_CONVERSATIONAL.json",
    ),
    "MATCHPULSE_CAPTIONS_SUBMISSION.srt": (
        "SUPERSEDED_SCRIPT",
        TARGET_DIRS["archive_scripts"] / "MATCHPULSE_CAPTIONS_SUBMISSION.srt",
    ),
    "MATCHPULSE_CAPTIONS_TECHNICAL.srt": (
        "SUPERSEDED_SCRIPT",
        TARGET_DIRS["archive_scripts"] / "MATCHPULSE_CAPTIONS_TECHNICAL.srt",
    ),
    # Final Documentation (stays in submission root)
    "DEMO_SCRIPT_120S.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "DEMO_SCRIPT_120S.md"),
    "IP_DATA_AND_SAFETY_REVIEW.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "IP_DATA_AND_SAFETY_REVIEW.md"),
    "MATCHPULSE_VIDEO_VERIFICATION.txt": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "MATCHPULSE_VIDEO_VERIFICATION.txt"),
    "PITCH.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "PITCH.md"),
    "PORTAL_SUBMISSION_WORKSHEET.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "PORTAL_SUBMISSION_WORKSHEET.md"),
    "PROJECT_DESCRIPTION.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "PROJECT_DESCRIPTION.md"),
    "REGISTRATION_AND_SUBMISSION_CHECKLIST.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "REGISTRATION_AND_SUBMISSION_CHECKLIST.md"),
    "TESTING_INSTRUCTIONS.md": ("FINAL_DOCUMENTATION", SUBMISSION_DIR / "TESTING_INSTRUCTIONS.md"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().lower()


def find_doc_references(filename: str) -> list[str]:
    """Search markdown, json, txt files in the repo for mentions of this filename."""
    matches = []
    for ext in ("*.md", "*.json", "*.txt"):
        for p in REPO_ROOT.glob(ext):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                if filename in text:
                    matches.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))
            except Exception:
                pass
        for p in SUBMISSION_DIR.glob(ext):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                if filename in text:
                    rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                    if rel not in matches:
                        matches.append(rel)
            except Exception:
                pass
    return sorted(matches)


def get_git_info() -> tuple[set[str], set[str]]:
    # Tracked files
    res = subprocess.run(
        ["git", "ls-files", "submission"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = {line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()}

    # Ignored files
    res2 = subprocess.run(
        ["git", "status", "--ignored", "--porcelain", "submission"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    ignored = set()
    for line in res2.stdout.splitlines():
        if line.startswith("!!"):
            ignored.add(line[3:].strip().replace("\\", "/"))

    return tracked, ignored


def main():
    print("=== MatchPulse Media Reorganize & Archive ===")

    # 1. Check approved active video gate
    candidate_path = SUBMISSION_DIR / EXPECTED_CANDIDATE_NAME
    if not candidate_path.exists():
        print(f"FATAL: Candidate video not found at {candidate_path}")
        sys.exit(1)

    candidate_sha = sha256_file(candidate_path)
    print(f"Candidate video SHA-256: {candidate_sha}")
    if candidate_sha != EXPECTED_CANDIDATE_SHA256:
        print("FATAL: SHA-256 mismatch!")
        print(f"  Expected: {EXPECTED_CANDIDATE_SHA256}")
        print(f"  Actual:   {candidate_sha}")
        sys.exit(2)
    print("Gate passed: Approved active video SHA-256 matches expected candidate.\n")

    # 2. Check if reorganization is needed or already performed
    tracked_files, ignored_files = get_git_info()

    # Determine location of each expected file
    pre_hashes = {}
    pre_bytes = {}
    inventory = []

    for fname, (classification, dest) in sorted(CLASSIFICATIONS.items()):
        src_root = SUBMISSION_DIR / fname
        if src_root.exists() and src_root != dest:
            current_loc = src_root
        elif dest.exists():
            current_loc = dest
        else:
            print(f"FATAL: File {fname} not found in submission root or at destination {dest}")
            sys.exit(3)

        rel_path = str(current_loc.relative_to(REPO_ROOT)).replace("\\", "/")
        file_sha = sha256_file(current_loc)
        stat = current_loc.stat()
        byte_size = stat.st_size
        mtime_utc = datetime.datetime.fromtimestamp(stat.st_mtime, datetime.UTC).isoformat()

        is_tracked = rel_path in tracked_files or str(src_root.relative_to(REPO_ROOT)).replace("\\", "/") in tracked_files
        is_ignored = rel_path in ignored_files or str(src_root.relative_to(REPO_ROOT)).replace("\\", "/") in ignored_files
        git_status = "tracked" if is_tracked else ("ignored" if is_ignored else "untracked")

        doc_refs = find_doc_references(fname)

        pre_hashes[fname] = file_sha
        pre_bytes[fname] = byte_size

        entry = {
            "filename": fname,
            "relative_path": str(src_root.relative_to(REPO_ROOT)).replace("\\", "/"),
            "current_location": rel_path,
            "extension": current_loc.suffix,
            "byte_size": byte_size,
            "last_modified_utc": mtime_utc,
            "sha256": file_sha,
            "git_status": git_status,
            "git_ignore_status": is_ignored,
            "is_tracked": is_tracked,
            "referenced_by_docs": doc_refs,
            "classification": classification,
            "proposed_destination": str(dest.relative_to(REPO_ROOT)).replace("\\", "/"),
        }
        inventory.append(entry)

    total_pre_count = len(inventory)
    total_pre_bytes = sum(pre_bytes.values())
    print(f"Total inventory count: {total_pre_count}")
    print(f"Total bytes: {total_pre_bytes:,} bytes")

    # 3. Create destination directories
    for _name, target_dir in TARGET_DIRS.items():
        if not target_dir.exists():
            print(f"Creating directory: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

    # 4. Execute moves
    move_log = []
    for item in inventory:
        src = REPO_ROOT / item["current_location"]
        dest = REPO_ROOT / item["proposed_destination"]

        if src == dest:
            print(f"[RETAIN] {item['filename']} -> remains at {item['current_location']}")
            move_log.append({
                "filename": item["filename"],
                "action": "retained",
                "source": item["current_location"],
                "destination": item["proposed_destination"],
                "sha256": item["sha256"],
            })
            continue

        if dest.exists():
            print(f"FATAL: Destination already exists: {dest}")
            sys.exit(4)

        print(f"[MOVE] {item['filename']} -> {item['proposed_destination']}")
        shutil.move(str(src), str(dest))
        move_log.append({
            "filename": item["filename"],
            "action": "moved",
            "source": item["current_location"],
            "destination": item["proposed_destination"],
            "sha256": item["sha256"],
        })

    # 5. Post-move verification
    print("\n=== Post-Move Verification ===")
    post_hashes = {}
    post_bytes = {}
    total_post_count = 0
    total_post_bytes = 0

    for item in inventory:
        dest = REPO_ROOT / item["proposed_destination"]
        if not dest.exists():
            print(f"FATAL: Post-move file missing at {dest}")
            sys.exit(5)

        post_sha = sha256_file(dest)
        stat = dest.stat()
        post_sz = stat.st_size

        if post_sz == 0:
            print(f"FATAL: Post-move zero-byte file detected: {dest}")
            sys.exit(6)

        if post_sha != item["sha256"]:
            print(f"FATAL: Hash mismatch after move for {item['filename']}!")
            print(f"  Pre:  {item['sha256']}")
            print(f"  Post: {post_sha}")
            sys.exit(7)

        post_hashes[item["filename"]] = post_sha
        post_bytes[item["filename"]] = post_sz
        total_post_count += 1
        total_post_bytes += post_sz

    print(f"Verified all {total_post_count} files preserved exact SHA-256.")
    print(f"Post-move count: {total_post_count} (Expected: {total_pre_count})")
    print(f"Post-move total bytes: {total_post_bytes:,} (Expected: {total_pre_bytes:,})")

    assert total_pre_count == total_post_count, "File count mismatch!"
    assert total_pre_bytes == total_post_bytes, "Total byte size mismatch!"

    # 6. Verify top-level submission directory
    top_level_files = [f for f in SUBMISSION_DIR.iterdir() if f.is_file()]
    top_level_names = {f.name for f in top_level_files}

    # Exactly ONE top-level MP4
    top_mp4s = [f.name for f in top_level_files if f.suffix.lower() == ".mp4"]
    print(f"\nTop-level MP4 files: {top_mp4s}")
    if top_mp4s != [EXPECTED_CANDIDATE_NAME]:
        print(f"FATAL: Expected exactly [{EXPECTED_CANDIDATE_NAME}], found {top_mp4s}")
        sys.exit(8)

    # NO top-level WAV
    top_wavs = [f.name for f in top_level_files if f.suffix.lower() == ".wav"]
    if top_wavs:
        print(f"FATAL: Found top-level WAV files: {top_wavs}")
        sys.exit(9)

    # NO top-level narration manifest
    top_manifests = [f.name for f in top_level_files if f.name.endswith(".manifest.json")]
    if top_manifests:
        print(f"FATAL: Found top-level narration manifests: {top_manifests}")
        sys.exit(10)

    # NO top-level narration script
    top_scripts = [f.name for f in top_level_files if "NARRATION" in f.name]
    if top_scripts:
        print(f"FATAL: Found top-level narration scripts: {top_scripts}")
        sys.exit(11)

    print("\nPhase 11 top-level validation PASSED:")
    print(f"  - Exactly one top-level MP4: {top_mp4s[0]}")
    print("  - Zero top-level WAV files")
    print("  - Zero top-level narration manifests")
    print("  - Zero top-level provisional/narration scripts")
    print(f"  - Remaining top-level files ({len(top_level_files)}): {sorted(top_level_names)}")

    # 7. Write full inventory and move log
    report = {
        "generated_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "summary": {
            "total_files": total_post_count,
            "total_bytes": total_post_bytes,
            "active_video": EXPECTED_CANDIDATE_NAME,
            "active_video_sha256": candidate_sha,
            "counts_by_classification": {},
        },
        "inventory": inventory,
        "move_log": move_log,
    }

    for item in inventory:
        c = item["classification"]
        report["summary"]["counts_by_classification"][c] = (
            report["summary"]["counts_by_classification"].get(c, 0) + 1
        )

    report_path = SUBMISSION_DIR / "archive" / "inventory_report.json"
    with open(report_path, "w", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
    print(f"\nInventory report written to {report_path.relative_to(REPO_ROOT)}")
    print("\nReorganization complete and verified successfully!")


if __name__ == "__main__":
    main()
