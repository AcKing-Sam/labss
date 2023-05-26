

def sort_file(filepath):

    with open(filepath, 'r') as fr:
        lines = fr.readlines()

    lines = sorted(lines, key=lambda x: x[0], reverse=False)

    with open(filepath, 'w') as fw:
        for line in lines:
            fw.write(line)


if __name__ == '__main__':
    sort_file('/home/sam/labss/results/gasless_send_list.txt')
