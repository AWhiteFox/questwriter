from typing import List, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu, QMessageBox, QCheckBox, QDoubleSpinBox, QInputDialog

from questlib import VariableDefinition

from model.generation import generate_new_variable_definition
from view import FileStateContainer


class VariableTreeWidget(QTreeWidget):
    def __init__(self, file_state: FileStateContainer, variables: List[VariableDefinition]):
        super().__init__()
        self.file_state = file_state
        self.variables = variables

        self.setColumnCount(2)
        self.setHeaderLabels(['Имя переменной', 'Стартовое значение'])
        self.header().setSectionResizeMode(QHeaderView.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        self.itemChanged.connect(self._on_self_item_changed)

        self._generate_items()

    def _generate_items(self) -> None:
        self.clear()
        for v in self.variables:
            item = self._generate_item(v)
            self.addTopLevelItem(item)
            item.init_widgets(self)

    def _generate_item(self, variable: VariableDefinition) -> 'VariableTreeWidgetItemBase':
        if variable.type is bool:
            return BoolTreeWidgetItem(self.file_state, variable)
        if variable.type is float:
            return FloatTreeWidgetItem(self.file_state, variable)

    def _context_menu(self, position: QPoint) -> None:
        menu = QMenu()

        menu.addAction('Добавить переменную', self._add_variable)
        menu.addSeparator()
        menu.addAction('Удалить', self._delete_variable)
        menu.actions()[-1].setEnabled(len(self.variables) > 0)

        menu.exec_(self.viewport().mapToGlobal(position))

    def _add_variable(self) -> None:
        selected_i = self.indexOfTopLevelItem(self.currentItem())

        new = self._generate_new_variable()
        if new is None:
            return

        self.variables.insert(selected_i + 1, new)
        self.file_state.set_dirty()

        new_item = self._generate_item(new)
        self.insertTopLevelItem(selected_i + 1, new_item)
        new_item.init_widgets(self)

    def _generate_new_variable(self) -> Optional[VariableDefinition]:
        title = '?'
        msg = 'Выберите тип переменной'
        options = ['Флаг', 'Число']
        s, ok = QInputDialog.getItem(self, title, msg, options, 0, False)
        if ok:
            if s == options[0]:
                return generate_new_variable_definition(False)
            if s == options[1]:
                return generate_new_variable_definition(0.0)
        return None

    def _delete_variable(self) -> None:
        title = 'Удалить'

        selected_i = self.indexOfTopLevelItem(self.currentItem())

        msg = f'Удалить переменную {self.variables[selected_i].name}?'
        res = QMessageBox.question(self, title, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if res == QMessageBox.Yes:
            del self.variables[selected_i]
            self.file_state.set_dirty()
            self.takeTopLevelItem(selected_i)

    def _on_self_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column == 0:
            self.variables[self.indexOfTopLevelItem(item)].name = item.text(column)
            self.file_state.set_dirty()


class VariableTreeWidgetItemBase(QTreeWidgetItem):
    def __init__(self, file_state: FileStateContainer, variable: VariableDefinition):
        super().__init__()
        self.file_state = file_state
        self.variable = variable
        self.value_widget = None

        self.setText(0, variable.name)
        self.setFlags(int(self.flags()) | QtCore.Qt.ItemIsEditable)

    def init_widgets(self, tree_widget: QTreeWidget) -> None:
        tree_widget.setItemWidget(self, 1, self.value_widget)


class BoolTreeWidgetItem(VariableTreeWidgetItemBase):
    def __init__(self, file_state: FileStateContainer, variable: VariableDefinition):
        super().__init__(file_state, variable)

        self.value_widget = QCheckBox()
        self.value_widget.setCheckState(variable.initial_value)

        self.value_widget.stateChanged.connect(self.on_check_box_value_changed)

    def on_check_box_value_changed(self, _: int) -> None:
        self.variable.initial_value = self.value_widget.checkState()
        self.file_state.set_dirty()


class FloatTreeWidgetItem(VariableTreeWidgetItemBase):
    def __init__(self, file_state: FileStateContainer, variable: VariableDefinition):
        super().__init__(file_state, variable)

        self.value_widget = QDoubleSpinBox()
        self.value_widget.setValue(variable.initial_value)

        self.value_widget.valueChanged.connect(self.on_spin_box_value_changed)

    def on_spin_box_value_changed(self, _: int) -> None:
        self.variable.initial_value = self.value_widget.value()
        self.file_state.set_dirty()