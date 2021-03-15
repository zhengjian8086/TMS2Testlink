from re import findall

from .excel_generator import ExcelGenerator
from tools.case_parser import CaseParser


class CreateExcel:
    def __init__(self, file_path):
        self.file_path = file_path
        self.mark = "TMS"

    def convert_to_excel(self, resource_list):
        sheet_info_dict = self.create_all_sheet_info_dict(resource_list)
        excel = ExcelGenerator(self.file_path, sheet_info=sheet_info_dict)
        excel.excel_generator()

    def convert_to_excel_from_tl(self, resource_list):
        self.mark = "TL"
        sheet_info_dict = self.create_all_sheet_info_dict(resource_list)
        excel = ExcelGenerator(self.file_path, sheet_info=sheet_info_dict)
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
        sheet_info = self.create_sheet_info(test_sheets)
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
            sheet_info["titles"] = [cur_line["name"].replace(" ", "_")]
            result.append(cur_line["name"][:10].replace("\\", "_").replace("/", "_"))
        line_stack.append(cur_line["name"].replace(" ", "_"))
        id_stack.append(cur_line["element_id"])
        tc_mark = False
        while test_line_list:
            cur_line = test_line_list.pop(0)
            if cur_line["tag_name"] == "TESTFOLDER":
                tc_mark = False
                cur_test_line = cur_line["name"].replace(" ", "_")
                if not len(id_stack) == 0:
                    if not cur_line["parentid"] == id_stack[0]:
                        if cur_line["parentid"] in id_stack:
                            id_index = id_stack.index(cur_line["parentid"])
                            for i in range(id_index):
                                line_stack.pop(0)
                                id_stack.pop(0)
                        else:
                            for i in range(len(id_stack)):
                                line_stack.pop(0)
                                id_stack.pop(0)
                line_stack.insert(0, cur_test_line)
                id_stack.insert(0, cur_line["element_id"])
            elif cur_line["tag_name"] == "TC":
                if not tc_mark:
                    sheet_info["values"].append([".".join(line_stack[::-1])])
                    tc_mark = True
                # next_node = test_line_list.pop(0)
                if self.mark == "TMS":
                    tc_content_dict = CaseParser().parse_tc(cur_line["text"])
                else:
                    tc_content_dict = CaseParser().parse_tc_from_tl(cur_line["text"])
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
                    mark = findall("\S+:$", text_list[i])
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
            tmp = findall(r"<p>([\S\s]+)<p>", item)[0]
            result.append(tmp)
        return tuple(result)
