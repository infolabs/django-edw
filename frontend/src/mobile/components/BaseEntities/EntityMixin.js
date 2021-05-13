import React from 'react';

const EntityMixin = Base => class extends Base {

  constructor() {
    super();
    this.maxLengthDescriptionTile = 70
  }

  handleScroll(e) {
    const {items, loading, meta} = this.props;
    if (e.nativeEvent.contentOffset.y + e.nativeEvent.layoutMeasurement.height * 2 > e.nativeEvent.contentSize.height
      && !loading && meta.count > items.length) {
      const meta = this.props.meta;
      const {subj_ids, limit, offset, request_options} = meta;
      let options = Object.assign(request_options, {'offset': offset + limit});
      this.props.notifyLoadingEntities();
      this.props.getEntities(this.props.entry_point_id, subj_ids, options);
    }
  }
};

export default EntityMixin
