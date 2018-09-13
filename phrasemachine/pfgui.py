from collections import OrderedDict
import hashlib
from typing import Callable, Union, Optional
import sys

import attr
import pyperclip
from Qt import QtWidgets
from Qt.QtCore import Qt

from config import Config, SavedSettings, DomainSettings
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


def label_converter(inp):
    if not isinstance(inp, QtWidgets.QLabel):
        inp = QtWidgets.QLabel(str(inp))
    return inp


Value_Cmd = Callable[[QtWidgets.QWidget], Union[str, int]]
Guessable = dict(
    [
        (QtWidgets.QComboBox, 'currentText'),
        (QtWidgets.QSpinBox, 'value'),
        (QtWidgets.QLineEdit, 'text'),
    ]
)


@attr.s(slots=True, auto_attribs=True)
class ParamInput(object):
    label: QtWidgets.QLabel = attr.ib(converter=label_converter)
    widget: QtWidgets.QWidget = attr.ib()
    settings: Optional[DomainSettings] = attr.ib(default=None)
    val_cmd: Optional[Value_Cmd] = attr.ib(default=None)

    @classmethod
    def guess_command(cls, label, widget):
        ret = cls(label, widget)
        for elem in Guessable:
            if isinstance(widget, elem):
                ret.val_cmd = getattr(ret.widget, Guessable[elem])
                return ret

        raise TypeError(
            '"widget" must be in {0!r} not {1}'.format(
                list(Guessable.keys()), type(widget)
            )
        )


class GeneratorWidget(QtWidgets.QWidget):
    settings = SavedSettings()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.inps = OrderedDict()
        self.layout, self.rows = QtWidgets.QGridLayout(), 0
        self.dialog_open = False
        self.setWindowTitle('Passphrase Generator')
        self.init_ui()

    def init_ui(self):
        self.inps['domain'] = ParamInput.guess_command(
            'Domain', QtWidgets.QComboBox(self)
        )
        self.inps['domain'].widget.addItems(Config.DOMAINS)

        self.inps['length'] = ParamInput.guess_command(
            'Number of Words in Passphrase',
            self.default_spinbox(Config.LENGTH),
        )

        self.inps['wlen_min'] = ParamInput.guess_command(
            'Minimum Number of Letters per Word',
            self.default_spinbox(Config.WLEN_MIN),
        )

        self.inps['wlen_max'] = ParamInput.guess_command(
            'Maximum Number of Letters per Word',
            self.default_spinbox(Config.WLEN_MAX),
        )

        self.inps['num'] = ParamInput.guess_command(
            'Passphrase iteration', self.default_spinbox(1)
        )

        self.inps['it_min'] = ParamInput.guess_command(
            'Minimum iterations for PBKDF2',
            self.default_spinbox(Config.IT_MIN),
        )

        self.inps['hmac'] = ParamInput.guess_command(
            'HMAC to use with PBKDF2', QtWidgets.QComboBox(self)
        )
        self.inps['hmac'].widget.addItems(ALGS)
        idx = self.inps['hmac'].widget.findText(Config.HMAC)
        if idx >= 0:
            self.inps['hmac'].widget.setCurrentIndex(idx)

        self.inps['master'] = ParamInput.guess_command(
            'Master Password', QtWidgets.QLineEdit(self)
        )
        self.inps['master'].widget.setEchoMode(QtWidgets.QLineEdit.Password)

        for param in self.inps.values():
            self.add_row(param.label, param.widget)

        generate_button = QtWidgets.QPushButton('Generate Passphrase')
        generate_button.clicked.connect(self.gen)

        add_domain_button = QtWidgets.QPushButton('Add Domain')

        save_button = QtWidgets.QPushButton('Save Settings')
        save_button.clicked.connect(self.save_settings)

        self.add_row(generate_button)
        self.add_row(add_domain_button)
        self.add_row(save_button)

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
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.gen()
        else:
            super(GeneratorWidget, self).keyReleaseEvent(e)

    def save_settings(self):
        self.settings.save()

    def gather_values(self):
        vals = {}
        for elem, param in self.inps.items():
            vals[elem] = param.val_cmd()
        vals['salt'] = Config.SALT
        return vals

    def gen(self):
        vals = self.gather_values()
        if vals['master']:
            print(vals)

            vals['words'] = self.read_words(
                vals.pop('wlen_min'), vals.pop('wlen_max')
            )
            passphrase = generate_passphrase(**vals)
            PassphraseDialog(self, passphrase).exec_()
        # else:
        #     QtWidgets.QMessageBox.warning(
        #         self,
        #         'No Master Password!',
        #         'You must provide a master password',
        #     )


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = GeneratorWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
