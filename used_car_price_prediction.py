# -*- coding: utf-8 -*-
"""Copy of used_car_price_prediction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1x7lHpG-N4fmXZT044Jqwyx4J8StFXDxi

**Part 1**: Load data
"""

#install kaggle dependancy
!pip install kaggle

from google.colab import files
files.upload()

!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/

!chmod 600 ~/.kaggle/kaggle.json

!kaggle datasets download -d austinreese/craigslist-carstrucks-data

from zipfile import ZipFile
file_name = "craigslist-carstrucks-data.zip"

with ZipFile(file_name, 'r') as zipp:
  zipp.extractall()
  print('Done')

"""**Part 1.5** Use Pandas to load the data into a dataframe

"""

import keras 
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import itertools
import random

df = pd.read_csv('vehicles.csv')
df.head()
# df.dtypes

"""**Part 2**: Pre Process data"""

#Remove unwanted features
X = df.drop(columns=['id', 'url', 'region_url', 'price', 'manufacturer', 'model', 'condition', 'cylinders', 'vin', 'drive', 'size', 'type', 'paint_color','image_url', 'description', 'county'])
y = df[['price']]
X.head()
X.dtypes

"""**Part 2.2** Use mean imputation for nan entries"""

# Takes a dataframe, list of columns to be encoded and prefixes for the new columns
# returns a one hot encoded version of the original dataframe.
def onehot_encode(df, columns, prefixes):
  df = df.copy()
  for column, prefix in zip(columns, prefixes):
    dummies = pd.get_dummies(df[column], prefix=prefix)
    df = pd.concat([df, dummies], axis=1)
    df = df.drop(column, axis=1)
  return df

#replace all missing entries with the mean of that column
X['year'].fillna(value=df['year'].mean(), inplace=True)
X['odometer'].fillna(value=df['odometer'].mean(), inplace=True)
X['lat'].fillna(value=df['lat'].mean(), inplace=True)
X['long'].fillna(value=df['long'].mean(), inplace=True)

def process(X):
  # One hot encode the categorical features so our data consists of all numbers
  X = onehot_encode(
      X,
      ['region', 'fuel', 'title_status', 'transmission', 'state'],
      ['reg', 'fuel', 'title', 'trans', 'state']
  )

  return X

X = process(X)
X.head()
# normalize the data
X = preprocessing.normalize(X, norm='l2')
y = preprocessing.normalize(y, norm='l2')

"""**Part 2.4** Create the test and train set"""

#use train_test_split from scikit to get a train and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=34)

"""**Part 2.6** Create the model

**2.6.1** Trying out different combinations of model parameters
"""

# Function to reset seeds for the sake of consistency
def reset_seeds():
  SEED = 100
  np.random.seed(SEED)
  tf.random.set_seed(SEED)
  random.seed(SEED)

#Create a sequential model which contains a single output node, the car's price in our case
def build_nn(params):
  model = keras.Sequential()
  for _ in range(0, params['num_layers']):
    model.add(keras.layers.Dense(params['units'], activation='relu'))
  # add the output layer
  model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
  model.compile(optimizer=params['optimizer'], loss=params['loss'], metrics=['accuracy'])
  return model

# Find best parameters
def find_best_params(params, X_train, y_train, X_test, y_test):
  best_params = dict()
  param_combinations = []
  
  keys = params.keys()
  values = (params[key] for key in keys)
  # create all combinations of the parameters
  param_combinations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]

  # replace 0 at 'max' with highest accuracy, {} at 'set' with the combination
  best_params = {'max': 0, 'params': {}}
  # Iterate over all combinations using one or more loops
  for param_combination in param_combinations:
    print(param_combination)
    # Reset seeds and build the model
    reset_seeds()
    model = build_nn(param_combination)

    # Train and evaluate the model using currect combination of parameters
    reset_seeds()
    if param_combination['epochs'] == 50:
      model.fit(X_train, y_train, batch_size=32, epochs=50, validation_split=0.2, shuffle=True, 
                callbacks=[keras.callbacks.EarlyStopping(patience=5)])
    else:
      model.fit(X_train, y_train, epochs=param_combination['epochs'])
    # evaluate the model
    reset_seeds()
    loss, accuracy = model.evaluate(X_test, y_test)
    print(accuracy)

    if accuracy > best_params['max']:
      best_params['max'] = accuracy
      best_params['params'] = param_combination
  return best_params

# test all combinations of the parameters to find the best one
X_train = np.array(X_train)
y_train = np.array(y_train)
X_test = np.array(X_test)
y_test = np.array(y_test)

# Create sets of hyperparameters in order to find which combination results in the most accurate model
parameters = {
    'num_layers': [2,3,5], 
    'units': [8, 16, 32, 40], 
    'loss': ['binary_crossentropy', 'mse'], 
    'optimizer': ['sgd', 'adam'],
    'epochs': [5, 10, 50]
    }

best_params = find_best_params(parameters, X_train, y_train, X_test, y_test)
# ran out of RAM so up to {'num_layers': 2, 'units': 40, 'loss': 'binary_crossentropy', 'optimizer': 'sgd', 'epochs': 5}, 
# best is: {'num_layers': 2, 'units': 32, 'loss': 'binary_crossentropy', 'optimizer': 'adam', 'epochs': 10} 
# with accuracy of 0.9183299541473389

print("Best parameters: {0}".format(best_params['params']))
# print accuracy of model with best set of parameters
print("Accuracy: {0}".format(best_params['max']))

best_params = {
    'num_layers': 2, 
    'units': 32, 
    'loss': 'binary_crossentropy', 
    'optimizer': 'adam',
    'epochs': 10
    }
model = build_nn(best_params)

"""**2.6.2** Building a model explicitly **(SKIP ALL OF 2.6.2 IF 2.6.1 CODE WAS USED)**"""

#Create a sequential model which contains a single output node, the car's price in our case
model = keras.Sequential()
#add the input layer - this layer receives the car data. This layer receives 473 entries, corresponding to the 473 features.
model.add(keras.layers.Dense(40, activation='relu', input_shape=(473,)))
#adding the hidden layer
#Each layer has 40 nodes, experimenting with different amount of nodes is recommended
#We use relu as our optimizer here. Experimenting with other optimizers is recommended
model.add(keras.layers.Dense(40, activation='relu'))
model.add(keras.layers.Dense(40, activation='relu'))
model.add(keras.layers.Dense(40, activation='relu'))
#adding the output layer
#the output layer contains a single nod
model.add(keras.layers.Dense(1))

model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])

model.fit(X_train, y_train, batch_size=32, epochs=50, validation_split=0.2, shuffle=True, callbacks=[keras.callbacks.EarlyStopping(patience=5)])

"""**Part 3** Test the model"""

result = model.evaluate(X_test, y_test)

"""**Part 4** Evaluate the model on custom sample"""

# TODO - transform categorical input to vector
# region	year	fuel	odometer	title_status	transmission	state	lat	long
test_data = pd.DataFrame(["Chicago", 2004, "gas", 130000.0, "clean", "automatic", "il", 45.944800, -91.869100])
test_data.values
# test_data = process(test_data)
# test_data = np.array(test_data)
# print(model.predict(test_data.reshape(1,4), batch_size=1))
