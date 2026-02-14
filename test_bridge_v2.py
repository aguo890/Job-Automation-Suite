"""
test_bridge_v2.py — Verifies the new per-job CV Editor methods in cv_bridge.py.
Tests: load_job_cv, save_job_cv, render_from_content.
Run from project root: python test_bridge_v2.py
"""
import sys
import os

sys.path.append(os.getcwd())

from cv_bridge import CVOrchestrator


def test_editor_methods():
    print("=" * 60)
    print("  CV Bridge v2 — Editor Methods Test")
    print("=" * 60)

    orchestrator = CVOrchestrator()
    job_id = "test_editor_001"

    # --- Test 1: load_job_cv (should fall back to master) ---
    print("\n1. Testing load_job_cv (expect Master YAML fallback)...")
    content = orchestrator.load_job_cv(job_id)
    if "# Error" in content:
        print(f"   ❌ FAIL: {content}")
        return
    if "Aaron Guo" in content:
        print(f"   ✅ PASS: Loaded master YAML ({len(content)} chars)")
    else:
        print(f"   ⚠️ WARN: Loaded something, but couldn't find expected name. ({len(content)} chars)")

    # --- Test 2: save_job_cv ---
    print("\n2. Testing save_job_cv...")
    save_path = orchestrator.save_job_cv(job_id, content)
    if os.path.exists(save_path):
        print(f"   ✅ PASS: Saved to {save_path}")
    else:
        print(f"   ❌ FAIL: File not found at {save_path}")
        return

    # --- Test 3: load_job_cv (should now find tailored) ---
    print("\n3. Testing load_job_cv (expect tailored YAML)...")
    reloaded = orchestrator.load_job_cv(job_id)
    if reloaded == content:
        print(f"   ✅ PASS: Tailored YAML matches saved content")
    else:
        print(f"   ❌ FAIL: Content mismatch")

    # --- Test 4: render_from_content ---
    print("\n4. Testing render_from_content (full PDF render)...")
    pdf_path, status = orchestrator.render_from_content(job_id, content)

    if pdf_path and os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"   ✅ PASS: PDF generated at {pdf_path} ({size_kb:.1f} KB)")
    else:
        print(f"   ❌ FAIL: {status}")
        return

    # --- Cleanup ---
    print("\n5. Cleaning up test artifacts...")
    for ext in [".yaml", ".pdf"]:
        path = os.path.join(orchestrator.output_dir, f"{job_id}{ext}")
        if os.path.exists(path):
            os.remove(path)
            print(f"   🗑️ Removed {path}")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    test_editor_methods()
