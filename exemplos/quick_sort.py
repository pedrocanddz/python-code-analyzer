def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)

if __name__ == "__main__":
    import random
    arr = [random.randint(0, 100000) for _ in range(10000)]
    sorted_arr = quick_sort(arr)
