An almost fully functional web browser, based on PyQt, that aims to never be more than 128 lines long. Or, as SLOCCOUNT would say, $3120 of code, baby!

## Current Features ##

  * Multiple tabs
  * Bookmarks
  * URL autocompletion
  * Background downloads
  * HTTP and SOCKS proxy support (see below for configuration)
  * Most of what you expect on a web browser

[![](http://twitpic.com/show/thumb/4bvpgh.png)](http://twitpic.com/4bvpgh)

_which one is a real browser and which one is a small hack written in a completely different toolkit?_

## Getting De Vicenzo ##

Right now, to get it you need to use SVN, or you can just download a file.

Here is the shorter version, called [devicenzo.py](http://code.google.com/p/devicenzo/source/browse/trunk/devicenzo.py) and here's one that's more compliant with the PEP8 coding standard, but is usually a few features behind: [devicenzo-pep8.py](http://code.google.com/p/devicenzo/source/browse/trunk/devicenzo-pep8.py).

After you get that file, you can run it (as long as you have PyQt installed) with "python2 devicenzo.py"

## Keyboard Shortcuts ##

  * Ctrl+D: Bookmark this page
  * Ctrl+L: Edit URL
  * Ctrl++: Zoom In
  * Ctrl+-: Zoom Out
  * Ctrl+0: Reset Zoom
  * Ctrl+T: New Tab
  * Ctrl+W: Close Tab
  * Ctrl+Tab: Next Tab
  * Ctrl+Shift+Tab: Previous Tab
  * Ctrl+F: Find in page text
  * Alt+left: Back in history
  * Alt+Right: Forward in history
  * Crtl+R: Reload page
  * Esc: Hide "Find" widget
  * F11: Toggle full screen mode (not really nice, though)
  * Ctrl+P: Print.
  * Ctrl+Q: Quit

There may be others I don't know about ;-)

## Known Bugs I will not Fix ##

  * On Linux, you will get icons for some buttons but other platforms they show text (Bookmark and New Tab, specifically). This is because windows has no platform default icons. So, complain to Microsoft ;-)

## Why the name De Vicenzo ##

Roberto De Vicenzo was a golfer. This project stinks of code golf. Fill in the blanks.

## How to Use a Proxy ##

De Vicenzo supports HTTP and SOCKS5 proxies. To enable HTTP proxy support, set the
http\_proxy environment variable to the correct value.

Examples:

  * `http_proxy=http://user@pass:my.proxy.hostname:8080` (authenticated HTTP proxy)
  * `http_proxy=http://my.proxy.hostname:3128` (unauthenticated HTTP proxy)
  * `http_proxy=socks://my.proxy.hostname` (unauthenticated SOCKS5 proxy)

On Linux and other Unixes, just put that in the command before starting De Vicenzo:

`http_proxy=http://my.proxy.hostname:3128 python devicenzo.py`

On windows... well, I have no idea, please tell me how it's done ;-)

## What De Vicenzo Is and Is Not ##

  * **Is Not** a browser for the general public. There are much better ones out there.
  * **Is Not** a rendering engine. De Vicenzo uses Qt's WebKit implementation and does it proudly!
  * **Is** A web browser. There are a bazillion others that rely on WebKit or embedding mozilla for the rendering, and they get to call themselves web browsers, why wouldn't De Vicenzo deserve it? ;-)