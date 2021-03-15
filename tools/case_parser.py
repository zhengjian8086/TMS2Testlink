from json import loads
from re import findall
from lxml import etree

from .main_function import MainFUnction


class CaseParser(MainFUnction):
    def parse_tc_from_tl(self, content):
        if content:
            info_dict = loads(content)
            description = []
            expected = []
            summary = [info_dict["summary"]]
            preconditions = [info_dict["preconditions"]]
            for item in info_dict["steps"]:
                description.append(item[0])
                expected.append(item[1])
            result = {
                "summary": self.deal_info_from_tl(summary, True),
                "preconditions": self.deal_info_from_tl(preconditions, True),
                "description": self.deal_info_from_tl(description),
                "expected": self.deal_info_from_tl(expected)
            }
        else:
            result = {
                "summary": ("NA",),
                "preconditions": ("NA",),
                "description": ("NA",),
                "expected": ("NA",)
            }
        return result

    def parse_tc(self, content):
        result = {}
        text_list = None
        if content:
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

    def deal_info_from_tl(self, lines, auto_number=False):
        result = []
        for line in lines:
            tmp = findall("\w\w[\s\S]+?(?=</p>)", line)
            for i in range(len(tmp)):
                result.append(self.auto_add_number(tmp[i], i) if auto_number else tmp[i])
        return tuple(result)

    @staticmethod
    def auto_add_number(line: str, num):
        return "{}. {}".format(str(num+1), line)

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
                result = tuple(tmp) if tmp else ("NA",)
                break
        return result
