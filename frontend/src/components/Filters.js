import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import TermsTree from 'components/TermsTree';
import ActionCreators from '../actions/index';


const Filters = props => {
  const {filters, entry_points, entry_point_id} = props;

  return (
    <>
      <div className="ex-btn-group visible-xs" role="group">
        <a className={"ex-btn ex-btn-default " + (filters.active ? "active" : "")} onClick={() => props.toggleFilters()}>
          <i className="fa fa-filter"/>&nbsp;<span>{gettext("Filters")}</span>
        </a>
        {filters.active &&
          <a className="ex-btn ex-btn-default" onClick={() => props.toggleFilters()}>
            <i className="fa fa-times" aria-hidden="true"/>
          </a>
        }
      </div>
      <div className={filters.active ? "" : "hidden-xs"}>
        <TermsTree entry_points={entry_points} entry_point_id={entry_point_id} />
      </div>
    </>
  )
};


const mapStateToProps = state => ({
    filters: state.terms.filters
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Filters);