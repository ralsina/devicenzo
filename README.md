# Introducing DeVicenzo

## What is it?

A web browser.

## What is different about it?

It's based on Qt's QtWebEngine, a port of the Chrome engine. All DeVicenzo adds is what used to be called the "chrome" around it. Yes, that is confusing.

But basically: it's just the UI on top of QtWebEngine so that it becomes
somewhat usable.

And it's done in under 256 lines of properly formatted Python code.

## Why?

Because I like to show off how expressive Python is, and how powerful Qt and PySide (and formerly PyQt) are, so I wrote it.

## No, really, why?

Why as in "why should I use it?" You probably douldn't! I know I don't!

If I were to come up with a motive: it surely doesn't spy on you except on how webpages in general spy on you? Also, deleting a single file should make it forget all about you.

## Why the name?

Ernesto DeVicenzo was a golfer. This is sort of code golf. So, it has a golfer's name.

## How do I use it?

If you have PySide2 installed in your system just execute `devicenzo.py`
If you don't, create a python virtualenv and install `pyside2` in it then execute `devicenzo.py`.

If that made no sense ... well, this is probably not the right browser for you :-) I may do some installers at some point but don't hold your breath.

## Define "256 lines of properly formatted Python code"

* Formatted using `black`
* No flake8 violations other than longish lines (nothing ridiculous)
* Sloccount reports < 256 LOC

## How can I contribute?

Why would you? Are you bored or something? But hey, patches welcome, I guess?