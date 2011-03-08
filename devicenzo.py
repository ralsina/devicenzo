#!/usr/bin/env python
"A web browser that will never exceed 128 lines of code. (not counting blanks)"

import sys, os, json
from PyQt4 import QtGui, QtCore, QtWebKit, QtNetwork

settings = QtCore.QSettings("ralsina", "devicenzo")


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.tabs = QtGui.QTabWidget(self, tabsClosable=True, movable=True, currentChanged=self.currentTabChanged, elideMode=QtCore.Qt.ElideRight, tabCloseRequested=lambda idx: self.tabs.widget(idx).deleteLater())
        self.setCentralWidget(self.tabs)
        self.tabWidgets = []
        self.star = QtGui.QAction(QtGui.QIcon.fromTheme("emblem-favorite"), "Bookmark", self, checkable=True, triggered=self.bookmarkPage, shortcut="Ctrl+d")
        self.newtab = QtGui.QAction(QtGui.QIcon.fromTheme("document-new"), "New Tab", self, triggered=lambda: self.addTab().url.setFocus(), shortcut="Ctrl+t")
        self.addAction(QtGui.QAction("Full Screen", self, checkable=True, toggled=lambda v: self.showFullScreen() if v else self.showNormal(), shortcut="F11"))
        self.bookmarks = self.get("bookmarks", {})
        self.bookmarkPage()  # Load the bookmarks menu
        self.history = self.get("history", []) + self.bookmarks.keys()
        self.completer = QtGui.QCompleter(QtCore.QStringList([QtCore.QString(u) for u in self.history]))
        self.cookies = QtNetwork.QNetworkCookieJar()
        self.cookies.setAllCookies([QtNetwork.QNetworkCookie.parseCookies(c)[0] for c in self.get("cookiejar", [])])
        [self.addTab(QtCore.QUrl(u)) for u in self.get("tabs", [])]
        self.bars = {}
        self.manager = QtNetwork.QNetworkAccessManager(self)

    def fetch(self, reply):
        destination = QtGui.QFileDialog.getSaveFileName(self, "Save File", os.path.expanduser(os.path.join('~', unicode(reply.url().path()).split('/')[-1])))
        if destination:
            bar = QtGui.QProgressBar(format='%p% - ' + os.path.basename(unicode(destination)))
            self.statusBar().addPermanentWidget(bar)
            reply.downloadProgress.connect(self.progress)
            reply.finished.connect(self.finished)
            self.bars[unicode(reply.url().toString())] = [bar, reply, unicode(destination)]

    def finished(self):
        reply = self.sender()
        url = unicode(reply.url().toString())
        bar, _, fname = self.bars[url]
        redirURL = unicode(reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute).toString())
        del self.bars[url]
        bar.deleteLater()
        if redirURL and redirURL != url:
            return self.fetch(redirURL, fname)
        with open(fname, 'wb') as f:
            f.write(str(reply.readAll()))

    progress = lambda self, received, total: self.bars[unicode(self.sender().url().toString())][0].setValue(100. * received / total)

    def closeEvent(self, ev):
        self.put("history", self.history)
        self.put("cookiejar", [str(c.toRawForm()) for c in self.cookies.allCookies()])
        self.put("tabs", [unicode(self.tabs.widget(i).url.text()) for i in range(self.tabs.count())])
        return QtGui.QMainWindow.closeEvent(self, ev)

    def put(self, key, value):
        "Persist an object somewhere under a given key"
        settings.setValue(key, json.dumps(value))
        settings.sync()

    def get(self, key, default=None):
        "Get the object stored under 'key' in persistent storage, or the default value"
        v = settings.value(key)
        return json.loads(unicode(v.toString())) if v.isValid() else default

    def addTab(self, url=QtCore.QUrl("")):
        self.tabs.setCurrentIndex(self.tabs.addTab(Tab(url, self), ""))
        return self.tabs.currentWidget()

    def currentTabChanged(self, idx):
        wb = self.tabs.widget(idx)
        if wb is None:
            return self.close()
        self.setWindowTitle(wb.title() or "De Vicenzo")
        for w in self.tabWidgets:
            w.hide()
        self.tabWidgets = [wb.tb, wb.pbar, wb.search]
        self.addToolBar(wb.tb)
        for w in self.tabWidgets[:-2]:
            w.show()

    def bookmarkPage(self, v=None):
        if v and v is not None:
            self.bookmarks[unicode(self.tabs.currentWidget().url.text())] = unicode(self.tabs.currentWidget().title())
        elif v is not None:
            del (self.bookmarks[unicode(self.tabs.currentWidget().url.text())])
        self.star.setMenu(QtGui.QMenu())
        [self.star.menu().addAction(QtGui.QAction(title, self, activated=lambda u=QtCore.QUrl(url): self.tabs.currentWidget().load(u))) for url, title in self.bookmarks.items()]
        self.put('bookmarks', self.bookmarks)

    def addToHistory(self, url):
        self.history.append(url)
        self.completer.setModel(QtGui.QStringListModel(list(set(self.bookmarks.keys() + self.history))))


