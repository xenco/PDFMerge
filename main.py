import ntpath
import sys

from PyPDF2 import PdfFileReader, PdfFileWriter
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QHBoxLayout, QListWidget, QListWidgetItem, \
    QMenu, QMessageBox, QPushButton, QVBoxLayout, QWidget


class File:
    def __init__(self, path):
        self.path = path
        self.icon = QIcon(QPixmap("./pdf.png"))
        self.name = ntpath.basename(self.path) + " (" + self.path + ")"


class ListWidget(QListWidget):
    def __init__(self, parent):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.installEventFilter(self)
        self.parent = parent
        self.currentRowChanged.connect(self.change)
        self.dragged_name = None

    def change(self, i):
        self.setCurrentRow(i)

        self.parent.btnSortUp.setEnabled(True)
        self.parent.btnSortDown.setEnabled(True)

        if i == 0:
            self.parent.btnSortUp.setEnabled(False)
        elif i == len(self.parent.files) - 1:
            self.parent.btnSortDown.setEnabled(False)

    def dragMoveEvent(self, *args, **kwargs):
        QListWidget.dragMoveEvent(self, *args, **kwargs)
        self.dragged_name = self.currentItem().text()

    def dropEvent(self, event):
        QListWidget.dropEvent(self, event)
        if event.isAccepted():
            self.parent.orderListByWidgetItems()
            if self.dragged_name:
                for i in range(self.count()):
                    if self.item(i).text() == self.dragged_name:
                        self.setCurrentRow(i)
                        break

    def eventFilter(self, source, event):
        if (event.type() == QEvent.ContextMenu and source is self):
            menu_itm = QMenu()
            menu_itm.addAction('Delete')

            menu_about = QMenu()
            menu_about.addAction('About')

            selected_item = source.itemAt(event.pos())
            if selected_item:
                if menu_itm.exec_(event.globalPos()):
                    self.parent.removeItem(selected_item)
            else:
                if menu_about.exec_(event.globalPos()):
                    QMessageBox.information(self, 'About', "© 2019 Enrico Costanzo\n"
                                                           "mail@ecostanzo.de\n"
                                                           "\n"
                                                           "PDF icon by Smashicons (smashicons.com)\n"
                                                           "PDF Lib: PyPDF2\n"
                                            )
            return True

        return super(ListWidget, self).eventFilter(source, event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.files = []
        self.last_selected = None

        self.resize(350, 300)
        self.move(300, 300)
        self.setWindowTitle('PDFMerge')
        self.setAcceptDrops(True)
        self.setWindowIcon(QIcon(QPixmap("./pdf.png")))

        self.layout = QVBoxLayout()

        self.list = ListWidget(self)
        self.layout.addWidget(self.list)

        self.layout_buttons = QHBoxLayout()

        self.btnSortUp = QPushButton("▲")
        self.btnSortUp.setEnabled(False)
        self.btnSortUp.clicked.connect(self.sortUp)
        self.layout_buttons.addWidget(self.btnSortUp)

        self.btnSortDown = QPushButton("▼")
        self.btnSortDown.setEnabled(False)
        self.btnSortDown.clicked.connect(self.sortDown)
        self.layout_buttons.addWidget(self.btnSortDown)

        self.layout_buttons.addStretch()

        self.btnMerge = QPushButton("Merge PDFs")
        self.btnMerge.clicked.connect(self.merge)
        self.layout_buttons.addWidget(self.btnMerge)

        self.layout.addLayout(self.layout_buttons)
        self.setLayout(self.layout)

        self.show()

    def sortUp(self):
        currentRow = self.list.currentRow()
        if currentRow > -1 and currentRow - 1 >= 0:
            self.files[currentRow - 1], self.files[currentRow] = self.files[currentRow], self.files[currentRow - 1]
            self.updateList()
            self.list.setCurrentRow(currentRow - 1)

    def sortDown(self):
        currentRow = self.list.currentRow()
        if currentRow > -1 and currentRow + 1 < len(self.files):
            self.files[currentRow + 1], self.files[currentRow] = self.files[currentRow], self.files[currentRow + 1]
            self.updateList()
            self.list.setCurrentRow(currentRow + 1)

    def merge(self):
        input_streams = []

        output_path = QFileDialog.getSaveFileName(self, "Save File As", "", "PDF File (*.pdf)")
        if output_path:
            output_stream = open(output_path[0], "wb")

            try:
                for f in self.files:
                    input_streams.append(open(f.path, 'rb'))

                writer = PdfFileWriter()
                for reader in map(PdfFileReader, input_streams):
                    for n in range(reader.getNumPages()):
                        writer.addPage(reader.getPage(n))
                writer.write(output_stream)
            finally:
                for f in input_streams:
                    f.close()

                output_stream.close()

        self.files = []
        self.updateList()

        QMessageBox.information(self, 'File saved',
                                "The merge was successful.\nThe merged file can be found here: \n\n" + output_path[0])

    def removeItem(self, item):
        for f in self.files:
            if f.name == item.text():
                self.files.remove(f)
        self.updateList()

    def updateList(self):
        self.list.clear()
        for f in self.files:
            self.list.addItem(QListWidgetItem(f.icon, f.name))

    def orderListByWidgetItems(self):
        new_list = []
        for i in range(len(self.list)):
            item_at_i = self.list.item(i)
            for f in self.files:
                if f.name == item_at_i.text():
                    new_list.append(f)
                    break
        self.files = new_list
        self.updateList()

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        dropped_files = e.mimeData().text().split()
        for f in dropped_files:
            self.files.append(File(f.replace("file://", "")))
        self.updateList()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainWindow = MainWindow()

    sys.exit(app.exec_())
