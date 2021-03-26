const reCache = url => {
  const tmp = Math.round(new Date().getTime());
  if (url.includes("?"))
    return `${url}&_=${tmp}`;
  else
    return `${url}?_=${tmp}`;
};

export default reCache
