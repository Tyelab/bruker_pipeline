from pathlib import Path
import csv

data_dir = Path("/snlkt/data/_DATA/specialk_cs/2p/raw/")

paths = [path for path in data_dir.glob("*")]

dictionary = {}

for i in paths:
    tmp = {}
    key = i.stem
    tmp ={li: [] for li in i.glob("*")}

    dictionary[key] = tmp


for i in dictionary.keys():
    for j in dictionary[i]:
        tmp = [p for p in j.glob("*_tiffs")]
        dictionary[i][j] = tmp
        

needs_conversion = []

for i in dictionary.keys():
    for j in dictionary[i]:
        if len(dictionary[i][j]) == 0:
            new = [z for z in j.glob("*raw*") if z.is_dir()]
            if len(new) == 0:
                print(j)
                break
            else:
                needs_conversion.append(new)


print(len(needs_conversion))


with open("needs_conversion.csv", "w") as f:
    write = csv.writer(f)
    write.writerows(needs_conversion)