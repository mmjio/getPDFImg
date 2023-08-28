from PyQt6.QtCore import pyqtSignal, QThread, pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressBar, QDialog, \
    QVBoxLayout
from fitz import fitz

from PIL import Image
from ui.main import Ui_MainWindow


class TimeThread(QThread):
    time_update = pyqtSignal()

    def __init__(self, pdf_path, img_path, text_path, total):
        super().__init__()
        self.stopped = False
        self.pdf = pdf_path
        self.img = img_path
        self.text = text_path
        self.total = total

    def convert_and_save_as_png(self, image, output_path):
        if image.colorspace.n == 4:  # 如果颜色空间为CMYK
            rgb_image = fitz.Pixmap(fitz.csRGB, image)
            pil_image = Image.frombytes("RGB", [rgb_image.width, rgb_image.height], rgb_image.samples)
            pil_image.save(output_path, format="PNG")
            pil_image.close()
            rgb_image = None
        else:
            image.save(output_path)

    def run(self):
        pdf_document = fitz.open(self.pdf)
        # 提取图片
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                pdf_document.extract_image(xref)
                image = fitz.Pixmap(pdf_document, xref)
                if image.n > 0:
                    image_file_path = f"{self.img}/page_{page_num + 1}_img_{img_index + 1}.png"
                    self.convert_and_save_as_png(image, image_file_path)
                    print(image_file_path)
                    image = None
            self.time_update.emit()
        text = ""
        # 提取文本
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            page_text = page.get_text()
            text += page_text + "\n\n"
        with open(self.text + "/output.txt", "w", encoding="utf-8") as text_file:
            text_file.write(text)
            self.time_update.emit()
        pdf_document.close()


class ProgressDialog(QDialog):
    def __init__(self, total, parent=None):
        super().__init__(None)
        self.init_ui(parent)
        self.total = parent

    def init_ui(self, total):
        self.setWindowTitle("正在提取...")
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, total)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    @pyqtSlot()
    def update(self):
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        if self.progress_bar.value() == self.total:
            self.accept()


class main_event(QMainWindow, Ui_MainWindow):
    custom_signal = pyqtSignal(int, str)

    # 初始化
    def __init__(self, ui):
        super().__init__()
        self.widget = ui
        self.init_events()

    def init_events(self):
        edit2 = self.widget.lineEdit_2
        edit3 = self.widget.lineEdit_3
        self.widget.pushButton.clicked.connect(self.showDialogFile)
        self.widget.pushButton_2.clicked.connect(lambda: self.showDialogDir(edit2))
        self.widget.pushButton_3.clicked.connect(lambda: self.showDialogDir(edit3))
        self.widget.pushButton_4.clicked.connect(self.show_progress)
        self.widget.pushButton_5.clicked.connect(self.check_colorspaces_in_pdf)

    def show_progress(self):
        if self.check() == 0:
            total = self.get_page_num(self.widget.lineEdit.text())
            progress_dialog = ProgressDialog(self, total)
            pdf = self.widget.lineEdit.text()
            img = self.widget.lineEdit_2.text()
            text = self.widget.lineEdit_3.text()
            time_thread = TimeThread(pdf, img, text, total)
            time_thread.time_update.connect(progress_dialog.update)
            time_thread.start()
            progress_dialog.exec()
            time_thread.stopped = True
            time_thread.wait()
            self.ok()

    def get_page_num(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        page_count = pdf_document.page_count
        pdf_document.close()
        return page_count

    # 选择文件
    def showDialogFile(self):
        fileName = QFileDialog.getOpenFileName()
        if fileName:
            self.widget.lineEdit.setText(fileName[0])

    # 选择目录
    def showDialogDir(self, edit):
        d = QFileDialog.getExistingDirectory()
        if d:
            edit.setText(d)

    def get(self):
        if self.check() == 0:
            self.ok()

    def check(self):
        l1 = self.widget.lineEdit.text()
        l2 = self.widget.lineEdit_2.text()
        l3 = self.widget.lineEdit_3.text()
        if l1 is None or l2 is None or l3 is None or l1 == "" or l2 == "" or l3 == "":
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("警告")
            message_box.setText("请填写文件或路径！")
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            return 1
        return 0

    def check_colorspaces_in_pdf(self):
        path = self.widget.lineEdit.text()
        if path == "" or path is None:
            self.check()
        pdf_document = fitz.open(path)
        message = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                image = fitz.Pixmap(pdf_document, xref)
                if image.n > 0:
                    text = f"Page {page_num + 1}, Image {img_index + 1}: Colorspace = {image.colorspace.name}\n"
                    message += text
                    print(f"Page {page_num + 1}, Image {img_index + 1}: Colorspace = {image.colorspace.name}")
                    # 清除图像数据，释放资源
                    image = None
        pdf_document.close()
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle("检测结果")
        message_box.setText(message)
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.exec()

    def ok(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle("完成")
        message_box.setText("执行完毕！")
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.exec()
