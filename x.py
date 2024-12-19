import os
loads = []
for file in list(os.walk("Assets/Payloads")):
    for f in file[2]:
        if f.endswith(".txt"):
            loads.append("".join(file[0].split("/")[2:]) + "/" + f)
print("\n".join(loads))