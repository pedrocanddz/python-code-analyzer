function mergeSort(arr) {
    if (arr.length <= 1) return arr;
    const mid = Math.floor(arr.length / 2);
    const left = mergeSort(arr.slice(0, mid));
    const right = mergeSort(arr.slice(mid));
    return merge(left, right);
}

function merge(left, right) {
    const result = [];
    while (left.length && right.length) {
        result.push(left[0] < right[0] ? left.shift() : right.shift());
    }
    return [...result, ...left, ...right];
}

const arr = Array.from({length: 10000}, () => Math.floor(Math.random() * 100000));
mergeSort(arr);
