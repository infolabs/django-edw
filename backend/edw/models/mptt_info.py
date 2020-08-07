# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import operator
from functools import reduce

from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from mptt.models import MPTTModel

from ..utils.hash_helpers import hash_unsorted_list
from ..utils.set_helpers import uniq


# ==============================================================================
# get_queryset_descendants
# ==============================================================================
def get_queryset_descendants(nodes, include_self=False, add_to_result=None):
    """
    RUS: Запрос к базе данных потомков. Если нет узлов,
    то возвращается пустой запрос.
    :param nodes: список узлов дерева, по которым необходимо отыскать потомков
    :param include_self: признак включения в результ исходного спичка узлов
    :param add_to_result: список ключей узлов которые необходимо дополнительно включить в результат
    :return: список узлов (QuerySet), отсортированный в порядке обхода дерева
    """
    if not nodes:
        # HACK: Emulate MPTTModel.objects.none(), because MPTTModel is abstract
        return EmptyQuerySet(MPTTModel)
    filters = []
    model_class = nodes[0].__class__

    if include_self:
        for n in nodes:
            if n.get_descendant_count():
                lft, rght = n.lft - 1, n.rght + 1
                filters.append(Q(tree_id=n.tree_id, lft__gt=lft, rght__lt=rght))
            else:
                filters.append(Q(pk=n.pk))
    else:
        for n in nodes:
            if n.get_descendant_count():
                lft, rght = n.lft, n.rght
                filters.append(Q(tree_id=n.tree_id, lft__gt=lft, rght__lt=rght))

    if add_to_result:
        if len(add_to_result) > 1:
            filters.append(Q(id__in=add_to_result))
        else:
            filters.append(Q(pk=add_to_result[0]))

    if filters:
        return model_class.objects.filter(reduce(operator.or_, filters))
    else:
        # HACK: Emulate model_class.objects.none()
        return model_class.objects.filter(id__isnull=True)


# ==============================================================================
# TermTreeInfo
# ==============================================================================
class TermTreeInfo(dict):
    """
    Helper class TermTreeInfo
    RUS: Вспомогательный класс
    """
    def __init__(self, root=None, *args, **kwargs):
        self.root = root
        super(TermTreeInfo, self).__init__(*args, **kwargs)

    def get_hash(self):
        """
        RUS: Получает список захэшированных неупорядоченных ключей,
        если они несозданы.
        """
        keys = [x.term.id for x in self.values() if x.is_leaf]
        return hash_unsorted_list(keys) if keys else ''

    def trim(self, ids=None):
        """
        RUS: Создает копию дерева. Расширяет его. Возвращает дерево, у которого удалены id лишних узлов.
        """
        tree = self.deepcopy()
        tree._expand()
        return tree.soft_trim(ids)

    def expand(self):
        """
        RUS: Добавляет в дерево ребенка к предкам.
        """
        tree = self.deepcopy()
        tree._expand()
        return tree

    def _expand(self):
        """
        RUS: Приватный метод, добавляет в дерево ребенка к предкам.
        """
        terms = [x.term for x in self.values() if x.is_leaf and not x.term.is_leaf_node()]
        if terms:
            for term in get_queryset_descendants(terms, include_self=False).filter(active=True):
                ancestor = self.get(term.parent_id)
                child = self[term.id] = TermInfo(term=term, is_leaf=True)
                ancestor.is_leaf = False
                ancestor.append(child)

    def soft_trim(self, ids=None):
        """
        RUS: Создает дерево, у которого удалены id лишних узлов.
        """
        if ids is None:
            ids = []
        # ids = uniq(ids)
        origin_root_term = self.root.term
        root = TermInfo(term=origin_root_term.__class__(semantic_rule=origin_root_term.semantic_rule,
                                                        active=origin_root_term.active))
        tree = TermTreeInfo(root)
        for pk in ids:
            src_node = self.get(pk)
            if src_node is not None:
                if pk not in tree:
                    node = tree[pk] = TermInfo(term=src_node.term, is_leaf=True)
                    src_ancestor = self.get(node.term.parent_id)
                    while src_ancestor:
                        ancestor = tree.get(src_ancestor.term.id)
                        if not ancestor:
                            node = tree[src_ancestor.term.id] = TermInfo(term=src_ancestor.term, is_leaf=False,
                                                                         children=[node])
                            if node.term.parent_id is None:
                                root.append(node)
                                break
                        else:
                            ancestor.is_leaf = False
                            ancestor.append(node)
                            break
                        src_ancestor = self.get(src_ancestor.term.parent_id)
                    else:
                        root.append(node)
        for ancestor in [x for x in tree.values() if x.is_leaf]:
            src_ancestor = self[ancestor.term.id]
            if len(src_ancestor):
                ancestor.is_leaf = False
                for src_node in src_ancestor:
                    ancestor.append(tree._copy_recursively(src_node))
        return tree

    def _copy_recursively(self, src_node):
        """
        RUS:  Вспомогательная функция, рекурсивно создает копию узла и его элементов.
        """
        node = self[src_node.term.id] = TermInfo(term=src_node.term, is_leaf=src_node.is_leaf)
        for src_child in src_node:
            node.append(self._copy_recursively(src_child))
        return node

    def deepcopy(self):
        """
        RUS: Создает копию дерева.
        """
        origin_root_term = self.root.term
        root = TermInfo(term=origin_root_term.__class__(semantic_rule=origin_root_term.semantic_rule,
                                                        active=origin_root_term.active))
        tree = TermTreeInfo(root)
        for src_node in self.root:
            root.append(tree._copy_recursively(src_node))
        return tree

    def _invert_recursively(self, node):
        """
        RUS:  Вспомогательная функция, рекурсивно формирует список (QuerySet) терминов инвенсии
        """
        child_ids = []
        child_not_leafs = []
        for child in node:
            child_ids.append(child.term.id)
            if not child.is_leaf:
                child_not_leafs.append(child)
        if node.term.semantic_rule == node.term.XOR_RULE:
            xor_children = node.term.get_children().order_by()
            xor_children = xor_children.exclude(id__in=child_ids) if len(child_ids) > 1 else xor_children.exclude(
                pk=child_ids[0])
            qss = [xor_children]
        else:
            qss = []
        for child in child_not_leafs:
            qss.extend(self._invert_recursively(child))
        return qss

    def invert(self):
        """
        RUS: Возвращает полный список (QuerySet) терминов "инверсии" дерева, отсортированный в порядке обхода дерева.
        Инверисией считаются термины не входящие в исходное дерево, но связанные с ним правилом "XOR"
        """
        qss = self._invert_recursively(self.root) if not self.root.is_leaf else []
        n = len(qss)
        if n:
            qs = qss.pop(0)
            if n > 1:
                qs = qs.union(*qss)
            result = get_queryset_descendants(qs, include_self=True)
        else:
            # HACK: Emulate TermModel.objects.none()
            result = self.root.term.__class__.objects.filter(id__isnull=True)
        return result

    def get_family(self):
        """
        RUS: Возвращает полный список (QuerySet) терминов дерева, отсортированный в порядке обхода дерева.
        """
        leafs = []
        not_leafs_ids = []
        for pk, node in self.items():
            if node.is_leaf:
                leafs.append(node.term)
            else:
                not_leafs_ids.append(pk)
        return get_queryset_descendants(leafs, include_self=True, add_to_result=not_leafs_ids)


