These are the source files to the game. If you want to run on Linux,
for example, you'll want to copy these to the root game directory
(the one that contains the music, images, etc. subfolders) and run
entry.py.

Theoretically it requires Python 2.4+ and Pygame 1.6-ish. However,
I have had reports of it running fine with Python 2.3.

Remember that you may have to kill esd or kartsd or whatever has
your mixer devices open for SDL_mixer to work -- otherwise you
won't get any audio.
