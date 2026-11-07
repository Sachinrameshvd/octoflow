from typing import List, Dict

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

class DatasetPipeline:
    def __init__(self):
        self.pipeline = Pipeline([
            ('scaler', StandardScaler())
        ])

    def fit_transform(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        return self.pipeline.fit_transform(df)

    def transform(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        return self.pipeline.transform(df)