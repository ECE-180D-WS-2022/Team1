import pokEEmon as pk
import pandas as pd


data = pd.read_csv("data/users/caleb/team.csv")
print(data)
for i in range(data.shape[0]):
    data.loc[i] = pk.level_up(data.loc[i], 5000)

print(data)
