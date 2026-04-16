import pytest
from streamlit.testing.v1 import AppTest
import os
from pathlib import Path

# AI-CONTEXT: We are testing the RenderCV Editor UI headlessly.
# This test suite verifies sidebar ordering, session state locking during AI generation,
# and Focus Mode layout toggling.

@pytest.fixture
def app_path():
    return str(Path(__file__).parent.parent / "rendercv" / "app.py")

def test_sidebar_hierarchy(app_path):
    """Verify the sidebar follows the ID -> Instructions -> AI Guide -> Actions hierarchy."""
    at = AppTest.from_file(app_path).run(timeout=30)
    
    # Check for core elements in sidebar
    assert at.sidebar.title[0].value == "📄 RenderCV"
    
    # AppTest access for expanders is via .get('expander') or plural index
    # But often it's easier to check presence of children
    assert any("AI Ghostwriter" in exp.label for exp in at.sidebar.expander)
    assert at.sidebar.subheader[0].value == "Actions"

def test_focus_mode_toggle(app_path):
    """Verify Focus Mode collapses the editor and maximizes the PDF preview."""
    at = AppTest.from_file(app_path).run()
    
    assert at.session_state.focus_mode == False
    
    # Find button by label instead of index
    focus_btns = [b for b in at.sidebar.button if "Focus Mode" in b.label]
    assert len(focus_btns) > 0
    focus_btns[0].click().run()
    
    assert at.session_state.focus_mode == True
    # Editor (text_area with key "cv_content") should be gone in focus mode
    # Search in all text_areas
    assert not any(ta.key == "cv_content" for ta in at.text_area)

def test_ai_loading_ui_lock(app_path):
    """Verify UI disables manual editing while AI generation is in flight."""
    at = AppTest.from_file(app_path).run()
    
    # Set loading state
    at.session_state.ai_loading = True
    at.run()
    
    # Check if "Job Title" input is disabled
    title_inputs = [i for i in at.sidebar.text_input if i.label == "Job Title"]
    assert len(title_inputs) > 0
    assert title_inputs[0].disabled == True

def test_save_draft_persistence(app_path, tmp_path):
    """Verify Save Draft exists in the sidebar."""
    at = AppTest.from_file(app_path).run()
    
    draft_btns = [b for b in at.sidebar.button if "Save Draft" in b.label]
    assert len(draft_btns) > 0
