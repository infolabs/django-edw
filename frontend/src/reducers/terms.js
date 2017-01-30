import { combineReducers } from 'redux';
import * as consts from 'constants/TermsTree';

/* Tree Data Structures */

class Tree {
  constructor(json) {
    this.json = json;
    this.hash = {};
    this.root = this.json2tree(json);
    this.loading = false;
  }

  merge(json) {
    for (const child of json) {
      const hashed = this.hash[child.id];
      if(child.children.length &&
         hashed && !hashed.children.length) {
        this.hash[child.id].children = this.json2tree(child.children, this.hash[child.id]).children;
      }
      this.merge(child.children);
    }
    this.loading = false;
    return Object.assign(new Tree([]), this);
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
        'view_class': child.view_class,
        'semantic_rule': child.semantic_rule,
        'specification_mode': child.specification_mode,
        'structure': child.structure,
        'is_leaf': child.is_leaf,
        'parent': parent
      };
      let item = new Item(options);
      this.hash[item.id] = item;
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
      'url': '',
      'short_description': '',
      'description': '',
      'view_class': '',
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

  isVisible() {
    return this.parent && this.isLimbDescendant() && !this.isLimbAndLeaf();
  }

}

/* Tagged Data Structures */

class TaggedItems {

  constructor(json = []) {
    this.array = [];
    this.cache = {};
    this.json2tagged(json);
    this.init = true;
  }

  json2tagged(json = []) {
    for (const child of json) {
      if (child.structure != null) {
        const pk = parseInt(child.id);
        this[pk] = true;
        this.cache[pk] = true;
        let index = this.array.indexOf(pk);
        if (index < 0) {
          this.array.push(pk);
        }
      }
      this.json2tagged(child.children);
    }
  }

  json2cache(json = []) {
    for (const child of json) {
      const pk = parseInt(child.id);
      if (child.structure != null) {
        this.cache[pk] = true;
      }
      this.json2tagged(child.children);
    }
  }

  isInCache(arr) {
    let ret = true;
    for (const pk of arr) {
      if (!this.cache[parseInt(pk)]) {
        ret = false;
        break;
      }
    }
    return ret;
  }

  setCache(json) {
    this.json2cache(json);
    return Object.assign(new TaggedItems(), this);
  }

  static isTaggable(item) {
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
    }
    this.init = false;
    return Object.assign(new TaggedItems(), this);
  }

  resetBranch(item) {
    this.untag(item);
    return Object.assign(new TaggedItems(), this);
  }

  resetItem(item) {
    for (const child of item.children) {
      this.untag(child);
    }
    return Object.assign(new TaggedItems(), this);
  }

  tag(item) {
    this[item.id] = true;
    if (item.parent && item.parent.semantic_rule == consts.SEMANTIC_RULE_OR)
      this.untagSiblings(item);
    let index = this.array.indexOf(item.id);
    if (index < 0 && item.id > -1) {
      this.array.push(item.id);
    }
    item.parent && this.tag(item.parent);
  }

  untag(item) {
    this[item.id] = false;
    let index = this.array.indexOf(item.id);
    if (index > -1) {
      this.array.splice(index, 1);
    }
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

  isORXORTagged(item) {
    let ret = false;
    if (item.parent && item.parent.parent &&
        item.parent.parent.semantic_rule &&
        this.constructor.isTaggable(item)) {
      ret = this.isAnyTagged(item.siblings);
      if (!ret) {
        ret = this.isORXORTagged(item.parent);
      }
    }
    return ret;
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

/* Real and Potetnrial items */

class RealPotentialItems {
  constructor(json) {
    const meta = json && json.results && json.results.meta,
      pots = meta && meta.potential_terms_ids || [],
      rils = meta && meta.real_terms_ids || [];
    this.has_metadata = !!meta;
    this.pots = {};
    this.rils = {};
    if (!this.has_metadata)
      return;
    for (let pot of pots)
      this.pots[pot] = true;
    for (let ril of rils)
      this.rils[ril] = true;
  }
}


function tree(state = new Tree([]), action) {
  switch (action.type) {
    case consts.LOAD_TREE:
      return new Tree(action.json);
    case consts.RELOAD_TREE:
      return state.merge(action.json);
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
    case consts.LOAD_TREE:
      return new TaggedItems(action.json);
    case consts.RELOAD_TREE:
      return state.setCache(action.json);
    case consts.TOGGLE_ITEM:
      return state.toggle(action.term);
    case consts.RESET_ITEM:
      return state.resetItem(action.term);
    case consts.RESET_BRANCH:
      return state.resetBranch(action.term);
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


function realPotential(state = new RealPotentialItems({}), action) {
  switch (action.type) {
    case consts.LOAD_ENTITIES:
      return new RealPotentialItems(action.json);
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
    real_potential: realPotential,
})


export default terms;

