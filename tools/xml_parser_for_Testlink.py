from json import dumps
from xml.dom import minidom

from .main_function import MainFUnction


class TLXMLConfig(MainFUnction):
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
        super(TLXMLConfig, self).__init__()
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

        return self.dom.documentElement

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
            if child.tagName == "details":
                try:
                    desc = child.childNodes[0].nodeValue
                except Exception:
                    desc = "NA"
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
                node_dict = self._prase_testcase(cur_node)
                if node_dict:
                    result.append(node_dict)
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
            if child.tagName == "testsuite":
                result.append(child)
        return result

    def _create_testcase_dict(self, node):
        result = {}
        name = node.getAttribute("name")
        element_id = node.getAttribute("internalid")
        parentid = node.getAttribute("parentid")
        text = self._create_text(node)
        result = {
            "tag_name": "TC",
            "name": name,
            "text": text,
            "element_id": element_id,
            "parentid": parentid,
            "test_type": None,
            "gid": None,
            "owner": None,
            "status": self.config["case_info"]["status"],
            "business_line": self.config["case_info"]["business_line"],
            "component": self.config["case_info"]["component"],
            "product": self.config["case_info"]["product"],
            "link": self.config["case_info"]["link"],
            "scope": self.config["case_info"]["scope"],
            "severity": self.config["case_info"]["severity"],
            "component_release_version": self.config["case_info"]["component_release_version"],
        }
        return result

    def _get_CDATA_value(self, node):
        try:
            return node.childNodes[0].nodeValue
        except IndexError:
            return "NA"

    def _create_text(self, node):
        summary = node.getElementsByTagName('summary')[0]
        preconditions = node.getElementsByTagName('preconditions')[0]
        step_list = node.getElementsByTagName('step')
        step_num = len(step_list) + 1
        tmp = {}
        step_number = 1
        for step in step_list:
            actions = self._get_CDATA_value(step.getElementsByTagName('actions')[0])
            expectedresults = self._get_CDATA_value(step.getElementsByTagName('expectedresults')[0])
            tmp[str(step_number)] = (actions, expectedresults)
            step_number += 1
        result = {
            "summary": self._get_CDATA_value(summary),
            "preconditions": self._get_CDATA_value(preconditions),
            "steps": [tmp[str(i)] for i in range(1, step_num)]
        }
        return dumps(result)

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

        result = None
        if node.tagName == "testsuite":
            tag_name = "TESTFOLDER"
            name = node.getAttribute("name")
            element_id = node.getAttribute("id")
            parentid = node.getAttribute("parentid")
            result = {
                "tag_name": tag_name,
                "name": name,
                "text": None,
                "element_id": element_id,
                "parentid": parentid,
                "test_type": None,
                "gid": None,
                "owner": None,
                "status": self.config["case_info"]["status"],
                "business_line": self.config["case_info"]["business_line"],
                "component": self.config["case_info"]["component"],
                "product": self.config["case_info"]["product"],
                "link": self.config["case_info"]["link"],
                "scope": self.config["case_info"]["scope"],
                "severity": self.config["case_info"]["severity"],
                "component_release_version": self.config["case_info"]["component_release_version"],
            }
        elif node.tagName == "testcase":
            result = self._create_testcase_dict(node)
        return result

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
        parent_id = root.getAttribute("id")
        for item in root.childNodes:
            if isinstance(item, minidom.Element):
                item.setAttribute("parentid", parent_id)
                result.append(item)
        return result


if __name__ == '__main__':
    tl = TLXMLConfig(r"D:\Script\TMS2Testlink2\tl.xml")
    root_content = tl.get_root_content()
    testcase_list = tl.create_final_list()
    print(testcase_list)
