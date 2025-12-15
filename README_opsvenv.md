# opsvenv (Python 3.12)

Short notes for the `opsvenv` development environment and `opsrequirements.txt`:

- **Purpose:** `opsvenv` is a dedicated virtual environment for running OpenSeesPy on Windows.
- **Python version:** Python 3.12 (installed in this workspace because the OpenSeesPy Windows wheels are built against Python 3.12).
- **Requirements file:** `opsrequirements.txt` contains the exact packages installed in `opsvenv`.

Quick commands:

```powershell
# create venv (if needed)
py -3.12 -m venv opsvenv

# activate
.\opsvenv\Scripts\Activate.ps1

# install pinned deps
python -m pip install -r opsrequirements.txt

# register Jupyter kernel (optional)
python -m ipykernel install --user --name opsvenv --display-name "opsvenv (Python 3.12)"

# quick import test
python -c "import openseespy.opensees as ops; print('openseespy OK')"
```

Notes:

- Do not overwrite the project's `requirements.txt`; `opsrequirements.txt` is a separate, environment-specific snapshot.
- On Windows, OpenSeesPy requires compiled binaries and the MSVC runtime — `Microsoft Visual C++ 2015-2022 Redistributable (x64)` is required.
- If you need a different Python version, you can either: 1) recreate a venv with that Python and install available wheels (may not exist for all Python versions), or 2) build OpenSeesPy from source (more involved).

If you want, I can add a small script to create and populate `opsvenv` automatically.
