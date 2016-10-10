import { GET_TERMS_TREE, 
         TOGGLE,
         TAG_TREE,
         SEMANTIC_RULE_OR,
         SEMANTIC_RULE_XOR,
         SEMANTIC_RULE_AND,
         STANDARD_SPECIFICATION,
         } from '../constants/TermsTree';
import { getTermsTree } from '../actions/TermsTreeActions';


class TermTreeModel {

  constructor(json, selected = []) {
    this.json = json;
    this.hash_table = {};
    this.selected = selected;
    this.tree = this.json2tree(json, {}, this);
  }

  json2tree(json, parent = {}, self) {
    let tree = [];
    json.forEach(function (child) {
      let item = new TermTreeItemModel(
        {"id": child.id,
         "name": child.name,
         "slug": child.slug,
         "tagged": (self.selected.indexOf(child.id) > -1),
         "semantic_rule": child.semantic_rule,
         "is_leaf": child.is_leaf,
         "parent": parent,
        }
      );
      item.children = self.json2tree(child.children, item, self);
      self.hash_table[item.id] = item;
      tree.push(item);
    });
    return tree;
  }

  toggle(toggled_item_id = -1) {
    let tree = this.tree;
    if (tree && tree.length > 0 && toggled_item_id && toggled_item_id > 0) {
      let item = this.hash_table[toggled_item_id];
      if(item)
        item.toggle();
    }
    this.selected = this.taggedIds(tree);
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
    this.tagged = false;
    this.semantic_rule = SEMANTIC_RULE_AND;
    this.specification_mode = STANDARD_SPECIFICATION;
    this.is_leaf = true;
    this.short_description = '';
    this.currentState = 'ex-state-default';
    this.view_class = '';
    this.description = '';
    this.parent = {};
    this.children = {};

    //this.short_description = null; // todo: Яровому допилить в сериалайзер
    //this.branch = false; // Использовать `structure`
    //this.trunk = false; // --//-- НЕТ ТАКОГО ПОЛЯ

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

  isChildrenTagged() {
    if ( typeof this._isChildrenTaggedCache === 'undefined' ) {
      let children = this.getChildren();

      if (this.semantic_rule == SEMANTIC_RULE_XOR) {
        children.forEach(function (child) {
          return child.tagged && child.isChildrenTagged();
        });
      } else {
        children.forEach(function (child) {
          gthis._isChildrenTaggedCache = child.isChildrenTagged();
        });
      }
    }
    return this._isChildrenTaggedCache;
  }

  toggle() {
    this.tagged = !this.tagged;
    this.toggle_tree();
  }

  toggle_tree() {
    if (this.tagged) {
      if (this.semantic_rule == SEMANTIC_RULE_OR) {
        this.getSiblings().forEach(function (item) {
            item.unTag();
        });
      }
    } else {
      this.unTag();
    }
  }

  unTag() {
    this.tagged = false;
    this.getChildren().forEach(function (child) {
      child.unTag();
    });
  }

  unsetChildren() {
    this.getChildren().forEach(function (child) {
      child.tagged = false;
    });
  }
}


const initialState = {};

export default function terms(state = initialState, action) {
  switch (action.type) {

  case GET_TERMS_TREE:
    return {
      terms_tree: new TermTreeModel(action.json, action.selected),
      action_type: GET_TERMS_TREE,
    };

  case TOGGLE:
    let tree = {tree: [], selected: []};
    if (state.terms_tree) {
      tree = state.terms_tree;
      tree.toggle(action.term.id);
    }
    return {
      terms_tree: tree,
      action_type: TOGGLE
    };

  default:
    return state;
  }
}
