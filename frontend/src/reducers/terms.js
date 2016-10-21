import { GET_TERMS_TREE, 
         TOGGLE,
         RESET_ITEM,
         SEMANTIC_RULE_OR,
         // SEMANTIC_RULE_XOR,
         SEMANTIC_RULE_AND,
         STANDARD_SPECIFICATION,
         EXPANDED_SPECIFICATION,
         REDUCED_SPECIFICATION,
         // STRUCTURE_TRUNK,
         STRUCTURE_LIMB,
         // STRUCTURE_BRANCH,
         // STRUCTURE_NULL,
         } from '../constants/TermsTree';
import { getTermsTree } from '../actions/TermsTreeActions';


class TermTreeModel {

  constructor(json, selected=[], tagged=[]) {
    this.json = json;
    this.hash_table = {};
    this.tagged = tagged; // todo: selected vs tagged?
    this.selected = selected;
    this.tree = this.json2tree(json, false, this);
  }

  json2tree(json, parent = false, self) {
    let tree = [];
    json.forEach(function (child) {
      let item = new TermTreeItemModel(
        {"id": child.id,
         "name": child.name,
         "slug": child.slug,
         "short_description": child.short_description,
         "tagged": (self.tagged.indexOf(child.id) > -1),
         "selected": (self.selected.indexOf(child.id) > -1),
         "semantic_rule": child.semantic_rule,
         "specification_mode": child.specification_mode,
         "structure": child.structure,
         "is_leaf": child.is_leaf,
         "parent": parent, // todo: <-- ', ' not python
        }
      );

      item.children = self.json2tree(child.children, item, self);
      self.hash_table[item.id] = item;

      // fix for root elements with unloaded children
      if (item.specification_mode == STANDARD_SPECIFICATION
          && parent == false && !item.selected && !item.children.length) {
        item.tagged = true;
      }

      tree.push(item);
    });
    return tree;
  }

  toggle(item_id = -1) {
    let tree = this.tree;
    if (tree && tree.length > 0 && item_id && item_id > 0) {
      let item = this.hash_table[item_id];
      if(item) {
        item.toggle();
        if (!item.children.length && this.selected.indexOf(item_id) == -1)
          this.selected.push(item_id);
        this.tagged = this.taggedIds(tree);
      }
    }

    return tree;
  }

  resetItem(item_id = -1) {
    let tree = this.tree;
    if (tree && tree.length > 0 && item_id && item_id > 0) {
      let item = this.hash_table[item_id];
      if(item)
        item.untag();
    }
    return tree;
  }

  taggedIds(tree = []) {
    let ids = [];
    for (let i = 0; i < tree.length; i++) {
      let child = tree[i];
      if (child.tagged)
        ids.push(child.id);
      ids = [...ids, ...this.taggedIds(child.getChildren())];
    }
    return ids;
  }
}

class TermTreeItemModel {

  constructor(options) {
    this.id = -1;
    this.name = '';
    this.slug = '';
    this.tagged = false; // tagged by user
    this.selected = false; // selected by server
    this.semantic_rule = SEMANTIC_RULE_AND;
    this.specification_mode = STANDARD_SPECIFICATION;
    this.structure = false;
    this.is_leaf = true;
    this.short_description = '';
    this.currentState = 'ex-state-default';
    this.view_class = '';
    this.description = '';
    this.parent = false;
    this.children = [];


    Object.assign(this, options);

  }

  getParent() {
    return this.parent;
  }

  getChildren() {
    return this.children;
  }

  getSiblings() {
    let parent = this.getParent();
    if (typeof parent.getChildren !== 'undefined' ) {
      let siblings = parent.getChildren();
      return siblings.filter(item => item.id != this.id);
    } else {
      return [];
    }
  }

  getLevel() {
    if ( typeof this._levelCache === 'undefined' ) {
      let parent = this.getParent();
      this._levelCache = (parent) ? parent.getLevel() + 1 : 0;
    }
    return this._levelCache;
  }

  areChildrenTagged() {
    let children = this.getChildren();
    for (let i = 0; i < children.length; i++) {
      let child = children[i];
      if (child.tagged)
        return true;
    }
    return false;
  }

  toggle() {
    this.tagged = !this.tagged;
    this.toggle_tree();
  }

  toggle_tree() {
    if (this.tagged) {
      if (this.parent.semantic_rule == SEMANTIC_RULE_OR) {
        this.getSiblings().forEach(function (item) {
            item.untag();
        });
      }
    } else {
      this.untag();
    }
  }

  untag() {
    this.tagged = false;
    this.getChildren().forEach(function (child) {
      child.untag();
    });
  }

