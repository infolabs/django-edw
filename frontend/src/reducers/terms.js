import { combineReducers } from 'redux';
import * as termConsts from 'constants/TermsTree';
import * as entityConsts from 'constants/Entities';

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
      if (child.children.length && hashed && !hashed.children.length) {
        this.hash[child.id].children = this.json2tree(
          child.children, this.hash[child.id]).children;
      }
      this.merge(child.children);
    }
    this.loading = false;
    return Object.assign(new Tree([]), this);
  }

  // Строим тематическое дерево
  json2tree(json, parent) {
    if (!parent)
      parent = new Item();

    let n = 0;
    for (const child of json) {
      // increment selected children count
      (child.structure !== termConsts.STRUCTURE_NULL && n++);
      let options = {
        'id': child.id, // Идентификатор
        'name': child.name, // Наименование
        'slug': child.slug, // Слаг
        'url': child.url, // Адрес в API
        'short_description': child.short_description, // Краткое описание
        'view_class': child.view_class, // Класс представления
        'semantic_rule': child.semantic_rule, // Семантическое правило (OR, XOR, AND)
        'specification_mode': child.specification_mode, // Режим конкретизации (стандартный, расширенный, сокращенный)
        'structure': child.structure, // Точка входа: trunk - корневой термин в тематической модели(не выводим в интерфейсе), limb - корневой термин в фильтре интерфейса, brunch - структура термина при наличии потомка, null - потомков нет(При выборе термина перезапрос не делаем)
        'is_leaf': child.is_leaf, // Термин в структуре относительно потомков (true - есть потомки, false - нет потомков)
        'parent': parent, // Родитель
      };
      let item = new Item(options);
      this.hash[item.id] = item;
      item.children = this.json2tree(child.children, item).children;
      parent.children.push(item);
    }
    // fix tree node semantic rule to 'OR', in case when semantic rule is 'XOR', but
    // selected children count more than one
    if (parent.semantic_rule === termConsts.SEMANTIC_RULE_XOR && n > 1)
      parent.semantic_rule = termConsts.SEMANTIC_RULE_OR;

    return parent;
  }
}

class Item {
  constructor(options) {
    let defaults = {
      'id': null,
      'name': '',
      'slug': '',
      'url': '',
      'short_description': '',
      'description': '',
      'view_class': '',
      'semantic_rule': termConsts.SEMANTIC_RULE_AND,
      'specification_mode': termConsts.STANDARD_SPECIFICATION,
      'structure': termConsts.STRUCTURE_NULL,
      'is_leaf': true,
      'parent': null,
      'children': [],
    };
    Object.assign(this, defaults, options);
  }

  get siblings() {
    return this.parent && this.parent.children ?
           this.parent.children.filter(item => item.id !== this.id) : [];
  }

  isLimbDescendant() {
    let ret = this.structure === termConsts.STRUCTURE_LIMB;
    if (!ret && this.parent) {
      ret = this.parent.structure === termConsts.STRUCTURE_LIMB;
      if (!ret)
        ret = this.parent.isLimbDescendant();
    }
    return ret;
  }

  isLimbAndLeaf() {
    return this.structure === termConsts.STRUCTURE_LIMB && this.is_leaf;
  }

  isLimbOrAnd(item) {
    return ((this.parent &&
      this.parent.semantic_rule === termConsts.SEMANTIC_RULE_AND) ||
      this.structure === termConsts.STRUCTURE_LIMB);
  }

  isLimbOrAndLeaf(item) {
    return ((this.parent &&
      this.parent.semantic_rule === termConsts.SEMANTIC_RULE_AND && this.is_leaf) ||
      this.structure === termConsts.STRUCTURE_LIMB);
  }

  isVisible() {
    return (this.parent && this.isLimbDescendant() && !this.isLimbAndLeaf()
            && !(this.parent.semantic_rule === termConsts.SEMANTIC_RULE_AND && this.is_leaf));
  }
}

/* Tagged Data Structures */

class TaggedItems {

  constructor(json = []) {
    this.items = [];
    this.prevItems = [];
    this.cache = {};
    this.entities_ignore = true;

    this.json2tagged(json);
    this.json2cache(json);
  }

  createFromJson(json = []) {
    this.json2tagged(json);
    this.json2cache(json);
    return Object.assign(new TaggedItems(), this);
  }

  copy() {
    let ret = Object.assign(new TaggedItems(), this);
    ret.items = this.items.slice();
    return ret;
  }

  json2tagged(json = []) {
    for (const child of json) {
      if (child.structure != null) {
        const pk = parseInt(child.id, 10);
        this[pk] = true;
        let index = this.items.indexOf(pk);
        if (index < 0)
          this.items.push(pk);

      }
      this.json2tagged(child.children);
    }
  }

  json2cache(json = []) {
    for (const child of json) {
      // expanded specifications are always cached because they're always loaded
      if (child.structure != null ||
          child.specification_mode === termConsts.EXPANDED_SPECIFICATION) {
        const pk = parseInt(child.id, 10);
        this.cache[pk] = true;
      }
      this.json2cache(child.children);
    }
  }

  isInCache() {
    let ret = true;
    for (const pk of this.items) {
      if (!this.cache[parseInt(pk, 10)]) {
        ret = false;
        break;
      }
    }
    return ret;
  }

  setCache(json) {
    this.recache = true;
    this.json2cache(json);
    return Object.assign(new TaggedItems(), this);
  }

