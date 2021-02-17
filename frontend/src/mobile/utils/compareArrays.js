export default function compareArrays(arrayOne = [], arrayTwo = []) {
    if (arrayOne.length !== arrayTwo.length){
        return false
    }
    arrayOne.sort();
    arrayTwo.sort();

    return arrayOne
        .map((val, i) => arrayTwo[i] === val)
        .every(isSame => isSame)
}