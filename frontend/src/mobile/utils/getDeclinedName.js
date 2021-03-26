export default (num) => {
    const baseName = ' объект';
    const declArr = ['ов', '', 'а', 'а', 'а', 'ов', 'ов', 'ов', 'ов', 'ов'];
    return num + baseName + declArr[`${num}`.slice(-1)];
}