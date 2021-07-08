export default (num = 0, baseName = 'объект') => {
    const declArr = ['ов', '', 'а', 'а', 'а', 'ов', 'ов', 'ов', 'ов', 'ов', 'ов', 'ов', 'ов', 'ов', 'ов'],
      twoLastNumSymbols = `${num}`.slice(-2);
    return `${num} ${baseName}${declArr[twoLastNumSymbols in declArr ? twoLastNumSymbols : twoLastNumSymbols.slice(-1)]}`;
};
