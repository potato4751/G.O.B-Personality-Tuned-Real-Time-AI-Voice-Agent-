# =====================================
# Q01 : Create DataFrame from Dictionary
# =====================================

import pandas as pd

d = {
    'col1': [1, 2],
    'col2': [3, 4],
    'col3': [5, 6],
    'col4': [7, 8]
}

df = pd.DataFrame(d)

print("Q01 DataFrame:")
print(df)
print()


# =====================================
# Q02 : Create new DataFrame with only col4
# =====================================

new_df = df[['col4']]

print("Q02 new_df (only col4):")
print(new_df)
print()


# =====================================
# Q03 : Change index names
# =====================================

df.index = ['first', 'second']

print("Q03 DataFrame with renamed index:")
print(df)
print()


# =====================================
# Q04 : Search for missing data
# =====================================

print("Q04 Missing Data (True means missing):")
print(df.isnull())
print()


# =====================================
# Q05 : Descriptive Statistics
# =====================================

print("Q05 Descriptive Statistics:")
print(df.describe())