import {
  getEntities,
  readEntities,
  setDataViewComponents,
  setCurrentView,
  getEntity,
  hideVisibleDetail,
} from './EntityActions';

import {
  notifyLoadingEntities,
  toggleDropdown,
  selectDropdown,
} from './EntityActions.js';

import {
  notifyLoadingTerms,
  readTree,
  toggleTerm,
  resetTerm,
  setPrevTaggedItems,
} from './TermsTreeActions';

import {
  loadTree,
  reloadTree,
  resetBranch,
} from './TermsTreeActions.js';

export default {
  getEntities,
  readEntities,
  notifyLoadingEntities,
  toggleDropdown,
  selectDropdown,
  loadTree,
  reloadTree,
  readTree,
  notifyLoadingTerms,
  toggleTerm,
  resetTerm,
  resetBranch,
  setDataViewComponents,
  setCurrentView,
  getEntity,
  hideVisibleDetail,
  setPrevTaggedItems,
};
