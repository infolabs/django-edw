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
