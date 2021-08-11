lst = []

for i in range(5):
    temp = [0]*5
    temp[i] = 1
    lst.append(temp)

print(lst)
print(lst[:][0])
print(lst[:, 0])