import pandas as pd
import pytest
from pathlib import Path
from analyst_studio.state import StudioState


def fresh():
    return StudioState(_reflex_internal_init=True)


def test_preview_apply_undo_and_new_upload_reset():
    state = fresh()
    state._load(pd.DataFrame({"x": [1., None, 3.]}), "a.csv")
    state.action = "Missing values"
    state.column = "x"
    state.method = "mean"
    state._prepare_preview()
    assert pd.isna(state._df.x.iloc[1])
    assert state.pending
    state.apply_preview()
    assert state._df.x.iloc[1] == 2
    assert len(state.history) == 1
    state.undo()
    assert pd.isna(state._df.x.iloc[1]) and not state.history
    state._load(pd.DataFrame({"y": [9]}), "b.csv")
    assert state.columns == ["y"] and not state.pending
    assert not state.history and not state.insight


def test_different_sessions_do_not_share_data():
    first, second = fresh(), fresh()
    first._load(pd.DataFrame({"x": [1]}), "one.csv")
    assert not second.loaded and second._df is None


def test_changed_form_invalidates_preview():
    state = fresh()
    state._load(pd.DataFrame({"x": [1, 1]}), "a.csv")
    state.set_action("Duplicates")
    state._prepare_preview()
    state.set_method("remove all")
    assert not state.pending


def test_failed_load_preserves_previous_dataset(monkeypatch):
    state = fresh()
    state._load(pd.DataFrame({"old": [1, 2]}), "old.csv")
    def broken_profile(frame):
        raise ValueError("Unsupported data")
    monkeypatch.setattr("analyst_studio.state.profile", broken_profile)
    import pytest
    with pytest.raises(ValueError):
        state._load(pd.DataFrame({"new": [3]}), "new.csv")
    assert state.filename == "old.csv"
    assert list(state._df.columns) == ["old"]


def test_failed_apply_preserves_data_and_undo_history(monkeypatch):
    state = fresh()
    state._load(pd.DataFrame({"x": [1, 1]}), "old.csv")
    state.set_action("Duplicates")
    state._prepare_preview()
    def broken_profile(frame):
        raise ValueError("Unsupported data")
    monkeypatch.setattr("analyst_studio.state.profile", broken_profile)
    state.apply_preview()
    assert len(state._df) == 2
    assert state.history == [] and state._snapshots == []
    assert state.pending and state.error


@pytest.mark.asyncio
async def test_upload_uses_selected_csv_format_and_preserves_data_on_failure():
    from io import BytesIO
    import reflex as rx
    state = fresh()
    state.csv_encoding = 'Windows-1252'
    state.csv_delimiter = 'Semicolon (;)'
    good = rx.UploadFile(file=BytesIO('name;amount\ncafé;12\n'.encode('cp1252')), path=Path('sales.csv'))
    async for _ in state.upload([good]):
        pass
    assert state._df.iloc[0].tolist() == ['café', 12]
    assert not state.error and not state.busy
    bad = rx.UploadFile(file=BytesIO(b'name;amount\nAda;12;extra\n'), path=Path('bad.csv'))
    async for _ in state.upload([bad]):
        pass
    assert 'บรรทัด 2' in state.error
    assert state.filename == 'sales.csv'
    assert state._df.iloc[0].tolist() == ['café', 12]
    assert not state.busy
