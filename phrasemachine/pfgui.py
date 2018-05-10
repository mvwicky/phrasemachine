import hashlib
import sys

import pyperclip
from Qt import QtWidgets
from Qt.QtCore import Qt

from config import Config
from pfgen import get_words, word_reg, generate_passphrase


ALGS = list(hashlib.algorithms_available)
INT_MAX = int(((1 << 32) - 1) / 2)


class PassphraseDialog(QtWidgets.QDialog):
    def __init__(self, parent, passphrase):
        QtWidgets.QDialog.__init__(self)
        self.parent = parent
        self.passphrase = passphrase

        self.setWindowTitle('Passphase')
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        phrase_label = QtWidgets.QLabel(self.passphrase)
        copy_btn = QtWidgets.QPushButton('Copy to Clipboard')
        copy_btn.clicked.connect(self.copy_to_clipboard)
        close_btn = QtWidgets.QPushButton('Close')
        close_btn.clicked.connect(self.accept)

        layout.addWidget(phrase_label)
        layout.addWidget(copy_btn)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.resize(250, 125)

    def copy_to_clipboard(self):
        pyperclip.copy(self.passphrase)


class ParamInput(object):
    __slots__ = ('label', 'inp_widget', )

    def __init__(self, label, inp_widget):
        if not isinstance(label, QtWidgets.QLabel):
            label = QtWidgets.QLabel(str(label))
        self.label = label
        self.inp_widget = inp_widget


class GeneratorWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.vals = {}
        self.layout, self.rows = QtWidgets.QGridLayout(), 0
        self.dialog_open = False
        self.setWindowTitle('Passphrase Generator')
        self.init_ui()

    def init_ui(self):
        # self.vals['domain'] = ParamInput(
        #     'Domain', QtWidgets.QComboBox(self)
        # )
        # self.vals['domain'].inp_widget.addItems(Config.DOMAINS)
        domain_label = QtWidgets.QLabel('Domain')
        self.domain_val = QtWidgets.QComboBox(self)
        self.domain_val.addItems(Config.DOMAINS)

        # self.vals['num_words'] = ParamInput(
        #     'Number of Words in Passphrase',
        #     self.default_spinbox(Config.LENGTH)
        # )
        num_words_label = QtWidgets.QLabel('Number of Words in Passphrase')
        self.num_words_val = self.default_spinbox(Config.LENGTH)

        # self.vals['wlen_min'] = ParamInput(
        #     'Minimum Number of Letters per Word',
        #     self.default_spinbox(Config.WLEN_MIN)
        # )
        wlen_min_label = QtWidgets.QLabel('Minimum Number of Letters per Word')
        self.wlen_min_val = self.default_spinbox(Config.WLEN_MIN)

        wlen_max_label = QtWidgets.QLabel('Maximum Number of Letters per Word')
        self.wlen_max_val = self.default_spinbox(Config.WLEN_MAX)

        num_label = QtWidgets.QLabel('Passphrase iteration')
        self.num_val = self.default_spinbox(1)

        it_min_label = QtWidgets.QLabel('Minimum iterations for PBKDF2')
        self.it_min_val = self.default_spinbox(Config.IT_MIN)
        self.it_min_val.setGroupSeparatorShown(True)

        hmac_label = QtWidgets.QLabel('HMAC to use with PBKDF2')
        self.hmac_val = QtWidgets.QComboBox(self)
        self.hmac_val.addItems(ALGS)
        idx = self.hmac_val.findText(Config.HMAC)
        if idx >= 0:
            self.hmac_val.setCurrentIndex(idx)

        master_label = QtWidgets.QLabel('Master Password')
        self.master_val = QtWidgets.QLineEdit(self)
        self.master_val.setEchoMode(QtWidgets.QLineEdit.Password)

        generate_button = QtWidgets.QPushButton('Generate Passphrase')
        generate_button.clicked.connect(self.gen)

        self.add_row(domain_label, self.domain_val)
        self.add_row(num_words_label, self.num_words_val)
        self.add_row(wlen_min_label, self.wlen_min_val)
        self.add_row(wlen_max_label, self.wlen_max_val)
        self.add_row(num_label, self.num_val)
        self.add_row(it_min_label, self.it_min_val)
        self.add_row(hmac_label, self.hmac_val)
        self.add_row(master_label, self.master_val)
        self.add_row(generate_button)

        self.setLayout(self.layout)
        self.resize(500, 600)

    def add_row(self, *args):
        for i, arg in enumerate(args):
            self.layout.addWidget(arg, self.rows, i)
        self.rows += 1

    def default_spinbox(self, val):
        ret = QtWidgets.QSpinBox(self)
        ret.setRange(1, INT_MAX)
        ret.setWrapping(False)
        ret.setValue(val)
        return ret

    @staticmethod
    def read_words(wlen_min, wlen_max):
        return get_words(
            Config.WORDLIST_FILE_NAME, word_reg(wlen_min, wlen_max)
        )

    def keyReleaseEvent(self, e):
        print(QtWidgets.QApplication.topLevelWidgets())
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.gen()
        else:
            super(GeneratorWidget, self).keyReleaseEvent(e)

    def gather_values(self):
        vals = {}
        vals['domain'] = self.domain_val.currentText()
        vals['num_words'] = self.num_words_val.value()
        vals['wlen_min'] = self.wlen_min_val.value()
        vals['wlen_max'] = self.wlen_max_val.value()
        vals['num'] = self.num_val.value()
        vals['it_min'] = self.it_min_val.value()
        vals['hmac'] = self.hmac_val.currentText()
        vals['master'] = self.master_val.text()
        return vals

    def gen(self):
        vals = self.gather_values()
        if vals['master']:
            words = self.read_words(vals['wlen_min'], vals['wlen_max'])
            passphrase = generate_passphrase(
                vals['master'],
                vals['domain'],
                vals['hmac'],
                vals['it_min'],
                vals['num'],
                words,
                vals['num_words']
            )
            PassphraseDialog(self, passphrase).exec_()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                'No Master Password!',
                'You must provide a master password'
            )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = GeneratorWidget()
    widget.show()
    sys.exit(app.exec_())
