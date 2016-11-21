import { combineReducers } from 'redux';
import * as consts from '../constants/TermsTree';

/* Tree Data Structures */

class Tree {
  constructor(json) {
    this.json = json;
    this.hash = {};
    this.root = this.json2tree(json);
    this.loading = false;
  }

  json2tree(json, parent) {
    if ( !parent ) {
      parent = new Item();
    }

    for (const child of json) {
      let options = {
        'id': child.id,
        'name': child.name,
        'slug': child.slug,
        'url': child.url,
        'short_description': child.short_description,
        'semantic_rule': child.semantic_rule,
        'specification_mode': child.specification_mode,
        'structure': child.structure,
        'is_leaf': child.is_leaf,
        'parent': parent
      };
      let item = new Item(options);
      item.children = this.json2tree(child.children, item).children;
      parent.children.push(item);
    }
    this.hash[parent.id] = parent;
    return parent;
  }
}

class Item {
  constructor(options) {
    let defaults = {
      'id': -1,
      'name': '',
      'slug': '',
      'url': '',
      'short_description': '',
      'description': '',
      'semantic_rule': consts.SEMANTIC_RULE_AND,
      'specification_mode': consts.STANDARD_SPECIFICATION,
      'structure': consts.STRUCTURE_NULL,
      'is_leaf': true,
      'parent': null,
      'children': []
    }
    Object.assign(this, defaults, options);
  }

  get siblings() {
    return this.parent && this.parent.children ?
           this.parent.children.filter(item => item.id != this.id) : [];
  }

  isLimbDescendant() {
    let ret = this.structure == consts.STRUCTURE_LIMB
    if (!ret && this.parent) {
      ret = this.parent.structure == consts.STRUCTURE_LIMB
      if (!ret)
        ret = this.parent.isLimbDescendant();
    }
    return ret;
  }

  isLimbAndLeaf() {
    return this.structure == consts.STRUCTURE_LIMB && this.is_leaf;
  }

  isLimbOrAnd(item) {
    return ((this.parent &&
      this.parent.semantic_rule == consts.SEMANTIC_RULE_AND) ||
      this.structure == consts.STRUCTURE_LIMB)
  }
}

/* Tagged Data Structures */

class TaggedItems {

  constructor(json) {
    this.array = [];
  }

  isTaggable(item) {
    return !((item.parent &&
      item.parent.semantic_rule == consts.SEMANTIC_RULE_AND) ||
      item.structure == consts.STRUCTURE_LIMB)
  }

  toggle(item) {
    if (item.isLimbOrAnd())
      return this;

    if (this[item.id]) {
      this.untag(item);
    } else {
      this.tag(item);
      if (item.parent && item.parent.semantic_rule == consts.SEMANTIC_RULE_OR)
        this.untagSiblings(item);
    }
    return Object.assign(new TaggedItems(), this);
  }

  resetItem(item) {
    this.untag(item);
    return Object.assign(new TaggedItems(), this);
  }

  tag(item) {
    this[item.id] = true;
    let index = this.array.indexOf(item.id);
    index < 0 && item.id > -1 && this.array.push(item.id);
    item.parent && this.tag(item.parent);
  }

  untag(item) {
    this[item.id] = false;
    let index = this.array.indexOf(item.id);
    index > -1 && this.array.splice(index, 1);
    for (const child of item.children) {
      this.untag(child);
    }
  }

  untagSiblings(item) {
    for (const sib of item.siblings) {
      this.untag(sib);
    }
  }

  isAnyTagged(arr) {
    let self = this;
    return arr.some(el => !!self[el.id]);
  }

  isAncestorTagged(item) {
    if (item.structure != consts.STRUCTURE_LIMB && item.parent) {
      if (this[item.parent.id])
        return true;
      else
        return this.isAncestorTagged(item.parent);
    }
    return false;
  }
}

/* Expanded Data Structures */

class ExpandedItems {

  constructor(json) {
    this.json2items(json)
  }

  json2items(json) {
    for (const child of json) {
      let mode = child.specification_mode,
          is_standard = mode == consts.STANDARD_SPECIFICATION,
          is_expanded = mode == consts.EXPANDED_SPECIFICATION,
          is_leaf = child.is_leaf,
          is_limb = child.structure == consts.STRUCTURE_LIMB;

      this[child.id] = ((is_standard && is_limb && !is_leaf) || is_expanded);

      this.json2items(child.children);
    }
  }

  toggle(item) {
    if (!item.isLimbOrAnd())
      return this;
    this[item.id] = !this[item.id];
    return Object.assign(new ExpandedItems([]), this); 
  }

  reload(json) {
    return Object.assign(new ExpandedItems(json), this);
  }
}

/* Requested Data Structures */

class Requested {

  constructor() {
    this.array = [];
  }

  toggle(item) {
    if (this[item.id] != true &&
        !item.is_leaf &&
        !item.children.length) {
      this[item.id] = true;
      this.array.push(item.id);
      return Object.assign(new Requested(), this);
    } else {
      return this;
    }
  }
}

