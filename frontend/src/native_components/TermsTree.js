import React, {useEffect, useRef} from 'react';
import {connect} from 'react-redux';
import {View} from 'react-native';
import {bindActionCreators} from 'redux';
import TermsTreeItem from './TermsTreeItem';
import ActionCreators from '../actions';
import parseRequestParams from '../utils/parseRequestParams';
import compareArrays from '../../utils/compareArrays';
import {termsTreeItemStyles as styles} from '../native_styles/terms';


function TermsTree(props) {

  const prevPropsRef = useRef(props);

  useEffect(() => {
    const {entry_points, entry_point_id, terms} = props,
      request_params = entry_points[entry_point_id.toString()].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids;

    if (!terms.tree.json.length) {
      props.actions.notifyLoadingTerms();
      props.actions.readTree(entry_point_id, term_ids);
    }
  }, []);

  useEffect(() => {
    const prevProps = prevPropsRef.current;
    const entry_points = prevProps.entry_points,
      entry_point_id = prevProps.entry_point_id,
      request_params = entry_points[entry_point_id.toString()].request_params || [],
      tagged_current = prevProps.terms.tagged,
      tagged_next = props.terms.tagged,
      meta = prevProps.entities.items.meta;

    if (!compareArrays(tagged_current.items, tagged_next.items)) {
      // reload tree
      if (!tagged_next.isInCache()) {
        props.actions.notifyLoadingTerms();
        props.actions.reloadTree(entry_point_id, tagged_next.items);
      }
      // reload entities
      if (!tagged_next.entities_ignore) {
        const params = parseRequestParams(request_params),
          subj_req_ids = params.subj_ids,
          options_arr = params.options_arr;

        let request_options = meta.request_options,
          subj_ids = meta.subj_ids || subj_req_ids;

        delete request_options.alike;
        request_options.terms = tagged_next.items;
        request_options.offset = 0;
        props.actions.notifyLoadingEntities();

        props.actions.getEntities(
          entry_point_id, subj_ids, request_options, options_arr
        );
      }

      prevPropsRef.current = props;
    }

    if (tagged_current.items.length !== tagged_next.items.length)
      props.termsIdsTaggedBranch.clear();
  });

  const {terms, actions, termsIdsTaggedBranch} = props,
    term = terms.tree.root,
    {tagged, expanded, realPotential} = terms;

  return term ? (
      <View style={styles.treeContainer}>
        <TermsTreeItem key={term.id}
                       term={term}
                       tagged={tagged}
                       expanded={expanded}
                       realPotential={realPotential}
                       actions={actions}
                       terms={terms}
                       termsIdsTaggedBranch={termsIdsTaggedBranch}/>
      </View>
    )
    : null;
}


const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => ({
  actions: bindActionCreators(ActionCreators, dispatch),
  dispatch: dispatch,
});


export default connect(mapStateToProps, mapDispatchToProps)(TermsTree);
