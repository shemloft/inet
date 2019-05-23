def split_range(start, end, parts):
    count = (end - start) // parts
    ranges = []
    current_start = start
    for i in range(0, parts - 1):
        ranges.append((current_start, current_start + count))
        current_start += count
    ranges.append((current_start, end + 1))
    return ranges
