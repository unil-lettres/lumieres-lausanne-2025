# functions.mk is sub makefile for helper functions
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>


define PRINT_HELP_PYSCRIPT
import re, sys
from glob import glob

sub_makefiles = glob('${CURDIR}/make/*.mk')

def parse_makefile(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            match = re.match(r'^([a-zA-Z_/-]+):.*?## (.*)$$', line.strip())
            if match:
                target, help = match.groups()
                print("%-25s %s" % (target, help))


for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_/-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-25s %s" % (target, help))


# Print help for the sub makefiles
for sub_makefile in sub_makefiles:
    parse_makefile(sub_makefile)
endef
export PRINT_HELP_PYSCRIPT

.PHONY: test/dockerignore
test/dockerignore:
	rsync -avn . /tmp --exclude-from .dockerignore