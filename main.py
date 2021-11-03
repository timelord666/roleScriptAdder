import os
import glob
import xml.etree.ElementTree as xml
import uuid
import re

base_path = "C:\\dmsScripted\\"
roles_path = base_path + "Roles\\"
catalogs_path = base_path + "Catalogs\\"
documents_path = base_path + "Documents\\"
reports_path = base_path + "Reports\\"
config = base_path + "Configuration.xml"
actions = ["Чтение", "Добавление", "Изменение", "Удаление"]
prefix = "l_"
file_type = ".xml"
ext = "Ext\\"
file_rights_name = "Rights"
branch_file = base_path + "CommonAttributes\\Филиал.xml"
contractor_condition = "ТекущаяТаблица ГДЕ (ТекущаяТаблица.Филиал В (&ДоступныеФилиалы) ИЛИ ТекущаяТаблица.ЭтоГруппа " \
                       "или ТекущаяТаблица.ОтветственныйДилер в (&ДоступныеДилеры) или ТекущаяТаблица.Ссылка в (" \
                       "&ДоступныеДилеры)) "
rights_dic = {
    'ЧтениеCatalog': ["Read", "View", "InputByString"],
    'ДобавлениеCatalog': ["Read", "Insert", "View", "InteractiveInsert"],
    'ИзменениеCatalog': ["Read", "Update", "View", "Edit"],
    'УдалениеCatalog': ["Read", "Update", "Delete", "View", "Edit", "InteractiveDelete", "InteractiveSetDeletionMark",
                        "InteractiveClearDeletionMark", "InteractiveDeleteMarked"],
    'ИспользованиеReport': ["Use", "View"],
    'delete_sub_objects': ["Read", "Update"],
    'ЧтениеDocument': ["Read", "View"],
    'ДобавлениеDocument': ["Read", "Insert", "View", "InteractiveInsert", "Posting", "InteractivePosting"],
    'ИзменениеDocument': ["Read", "Update", "View", "Edit", "Posting", "UndoPosting", "InteractivePosting",
                          "InteractiveUndoPosting", "InteractivePostingRegular", "InteractiveChangeOfPosted"],
    'УдалениеDocument': ["Read", "Update", "Delete", "View", "Edit", "InteractiveDelete", "InteractiveSetDeletionMark",
                         "InteractiveClearDeletionMark", "InteractiveDeleteMarked", "Posting", "UndoPosting",
                         "InteractivePosting", "InteractiveUndoPosting", "InteractivePostingRegular",
                         "InteractiveChangeOfPosted"],
}
and_string = " И "
curr_table_string = "ТекущаяТаблица где "
constraints = {
    'Филиал': "ТекущаяТаблица.Филиал в (&ДоступныеФилиалы)",
    'Бренд': "ТекущаяТаблица.Бренд в (&ДоступныеБренды)",
    'Дилер': "ТекущаяТаблица.Дилер в (&ДоступныеДилеры)",
    'Склад': "ТекущаяТаблица.Склад в (&ДоступныеСклады)",
    'Бренды': "ТекущаяТаблица.Ссылка в (&ДоступныеБренды)",
    'Филиалы': "ТекущаяТаблица.Ссылка в (&ДоступныеФилиалы)",
    'Склады': "ТекущаяТаблица.Ссылка в (&ДоступныеСклады)",
    'Номенклатура': "ТекущаяТаблица.Номенклатура.Бренд в (&ДоступныеБренды)",
    'Номенклатуры': "ТекущаяТаблица.Ссылка.Бренд в (&ДоступныеБренды)"
}
where_string = "ГДЕ "
constraints_registers = {
    'Филиал': "Филиал В(&ДоступныеФилиалы)",
    'Бренд': " Бренд в (&ДоступныеБренды)",
    'Номенклатура': "Номенклатура.Бренд в (&ДоступныеБренды)",
    'Дилер': "Дилер В (&ДоступныеДилеры)",
    'Склад': "Склад в (&ДоступныеСклады)"
}

constraints_fields = ["Филиал", "Филиалы", "Бренд", "Бренды", "Дилер", "Склад", "Склады", "Номенклатура",
                      "Номенклатуры"]


