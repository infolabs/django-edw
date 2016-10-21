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
        'children': this.json2tree(child, parent).children
      };
      parent.children.push(new Item(options));
    }
    return parent;
  }
}


class Item {
  constructor(options) {
    defaults = {
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
}


class RequestedState extends Array {
  constructor() {
    super();
  }
}

class ToggledState extends Array {
  constructor() {
    super();
  }
}

class ExpandedState extends Array {
  constructor() {
    super();
  }
}

class InfoState extends Array {
  constructor() {
    super();
  }
}
