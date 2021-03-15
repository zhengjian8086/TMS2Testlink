import os
import re
import sys

from pprint import pprint
from lxml import etree
from main_function import MainFUnction
from xml_parser_for_TMS import TMSXMLConfig
from xml_generator_from_TMS import XMLGeneratorFromTMS
from excel_generator import ExcelGenerator


class ConvertToXML(MainFUnction):
    """Import test case from TMS to TestLink.
     Args:
         filepath           type(str)           TMS test cases file path
         exportpath         type(str)           TestLink test cases config export path
     Example:
     Return:
     Author: zheng, jian
     IsInterface: False
     ChangeInfo: zheng, jian 2020-11-05
    """

    def __init__(self, file_path, export_path):
        super(ConvertToXML, self).__init__()
        self.file_path = file_path
        self.export_path = export_path

    def convert_to_xml(self):
        """Start to create TestLink xml.
         Args:
         Example:
         Return:
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        dom = TMSXMLConfig(self.file_path)
        root_content = dom.get_root_content()
        xml_writer = XMLGeneratorFromTMS(self.export_path)
        if self.config["rename"]["switch"] != "true":
            xml_writer.add_root_node(root_content)
        testcase_queue_list = []
        for testcase in dom.testfolder_list:
            testcase_queue_list.append(dom.testcase_breadth_prase(testcase))
        if self.config["rename"]["switch"] == "true":
            count = 0
            for item in testcase_queue_list[0]:
                if item["name"] == self.config["rename"]["target_dir"]:
                    break
                count += 1
            for i in range(count):
                testcase_queue_list[0].pop(0)
        xml_writer.add_testcase_to_root(testcase_queue_list)
        xml_writer.save_file()

    def convert_to_excel(self):
        """Start to create test case excel.
         Args:
         Example:
         Return:
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-06
        """

        dom = TMSXMLConfig(self.file_path)
        test_sheets = self.get_test_sheet_list(dom)
        sheet_info_dict = self.create_all_sheet_info_dict(test_sheets)
        excel = ExcelGenerator(self.export_path, sheet_info=sheet_info_dict)
        excel.excel_generator()

    def create_all_sheet_info_dict(self, test_sheets):
        """Create a dict for excel.
         Args:
             test_sheets               type(list)                       sheet info list
         Example:
         Return:
             sheet_info_dict           type(dict)                       dict for create excel
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        sheet_info_dict = {}
        for test_sheet in test_sheets:
            sheet_info = self.create_sheet_info(test_sheet)
            sheet_info_dict[sheet_info[0]] = sheet_info[1]
        return sheet_info_dict

    def create_sheet_info(self, test_line_list):
        """Create a sheet from list .
         Args:
             testcase_queue   type(list)                       list of test case dict
         Example:
         Return:
             result           type(list)                       list of sheet info
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = []
        sheet_info = {
            "titles": None,
            "values": [[
                "Module",
                "No.",
                "Description",
                "Preconditions",
                "Step actions",
                "Expected results",
                "Execution",
                "Auto status",
                "Priority",
                "Results",
                "Tester",
                "Date",
                "remarks",
            ]]
        }
        line_stack = []
        id_stack = []
        cur_line = test_line_list.pop(0)
        if cur_line["tag_name"] == "TESTFOLDER":
            if len(test_line_list) > 0 and test_line_list[0]["tag_name"] == "DESC":
                test_line_list.pop(0)
            sheet_info["titles"] = [cur_line["name"].replace(" ", "_")]
            result.append(cur_line["name"][:10])
        line_stack.append(cur_line["name"].replace(" ", "_"))
        id_stack.append(cur_line["element_id"])
        tc_mark = False
        while test_line_list:
            cur_line = test_line_list.pop(0)
            if cur_line["tag_name"] == "TESTFOLDER":
                tc_mark = False
                if len(test_line_list) > 0 and test_line_list[0]["tag_name"] == "DESC":
                    test_line_list.pop(0)
                    cur_test_line = cur_line["name"].replace(" ", "_")
                else:
                    cur_test_line = cur_line["name"].replace(" ", "_")
                if cur_line["parentid"] == id_stack[0]:
                    line_stack.insert(0, cur_test_line)
                    id_stack.insert(0, cur_line["element_id"])
                else:
                    id_index = id_stack.index(cur_line["parentid"])
                    for i in range(id_index):
                        line_stack.pop(0)
                        id_stack.pop(0)
                    line_stack.insert(0, cur_test_line)
                    id_stack.insert(0, cur_line["element_id"])
            elif cur_line["tag_name"] == "TC":
                if not tc_mark:
                    sheet_info["values"].append([".".join(line_stack[::-1])])
                    tc_mark = True
                tc_content_dict = None
                if test_line_list[0]["tag_name"] == "DESC":
                    next_node = test_line_list.pop(0)
                    if next_node["text"]:
                        tc_content_dict = self._parse_tc(next_node["text"])
                    else:
                        tc_content_dict = {
                            "Goal": None,
                            "Preconditions": None,
                            "Description": None,
                            "Expected Result: ": None
                        }
                sheet_info["values"].append([
                    "",
                    self._file_name_handler(cur_line["name"]),
                    self._get_content_str(tc_content_dict["summary"]),
                    self._get_content_str(tc_content_dict["preconditions"]),
                    self._get_content_str(tc_content_dict["description"]),
                    self._get_content_str(tc_content_dict["expected"]),
                    "A",
                    "N",
                    "H",
                ])
        result.append(sheet_info)
        return result

    def _parse_tc(self, content):
        """Parse test case content from text.
         Args:
             content           type(str)           test case content string
         Example:
         Return:
             result            type(dict)          dict of test case content
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = {}
        desc_html = etree.HTML(content)
        text_list = desc_html.xpath('//span//text()')
        text_list = self._remove_space(text_list)

        if text_list:
            result["summary"] = self._create_case_dict(text_list, self.config["mapping"]["summary"])
            result["preconditions"] = self._create_case_dict(text_list, self.config["mapping"][
                "preconditions"])
            result["description"] = self._create_case_dict(text_list,
                                                           self.config["mapping"]["description"])
            result["expected"] = self._create_case_dict(text_list,
                                                        self.config["mapping"]["expected"])
        else:
            result = {
                "summary": None,
                "preconditions": None,
                "description": None,
                "expected": None
            }
        return result

    @staticmethod
    def _file_name_handler(file_name):
        """Deal space and special char.
         Args:
             file_name        type(str)                       original string
         Example:
         Return:
             result           type(str)                       after deal string
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = file_name.replace(" ", "_")
        result = result.replace('"', "")
        result = result.replace("'", "")
        return result

    @staticmethod
    def _remove_space(str_list):
        """remove special field.
         Args:
             str_list               type(list)                      string list
         Example:
         Return:
             result                 type(list)                      string list no special field
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = []
        for item in str_list:
            if not item == "\xa0" and not item == " ":
                item = item.strip()
                result.append(item.replace("\xa0", " "))
        return result

    @staticmethod
    def _get_content_str(content_iterable):
        """Combine str to element <p> from iterable objects .
         Args:
             content_iterable           type(iterable objects)           a string iterable objects
         Example:
         Return:
             result                     type(str)                        Strings branched with <p>
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """
        result = ""
        templete = "{line}\r\n"
        if content_iterable:
            for line in content_iterable:
                line = line.strip()
                if not line == "" and line:
                    result += templete.format(line=line)
        else:
            result = "NA"
        return result

    @staticmethod
    def _create_case_dict(text_list, cur_title_list):
        result = ("NA",)
        for title in cur_title_list:
            if title in text_list:
                t_index = text_list.index(title)
                tmp = []
                for i in range(t_index + 1, len(text_list)):
                    mark = re.findall("\S+:$", text_list[i])
                    if not mark:
                        tmp.append(text_list[i])
                    else:
                        break
                # result = ConvertToXML.deal_content_list(tmp) if tmp else ("NA",)
                result = tuple(tmp) if tmp else ("NA",)
                break
        return result

    @staticmethod
    def get_test_sheet_list(dom):
        """Create a dict for excel.
          Args:
              dom                   type(document object)            document object
          Example:
          Return:
              test_sheets           type(list)                       list of sheet info
          Author: zheng, jian
          IsInterface: False
          ChangeInfo: zheng, jian 2020-11-05
         """

        test_sheets = []
        for test_case in dom.testfolder_list:
            test_sheets.append(dom.testcase_breadth_prase(test_case))
        return test_sheets

    @staticmethod
    def deal_content_list(content_list):
        result = []
        for item in content_list:
            print(item)
            tmp = re.findall(r"<p>([\S\s]+)<p>", item)[0]
            result.append(tmp)
        return tuple(result)


def pre_check():
    if len(sys.argv) <= 1:
        print(
            """
                xxx.exe file_path export_path
                exp: xxx.exe TMS_config.xml TestLink_config.xml
            """
        )
        sys.exit()
    if not os.path.exists("config.ini"):
        print(
            """
                config.ini not exist
            """
        )
        sys.exit()


def prepare():
    path = os.getcwd()
    file_path_usr = r"{}\{}".format(path, sys.argv[1])
    export_path_usr = r"{}\{}".format(path, sys.argv[2])
    return file_path_usr, export_path_usr


if __name__ == '__main__':
    pre_check()
    file_path_usr, export_path_usr = prepare()
    convert = ConvertToXML(
        file_path=file_path_usr,
        export_path=export_path_usr
    )
    if convert.config["feature"]["switch"] == "1":
        convert.convert_to_xml()
    else:
        convert.convert_to_excel()
