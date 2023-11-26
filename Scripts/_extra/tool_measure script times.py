import timeit

code1 = """
for i in range(3):
    print("one")
"""

code2 = """
print("two")
"""

# Measure time.
time1 = timeit.timeit(stmt=code1, number=1000, globals=globals())
time2 = timeit.timeit(stmt=code2, number=1000, globals=globals())

print(f"Time for first code: {time1}")
print(f"Time for second code: {time2}")