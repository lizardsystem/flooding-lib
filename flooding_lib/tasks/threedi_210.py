# Start 3Di calculation using 3Di exe
# Run this under windows.
# This will produce a .nc file.
from threedi_win import setup_and_run_3di


def run_threedi_task(some_id):
    """
    3Di task
    """
    mdu_full_path = "Z:\\git\\sites\\flooding\\driedi\\Vecht\\vecht_autostartstop.mdu"
    setup_and_run_3di(mdu_full_path)
