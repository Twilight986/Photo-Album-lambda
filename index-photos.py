import json
import boto3
import os
import sys
import uuid
import requests
#from botocore.vendored import requests
# from PIL import Image
# import PIL.Image
from datetime import *

ES_HOST = 'https://search-coms6998hw2-if6wqsl2ycyzxsmj4ujcjvkrem.us-east-1.es.amazonaws.com'
REGION = 'us-east-1'
aws_auth = ('admin', 'Coms6998!')
def get_url(index, type):
    url = ES_HOST + '/' + index + '/' + type
    return url
    
# def resize_image(image_path, resized_path):
#     with Image.open(image_path) as image:
#         image.thumbnail(tuple(x / 2 for x in image.size))
#         image.save(resized_path)

def lambda_handler(event, context):
    print("EVENT --- {}".format(json.dumps(event)))

    headers = { "Content-Type": "application/json" }
    rek = boto3.client('rekognition','us-east-1')
    
    # get the image information from S3
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size'] # up to 5MB
        
        print('bucket is ' + bucket)
        print('key is ' + key)
        # detect the labels of current image
        labels = rek.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10
        )
        
    print("IMAGE LABELS --- {}".format(labels['Labels']))
    
    # prepare JSON object
    obj = {}
    obj['objectKey'] = key
    obj["bucket"] = bucket
    obj["createdTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    obj["labels"] = []
        
    for label in labels['Labels']:
        obj["labels"].append(label['Name'])
    
    print("JSON OBJECT --- {}".format(obj))
    
    # post the JSON object into ElasticSearch, _id is automaticlly increased
    url = get_url('photos', 'Photo')
    print("ES URL --- {}".format(url))
    obj = json.dumps(obj)
    req = requests.post(url, auth=aws_auth, data=obj, headers=headers)
        
    print("Success: ", req)
    return {
        'statusCode': 200,
        'headers': {
            	'Access-Control-Allow-Headers': '*',
				'Access-Control-Allow-Origin': '*',
				'Access-Control-Allow-Methods': '*'
        },
        'body': json.dumps("Image labels have been successfully detected!")
    }