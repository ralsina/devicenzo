#!/usr/bin/env python
"A web browser that will never exceed 128 lines of code. (not counting blanks)"

import sys, json
from PyQt4 import QtGui, QtCore, QtWebKit

settings = QtCore.QSettings("ralsina", "devicenzo")


class MainWindow(QtGui.QMainWindow):
    def __init__(self, url):
        QtGui.QMainWindow.__init__(self)
        self.tabs = QtGui.QTabWidget(self, tabsClosable=True, movable=True, currentChanged=self.currentTabChanged, elideMode=QtCore.Qt.ElideRight)
        self.setCentralWidget(self.tabs)
        self.sb = self.statusBar()
        self.tabWidgets = []
        self.addTab(url)

    def addTab(self, url=QtCore.QUrl()):
        t = Tab(url, self)
        self.tabs.addTab(t, "")
        return t

    def currentTabChanged(self, idx):
        wb = self.tabs.widget(idx)
        self.setWindowTitle(wb.title() or "De Vicenzo")
        for w in self.tabWidgets:
            w.hide()
        self.tabWidgets = [wb.tb, wb.pbar, wb.search]
        self.addToolBar(wb.tb)
        for w in self.tabWidgets[:-2]:
            w.show()


class Tab(QtWebKit.QWebView):
    def __init__(self, url, container):
        self.container = container
        self.pbar = QtGui.QProgressBar()
        QtWebKit.QWebView.__init__(self, loadProgress=lambda v: (self.pbar.show(), self.pbar.setValue(v)) if self.amCurrent() else None, loadFinished=self.pbar.hide, loadStarted=lambda: self.pbar.show() if self.amCurrent() else None, titleChanged=lambda t: container.tabs.setTabText(container.tabs.indexOf(self), t) or (container.setWindowTitle(t) if self.amCurrent() else None))

        self.bookmarks = self.get("bookmarks", {})
        self.pbar.setMaximumWidth(120)
        container.sb.addPermanentWidget(self.pbar)
        self.pbar.hide()

        self.tb = QtGui.QToolBar("Main Toolbar")
        for a in (QtWebKit.QWebPage.Back, QtWebKit.QWebPage.Forward, QtWebKit.QWebPage.Reload):
            self.tb.addAction(self.pageAction(a))

        self.url = QtGui.QLineEdit(returnPressed=lambda: self.setUrl(QtCore.QUrl.fromUserInput(self.url.text())))
        self.tb.addWidget(self.url)
        self.star = QtGui.QAction(QtGui.QIcon.fromTheme("emblem-favorite"), "Bookmark", self, checkable=True, triggered=self.bookmarkPage)
        self.tb.addAction(self.star)
        self.bookmarkPage()  # This triggers building the bookmarks menu
        self.newtab = QtGui.QAction(QtGui.QIcon.fromTheme("document-new"), "New Tab", self, triggered=self.createWindow)
        self.tb.addAction(self.newtab)

        self.urlChanged.connect(lambda u: self.url.setText(u.toString()))
        self.urlChanged.connect(lambda: self.url.setCompleter(QtGui.QCompleter(QtCore.QStringList([QtCore.QString(i.url().toString()) for i in self.history().items()]), caseSensitivity=QtCore.Qt.CaseInsensitive)))
        self.urlChanged.connect(lambda u: self.star.setChecked(unicode(u.toString()) in self.bookmarks))

        self.statusBarMessage.connect(container.sb.showMessage)
        self.page().linkHovered.connect(lambda l: container.sb.showMessage(l, 3000))

        self.search = QtGui.QLineEdit(returnPressed=lambda: self.findText(self.search.text()))
        self.search.hide()
        self.showSearch = QtGui.QShortcut("Ctrl+F", self, activated=lambda: self.search.show() or self.search.setFocus())
        self.hideSearch = QtGui.QShortcut("Esc", self, activated=lambda: (self.search.hide(), self.setFocus()))

        self.quit = QtGui.QShortcut("Ctrl+Q", self, activated=self.close)
        self.zoomIn = QtGui.QShortcut("Ctrl++", self, activated=lambda: self.setZoomFactor(self.zoomFactor() + 0.2))
        self.zoomOut = QtGui.QShortcut("Ctrl+-", self, activated=lambda: self.setZoomFactor(self.zoomFactor() - 0.2))
        self.zoomOne = QtGui.QShortcut("Ctrl+=", self, activated=lambda: self.setZoomFactor(1))
        self.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)

        container.sb.addPermanentWidget(self.search)
        self.load(url)

    amCurrent = lambda self: self.container.tabs.currentWidget() == self

    def put(self, key, value):
        "Persist an object somewhere under a given key"
        settings.setValue(key, json.dumps(value))
        settings.sync()

    def get(self, key, default=None):
        "Get the object stored under 'key' in persistent storage, or the default value"
        v = settings.value(key)
        return json.loads(unicode(v.toString())) if v.isValid() else default

    def bookmarkPage(self, v=None):
        if v and v is not None:
            self.bookmarks[unicode(self.url.text())] = unicode(self.windowTitle())
        elif v is not None:
            del (self.bookmarks[unicode(self.url.text())])
        self.star.setMenu(QtGui.QMenu())
        [self.star.menu().addAction(QtGui.QAction(title, self, activated=lambda u=QtCore.QUrl(url): self.load(u))) for url, title in self.bookmarks.items()]
        self.put('bookmarks', self.bookmarks)

    def createWindow(self, windowType):
        return self.container.addTab()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    if len(sys.argv) > 1:
        url = QtCore.QUrl.fromUserInput(sys.argv[1])
    else:
        url = QtCore.QUrl('http://www.python.org')
    wb = MainWindow(url)
    wb.show()
    sys.exit(app.exec_())
