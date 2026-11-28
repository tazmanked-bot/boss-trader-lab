"""Gate then limit-exec; only the parent selects fixed reviewed build argv."""
import os
import resource
import select
import sys

fd = int(sys.argv[1]); budget = int(sys.argv[2])
if not select.select([fd], [], [], 10)[0] or os.read(fd, 1) != b'1':
    raise SystemExit(90)
os.close(fd)
os.umask(0o077); os.nice(10)
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
for key, value in ((resource.RLIMIT_CPU, budget), (resource.RLIMIT_CORE, 0),
                   (resource.RLIMIT_NOFILE, 256), (resource.RLIMIT_FSIZE, 256*1024**2)):
    _, hard = resource.getrlimit(key)
    value = value if hard < 0 else min(value, hard)
    resource.setrlimit(key, (value, value))
os.execve(sys.argv[3], sys.argv[3:], dict(os.environ))
