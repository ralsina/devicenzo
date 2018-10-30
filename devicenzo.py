#!/usr/bin/env python2
"A web browser that will never exceed 256 lines of code (black-formatted) (not counting blanks)"

import json
import os
import sys

from PySide2 import QtCore, QtGui, QtNetwork, QtWebEngineWidgets, QtWidgets

settings = QtCore.QSettings("ralsina", "devicenzo")


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.tabs = QtWidgets.QTabWidget(
            self, tabsClosable=True, movable=True, elideMode=QtCore.Qt.ElideRight
        )
        self.tabs.tabCloseRequested.connect(
            lambda idx: self.tabs.widget(idx).deleteLater()
        )
        self.tabs.currentChanged.connect(self.currentTabChanged)
        self.setCentralWidget(self.tabs)
        self.bars = {}
        self.star_action = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("emblem-favorite"),
            "Bookmark",
            self,
            checkable=True,
            triggered=self.bookmarkPage,
            shortcut="Ctrl+d",
        )
        self.tabs.setCornerWidget(
            QtWidgets.QToolButton(
                self,
                text="New Tab",
                icon=QtGui.QIcon.fromTheme("document-new"),
                clicked=lambda: self.addTab().url.setFocus(),
                shortcut="Ctrl+t",
            )
        )
        self.full_screen_action = QtWidgets.QAction(
            "Full Screen", self, checkable=True, shortcut=QtGui.QKeySequence.FullScreen
        )
        self.full_screen_action.toggled.connect(
            lambda v: self.showFullScreen() if v else self.showNormal()
        )
        self.addAction(self.full_screen_action)
        self.bookmarks = self.get("bookmarks", {})
        # Bookmarks seem broken
        self.bookmarkPage()  # Load the bookmarks menu
        self.history = self.get("history", []) + list(self.bookmarks.keys())
        self.completer = QtWidgets.QCompleter(self.history)

        # Use a app-wide, persistent cookiejar
        self.cookies = QtNetwork.QNetworkCookieJar(QtCore.QCoreApplication.instance())
        self.cookies.setAllCookies(
            [
                QtNetwork.QNetworkCookie.parseCookies(c)[0]
                for c in self.get("cookiejar", [])
            ]
        )

        # Downloads bar at the bottom of the window
        self.downloads = QtWidgets.QToolBar("Downloads")
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.downloads)

        # Proxy support
        proxy_url = QtCore.QUrl(os.environ.get("http_proxy", ""))
        QtNetwork.QNetworkProxy.setApplicationProxy(
            QtNetwork.QNetworkProxy(
                QtNetwork.QNetworkProxy.HttpProxy if proxy_url.scheme().startswith(
                    "http"
                ) else QtNetwork.QNetworkProxy.Socks5Proxy,
                proxy_url.host(),
                proxy_url.port(),
                proxy_url.userName(),
                proxy_url.password(),
            )
        ) if "http_proxy" in os.environ else None

        [self.addTab(QtCore.QUrl(u)) for u in self.get("tabs", [])]

    def fetch(self, reply):
        destination = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save File",
            os.path.expanduser(os.path.join("~", reply.url().path().split("/")[-1])),
        )
        if destination:
            bar = QtWidgets.QProgressBar(
                format="%p% - " + os.path.basename(destination)
            )
            cancel = QtWidgets.QToolButton(
                bar, icon=QtGui.fromTheme("process-stop"), clicked=reply.abort
            )
            self.downloads.addWidget(bar)
            reply.downloadProgress.connect(self.progress)
            reply.finished.connect(self.finished)
            self.bars[reply.url().toString()] = [bar, reply, destination, cancel]

    def finished(self):
        url = self.sender().url().toString()
        bar, reply, fname, cancel = self.bars[url]
        redirURL = reply.attribute(
            QtNetwork.QNetworkRequest.RedirectionTargetAttribute
        ).toString()
        del self.bars[url]
        bar.deleteLater()
        cancel.deleteLater()
        if redirURL and redirURL != url:
            return self.fetch(redirURL, fname)

        with open(fname, "wb") as f:
            f.write(str(reply.readAll()))

    def progress(self, received, total):
        self.bars[self.sender().url().toString()][0].setValue(100. * received / total)

    def closeEvent(self, ev):
        self.put("history", self.history)
        self.put("cookiejar", [str(c.toRawForm()) for c in self.cookies.allCookies()])
        self.put(
            "tabs", [self.tabs.widget(i).url.text() for i in range(self.tabs.count())]
        )
        return QtWidgets.QMainWindow.closeEvent(self, ev)

    def put(self, key, value):
        "Persist an object somewhere under a given key"
        settings.setValue(key, json.dumps(value))
        settings.sync()

    def get(self, key, default=None):
        "Get the object stored under 'key' in persistent storage, or the default value"
        v = settings.value(key)
        return json.loads(v) if v else default

    def addTab(self, url=QtCore.QUrl("")):
        self.tabs.setCurrentIndex(self.tabs.addTab(Tab(url, self), ""))
        return self.tabs.currentWidget()

    def currentTabChanged(self, idx):
        if self.tabs.widget(idx) is None:
            return self.close()

        self.setWindowTitle(self.tabs.widget(idx).wb.title() or "De Vicenzo")

    def bookmarkPage(self, v=None):
        if v and v is not None:
            self.bookmarks[
                self.tabs.currentWidget().url.text()
            ] = self.tabs.currentWidget().wb.title()
        elif v is not None:
            del (self.bookmarks[self.tabs.currentWidget().url.text()])
        self.star_action.setMenu(QtWidgets.QMenu())
        [
            self.star_action.menu().addAction(
                QtWidgets.QAction(
                    title,
                    self,
                    triggered=lambda u=QtCore.QUrl(url): self.tabs.currentWidget().load(
                        u
                    ),
                )
            )
            for url, title in self.bookmarks.items()
        ]
        self.put("bookmarks", self.bookmarks)

    def addToHistory(self, url):
        self.history.append(url)
        self.completer.setModel(
            QtCore.QStringListModel(
                list(set(list(self.bookmarks.keys()) + self.history))
            )
        )


