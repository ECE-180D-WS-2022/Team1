import pandas as pd
import csv

df = pd.read_csv('all_pokemon.csv')
del df["Type 2"]
del df["#"]
del df["Total"]
del df["Generation"]
del df["Legendary"]
df.rename(columns={"Type 1": "type", "Sp. Atk": "special_attack", "Sp. Def": "special_defense"}, inplace=True)
df['xp_reward'] = 82
df["move1"] = "Thunderbolt"
df["move2"] = "Tackle"
df["move3"] = "Water Gun"
df["move4"] = "Flamethrower"
df["xp_accumulated"] = 0
df["level"] = 0
df.columns = df.columns.str.lower()


df.to_csv( "../data/pokemon.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
print(df)
