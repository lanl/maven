try:
    from dsi.dsi import DSI
    from dsi.sync import Sync
except Exception:
    print("Add the DSI HPC module to your shell config file")

import shutil
import os
import subprocess

staging_folder = 00000
t1_db = 11111
t2_db = 22222
data_folder = 33333
campaign_path = 44444
tier2_table = 55555

# change cwd to that scratch folder which has t1 db, t2 db, and data/
os.chdir(staging_folder)

# TODO: see if we can check conduit without full path
result = subprocess.run(["module avail conduit"], shell=True, executable="/bin/bash", capture_output=True)
if "conduit/conduit-x86_64 (L)" in str(result.stderr):
    copy_tool = "conduit"
elif shutil.which("pfcp"):
    copy_tool = "pfcp"
else:
    print("Only testing on this HPC for now")
    assert False

# delete data in t2 locations table after moving to scratch but before moving to campaign
store = DSI(t2_db, silence_messages=True)
df = store.get_table(tier2_table, True, True)
df.iloc[0, 1:] = None # delete all col data except the dsi_table_name col
store.update(df)

full_data_path = os.path.join(staging_folder, data_folder, "")
# can skip index as data has not changed from local -> scratch -> campaign
fed_df = store.get_table("federated", True, True)
fed_df["local_location"] = full_data_path
fed_df["remote_location"] = os.path.join(campaign_path, t2_db.removesuffix(".db"))
store.update(fed_df)
store.close()

try:
    s = Sync(t2_db, isVerbose=True, skip_index=True, add_dbs=[t1_db])
    s.index(full_data_path, campaign_path)
    s.copy(copy_tool)
except Exception as e:
    print(f"DSI HPC Staging to Campaign Move Error{e}")
