#!/bin/sh
# Records site/demo.sh with asciinema and renders site/img/demo.gif with agg. Run from the repo root.
set -e
asciinema rec --overwrite --cols 100 --rows 22 -c "bash site/demo.sh" /tmp/dokdok-demo.cast
agg --font-size 15 --theme monokai --speed 1.2 --last-frame-duration 3 /tmp/dokdok-demo.cast site/img/demo.gif
ls -la site/img/demo.gif
