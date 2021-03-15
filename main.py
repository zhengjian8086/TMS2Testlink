from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QMessageBox, \
    QLineEdit

from UI.mainForm import Ui_MainWindow
from model.node_model import NodeModel
from model.case_model import CaseModel
from tools.xml_parser_for_TMS import TMSXMLConfig
from tools.xml_parser_for_Testlink import TLXMLConfig
from tools.xml_generator_from_TMS import XMLGeneratorFromTMS
from tools.main_function import MainFUnction
from tools.generator_excel import CreateExcel


class MainWindow(QMainWindow, Ui_MainWindow, MainFUnction):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.init_model()
        self.init_event()

    def init_model(self):
        self.node_model = NodeModel()

    def init_event(self):
        self.importButton.clicked.connect(self.import_config_file)
        self.pullButton.clicked.connect(self.pull_config_from_tms_tree)
        # self.deleteButton.clicked.connect(self.delete_config_from_my_tree)
        self.exportButton.clicked.connect(self.export_config_file)
        # self.radioButton_tl.toggled.connect(lambda :None)
        # self.radioButton_tms.toggled.connect(lambda :None)

        # self.tmsTree.clicked.connect(self.tms_tree_onclicked)
        self.node_model.model.itemChanged.connect(self.node_model_checked_change)
        # self.node_model.my_model.itemChanged.connect(self.node_model_checked_change)
        self.node_model.my_model.dataChanged.connect(self.my_node_model_checked_change)

        self.tmsTree.header().hide()
        self.myTree.header().hide()
        self.radioButton_tl.setChecked(True)

    def import_config_file(self):
        file_path = QFileDialog.getOpenFileName(self, 'Select config file')[0]
        if not file_path:
            return
        if self._is_tms_radio_button:
            dom = TMSXMLConfig(file_path)
        else:
            dom = TLXMLConfig(file_path)
        root_content = dom.get_root_content()
        testcase_list = dom.create_final_list()
        self.node_model.add_root(root_content)
        self.node_model.add_nodes_from_queue(testcase_list)
        self.tmsTree.setModel(self.node_model.model)

    def pull_config_from_tms_tree(self):
        self.node_model.get_all_checked_node()
        self.myTree.setModel(self.node_model.my_model)

    def delete_config_from_my_tree(self):
        pass

    def export_config_file(self):
        row_mark = self.node_model.my_model.rowCount()
        root_value = None
        ok = None
        if row_mark == 0:
            return
        elif row_mark > 1:
            root_value, ok = QInputDialog.getText(self, "输入根节点名称", "请输入根节点名称:", QLineEdit.Normal,
                                                  "Root")
        file_info = QFileDialog.getSaveFileName(self, "Select config file", "",
                                                'xls(*.xls);;XML(*.xml)')
        xml_writer = XMLGeneratorFromTMS(file_info[0])
        excel_creater = CreateExcel(file_info[0])
        if root_value:
            xml_writer.add_root_node((root_value, None))
        if file_info[1] == "XML(*.xml)":
            xml_writer.add_testcase_to_root(self.node_model.create_config_file())
            xml_writer.save_file()
        elif file_info[1] == "xls(*.xls)":
            excel_config = self.node_model.create_config_file()
            if self._is_tms_radio_button:
                excel_creater.convert_to_excel(excel_config)
            else:
                excel_creater.convert_to_excel_from_tl(excel_config)

    def tms_tree_onclicked(self, index):
        case_model = CaseModel()
        case_model.get_case_info(index)
        if self._is_tms_radio_button:
            case_model.get_case_content("TMS", index)
        else:
            case_model.get_case_content("Testlink", index)
        self.contentList.setModel(case_model.info_model)
        self.caseView.setModel(case_model.content_model)

    def node_model_checked_change(self, index):
        self.node_model.model.itemChanged.disconnect()
        self.node_model.checked_change(index)
        self.node_model.model.itemChanged.connect(self.node_model_checked_change)

    def my_node_model_checked_change(self, index):
        self.node_model.my_model.dataChanged.disconnect()
        self.node_model.my_node_model_checked_change(index)
        self.node_model.my_model.dataChanged.connect(self.my_node_model_checked_change)

    @property
    def _is_tms_radio_button(self):
        return True if self.radioButton_tms.isChecked() else False


if __name__ == '__main__':
    app = QApplication(argv)
    mainWindow = MainWindow()
    mainWindow.show()
    exit(app.exec_())