def find_owners(path):
    owners_dic = {}

    for file in glob.iglob(path + "*.xml"):
        tree = xml.parse(file)
        root = tree.getroot()
        catalog_elem = root.find("{http://v8.1c.ru/8.3/MDClasses}Catalog")
        props = catalog_elem.find("{http://v8.1c.ru/8.3/MDClasses}Properties")
        owners_elem = props.find("{http://v8.1c.ru/8.3/MDClasses}Owners")
        for item in owners_elem.iter():
            if item.tag.rpartition("}")[2] != "Item":
                continue

            if item.text.rpartition(".")[0] == "Catalog":
                owner = item.text.rpartition(".")[2]
                if owner not in owners_dic:
                    owners_dic[owner] = []
                sub_objs = owners_dic[owner]
                sub_objs.append("Catalog" + "." + os.path.basename(file).rpartition(".")[0])
                owners_dic[owner] = sub_objs

    return owners_dic


def register_all_namespaces(filename):
    namespaces = dict([node for _, node in xml.iterparse(filename, events=['start-ns'])])

    for ns in namespaces:
        xml.register_namespace(ns, namespaces[ns])

    xml.register_namespace("app", "http://v8.1c.ru/8.2/managed-application/core")


def collect_uids():
    id_list = []
    for file in glob.iglob(base_path + "/**/*.xml", recursive=True):
        tree = xml.parse(file)
        root = tree.getroot()
        for elem in root.iter():
            if elem.attrib.get("uuid"):
                id_list.append(elem.attrib.get("uuid"))
    return id_list


def generate_uuid(uids):
    uid = uuid.uuid1()

    while uid in uids:  # шанс конечно очень маленький что окажется не уникальным, но всё же
        uid = uuid.uuid1()

    return str(uid)


def change_case(str):
    s1 = re.sub('(.)([А-Я][а-я]+)', r'\1 \2', str)
    return re.sub('([а-я0-9])([А-Я])', r'\1 \2', s1).lower()


def create_base_role_file(uids, action, meta_name):
    role_name = prefix + action + meta_name

    root = xml.Element("MetaDataObject")
    root.set("xmlns", "http://v8.1c.ru/8.3/MDClasses")
    root.set("xmlns:app", "http://v8.1c.ru/8.2/managed-application/core")
    root.set("xmlns:cfg", "http://v8.1c.ru/8.1/data/enterprise/current-config")
    root.set("xmlns:cmi", "http://v8.1c.ru/8.2/managed-application/cmi")
    root.set("xmlns:ent", "http://v8.1c.ru/8.1/data/enterprise")
    root.set("xmlns:lf", "http://v8.1c.ru/8.2/managed-application/logform")
    root.set("xmlns:style", "http://v8.1c.ru/8.1/data/ui/style")
    root.set("xmlns:sys", "http://v8.1c.ru/8.1/data/ui/fonts/system")
    root.set("xmlns:v8", "http://v8.1c.ru/8.1/data/core")
    root.set("xmlns:v8ui", "http://v8.1c.ru/8.1/data/ui")
    root.set("xmlns:web", "http://v8.1c.ru/8.1/data/ui/colors/web")
    root.set("xmlns:win", "http://v8.1c.ru/8.1/data/ui/colors/windows")
    root.set("xmlns:xen", "http://v8.1c.ru/8.3/xcf/enums")
    root.set("xmlns:xpr", "http://v8.1c.ru/8.3/xcf/predef")
    root.set("xmlns:xr", "http://v8.1c.ru/8.3/xcf/readable")
    root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("version", "2.7")

    role_elem = xml.Element("Role")
    role_elem.set("uuid", generate_uuid(uids))
    props = xml.Element("Properties")
    name = xml.SubElement(props, "Name")
    name.text = role_name
    synonym = xml.Element("Synonym")
    v8item = xml.Element("v8:item")
    lang = xml.SubElement(v8item, "v8:lang")
    lang.text = "ru"
    content = xml.SubElement(v8item, "v8:content")
    content.text = action + " " + change_case(meta_name)
    synonym.append(v8item)
    props.append(synonym)
    comment = xml.SubElement(props, "Comment")
    comment.text = "Создано скриптом"
    role_elem.append(props)
    root.append(role_elem)

    tree = xml.ElementTree(root)
    with open(roles_path + prefix + action + meta_name + file_type, 'wb') as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)


