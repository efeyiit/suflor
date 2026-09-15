"""KRT k7 -- K6'nin metni: `QThread.currentThread() is app.thread()` PySide6'da ana threadde True mu, Python threadinde False mu?
    python .agents/tasks/T-013/krt_kosumlari/k7_thread_kimlik.py   (offscreen)
"""
import os; os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys, threading
from PySide6 import QtCore, QtWidgets
app = QtWidgets.QApplication(sys.argv)
a = QtCore.QThread.currentThread(); b = app.thread()
print(f"ana thread: currentThread() is app.thread() -> {a is b}; == -> {a == b}; id esit={id(a) == id(b)}")
son = {}
def th():
    c = QtCore.QThread.currentThread(); son["is"] = c is app.thread(); son["eq"] = c == app.thread(); son["isMain"] = QtCore.QThread.isMainThread() if hasattr(QtCore.QThread, "isMainThread") else None
t = threading.Thread(target=th); t.start(); t.join()
print(f"python thread: is -> {son['is']}; == -> {son['eq']}; QThread.isMainThread() -> {son['isMain']}")
print(f"ana thread QThread.isMainThread() -> {QtCore.QThread.isMainThread() if hasattr(QtCore.QThread, 'isMainThread') else 'yok'}")
