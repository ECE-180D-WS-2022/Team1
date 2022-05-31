import os
import pandas as pd
import PkUtils as ut
import csv

class User:
    def __init__(self, learnset, username = None):
        if username is not None:
            self.username = username
            self.path = "data/users/" + self.username
            self.gamestats_df, self.team_df = self.get_user_files(learnset)
        else:
            self.username = None
            self.team_df = None

    def get_user_files(self, learnset):
        """
        get the appropiate gamestats and team files if it exists, else create the folder and copy in the default
        """
        if not os.path.isdir(self.path):
            os.mkdir(self.path, 0o777)
            gamestats_df = pd.DataFrame(data={'games_played': [0], 'wins': [0]})
            basepk_df = pd.read_csv("data/new_pokemon_withMoves.csv")
            team_df = basepk_df.sample(n = 3)
            team_df.reset_index(drop=True, inplace=True)
            for i in range(team_df.shape[0]):
                team_df.loc[i] = ut.level_up(team_df.loc[i], 0, learnset)
            team_df.to_csv(self.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            gamestats_df.to_csv(self.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
        else:
            gamestats_df = pd.read_csv(self.path + "/gamestats.csv")
            team_df = pd.read_csv(self.path + "/team.csv")
        return gamestats_df, team_df
