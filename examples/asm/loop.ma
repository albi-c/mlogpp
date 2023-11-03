i = 0
a:
    i = i + 1
    print(i)
    print("\n")
    cell1[i] = i
    i = cell1[i]
    ${x = 5}
    print(${x})
    print(${"\"" + "X" * x + "\""})
    ${"print(" + str(x / 2) + ")"}
    :a (i < ${x * 2})
    ${"cell" + x}[0] = y

printflush(message1)
