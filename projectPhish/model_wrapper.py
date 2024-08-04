import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class TextModelWrapper(BaseEstimator, TransformerMixin):
    def __init__(self, vectorizer, model):
        self.vectorizer = vectorizer
        self.model = model
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self.model.predict_proba(self.vectorizer.transform(X))

    def predict_proba(self, X):
        if isinstance(X, np.ndarray):
            X = X.tolist()  # Convert NumPy array to list of strings if necessary
        return self.model.predict_proba(self.vectorizer.transform(X))
