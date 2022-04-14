import pandas as pd
import csv

df = pd.read_csv('pokemon_names.csv')
del df["id"]
del df["height"]
del df["weight"]
del df["order"]
df.rename(columns={"identifier": "name", "species_id": "id"}, inplace=True)
'''
df['xp_reward'] = 82
df["move1"] = "Thunderbolt"
df["move2"] = "Tackle"
df["move3"] = "Water Gun"
df["move4"] = "Flamethrower"
df["xp_accumulated"] = 0
df["level"] = 0
'''
df.columns = df.columns.str.lower()


df.to_csv( "../pokemon_db/import_pokemon_filtered.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
#print(df)

with open('import_pokemon_filtered.csv', 'rt') as inp, open('import_pokemon_filtered_2.csv', 'wt') as out:
    writer = csv.writer(out)
    for row in csv.reader(inp):
        if row[3] != "0":
            writer.writerow(row)

df = pd.read_csv('import_pokemon_filtered_2.csv')
del df['is_default']

df.to_csv( "../pokemon_db/import_pokemon_filtered_3.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)

#stat order: hp/atk/def/spatk/spdef/spd
