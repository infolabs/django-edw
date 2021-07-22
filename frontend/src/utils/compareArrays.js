export default function compareArrays(a = [], b = []) {
  if (a === b)
    return true;

  if (a === null || b === null)
    return false;

  if (a.length !== b.length)
    return false;

  a.sort();
  b.sort();

  return a
    .map((val, i) => b[i] === val)
    .every(isSame => isSame);
}
