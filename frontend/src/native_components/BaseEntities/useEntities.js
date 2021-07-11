const maxLengthDescriptionTile = 70;
const maxLengthDescriptionListRelated = 90;
const mediaRegExp = /.*<img.*?src=(['"])(.*?)(['"])/;


export default function useEntities(props) {

  function handleScroll(e) {
    const {items, loading, meta} = props;
    if (e.nativeEvent.contentOffset.y + e.nativeEvent.layoutMeasurement.height * 2 > e.nativeEvent.contentSize.height
      && !loading && meta.count > items.length) {
      const {subj_ids, limit, offset, request_options} = meta;
      let options = Object.assign(request_options, {'offset': offset + limit});
      props.notifyLoadingEntities();
      props.getEntities(props.entry_point_id, subj_ids, options, [], true);
    }
  }

  return {maxLengthDescriptionTile, maxLengthDescriptionListRelated, mediaRegExp, handleScroll};
}


export function useEntityItem(props) {
  const {navigation} = props,
    {id, entity_model} = props.data;

  function onPress(event) {
    navigation.navigate(entity_model, {id});
  }

  return {onPress};
}