# ==============================================================================
# TermInfo
# ==============================================================================
class TermInfo(list):
    """
    Class TermInfo
    Usage: tree = TermInfo.decompress(root_term, term_ids_set), result type is TermTreeInfo
    Для собирания дерева терминов TermTreeInfo.
    """
    def __init__(self, term=None, is_leaf=False, children=(), attrs=None):
        """
        RUS: Конструктор класса объекта.
        """
        super(TermInfo, self).__init__(children)
        self.attrs = attrs or {}
        self.term, self.is_leaf = term, is_leaf

    def get_children_dict(self):
        """
        RUS: Возвращает по id термина ребенка значение.
        """
        result = {}
        for child in self:
            result[child.term.id] = child
        return result

    def get_descendants_ids(self):
        """
        RUS: Возвращает список из id термина ребенка и id его предков.
        """
        result = []
        for child in self:
            result.append(child.term.id)
            result.extend(child.get_descendants_ids())
        return result

    @staticmethod
    def decompress(root_term, value):
        """
        RUS: Собирает дерево.
        """
        if value is None:
            value = []
        value = uniq(value)

        root = TermInfo(term=root_term)
        model_class = root_term.__class__

        tree = TermTreeInfo(root)
        for term in model_class.objects.filter(pk__in=value).select_related('parent'):
            if term.id not in tree:
                node = tree[term.id] = TermInfo(term=term, is_leaf=True)
                term_parent = term.parent
                if term_parent:
                    ancestor = tree.get(term_parent.id)
                    if ancestor is not None:
                        ancestor.is_leaf = False
                        ancestor.append(node)
                    else:
                        node = tree[term_parent.id] = TermInfo(term=term_parent, is_leaf=False, children=[node])
                        if term_parent.parent_id is not None:
                            for term_ancestor in term_parent.get_ancestors(ascending=True).exclude(pk__in=tree.keys()):
                                node = tree[term_ancestor.id] = TermInfo(term=term_ancestor, is_leaf=False,
                                                                         children=[node])
                            ancestor = tree.get(node.term.parent_id)
                            if ancestor is not None:
                                ancestor.is_leaf = False
                                ancestor.append(node)
                            else:
                                root.append(node)
                        else:
                            root.append(node)
                else:
                    root.append(node)

        return tree
