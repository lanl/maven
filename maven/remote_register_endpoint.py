import os
import subprocess
from pathlib import Path

staging_folder = 00000
endpoint_line = 11111
proj_name = 22222
diana_endpoint = 33333

# change cwd to that scratch folder which has t1 db, t2 db, and data/
os.chdir(staging_folder)

# create txt file
endpoint_txt_name = f"{proj_name}_endpoint.txt"
Path(endpoint_txt_name).write_text(endpoint_line, encoding="utf-8")
Path(endpoint_txt_name).chmod(0o644)

shell = os.environ.get("SHELL")
pfcp_result = subprocess.run(["module avail marfs"], shell=True, executable=shell, capture_output=True)
conduit_result = subprocess.run(["module avail conduit"], shell=True, executable=shell, capture_output=True)
if "marfs-x86_64" in str(pfcp_result.stderr):
    copy_command = ["bash", "-lc", f"module load marfs && pfcp {endpoint_txt_name} {os.path.join(diana_endpoint, endpoint_txt_name)}"]

elif "conduit/conduit-x86_64" in str(conduit_result.stderr):
    result = subprocess.run(["bash", "-lc", "type conduit"], capture_output=True, text=True)
    copy_command = str(result.stdout).split()
    for idx, s in enumerate(copy_command):
        if "/" in s:
            copy_command = copy_command[idx:idx+3]
            break
    copy_command.extend(["cp", endpoint_txt_name, os.path.join(diana_endpoint, endpoint_txt_name)])

else:
    print("Only testing on this HPC for now")
    assert False

process = subprocess.Popen(copy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
stdout, stderr = process.communicate()
if process.returncode != 0:
    print("Endpoint error", stderr)
    assert False