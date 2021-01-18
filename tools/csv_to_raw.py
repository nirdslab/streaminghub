import glob

import pandas as pd

if __name__ == '__main__':
    files = glob.glob('../datasets/nback-csv/*.csv')
    for file in files:
        print(file)
        df = pd.read_csv(file)
        df = df[['x', 'y', 't']]
        df.to_csv(file.replace('nback-csv', 'nback-raw').replace('.csv', '.raw'), sep=' ', index=False, header=False)