  untagChildren() {
    this.getChildren().forEach(function (child) {
      child.untag();
    });
  }

  unsetChildren() {
    this.getChildren().forEach(function (child) {
      child.tagged = false;
    });
  }

  isLimbLine() {
    if (this.structure == STRUCTURE_LIMB)
      return true;
    let parent = this.getParent();
    if (parent) {
      if (parent.structure == STRUCTURE_LIMB)
        return true;
      return parent.isLimbLine();
    }
    return false;
  }

  isExpanded() {
    let mode = this.specification_mode;
    if (mode == STANDARD_SPECIFICATION && this.structure == STRUCTURE_LIMB && !this.tagged) {
      return true;
    }
    if (mode == STANDARD_SPECIFICATION && this.structure != STRUCTURE_LIMB && this.tagged) {
      return true;
    }
    if (mode == EXPANDED_SPECIFICATION && !this.tagged) {
      return true;
    }
    if (mode == REDUCED_SPECIFICATION && this.tagged) {
      return true;
    }
    return false;
  }
}


const initialState = {};

export default function terms(state = initialState, action) {
  switch (action.type) {

  case GET_TERMS_TREE:
    return {
      terms_tree: new TermTreeModel(action.json, action.selected, action.tagged),
      do_request: false,
    };

  case TOGGLE:
    let tree_toggle = {tree: [], selected: [], tagged: []},
      do_request_toggle = true;
    if (state.terms_tree) {
      tree_toggle = state.terms_tree;

      do_request_toggle = false;
      // check if we need to send server request for new data:
      let old_selected = tree_toggle.selected.slice();
      tree_toggle.toggle(action.term.id);
      let new_selected = tree_toggle.selected;
      if (old_selected.toString() != new_selected.toString())
        do_request_toggle = true;

    }
    return {
      terms_tree: tree_toggle,
      do_request: do_request_toggle,
    };

  case RESET_ITEM:
    let tree_reset = state.terms_tree;
    tree_reset.resetItem(action.term.id);
    return {
      terms_tree: tree_reset,
      do_request: false,
    };

  default:
    return state;
  }
}


/* Набросал структуру данных для редусера */

/*
{

    tree: { // Объект 'tree' заполняется после получения данных с сервера и не меняется непосредственно пользователем,
            // поэтому редусер после клика пользователя может просто копировать ссылку на текущий обьект
            // результат будет pure, новый экземпляр создается только после ответа с сервера

        'root': { // Виртуалный корневой узел создается после парсинга результата, точка входа tree['root'],
                  // узлы также содержат логику рекурсивного описания работы модели например: переключение узла (toggle) selected_state['term_id'],
                        // каскадный сброс или установка selected_state
            parent: null,
            children: [
              <указатель на term_1>,
              ...
        },
        1: {
            id: 1,
            parent: <указатель на parent_term>, // используется для оптимизации работы функционала c selected_state,
                                                // null если верхний уровень
            name: 'term 1 blabla',
            view_class: '',
            semantic_rule: 10,
            structure: null, // trunk, limb, branch или null
            short_description: 'some text', // на акшон showDescription(<id>)
                                            // если short_description != '' && descriptions[<term_id_1>] == ''
                                            // запрос на сервер detail нода и врезультате вызов setDescription(<id>, <description>)
            children: [
              <указатель на children_term_1>,
              <указатель на children_term_2>,
              ...
            ]

        },
        <children_term_1> : {
           ...
        }

    },


    // для акшонов типа toggle('term_id') или unsetChildren('term_id')
    selected_state: { //  Содержит состояние выбранных терминов, изначально заполняется через
              // _.map(tree, (key, obj) => { return (obj.structure != null )} )
                //  меняется акшонами, нужно всегда создавать новый экземпляр
        '1': true,
        <children_term_1>: false,
        <children_term_2>: true,
        ...

    },

    // для акшонов типа showDescription('term_id')
    descriptions_state: {
      show: <id>, // ID нода дескриптион которого отображается или null вслучае когда не отображаем дескриптион
      descriptions: {
        1: 'description1',
        <children_term_2>: 'description2',
          ...
      }
    },

    // для акшонов типа excpand('term_id') и collapce('term_id')
    // изначально заполняется через что-то типа
    // _.map(tree, (key, obj) => { return (obj.structure != null && obj.specification_mode != REDUCED_SPECIFICATION )} )
    collapsed_state: {
      1: true,
      <children_term_2>: false, ...
      }

    //

    // далее добавятся сткруктуры для potential_terms и real_terms...


}
*/