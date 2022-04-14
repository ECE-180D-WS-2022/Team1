import pandas as pd
import csv

df = pd.read_csv('moves.csv')
del df["super_contest_effect_id"]
del df["contest_effect_id"]
del df["contest_type_id"]
del df["effect_chance"]
del df["effect_id"]
del df["priority"]
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
