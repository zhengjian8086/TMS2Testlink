#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
automate framework
"""

from json import dumps
from xml.dom import minidom
from .main_function import MainFUnction


class TMSXMLConfig(MainFUnction):
    """Parse test case config file from TMS.
     Args:
         filepath           type(str)           TMS test cases file path
     Example:
     Return:
     Author: zheng, jian
     IsInterface: False
     ChangeInfo: zheng, jian 2020-11-05
    """

    status_dict = {
        "Design": "1",
        "Obsolete": "5",
        "Ready": "7",
        "Repair": "4",
        "Workaround": "6"
    }

    def __init__(self, filepath=None):
        super(TMSXMLConfig, self).__init__()
        self.filepath = filepath
        self.dom = self.loading_xml()
        self.root = self.get_root_node()
        self.case_count = 1

    def loading_xml(self):
        """Loading xml and return a document object.
         Args:
         Example:
         Return:
             dom            type(xml.dom.minidom.Document)               xml document object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        dom = minidom.parse(self.filepath)
        return dom

    def get_root_node(self):
        """Get root node from document.
         Args:
         Example:
         Return:
             root           type(xml.dom.minidom.Element)           element object of root node
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        start_node = self.dom.documentElement
        testplan_node = start_node.getElementsByTagName('TESTPLAN')[0]
        root_node = self._get_all_children(testplan_node)[0]
        root = self._get_all_children(root_node)[0]
        return root

    def get_root_content(self):
        """Get root node content.
         Args:
         Example:
         Return:
             result           type(tuple)           tuple of root node content
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        name = self.root.getAttribute("name")
        children_list = self._get_all_children(self.root)
        desc = None
        for child in children_list:
            if child.tagName == "DESC":
                desc = child.childNodes[0].data
        result = {
            "name": name,
            "text": desc,
            "tag_name": "TESTFOLDER",
        }
        return result

    def testcase_breadth_prase(self, root):
        """Use breadth traversal to resolve root nodes.
         Args:
             root           type(xml.dom.minidom.Element)           element object of root node
         Example:
         Return:
             result           type(list)                            list with node info dict
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        if not root:
            return []
        result = []
        node_stack = [root]
        while node_stack:
            cur_node = node_stack.pop(0)
            if cur_node:
                result.append(
                    self._prase_testcase(cur_node)
                )
                for i in self._get_all_children(cur_node)[::-1]:
                    node_stack.insert(0, i)
        return result

    def create_final_list(self):
        testcase_queue_list = []
        for testcase in self.testfolder_list:
            testcase_queue_list.append(self.testcase_breadth_prase(testcase))
        return testcase_queue_list

    @property
    def testfolder_list(self):
        """Iterable object containing test folder nodes.
         Args:
         Example:
         Return:
         item           type(xml.dom.minidom.Element)                       test folder node
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        tcfolder_list = self._get_all_folder(self.root)
        for item in tcfolder_list:
            yield item

    def _get_all_folder(self, root):
        """Get list of test folder nodes.
         Args:
             root           type(xml.dom.minidom.Element)         element object of test folder node
         Example:
         Return:
             result           type(list)                          list with test folder nodes
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = []
        children_list = self._get_all_children(root)
        for child in children_list:
            if child.tagName == "TESTFOLDER":
                result.append(child)
        return result

    def _prase_testcase(self, node):
        """Get dict of test case info.
         Args:
             root           type(xml.dom.minidom.Element)          element object of test case node
         Example:
         Return:
             result           type(dict)                           dict with test case info
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        tag_name = node.tagName
        name = node.getAttribute("name")
        element_id = node.getAttribute("id")
        parentid = node.getAttribute("parentid")
        if tag_name == "TC":
            test_type = "auto" if node.getAttribute("auto") == "True" else "manual"
            gid = node.getAttribute("designer")
            owner = node.getAttribute("designer_f")
            status = \
                self.status_dict[node.getAttribute("state")] if node.getAttribute(
                    "state") else None
        else:
            test_type = None
            gid = None
            owner = None
            status = None
        text = None
        if tag_name == "DESC":
            if node.childNodes:
                text = node.childNodes[0].data
        result = {
            "tag_name": tag_name,
            "name": name,
            "text": text,
            "element_id": element_id,
            "parentid": parentid,
            "test_type": test_type,
            "gid": gid,
            "owner": owner,
            "status": self.config["case_info"]["status"],
            "business_line": self.config["case_info"]["business_line"],
            "component": self.config["case_info"]["component"],
            "product": self.config["case_info"]["product"],
            "link": self.config["case_info"]["link"],
            "scope": self.config["case_info"]["scope"],
            "severity": self.config["case_info"]["severity"],
            "component_release_version": self.config["case_info"]["component_release_version"],
        }
        if tag_name == "TC":
            if node.getAttribute("step") == "True":
                text_step = self._deal_test_with_steps(node)
                result["text_step"] = text_step
        return result

    def _deal_test_with_steps(self, node):
        step_list = node.getElementsByTagName("TCSTEP")
        step_num = len(step_list) + 1
        tmp = {}
        for step in step_list:
            step_number = step.getAttribute('order')
            actions = step.getElementsByTagName('DESC')[0].childNodes[0].data
            expectedresults = step.getElementsByTagName('EXP')[0].childNodes[0].data
            tmp[str(step_number)] = (actions, expectedresults)
        result = {
            "steps": [tmp[str(i)] for i in range(1, step_num)]
        }
        return dumps(result)

    @staticmethod
    def _get_all_children(root):
        """Get list of children element object.
         Args:
             root           type(xml.dom.minidom.Element)           element object of root node
         Example:
         Return:
             result           type(list)                            list with children nodes
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        result = []
        for item in root.childNodes:
            if isinstance(item, minidom.Element) and item.tagName != "UDF":
                result.append(item)
        return result
