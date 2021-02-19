import numpy as np
import pandas as pd

COMPARISONS_PATH = "../comparisons"

if __name__ == '__main__':
    print("ADHD_SIN ========================================================")

    # global rmse ADHD SIN
    df = pd.read_csv(f"{COMPARISONS_PATH}/adhd_sin_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Global RMSE')
    print(df[['rmse', 'points']])

    # noise-level rmse ADHD SIN
    df = pd.read_csv(f"{COMPARISONS_PATH}/adhd_sin_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['noise', 'noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Per-Noise Level RMSE')
    print(df[['rmse', 'points']])

    print("N_BACK ==========================================================")

    # global rmse N-BACK
    df = pd.read_csv(f"{COMPARISONS_PATH}/n_back_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Global RMSE')
    print(df[['rmse', 'points']])

    # mode-level rmse ADHD SIN
    df = pd.read_csv(f"{COMPARISONS_PATH}/n_back_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['mode', 'noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Per-Mode Level RMSE')
    print(df[['rmse', 'points']])

    # task-level rmse ADHD SIN
    df = pd.read_csv(f"{COMPARISONS_PATH}/n_back_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['task', 'noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Per-Task Level RMSE')
    print(df[['rmse', 'points']])

    # point-level rmse ADHD SIN
    df = pd.read_csv(f"{COMPARISONS_PATH}/n_back_synt_data_comparison.csv")
    df['sse'] = df['rmse'] * df['rmse'] * df['points']
    df = df.groupby(['position', 'noise_model', 'tracker_model'])[['sse', 'points']].agg("sum")
    df['rmse'] = np.sqrt(df['sse'] / df['points'])
    print('Per-Point Level RMSE')
    print(df[['rmse', 'points']])
