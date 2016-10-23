import { combineReducers } from 'redux';
import _ from 'underscore';
import * as consts from '../constants/TermsTree';


class Tree {
  constructor(json) {
    this.json = json;
    this.root = this.json2tree(json);
  }

  json2tree(json, parent = false) {
    if (parent == false) {
      parent = new Item();
    }
    for (let i = 0; i < json.length; i++) {
      let child = json[i];
      let options = {
        'id': child.id,
        'name': child.name,
        'slug': child.slug,
        'short_description': child.short_description,
        'semantic_rule': child.semantic_rule,
        'specification_mode': child.specification_mode,
        'structure': child.structure,
        'is_leaf': child.is_leaf,
        'parent': parent,
      };
      let item = new Item(options);
      item.children = this.json2tree(child.children, item).children;
      parent.children.push(item);
    }
    return parent;
  }
}


class Item {
  constructor(options) {
    let defaults = {
      'id': -1,
      'name': '',
      'slug': '',
      'short_description': '',
      'semantic_rule': consts.SEMANTIC_RULE_AND,
      'specification_mode': consts.STANDARD_SPECIFICATION,
      'structure': consts.STRUCTURE_NULL,
      'is_leaf': true,
      'parent': false,
      'children': []
    }
    Object.assign(this, defaults);
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
    if (!_.isUndefined(parent.getChildren)) {
      let siblings = parent.getChildren();
      return siblings.filter(item => item.id != this.id);
    } else {
      return [];
    }
  }

  isLimbDescendant() {
    if (this.structure == consts.STRUCTURE_LIMB)
      return true;
    let parent = this.getParent();
    if (parent != false) {
      if (parent.structure == consts.STRUCTURE_LIMB)
        return true;
      return parent.isLimbDescendant();
    }
    return false;
  }

  isLimbAndLeaf() {
    return (
      this.structure == consts.STRUCTURE_LIMB && this.is_leaf
    )
  }
}

class Tagged extends Array {
  constructor() {
    super();
  }
}

class Requested extends Array {
  constructor() {
    super();
  }
}

class ExpandedChildren extends Array {
  constructor() {
    super();
  }
}

class ExpandedInfo extends Array {
  constructor() {
    super();
  }
}

const initialState = {};

function tree(state = initialState, action) {
  switch (action.type) {
    case consts.GET_TERMS_TREE:
      return new Tree(action.json);
    default:
      return state;
  }
}

function tagged(state = initialState, action) {
  switch (action.type) {
    case consts.TOGGLE:
      return new Tagged();
    default:
      return state;
  }
}

const terms = combineReducers({
    tree: tree,
    tagged: tagged
})

export default terms;

