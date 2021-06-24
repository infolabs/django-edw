import {
  getEntities,
  readEntities,
  setDataViewComponents,
  setCurrentView,
  getEntity,
  hideVisibleDetail
} from './EntityActions';

import {
  toggleDropdown,
  selectDropdown,
  notifyLoadingEntities,
} from './EntityActions.js';

import {
  loadTree,
  reloadTree,
  readTree,
  setPrevTaggedItems
} from './TermsTreeActions';

import {
  resetTerm,
  resetBranch,
  toggleTerm,
  notifyLoadingTerms,
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
  setPrevTaggedItems
}
