from PyQt5.QtCore import Qt, QStringListModel

from tools.case_parser import CaseParser


class CaseModel:
    def __init__(self):
        self.info_model = QStringListModel()
        self.content_model = QStringListModel()

    def get_case_info(self, source):
        info_dict = source.data(Qt.UserRole)
        tmp = []
        for key, value in info_dict.items():
            tmp.append(key + ":" + str(value))
        self.info_model.setStringList(tmp)

    def get_case_content(self, mark, source):
        info_dict = source.data(Qt.UserRole)
        tmp = []
        if mark=="TMS":
            result=CaseParser().parse_tc(info_dict["text"])
        else:
            result=CaseParser().parse_tc_from_tl(info_dict["text"])
        for key, value in result.items():
            tmp.append(key + ":" + str(value))
        self.info_model.setStringList(tmp)
