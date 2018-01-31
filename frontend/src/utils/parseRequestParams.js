
function parseIntList(param, name) {
  let ret = [];
  const q = name + "=";
  const r = new RegExp("^" + q, "g");
  if (param.startsWith(q)) {
    const param_str = param.replace(r, "");
    if (param_str) {
      let param_int = parseInt(param_str);
      if (isNaN(param_int)) {
        ret = param_str.value.split(",");
      } else {
        ret.push(param_int);
      }
    }
  }
  return ret;
}

export default function parseRequestParams(request_params) {
    let term_ids = [];
    let subj_ids = [];
    let limit = -1;
    let options_arr = [];

    for (const param of request_params) {
        if (param.startsWith("terms=")) {
          term_ids = parseIntList(param, "terms");
        } else if (param.startsWith("subj=")) {
          subj_ids = parseIntList(param, "subj");
        } else if (param.startsWith("limit=")) {
          limit = parseIntList(param, "limit");
        } else {
          options_arr.push(param);
        }
    }

    return { term_ids, subj_ids, limit, options_arr };
}
