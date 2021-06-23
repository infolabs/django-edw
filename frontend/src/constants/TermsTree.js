// Tree Actions
export const LOAD_TERMS_TREE = 'LOAD_TERMS_TREE';
export const RELOAD_TERMS_TREE = 'RELOAD_TERMS_TREE';
export const LOAD_TERM = 'LOAD_TERM';
export const TOGGLE_FILTERS = 'TOGGLE_FILTERS';
export const TOGGLE_TERM = 'TOGGLE_TERM';
export const RESET_BRANCH = 'BRANCH_RESET';
export const RESET_TERM = 'RESET_TERM';
export const SHOW_INFO = 'SHOW_TERM_INFO';
export const HIDE_INFO = 'HIDE_TERM_INFO';
export const NOTIFY_LOADING_TERMS = 'NOTIFY_LOADING_TERMS';
// Native
export const SET_PREV_TAGGED_ITEMS = 'SET_PREV_TAGGED_ITEMS';
export const actionTypes = {
  LOAD_TERMS_TREE,
  RELOAD_TERMS_TREE,
  TOGGLE_TERM,
  RESET_BRANCH,
  RESET_TERM,
  NOTIFY_LOADING_TERMS,
  SET_PREV_TAGGED_ITEMS
};
// Semantic Rules
export const SEMANTIC_RULE_OR = 10;
export const SEMANTIC_RULE_XOR = 20;
export const SEMANTIC_RULE_AND = 30;
// Native
export const semanticRules = {
  SEMANTIC_RULE_OR,
  SEMANTIC_RULE_XOR,
  SEMANTIC_RULE_AND
};
// Structures
export const STRUCTURE_TRUNK = "trunk";
export const STRUCTURE_LIMB = "limb";
export const STRUCTURE_BRANCH = "branch";
export const STRUCTURE_NULL = null;
// Native
export const structures = {
  STRUCTURE_TRUNK,
  STRUCTURE_LIMB,
  STRUCTURE_BRANCH,
  STRUCTURE_NULL
};
// Specifications
export const STANDARD_SPECIFICATION = 10;
export const EXPANDED_SPECIFICATION = 20;
export const REDUCED_SPECIFICATION = 30;
// Native
export const specifications = {
  STANDARD_SPECIFICATION,
  EXPANDED_SPECIFICATION,
  REDUCED_SPECIFICATION
};

// TODO: move to a separate file
// RECACHE_RATE
export const RECACHE_RATE = 60000;
// Multiple datamarts
export const CHANGE_ACTIVE_DATA_MART = 'CHANGE_ACTIVE_DATA_MART';
