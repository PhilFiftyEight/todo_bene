#!/usr/bin/env fish

rm -v -f /Users/philippe/works/todo_bene/docs/media/01-setup.gif
cd /Users/philippe/works/todo_bene/
cp /Users/philippe/works/todo_bene/docs/media/01-setup.tape ./01-setup.tape

vhs 01-setup.tape -o /Users/philippe/works/todo_bene/docs/media/01-setup.gif

#rm -v -f /Users/philippe/.config/todo_bene/config.json dev.db todo_bene.log ./01-setup.tape ./.env
rm -v ./01-setup.tape
