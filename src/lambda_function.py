'''
Reference code to showcase MXNet model prediction on AWS Lambda 

@author: Sunil Mallya (smallya@amazon.com)
version: 0.2
'''

import os
import boto3
import json
import tempfile
import urllib2 
from urllib import urlretrieve

import mxnet as mx
import numpy as np

from PIL import Image
from collections import namedtuple
Batch = namedtuple('Batch', ['data'])

f_params = 'resnet-18-0000.params'
f_symbol = 'resnet-18-symbol.json'
    
#params
f_params_file = tempfile.NamedTemporaryFile()
urlretrieve("http://data.dmlc.ml/mxnet/models/imagenet/resnet/18-layers/resnet-18-0000.params", f_params_file.name)
f_params_file.flush()

#symbol
f_symbol_file = tempfile.NamedTemporaryFile()
urlretrieve("http://data.dmlc.ml/mxnet/models/imagenet/resnet/18-layers/resnet-18-symbol.json", f_symbol_file.name)
f_symbol_file.flush()

def load_model(s_fname, p_fname):
    """
    Load model checkpoint from file.
    :return: (arg_params, aux_params)
    arg_params : dict of str to NDArray
        Model parameter, dict of name to NDArray of net's weights.
    aux_params : dict of str to NDArray
        Model parameter, dict of name to NDArray of net's auxiliary states.
    """
    symbol = mx.symbol.load(s_fname)
    save_dict = mx.nd.load(p_fname)
    arg_params = {}
    aux_params = {}
    for k, v in save_dict.items():
        tp, name = k.split(':', 1)
        if tp == 'arg':
            arg_params[name] = v
        if tp == 'aux':
            aux_params[name] = v
    return symbol, arg_params, aux_params

def predict(url, mod, synsets):
    '''
    predict labels for a given image
    '''

    req = urllib2.urlopen(url)
    img_file = tempfile.NamedTemporaryFile()
    img_file.write(req.read())
    img_file.flush()
    print("checkpoing0")
 
    img = Image.open(img_file.name)
    print("checkpoint1")

    # PIL conversion
    #size = 224, 224
    #img = img.resize((224, 224), Image.ANTIALIAS)
   
    # center crop and resize
    # ** width, height must be greater than new_width, new_height 
    new_width, new_height = 224, 224
    width, height = img.size   # Get dimensions
    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2

    img = img.crop((left, top, right, bottom))
    # convert to numpy.ndarray
    sample = np.asarray(img)
    # swap axes to make image from (224, 224, 3) to (3, 224, 224)
    sample = np.swapaxes(sample, 0, 2)
    img = np.swapaxes(sample, 1, 2)
    img = img[np.newaxis, :] 
 
    # forward pass through the network
    print("checkpoint2")
    mod.forward(Batch([mx.nd.array(img)]))
    print("checkpoint3")
    #print(mod.get_outputs()[0].asnumpy())
    if not mod.get_outputs():
        return ''
    #try:
    #    prob = mod.get_outputs()[0].asnumpy()
    #except:
    #    print("unexpected error:", sys.exc_info()[0])
    #    raise
    prob = mod.get_outputs()[0].asnumpy()
    #prob = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    print("checkpoing4")

    prob = np.squeeze(prob)
    print("checkpoing5")

    a = np.argsort(prob)[::-1]
    out = '' 
    for i in a[0:5]:
        out += 'probability=%f, class=%s , ' %(prob[i], synsets[i])
        print('probability=%f, class=%s , ' %(prob[i], synsets[i]))
    out += "\n"
    print("checkpoing6")
    return out

with open('synset.txt', 'r') as f:
    synsets = [l.rstrip() for l in f]

def lambda_handler(event, context):

    url = ''
    try:
        # API Gateway GET method
        if event['httpMethod'] == 'GET':
            url = event['queryStringParameters']['url']
        # API Gateway POST method
        elif event['httpMethod'] == 'POST':
            data = json.loads(event['body'])
            url = data['url']
    except KeyError:
        # direct invocation
        url = event['url']
    
    sym, arg_params, aux_params = load_model(f_symbol_file.name, f_params_file.name)
<<<<<<< HEAD
    mod = mx.mod.Module(symbol=sym,label_names=None)
    mod.bind(for_training=False, data_shapes=[('data', (1,3,224,224))])
    mod.set_params(arg_params, aux_params, allow_missing=True)
    print("before predict")
=======
    mod = mx.mod.Module(symbol=sym, label_names=None)
    mod.bind(for_training=False, data_shapes=[('data', (1,3,224,224))], label_shapes=mod._label_shapes)
    mod.set_params(arg_params, aux_params, allow_missing=True)
>>>>>>> 5047e4f49a16d7d7c47ccbfd157d4baa1a7c0bf5
    labels = predict(url, mod, synsets)
    print("after predict")
    
    out = {
            "headers": {
                "content-type": "application/json",
                "Access-Control-Allow-Origin": "*"
                },
            "body": labels,  
            "statusCode": 200
          }
    return out
