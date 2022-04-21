import numpy as np
import sys
import time
#import pokepy
import random
import os
import copy
import csv
import pandas as pd


def import_moves():
    df = pd.read_csv()
    del df["super_contest_effect_id"]
    del df["contest_effect_id"]
    del df["contest_type_id"]
    del df["effect_chance"]
    del df["effect_id"]
    del df["damage_class_id"]
    del df["target_id"]
    del df["priority"]
    del df["generation_id"]

    df.columns = df.columns.string.lower()

    df.drop([10001, 10018)

    for row in df["type_id"]:
        if 
