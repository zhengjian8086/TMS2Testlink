from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt, QModelIndex


class NodeModel:
    def __init__(self):
        self.model = QStandardItemModel()
        self.my_model = QStandardItemModel()
        self.root = self.model.invisibleRootItem()
        self.root_index = self.root.index()

    def add_root(self, item):
        self.root = self.model.invisibleRootItem()
        self.root.removeRows(0, self.root.rowCount())
        cur_node = self.create_node(item)
        self.root.appendRow(cur_node)
        self.root = cur_node
        self.root_index = cur_node.index()

    def add_nodes_from_queue(self, test_queue):
        for test_list in test_queue:
            self.root.appendRow(self.add_testcase_from_queue(test_list))

    def add_testcase_from_queue(self, testcase_queue):
        node_stack = []
        id_stack = []
        cur_testcase = testcase_queue.pop(0)
        if cur_testcase["tag_name"] == "TESTFOLDER":
            if len(testcase_queue) > 0 and testcase_queue[0]["tag_name"] == "DESC":
                desc = testcase_queue.pop(0)
                cur_testcase["text"] = desc["text"]
            cur_node = self.create_node(cur_testcase)
            node_stack.append(cur_node)
            id_stack.append(cur_testcase["element_id"])
        while testcase_queue:
            cur_testcase = testcase_queue.pop(0)
            if cur_testcase["tag_name"] == "TESTFOLDER":
                if len(testcase_queue) > 0 and testcase_queue[0]["tag_name"] == "DESC":
                    desc = testcase_queue.pop(0)
                    cur_testcase["text"] = desc["text"]
                cur_node = self.create_node(cur_testcase)
                if cur_testcase["parentid"] == id_stack[0]:
                    node_stack[0].appendRow(cur_node)
                    node_stack.insert(0, cur_node)
                    id_stack.insert(0, cur_testcase["element_id"])
                else:
                    id_index = id_stack.index(cur_testcase["parentid"])
                    for i in range(id_index):
                        node_stack.pop(0)
                        id_stack.pop(0)
                    node_stack[0].appendRow(cur_node)
                    node_stack.insert(0, cur_node)
                    id_stack.insert(0, cur_testcase["element_id"])

            elif cur_testcase["tag_name"] == "TC":
                if testcase_queue and testcase_queue[0]["tag_name"] == "DESC":
                    next_node = testcase_queue.pop(0)
                    cur_testcase["text"] = next_node["text"]
                cur_node = self.create_node(cur_testcase)
                node_stack[0].appendRow(cur_node)
        result = node_stack.pop()
        return result

    def sync_checked_state(self, root: QStandardItem):
        result = []
        target_state = root.checkState()
        node_stack = [root]
        while node_stack:
            cur_node = node_stack.pop(0)
            if not cur_node.checkState() == target_state:
                cur_node.setCheckState(target_state)
            for i in self._get_all_children(cur_node)[::-1]:
                node_stack.insert(0, i)
        return result

    def sync_data_state(self, root: QStandardItem):
        template = root.data(Qt.TextDate)
        count = 1
        result = []
        node_stack = [root]
        while node_stack:
            cur_node = node_stack.pop(0)
            count = self._rename_user_data(cur_node, template, count)
            for i in self._get_all_children(cur_node)[::-1]:
                node_stack.insert(0, i)
        return result

    def my_node_model_checked_change(self, node_index: QModelIndex):
        node = self.my_model.itemFromIndex(node_index)
        self.sync_data_state(node)

    def checked_change(self, node: QStandardItem):
        self.sync_checked_state(node)

    def get_all_checked_node(self):
        my_root = self.my_model.invisibleRootItem()
        my_root.removeRows(0, my_root.rowCount())
        target_stack = [my_root]
        rec_stack = []
        node_stack = [self.root]
        while node_stack:
            cur_node = node_stack.pop(0)
            if cur_node.checkState() == Qt.Checked:
                cur_info_dict = cur_node.data(Qt.UserRole)
                if cur_info_dict["tag_name"] == "TESTFOLDER":
                    new_node = self.create_node(cur_info_dict)
                    if not len(rec_stack) == 0:
                        if cur_node.parent() in rec_stack:
                            for i in range(rec_stack.index(cur_node.parent())):
                                target_stack.pop(0)
                                rec_stack.pop(0)
                        elif cur_node.parent() == self.root:
                            for i in range(len(rec_stack)):
                                target_stack.pop(0)
                                rec_stack.pop(0)
                    target_stack[0].appendRow(new_node)
                    target_stack.insert(0, new_node)
                    rec_stack.insert(0, cur_node)
                elif cur_info_dict["tag_name"] == "TC":
                    new_node = self.create_node(cur_info_dict)
                    target_stack[0].appendRow(new_node)
            for i in self._get_all_children(cur_node)[::-1]:
                node_stack.insert(0, i)

    def create_config_file(self):
        result = []
        my_root = self.my_model.invisibleRootItem()
        node_stack = [my_root]
        while node_stack:
            cur_node = node_stack.pop(0)
            if cur_node.checkState() == Qt.Checked:
                result.append(cur_node.data(Qt.UserRole))
            for i in self._get_all_children(cur_node)[::-1]:
                node_stack.insert(0, i)
        return result

    @staticmethod
    def create_node(info_dict):
        user_data = {}
        node_info_keys = ("tag_name", "name", "text", "element_id", "parentid",
                          "test_type", "gid", "owner", "status", "business_line",
                          "component", "product", "link", "scope", "severity",
                          "component_release_version")
        for i in node_info_keys:
            if i in info_dict.keys():
                user_data[i] = info_dict[i]
            else:
                user_data[i] = None
        if "text_step" in info_dict.keys():
            user_data["text_step"] = info_dict["text_step"]
        cur_node = QStandardItem(user_data["name"])
        cur_node.setData(user_data, Qt.UserRole)
        cur_node.setCheckable(True)
        cur_node.setTristate(True)
        cur_node.setCheckState(Qt.Checked)
        return cur_node

    @staticmethod
    def _get_all_children(root: QStandardItem):
        result = []
        row_count = root.rowCount()
        if not row_count == 0:
            for i in range(row_count):
                result.append(root.child(i))
        return result

    @staticmethod
    def _rename_user_data(cur_node, template, count):
        if cur_node.checkState() == Qt.Checked and cur_node.data(Qt.UserRole)["tag_name"] == "TC":
            tmp = cur_node.data(Qt.UserRole)
            tmp["name_old"] = tmp["name"]
            tmp["name"] = "test_{}_{}".format(template, str(count).zfill(3))
            cur_node.setData(tmp["name"], Qt.TextDate)
            cur_node.setData(tmp, Qt.UserRole)
            count += 1
        return count


if __name__ == '__main__':
    pass
