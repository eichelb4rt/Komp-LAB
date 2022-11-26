def main():
    # cool inputs for task 1
    max_n_task1 = 20
    inputs_task1 = []
    for n in range(max_n_task1):
        # 010
        inputs_task1.append("0" * n + "1" * n + "0" * n)
        # 0100, 0110, 0010
        inputs_task1.append("0" * n + "1" * n + "0" * (n + 1))
        inputs_task1.append("0" * n + "1" * (n + 1) + "0" * n)
        inputs_task1.append("0" * (n + 1) + "1" * n + "0" * n)
        # 01100, 00100, 00110
        inputs_task1.append("0" * n + "1" * (n + 1) + "0" * (n + 1))
        inputs_task1.append("0" * (n + 1) + "1" * n + "0" * (n + 1))
        inputs_task1.append("0" * (n + 1) + "1" * (n + 1) + "0" * n)
    with open("inputs/inputs_task1.txt", 'w') as f:
        f.write("\n".join(inputs_task1))

    # cool inputs for task 2
    max_n_task2 = 64
    inputs_task2 = [f"{bin(x)[2:]}${bin(y)[2:]}" for x in range(max_n_task2) for y in range(max_n_task2)]
    with open("inputs/inputs_task2.txt", 'w') as f:
        f.write("\n".join(inputs_task2))

    # worst case inputs for task 2
    max_n_task2_worst = 7
    inputs_task2_worst = [f"{bin(2**n - 1)[2:]}${bin(2**n - 1)[2:]}" for n in range(max_n_task2_worst)]
    with open("inputs/inputs_task2_worst.txt", 'w') as f:
        f.write("\n".join(inputs_task2_worst))


if __name__ == "__main__":
    main()