  static isTaggable(item) {
    return !item.isLimbOrAndLeaf();
  }

  toggle(item) {
    if (item.isLimbOrAndLeaf() ||
        item.isLimbOrAnd() && item.children.length)
      return this;

    let ret = this.copy();

    // no need to reload entities
    ret.entities_ignore = item.isLimbOrAnd() && !item.is_leaf;

    if (ret[item.id])
      ret.untag(item);
    else
      ret.tag(item);

    return ret;
  }

  resetBranch(item) {
    let ret = this.copy();
    ret.entities_ignore = false;
    ret.untag(item);
    return ret;
  }

  resetTerm(item) {
    let ret = this.copy();
    ret.entities_ignore = false;
    for (const child of item.children)
      ret.untag(child);

    return ret;
  }

  tag(item) {
    // ignore and
    if (item.parent && item.parent.semantic_rule !== termConsts.SEMANTIC_RULE_AND)
      this[item.id] = true;

    if (item.parent && item.parent.semantic_rule === termConsts.SEMANTIC_RULE_XOR)
      this.untagSiblings(item);

    let index = this.items.indexOf(item.id);
    if (index < 0 && item.id != null) {
    // if (index < 0 && item.id > -1) {
      this.items.push(item.id);
    }
    item.parent && this.tag(item.parent);
  }

  untag(item) {
    // ignore limb or and once tagged
    if (!item.isLimbOrAnd())
      this[item.id] = false;
    let index = this.items.indexOf(item.id);
    if (index > -1)
      this.items.splice(index, 1);

    for (const child of item.children)
      this.untag(child);

  }

  untagSiblings(item) {
    for (const sib of item.siblings)
      this.untag(sib);
  }

  isAnyTagged(arr) {
    // eslint-disable-next-line consistent-this
    let self = this;
    return arr.some(el => !!self[el.id]);
  }

  isAncestorTagged(item) {
    if (item.structure !== termConsts.STRUCTURE_LIMB && item.parent &&
        item.parent.semantic_rule !== termConsts.SEMANTIC_RULE_AND ) {
      if (this[item.parent.id])
        return true;
      else
        return this.isAncestorTagged(item.parent);
    }
    return false;
  }

  setPrevTagged() {
    this.prevItems = this.items;
    return this;
  }
}

/* Expanded Data Structures */

class ExpandedItems {

  constructor(json) {
    this.json2items(json);
  }

  json2items(json) {
    for (const child of json) {
      let mode = child.specification_mode,
          is_standard = mode === termConsts.STANDARD_SPECIFICATION,
          is_expanded = mode === termConsts.EXPANDED_SPECIFICATION,
          is_leaf = child.is_leaf,
          is_limb = child.structure === termConsts.STRUCTURE_LIMB;

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
    if (!this[item.id] &&
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


export function tree(state = new Tree([]), action) {
  switch (action.type) {
    case termConsts.LOAD_TERMS_TREE:
      return new Tree(action.json);
    case termConsts.RELOAD_TERMS_TREE:
      return state.merge(action.json);
    case termConsts.NOTIFY_LOADING_TERMS:
      return Object.assign(state, {'loading': true});
    default:
      return state;
  }
}


function details(state = {}, action) {
  const item = action.json;
  switch (action.type) {
    case termConsts.LOAD_TERM:
      state[item.id] = item;
      return Object.assign({}, state);
    default:
      return state;
  }
}

function requested(state = new Requested(), action) {
  switch (action.type) {
    case termConsts.TOGGLE_TERM:
      return state.toggle(action.term);
    default:
      return state;
  }
}


function tagged(state = new TaggedItems(), action) {
  switch (action.type) {
    case termConsts.LOAD_TERMS_TREE:
      return new TaggedItems().createFromJson(action.json);
    case termConsts.RELOAD_TERMS_TREE:
      return state.setCache(action.json);
    case termConsts.TOGGLE_TERM:
      return state.toggle(action.term);
    case termConsts.RESET_TERM:
      return state.resetTerm(action.term);
    case termConsts.RESET_BRANCH:
      return state.resetBranch(action.term);
    case termConsts.SET_PREV_TAGGED_ITEMS:
      return state.setPrevTagged();
    default:
      return state;
  }
}


function expanded(state = new ExpandedItems([]), action) {
  switch (action.type) {
    case termConsts.LOAD_TERMS_TREE:
      return new ExpandedItems(action.json);
    case termConsts.RELOAD_TERMS_TREE:
      return state.reload(action.json);
    case termConsts.TOGGLE_TERM:
      return state.toggle(action.term);
    default:
      return state;
  }
}


function infoExpanded(state = new ExpandedInfoItems(), action) {
  switch (action.type) {
    case termConsts.SHOW_INFO:
      return state.show(action.term);
    case termConsts.HIDE_INFO:
      return state.hide(action.term);
    default:
      return state;
  }
}


function realPotential(state = new RealPotentialItems({}), action) {
  switch (action.type) {
    case entityConsts.LOAD_ENTITIES:
      return new RealPotentialItems(action.json);
    default:
      return state;
  }
}

const filters = (state = {active: false}, action) => {
  switch (action.type) {
    case termConsts.TOGGLE_FILTERS:
      return {...state, active: !state.active};
    default:
      return state;
  }
};


const terms = combineReducers({
    tree: tree,
    details: details,
    requested: requested,
    tagged: tagged,
    expanded: expanded,
    infoExpanded: infoExpanded,
    realPotential: realPotential,
    filters,
});


export default terms;