def create_rights_file(action, meta_name, objects, rights, fields, pre_condition):
    role_name = prefix + action + meta_name
    folders_name = role_name + "\\" + ext
    root = xml.Element("Rights")
    root.set("xmlns", "http://v8.1c.ru/8.2/roles")
    root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:type", "Rights")
    root.set("version", "2.7")
    set_for_new_obj = xml.SubElement(root, "setForNewObjects")
    set_for_new_obj.text = "false"
    set_for_attrib = xml.SubElement(root, "setForAttributesByDefault")
    set_for_attrib.text = "true"
    indep_righ_of_ch_obj = xml.SubElement(root, "independentRightsOfChildObjects")
    indep_righ_of_ch_obj.text = "false"
    for obj in objects:
        obj_elem = xml.Element("object")
        obj_name = xml.SubElement(obj_elem, "name")
        obj_name.text = obj
        for right in rights:
            right_elem = xml.Element("right")
            right_name = xml.SubElement(right_elem, "name")
            right_name.text = right
            right_value = xml.SubElement(right_elem, "value")
            right_value.text = "true"

            if (right == "Read") & (len(fields) > 0):
                restriction = xml.Element("restrictionByCondition")
                condition = xml.SubElement(restriction, "condition")
                text = pre_condition

                for field in fields:
                    condition_text = constraints[field]
                    if text == pre_condition:
                        text = text + condition_text
                    else:
                        text = text + and_string + condition_text

                if meta_name == "Контрагенты":
                    text = contractor_condition
                elif meta_name == "Номенклатура":
                    text = "ТекущаяТаблица где ТекущаяТаблица.Бренд в (&ДоступныеБренды) ИЛИ ТекущаяТаблица.ЭтоГруппа"
                condition.text = text

                right_elem.append(restriction)

            obj_elem.append(right_elem)
        root.append(obj_elem)

    if (meta_name in owners) & (action == "Удаление"):
        for sub_obj in owners[meta_name]:
            sub_meta_name = sub_obj.rpartition(".")[2]
            sub_fields = collect_fields(catalogs_path + sub_meta_name + ".xml", sub_meta_name, "Catalog")
            obj_elem = xml.Element("object")
            obj_name = xml.SubElement(obj_elem, "name")
            obj_name.text = sub_obj
            for right in rights_dic["delete_sub_objects"]:
                right_elem = xml.Element("right")
                right_name = xml.SubElement(right_elem, "name")
                right_name.text = right
                right_value = xml.SubElement(right_elem, "value")
                right_value.text = "true"

                # if (right == "Read") & (len(sub_fields) > 0):
                #     restriction = xml.Element("restrictionByCondition")
                #     condition = xml.SubElement(restriction, "condition")
                #     text = pre_condition
                #
                #     for field in sub_fields:
                #         condition_text = constraints[field]
                #         if text == pre_condition:
                #             text = text + condition_text
                #         else:
                #             text = text + and_string + condition_text
                #
                #     if sub_meta_name == "Контрагенты":
                #         text = contractor_condition
                #     condition.text = text
                #
                #     right_elem.append(restriction)
                obj_elem.append(right_elem)
            root.append(obj_elem)
    os.makedirs(roles_path + folders_name)
    tree = xml.ElementTree(root)
    with open(roles_path + folders_name + file_rights_name + file_type, "wb"):
        tree.write(roles_path + folders_name + file_rights_name + file_type, xml_declaration=True, encoding='utf-8')


def add_new_role(action, meta_name):
    register_all_namespaces(config)
    tree = xml.parse(config)
    root = tree.getroot()
    # root.set("xmlns", "http://v8.1c.ru/8.3/MDClasses")
    root.set("xmlns:app", "http://v8.1c.ru/8.2/managed-application/core")
    root.set("xmlns:cfg", "http://v8.1c.ru/8.1/data/enterprise/current-config")
    root.set("xmlns:cmi", "http://v8.1c.ru/8.2/managed-application/cmi")
    root.set("xmlns:ent", "http://v8.1c.ru/8.1/data/enterprise")
    root.set("xmlns:lf", "http://v8.1c.ru/8.2/managed-application/logform")
    root.set("xmlns:style", "http://v8.1c.ru/8.1/data/ui/style")
    root.set("xmlns:sys", "http://v8.1c.ru/8.1/data/ui/fonts/system")
    # root.set("xmlns:v8", "http://v8.1c.ru/8.1/data/core")
    # root.set("xmlns:v8ui", "http://v8.1c.ru/8.1/data/ui")
    root.set("xmlns:web", "http://v8.1c.ru/8.1/data/ui/colors/web")
    root.set("xmlns:win", "http://v8.1c.ru/8.1/data/ui/colors/windows")
    root.set("xmlns:xen", "http://v8.1c.ru/8.3/xcf/enums")
    root.set("xmlns:xpr", "http://v8.1c.ru/8.3/xcf/predef")
    # root.set("xmlns:xr", "http://v8.1c.ru/8.3/xcf/readable")
    root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema")
    # root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("version", "2.7")
    configuration = root.find("{http://v8.1c.ru/8.3/MDClasses}Configuration")
    child_objects = configuration.find("{http://v8.1c.ru/8.3/MDClasses}ChildObjects")
    role = xml.SubElement(child_objects, "Role")
    role.text = prefix + action + meta_name
    tree.write(config, encoding='utf-8', xml_declaration=True)


