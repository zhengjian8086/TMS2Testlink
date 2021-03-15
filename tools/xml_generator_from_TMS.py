import re
from json import loads

from .main_function import MainFUnction
from tools.case_parser import CaseParser
from xml.dom import minidom
from lxml import etree


class XMLGeneratorFromTMS(MainFUnction):
    """Create test case config file for TestLink.
     Args:
         filename           type(str)           new test case config file path
     Example:
     Return:
     Author: zheng, jian
     IsInterface: False
     ChangeInfo: zheng, jian 2020-11-05
    """

    def __init__(self, filename="TestLink_config.xml"):
        super(XMLGeneratorFromTMS, self).__init__()
        self.filename = filename
        self.dom = minidom.Document()
        self.root_node = None

    def add_root_node(self, data):
        """Add root node for document.
         Args:
             data           type(tuple)                             data with root info
         Example:
         Return:
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        self.root_node = self._add_testsuit_node(data[0], data[1])

    def add_testcase_from_queue(self, testcase_queue):
        """Create a test suit from queue .
         Args:
             testcase_queue   type(list)                       list of test case dict
         Example:
         Return:
             result           type(xml.dom.minidom.Element)    test suit node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        node_stack = [self.root_node]
        id_stack = []
        while testcase_queue:
            cur_testcase = testcase_queue.pop(0)
            if cur_testcase["tag_name"] == "TESTFOLDER":
                cur_node = self._add_testsuit_node(cur_testcase["name"], cur_testcase["text"])
                if id_stack:
                    if not cur_testcase["parentid"] == id_stack[0]:
                        if cur_testcase["parentid"] in id_stack:
                            id_index = id_stack.index(cur_testcase["parentid"])
                        else:
                            id_index = len(id_stack)
                        for i in range(id_index):
                            node_stack.pop(0)
                            id_stack.pop(0)
                node_stack[0].appendChild(cur_node)
                node_stack.insert(0, cur_node)
                id_stack.insert(0, cur_testcase["element_id"])
            elif cur_testcase["tag_name"] == "TC":
                tc_content_dict = CaseParser().parse_tc(cur_testcase["text"])
                cur_node = self._add_testcase_node(cur_testcase, tc_content_dict)
                node_stack[0].appendChild(cur_node)

    def add_testcase_to_root(self, testcase_queue_list):
        """Add all test suit node to root.
         Args:
             testcase_queue_list   type(list)                       list of test suit
         Example:
         Return:
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """
        if not self.root_node:
            root_tmp = testcase_queue_list.pop(0)
            self.add_root_node((root_tmp["name"], root_tmp["text"]))
        self.add_testcase_from_queue(testcase_queue_list)

    def save_file(self):
        """Add root node to document and output xml file.
         Args:
         Example:
         Return:
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        self.dom.appendChild(self.root_node)
        try:
            with open(self.filename, 'w', encoding='UTF-8') as fh:
                self.dom.writexml(fh, indent='', addindent='\t', newl='\n', encoding='UTF-8')
                print('OK')
        except Exception as err:
            print('错误：{err}'.format(err=err))

    def _add_testsuit_node(self, name, details):
        """Create a test suit node object.
         Args:
             name               type(str)                       node tag name
             details            type(str)                       node text content
         Example:
         Return:
             testsuit_node      type(xml.dom.minidom.Element)   test suit node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        tag_name = "testsuite"
        testsuit_node = self.dom.createElement(tag_name)
        testsuit_node.setAttribute("name", name)
        if not details:
            details_node = self.dom.createElement('details')
            details_text = self.dom.createTextNode(str(details))
            details_node.appendChild(details_text)
            testsuit_node.appendChild(details_node)
        return testsuit_node

    def _add_testcase_node(self, testcase, tc_content_dict):
        """Create a test case node object.
         Args:
             testcase                   type(dict)                       dict of element info
             tc_content_dict            type(dict)                       dict of test case info
         Example:
         Return:
             testcase_node      type(xml.dom.minidom.Element)            test case node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        name = testcase["name"]
        test_type = testcase["test_type"]
        tag_name = "testcase"
        testcase_node = self.dom.createElement(tag_name)
        testcase_node.setAttribute("name", name)

        summary_node = self.dom.createElement('summary')
        summary_text = self.dom.createTextNode(
            self._get_content_str(tc_content_dict["summary"],
                                  title=testcase["name_old"] if "name_old" in testcase.keys() else
                                  testcase["name"]))
        summary_node.appendChild(summary_text)

        preconditions_node = self.dom.createElement('preconditions')
        preconditions_text = self.dom.createTextNode(
            self._get_content_str(tc_content_dict["preconditions"])
        )
        preconditions_node.appendChild(preconditions_text)

        status_node = self.dom.createElement('status')
        status_text = self.dom.createTextNode(testcase["status"])
        status_node.appendChild(status_text)

        if "text_step" in testcase.keys():
            steps_node = self._add_steps_node_with_steps(test_type, testcase["text_step"])
        else:
            steps_node = self._add_steps_node(
                test_type,
                tc_content_dict["description"],
                tc_content_dict["expected"]
            )

        custom_fields_node = self._add_custom_fields(testcase)

        testcase_node.appendChild(summary_node)
        testcase_node.appendChild(preconditions_node)
        testcase_node.appendChild(status_node)
        testcase_node.appendChild(steps_node)
        testcase_node.appendChild(custom_fields_node)

        return testcase_node

    def _add_custom_fields(self, testcase):
        """Create a customer node for test case node object.
         Args:
             testcase                   type(dict)                      test case info
         Example:
         Return:
             custom_fields_node         type(xml.dom.minidom.Element)   customer node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        order = [item for item in self.config["custom_fields"].items()]

        custom_fields_node = self.dom.createElement('custom_fields')

        for item in order:
            custom_field_node = self.dom.createElement('custom_field')
            name_node = self.dom.createElement('name')
            name_text = self.dom.createCDATASection(item[1])
            name_node.appendChild(name_text)
            value_node = self.dom.createElement('value')
            value_text = self.dom.createCDATASection(testcase[item[0]])
            value_node.appendChild(value_text)
            custom_field_node.appendChild(name_node)
            custom_field_node.appendChild(value_node)

            custom_fields_node.appendChild(custom_field_node)

        return custom_fields_node

    def _add_simple_step(self, index, test_type, step_text, expected_text):
        """Create a step node for test case node object.
         Args:
             index                   type(int)                      number of step
             test_type               type(str)                      manual or auto
             step_text               type(str)                      test case step info
             expected_text           type(str)                      test case expected info
         Example:
         Return:
             step_node               type(xml.dom.minidom.Element)  step node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        type_dict = {
            "manual": "1",
            "auto": "2"
        }
        step_node = self.dom.createElement('step')

        step_number_node = self.dom.createElement('step_number')
        step_number_text = self.dom.createTextNode(str(index + 1))
        step_number_node.appendChild(step_number_text)

        actions_node = self.dom.createElement('actions')
        actions_text = self.dom.createTextNode(step_text)
        actions_node.appendChild(actions_text)

        expectedresults_node = self.dom.createElement('expectedresults')
        expectedresults_text = self.dom.createTextNode(expected_text)
        expectedresults_node.appendChild(expectedresults_text)

        execution_type_node = self.dom.createElement('execution_type')
        execution_type_text = self.dom.createTextNode(type_dict[test_type])
        execution_type_node.appendChild(execution_type_text)

        step_node.appendChild(step_number_node)
        step_node.appendChild(actions_node)
        step_node.appendChild(expectedresults_node)
        step_node.appendChild(execution_type_node)

        return step_node

    def _add_steps_node(self, test_type, step_text_list, expected_text_list):
        """Create steps node for test case node object.
         Args:
             test_type               type(str)                      manual or auto
             step_text_list          type(str)                      list of test case step info
             expected_text_list      type(str)                      list of test case expected info
         Example:
         Return:
             steps_node              type(xml.dom.minidom.Element)  steps node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        steps_node = self.dom.createElement('steps')
        if step_text_list and expected_text_list and len(step_text_list) == len(expected_text_list):
            for i in range(len(step_text_list)):
                step_node = self._add_simple_step(
                    i,
                    test_type,
                    step_text_list[i],
                    expected_text_list[i]
                )
                steps_node.appendChild(step_node)
        else:
            step_node = self._add_simple_step(
                0,
                test_type,
                self._get_content_str(step_text_list),
                self._get_content_str(expected_text_list)
            )
            steps_node.appendChild(step_node)
        return steps_node

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

    def _add_steps_node_with_steps(self, test_type, content):
        """Create steps node for test case node object.
         Args:
             test_type               type(str)                      manual or auto
             step_text_list          type(str)                      list of test case step info
             expected_text_list      type(str)                      list of test case expected info
         Example:
         Return:
             steps_node              type(xml.dom.minidom.Element)  steps node object
         Author: zheng, jian
         IsInterface: False
         ChangeInfo: zheng, jian 2020-11-05
        """

        steps_node = self.dom.createElement('steps')
        info_list = loads(content)["steps"]
        description = []
        expected = []
        for item in info_list:
            description.append(item[0])
            expected.append(item[1])
        for i in range(len(description)):
            step_node = self._add_simple_step(
                i,
                test_type,
                description[i],
                expected[i]
            )
            steps_node.appendChild(step_node)
        return steps_node

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
    def _get_content_str(content_iterable, title=None):
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
        templete = "<p>{line}</p>"
        result = templete.format(line=title) if title else ""
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
                result = tuple(tmp) if tmp else ("NA",)
                break
        return result


if __name__ == '__main__':
    xml = XMLGeneratorFromTMS()
    text_list = ['Test Steps:', '1. Prepare one registed BM and connect it to LSC.',
                 '2. Go to "Online settings" and configure "Cloud Data Transfer Settings" .',
                 '3. Factory reset BM.', 'Expected Results:', '1. The configured data is missing.']
    text_list_error = ['Test Steps:', ]
    tmp = xml._create_case_dict(text_list_error, xml.config["mapping"]["description"])
    print(tmp)
