import shutil
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
Path(f"{proj_name}_endpoint.txt").write_text(endpoint_line, encoding="utf-8")
Path(f"{proj_name}_endpoint.txt").chmod(0o644)

result = subprocess.run(["module avail conduit"], shell=True, executable="/bin/bash", capture_output=True)
if "conduit/conduit-x86_64" in str(result.stderr):
    result = subprocess.run(["bash", "-lc", "type conduit"], capture_output=True, text=True)
    copy_command = str(result.stdout).split()
    for idx, s in enumerate(copy_command):
        if "/" in s:
            copy_command = copy_command[idx:idx+3]
            break
    copy_command.extend(["cp", f"{proj_name}_endpoint.txt", os.path.join(diana_endpoint, f"{proj_name}_endpoint.txt")])

elif shutil.which("pfcp"):
    copy_command = ["pfcp", f"{proj_name}_endpoint.txt", os.path.join(diana_endpoint, f"{proj_name}_endpoint.txt")]
    
else:
    print("Only testing on this HPC for now")
    assert False

process = subprocess.Popen(copy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
stdout, stderr = process.communicate()
if process.returncode != 0:
    print("Endpoint error", stderr)
    assert False