import { GET_TERMS_TREE, TOGGLE, TAG_TREE } from '../constants/RubricatorActionTypes';
import { getTermsTree } from '../actions/RubricatorActions';


class TermModel {

  constructor() {
    this.id = -1;
    this.name = '';
    this.slug = '';
    this.tagged = false;
    // Method must be "hierarchy", "facet" or "determinant"
    this.method = 'determinant';
    this.branch = false;
    this.trunk = false;
    this.has_extra = false;
    this.short_description = null;
    this.tags = null;
    this.description = null;
    this.currentState = 'ex-state-default';
    this.parent = {};
    this.children = [];
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

      if (this.method == 'determinant') {
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
      if (this.method == 'facet') {
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


function json2tree(json, parent = {}, selected = []) {
  let tree = [];
  json.forEach(function (child) {
    let item = new TermModel();
    item.id = child.id;
    item.name = child.name;
    item.slug = child.slug;
    if (selected.indexOf(item.id) > -1)
      item.tagged = true;
    switch (child.semantic_rule) {
      case 10:
        item.method = 'facet';
        break;
      case 20:
        item.method = 'determinant';
        break;
      case 30:
        item.method = 'hierarchy';
        break;
    }
    item.branch = child.is_leaf;
    item.trunk = !child.is_leaf;
    item.parent = parent;
    item.children = json2tree(child.children, item, selected);
    tree.push(item);
  });
  return tree;
}


function findItemById(tree, item_id) {
  for (let i = 0; i < tree.length; i++) {
    let child = tree[i],
        ret = -1;
    if (child.id == item_id)
      return child;
    else
      ret = findItemById(child.getChildren(), item_id);
    if (ret != -1)
      return ret;
  }
  return -1;
}


function toggleTree(tree = [], toggled_item_id = -1) {
  if (tree && tree.length > 0 && toggled_item_id && toggled_item_id > 0) {
    let item = findItemById(tree, toggled_item_id);
    if (item != -1) {
      item.toggle();
    }
  }
  return tree;
}

function taggedIds(tree = []) {
  let ids = [];
  for (let i = 0; i < tree.length; i++) {
    let child = tree[i];
    if (child.tagged)
      ids.push(child.id);
    ids = [...ids, ...taggedIds(child.getChildren())];
  }
  return ids;
}

const initialState = {};

export default function terms(state = initialState, action) {
  switch (action.type) {

  case GET_TERMS_TREE:
    let tree1 = json2tree([...action.json], {}, action.selected),
        tagged_ids1 = taggedIds(tree1);
    return {
      terms_tree: tree1,
      aux: 'get_tree',
      tagged_ids: tagged_ids1,
    };

  case TOGGLE:
    let tree2 = [...toggleTree(state.terms_tree, action.term.id)],
        tagged_ids2 = taggedIds(tree2);
    return {
      terms_tree: tree2,
      aux: 'toggle',
      tagged_ids: tagged_ids2,
    };

  default:
    return state;
  }
}
