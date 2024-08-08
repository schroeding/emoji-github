#!/usr/bin/env bash

# the emojis.md file is based on this repository: https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md
# note that it will work for any markdown or text file, as long as the emoji names are written somewhere like this: `:emoji:`
grep -oP ':\K[A-z0-9]+(?=:)' emojis.md | sort -u | sed 's/^/:/' | sed 's/$/:/' > emojis_list.txt