class Tab(QtWebKit.QWebView):
    def __init__(self, url, container):
        self.container = container
        self.pbar = QtGui.QProgressBar(maximumWidth=120, visible=False)
        QtWebKit.QWebView.__init__(self, loadProgress=lambda v: (self.pbar.show(), self.pbar.setValue(v)) if self.amCurrent() else None, loadFinished=self.pbar.hide, loadStarted=lambda: self.pbar.show() if self.amCurrent() else None, titleChanged=lambda t: container.tabs.setTabText(container.tabs.indexOf(self), t) or (container.setWindowTitle(t) if self.amCurrent() else None))
        self.page().networkAccessManager().setCookieJar(container.cookies)
        self.page().setForwardUnsupportedContent(True)
        self.page().unsupportedContent.connect(container.fetch)

        container.statusBar().addPermanentWidget(self.pbar)

        self.tb = QtGui.QToolBar("Main Toolbar")
        for a, sc in [[QtWebKit.QWebPage.Back, "Alt+Left"], [QtWebKit.QWebPage.Forward, "Alt+Right"], [QtWebKit.QWebPage.Reload, "Ctrl+r"]]:
            self.tb.addAction(self.pageAction(a))
            self.pageAction(a).setShortcut(sc)

        self.url = QtGui.QLineEdit(returnPressed=lambda: self.setUrl(QtCore.QUrl.fromUserInput(self.url.text())))
        self.url.setCompleter(container.completer)
        self.tb.addWidget(self.url)
        self.tb.addAction(container.star)
        self.tb.addAction(container.newtab)

        # FIXME: if I was seriously golfing, all of these can go in a single lambda
        self.urlChanged.connect(lambda u: self.url.setText(u.toString()))
        self.urlChanged.connect(lambda u: container.addToHistory(unicode(u.toString())))
        self.urlChanged.connect(lambda u: container.star.setChecked(unicode(u.toString()) in container.bookmarks) if self.amCurrent() else None)

        self.statusBarMessage.connect(container.statusBar().showMessage)
        self.page().linkHovered.connect(lambda l: container.statusBar().showMessage(l, 3000))

        self.search = QtGui.QLineEdit(returnPressed=lambda: self.findText(self.search.text()))
        self.search.hide()
        self.showSearch = QtGui.QShortcut("Ctrl+F", self, activated=lambda: self.search.show() or self.search.setFocus())
        self.hideSearch = QtGui.QShortcut("Esc", self, activated=lambda: (self.search.hide(), self.setFocus()))

        self.do_close = QtGui.QShortcut("Ctrl+W", self, activated=lambda: container.tabs.removeTab(container.tabs.indexOf(self)))
        self.do_quit = QtGui.QShortcut("Ctrl+q", self, activated=lambda: container.close())
        self.zoomIn = QtGui.QShortcut("Ctrl++", self, activated=lambda: self.setZoomFactor(self.zoomFactor() + 0.2))
        self.zoomOut = QtGui.QShortcut("Ctrl+-", self, activated=lambda: self.setZoomFactor(self.zoomFactor() - 0.2))
        self.zoomOne = QtGui.QShortcut("Ctrl+0", self, activated=lambda: self.setZoomFactor(1))
        self.urlFocus = QtGui.QShortcut("Ctrl+l", self, activated=self.url.setFocus)

        self.previewer = QtGui.QPrintPreviewDialog(paintRequested=self.print_)
        self.do_print = QtGui.QShortcut("Ctrl+p", self, activated=self.previewer.exec_)
        self.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)

        container.statusBar().addPermanentWidget(self.search)
        self.load(url)

    amCurrent = lambda self: self.container.tabs.currentWidget() == self

    def createWindow(self, windowType):
        return self.container.addTab()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    wb = MainWindow()
    for url in sys.argv[1:]:
        wb.addTab(QtCore.QUrl.fromUserInput(url))
    if wb.tabs.count() == 0:
        wb.addTab(QtCore.QUrl('http://devicenzo.googlecode.com'))
    wb.show()
    sys.exit(app.exec_())