/* Expanded Info Structures */

class ExpandedInfoItems {
  show(item) {
    let ei = new ExpandedInfoItems();
    ei[item.id] = true;
    return ei;
  }

  hide(item) {
    return new ExpandedInfoItems();
  }
}

/* Entities */

class EtitiesManager {
  constructor(json, request_options) {
    this.objects = this.json2objects(json);
    this.meta = this.json2meta(json, request_options);
  }

  json2objects(json) {
    return json.results && json.results.objects || [];
  }

  json2meta(json, request_options) {
    let meta = json.results && json.results.meta || {};
    meta.count = json.count;
    meta.limit = json.limit;
    meta.offset = json.offset;
    meta.next = json.next;
    meta.previous = json.previous;
    meta.request_options = request_options;
    return meta;
  }
}

/* Dropdown */

class Dropdown {
  constructor(options) {
    let defaults = {
      'open': false,
      'request_var': '',
      'selected': '',
      'options': {}
    };
    Object.assign(this, defaults, options);
  }
}

class Dropdowns {
  constructor(json) {
    if (!(json && json.results))
      return;

    const data_mart = json.results.meta.data_mart,
          modes = data_mart.entities_ordering_modes;
    const ordering_options = {
      'request_var': 'ordering',
      'selected': modes[json.results.meta.ordering],
      'options': modes
    };
    this['ordering'] = new Dropdown(ordering_options);
    const limit = json.limit;
    const limit_options = {
      'request_var': 'limit',
      'selected': limit,
      'options': {limit: limit, 20: 20, 30: 30}
    };
    this['limits'] = new Dropdown(limit_options);
  }

  toggle(name) {
    let ret = this;
    let item = this[name];
    if (item) {
      if (!item.open) {
        for (let key in this)
          this[key].open = false;
        item.open = true;
      } else {
        item.open = false;
      }
      ret = Object.assign(new Dropdowns(), this);
    }
    return ret;
  }

  select(name, selected) {
    let ret = this;
    let item = this[name];
    if (item && item.selected != item.options[selected]) {
      item.open = false;
      item.selected = item.options[selected]
      ret = Object.assign(new Dropdowns(), this);
    }
    return ret;
  }

  hide_all() {
    for (let key in this)
      this[key].open = false;
    return Object.assign(new Dropdowns(), this);
  }
}


function tree(state = new Tree([]), action) {
  switch (action.type) {
    case consts.LOAD_TREE:
      return new Tree(action.json);
    case consts.RELOAD_TREE:
      return new Tree(action.json);
    case consts.NOTIFY_LOADING:
      return Object.assign(state, {'loading': true});
    default:
      return state;
  }
}

function details(state = {}, action) {
  switch (action.type) {
    case consts.LOAD_ITEM:
      const item = action.json;
      state[item.id] = item;
      return Object.assign({}, state);
    default:
      return state;
  }
}

function requested(state = new Requested(), action) {
  switch (action.type) {
    case consts.TOGGLE_ITEM:
      return state.toggle(action.term);
    default:
      return state;
  }
}

function tagged(state = new TaggedItems(), action) {
  switch (action.type) {
    case consts.TOGGLE_ITEM:
      return state.toggle(action.term);
    case consts.RESET_ITEM:
      return state.resetItem(action.term);
    default:
      return state;
  }
}

function expanded(state = new ExpandedItems([]), action) {
  switch (action.type) {
    case consts.LOAD_TREE:
      return new ExpandedItems(action.json);
    case consts.RELOAD_TREE:
      return state.reload(action.json);
    case consts.TOGGLE_ITEM:
      return state.toggle(action.term);
    default:
      return state;
  }
}

function infoExpanded(state = new ExpandedInfoItems(), action) {
  switch (action.type) {
    case consts.SHOW_INFO:
      return state.show(action.term);
    case consts.HIDE_INFO:
      return state.hide(action.term);
    default:
      return state;
  }
}

function infoExpanded(state = new ExpandedInfoItems(), action) {
  switch (action.type) {
    case consts.SHOW_INFO:
      return state.show(action.term);
    case consts.HIDE_INFO:
      return state.hide(action.term);
    default:
      return state;
  }
}

function entities(state = new EtitiesManager({}, {}), action) {
  switch (action.type) {
    case consts.LOAD_ENTITIES:
      return new EtitiesManager(action.json, action.request_options);
    default:
      return state;
  }
}

function dropdowns(state = new Dropdowns({}), action) {
  switch (action.type) {
    case consts.LOAD_ENTITIES:
      return new Dropdowns(action.json);
    case consts.TOGGLE_DROPDOWN:
      return state.toggle(action.dropdown_name);
    case consts.SELECT_DROPDOWN:
      return state.select(action.dropdown_name, action.selected);
    default:
      return state;
  }
}

const terms = combineReducers({
    tree: tree,
    details: details,
    requested: requested,
    tagged: tagged,
    expanded: expanded,
    info_expanded: infoExpanded,
    entities: entities,
    dropdowns: dropdowns
})

export default terms;