def collect_fields(file, meta_name, type):
    fields = []
    tree = xml.parse(file)
    root = tree.getroot()
    catalog = root.find("{http://v8.1c.ru/8.3/MDClasses}" + type)
    if meta_name in constraints_fields:
        fields.append(meta_name)
    ch_obj = catalog.find("{http://v8.1c.ru/8.3/MDClasses}ChildObjects")
    for elem in ch_obj.iter():
        tag_name = elem.tag.rpartition("}")[2]
        if tag_name == "TabularSection":
            return fields

        if tag_name == "Attribute":

            props = elem.find("{http://v8.1c.ru/8.3/MDClasses}Properties")
            field_name = props.find("{http://v8.1c.ru/8.3/MDClasses}Name")
            if field_name.text in constraints_fields:
                if (meta_name != "ЗаказПокупателя") & (field_name.text != "Бренд"):  # Исключение для заказа покупателя,
                    # так как бренд там темерь не заполняется
                    if field_name.text not in fields:
                        fields.append(field_name.text)

    if "Филиал" not in fields:
        if meta_name in branch_in_use_list:
            if meta_name != "ДоговорыКонтрагентов":  # исключение для договоров так как филиал там не заполнен,
                # хотя надо бы реквизит удалить
                fields.append("Филиал")

    return fields


def branch_in_use():
    meta_objects = []

    tree = xml.parse(branch_file)
    root = tree.getroot()

    comm_attrib = root.find("{http://v8.1c.ru/8.3/MDClasses}CommonAttribute")
    props = comm_attrib.find("{http://v8.1c.ru/8.3/MDClasses}Properties")
    content = props.find("{http://v8.1c.ru/8.3/MDClasses}Content")
    items = content.findall("{http://v8.1c.ru/8.3/xcf/readable}Item")

    for item in items:
        use = item.find("{http://v8.1c.ru/8.3/xcf/readable}Use")
        if use.text == "Use":
            meta_data = item.find("{http://v8.1c.ru/8.3/xcf/readable}Metadata")
            meta_name = meta_data.text.rpartition(".")[2]
            meta_objects.append(meta_name)

    return meta_objects


def create_roles(file, actions, type):
    meta_name = os.path.basename(file).rpartition(".")[0]
    objs = [type + "." + meta_name]
    if meta_name == "ОсновныеСредства":
        if type == "Catalog":
            meta_name = meta_name + "Справочник"
        elif type == "Register":
            meta_name = meta_name + "Отчёт"
        else:
            meta_name = meta_name + "Документ"

    fields = collect_fields(file, meta_name, type)

    for action in actions:
        create_base_role_file(uids, action, meta_name)
        create_rights_file(action, meta_name, objs, rights_dic[action + type], fields, curr_table_string)
        add_new_role(action, meta_name)


if __name__ == '__main__':
    owners = find_owners(catalogs_path)
    uids = collect_uids()
    branch_in_use_list = branch_in_use()
    for file in glob.iglob(catalogs_path + "/*.xml"):
        create_roles(file, actions, "Catalog")

    for file in glob.iglob(documents_path + "/*.xml"):
        create_roles(file, actions, "Document")

    for file in glob.iglob((reports_path + "/*.xml")):
        create_roles(file, ["Использование"], "Report")

    # fields = collect_fields("C:\\dmsClean\\Catalogs\\ДоговорыКонтрагентов.xml", "ДоговорыКонтрагентов")
    # fields.append("Филиал")
    # create_base_role_file(uids, "Чтение", "ДоговорыКонтрагентов")
    # create_rights_file("Чтение", "ДоговорыКонтрагентов", ["Catalog.ДоговорыКонтрагентов"], ["Read", "View"], fields,
    #                    curr_table_string)
    # add_new_role("Чтение", "ДоговорыКонтрагентов")
    # print(collect_fields("C:\\dmsScripted\\Documents\\ЗаказПокупателя.xml", "ЗаказПокупателя", "Document"))
