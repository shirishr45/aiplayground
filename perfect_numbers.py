"""
Perfect numbers via Euler-Euclid theorem:
  2^(p-1) * (2^p - 1) is perfect when (2^p - 1) is a Mersenne prime.
This is far faster than trial division for large perfect numbers.
"""
def isprime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def find_perfect_numbers(count: int) -> list[int]:
    results = []
    p = 2
    while len(results) < count:
        mersenne = (1 << p) - 1  # 2^p - 1
        if isprime(mersenne):
            perfect = (1 << (p - 1)) * mersenne  # 2^(p-1) * (2^p - 1)
            results.append(perfect)
        p += 1
    return results


if __name__ == "__main__":
    numbers = find_perfect_numbers(5)
    for i, n in enumerate(numbers, 1):
        print(f"{i}: {n:,}")