class Tab(QtWidgets.QWidget):

    def __init__(self, url, container):
        super(Tab, self).__init__()
        self.container = container
        self.web_view = QtWebEngineWidgets.QWebEngineView()
        self.progress_bar = QtWidgets.QProgressBar(
            self.container.statusBar(), maximumWidth=120, visible=False
        )
        self.web_view.loadProgress.connect(
            lambda v: (
                self.progress_bar.show(), self.progress_bar.setValue(v)
            ) if self.amCurrent() else None
        )
        self.web_view.loadFinished.connect(self.progress_bar.hide)
        self.web_view.loadStarted.connect(
            lambda: self.progress_bar.show() if self.amCurrent() else None
        )
        self.web_view.titleChanged.connect(
            lambda t: container.tabs.setTabText(container.tabs.indexOf(self), t)
            or (container.setWindowTitle(t) if self.amCurrent() else None)
        )
        self.web_view.iconChanged.connect(
            lambda: container.tabs.setTabIcon(
                container.tabs.indexOf(self), self.web_view.icon()
            )
        )
        # self.wb.page().networkAccessManager().setCookieJar(container.cookies)
        # self.wb.page().setForwardUnsupportedContent(True)
        # self.wb.page().unsupportedContent.connect(container.fetch)
        # self.wb.page().downloadRequested.connect(lambda req: container.fetch(self.page().networkAccessManager().get(req)))
        self.tb = QtWidgets.QToolBar("Main Toolbar", self)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tb, stretch=0)
        layout.addWidget(self.web_view, stretch=1000)
        layout.activate()
        self.setLayout(layout)
        for a, sc in [
            [QtWebEngineWidgets.QWebEnginePage.Back, "Alt+Left"],
            [QtWebEngineWidgets.QWebEnginePage.Forward, "Alt+Right"],
            [QtWebEngineWidgets.QWebEnginePage.Reload, "Ctrl+r"],
        ]:
            self.tb.addAction(self.web_view.pageAction(a))
            self.web_view.pageAction(a).setShortcut(sc)

        self.url = QtWidgets.QLineEdit()
        self.url.returnPressed.connect(
            lambda: self.web_view.load(QtCore.QUrl.fromUserInput(self.url.text()))
        )
        self.url.setCompleter(container.completer)
        self.tb.addWidget(self.url)
        self.tb.addAction(container.star_action)

        # FIXME: if I was seriously golfing, all of these can go in a single lambda
        self.web_view.urlChanged.connect(lambda u: self.url.setText(u.toString()))
        self.web_view.urlChanged.connect(lambda u: container.addToHistory(u.toString()))
        self.web_view.urlChanged.connect(
            lambda u: container.star_action.setChecked(
                u.toString() in container.bookmarks
            ) if self.amCurrent() else None
        )

        # FIXME: do this using a tooltip
        self.web_view.page().linkHovered.connect(
            lambda l: container.statusBar().showMessage(l, 3000)
        )

        self.search = QtWidgets.QLineEdit(
            self.web_view, visible=False, maximumWidth=200
        )
        self.search.returnPressed.connect(
            lambda: self.web_view.findText(self.search.text())
        )
        self.search.textChanged.connect(
            lambda: self.web_view.findText(self.search.text())
        )
        self.showSearch = QtWidgets.QShortcut(QtGui.QKeySequence.Find, self)
        self.showSearch.activated.connect(
            lambda: self.search.show() or self.search.setFocus()
        )
        self.hideSearch = QtWidgets.QShortcut(
            "Esc", self, activated=lambda: (self.search.hide(), self.setFocus())
        )

        self.zoomIn = QtWidgets.QShortcut(QtGui.QKeySequence.ZoomIn, self)
        self.zoomIn.activated.connect(
            lambda: self.web_view.setZoomFactor(self.web_view.zoomFactor() + 0.2)
        )
        self.zoomOut = QtWidgets.QShortcut(QtGui.QKeySequence.ZoomOut, self)
        self.zoomOut.activated.connect(
            lambda: self.web_view.setZoomFactor(self.web_view.zoomFactor() - 0.2)
        )
        self.zoomOne = QtWidgets.QShortcut(
            "Ctrl+0", self, activated=lambda: self.web_view.setZoomFactor(1)
        )
        self.urlFocus = QtWidgets.QShortcut("Ctrl+l", self, activated=self.url.setFocus)

        # self.previewer = QtWidgets.QPrintPreviewDialog(paintRequested=self.wb.print_)
        # self.do_print = QtWidgets.QShortcut("Ctrl+p", self, activated=self.previewer.exec_)
        # self.wb.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        # self.wb.settings().setIconDatabasePath(tempfile.mkdtemp())

        self.web_view.load(url)

    def amCurrent(self):
        return self.container.tabs.currentWidget() == self

    def createWindow(self, windowType):
        return self.container.addTab()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wb = MainWindow()
    for url in sys.argv[1:]:
        wb.addTab(QtCore.QUrl.fromUserInput(url))
    if wb.tabs.count() == 0:
        wb.addTab(QtCore.QUrl("http://devicenzo.googlecode.com"))
    wb.show()
    sys.exit(app.exec_())
