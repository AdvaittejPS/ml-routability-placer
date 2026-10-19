#!/bin/bash
# Run OpenROAD Docker image to perform FastRoute/TritonRoute on the given DEF.
# Usage: ./scripts/run_openroad.sh path/to/design.def

if [ -z "$1" ]; then
  echo "Usage: $0 path/to/design.def"
  exit 1
fi
DEF=$1
CONTAINER=openroad/openroad:latest

docker run --rm -v $(pwd):/work -w /work ${CONTAINER} /bin/bash -lc "
  set -e
  # quick script: read DEF, run FastRoute and TritonRoute via OpenROAD TCL
  echo 'read_def ${DEF}' > run.tcl
  echo 'read_lef ./python/parser/example_ami33.yal' >> run.tcl
  echo 'place_macros' >> run.tcl
  echo 'global_route -engine fastroute' >> run.tcl
  echo 'write_verilog routed.v' >> run.tcl
  echo 'exit' >> run.tcl
  openroad -exit run.tcl
"
