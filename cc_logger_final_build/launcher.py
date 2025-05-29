
import subprocess
import os
import sys

# Resolve path to actual Streamlit app script
script_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
script_path = os.path.join(script_dir, "cc_logger_lan_only.py")

# Call the streamlit app (assuming it's bundled)
subprocess.call(["streamlit", "run", script_path, "--server.address=localhost"])
