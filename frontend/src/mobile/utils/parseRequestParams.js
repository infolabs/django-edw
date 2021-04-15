function parseIntList(param, name) {
  let ret = [],
    arr = param.replace(`${name}=`, '').split(',');
  for (const value of arr) {
    const num = parseInt(value);
    if (!isNaN(num))
      ret.push(num);
  }
  return ret;
}

export default function parseRequestParams(request_params) {
  let term_ids = [],
    subj_ids = [],
    limit = -1,
    options_arr = [];

  for (const param of request_params) {
    if (param.startsWith("terms="))
      term_ids = parseIntList(param, "terms");
    else if (param.startsWith("subj="))
      subj_ids = parseIntList(param, "subj");
    else if (param.startsWith("limit="))
      limit = parseIntList(param, "limit");
    else
      options_arr.push(param);
  }
  return {term_ids, subj_ids, limit, options_arr};
}
