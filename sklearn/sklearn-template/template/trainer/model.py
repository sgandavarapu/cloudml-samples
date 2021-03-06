# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""ML model definitions."""

import functools

import numpy as np
from sklearn import compose
from sklearn import ensemble
from sklearn import impute
from sklearn import pipeline
from sklearn import preprocessing

from trainer import metadata
from trainer import utils


def get_estimator(flags):
  """Generate ML Pipeline which include both pre-processing and model training.

  Args:
    flags: (argparse.ArgumentParser), parameters passed from command-line

  Returns:
    sklearn.pipeline.Pipeline
  """

  classifier = ensemble.RandomForestClassifier(
      n_estimators=flags.n_estimators,
      max_depth=flags.max_depth,
      min_samples_leaf=flags.min_samples_leaf,
      criterion=flags.criterion,
  )

  numeric_transformer = pipeline.Pipeline([
      ('imputer', impute.SimpleImputer(strategy='median')),
      ('scaler', preprocessing.StandardScaler()),
  ])

  # Apply scale transformation to numerical attributes.
  # Log transformation is used here.
  numeric_log_transformer = pipeline.Pipeline([
      ('imputer', impute.SimpleImputer(strategy='median')),
      ('log', preprocessing.FunctionTransformer(
          func=np.log1p, inverse_func=np.expm1, validate=True)),
      ('scaler', preprocessing.StandardScaler()),
  ])

  # Bucketing numerical attributes
  numeric_bin_transformer = pipeline.Pipeline([
      ('imputer', impute.SimpleImputer(strategy='median')),
      ('bin', preprocessing.KBinsDiscretizer(n_bins=3, encode='onehot-dense')),
  ])

  categorical_transformer = pipeline.Pipeline([
      ('imputer', impute.SimpleImputer(
          strategy='constant', fill_value='missing')),
      ('onehot', preprocessing.OneHotEncoder(
          handle_unknown='ignore', sparse=False)),
  ])

  feature_columns = metadata.FEATURE_COLUMNS

  boolean_mask = functools.partial(utils.boolean_mask, feature_columns)
  preprocessor = compose.ColumnTransformer([
      ('numeric', numeric_transformer,
       boolean_mask(metadata.NUMERIC_FEATURES)),
      ('numeric_log', numeric_log_transformer,
       boolean_mask(metadata.NUMERIC_FEATURES)),
      ('numeric_bin', numeric_bin_transformer,
       boolean_mask(metadata.NUMERIC_FEATURES)),
      ('categorical', categorical_transformer,
       boolean_mask(metadata.CATEGORICAL_FEATURES)),
  ])

  estimator = pipeline.Pipeline([
      ('preprocessor', preprocessor),
      ('classifier', classifier),
  ])

  return estimator
