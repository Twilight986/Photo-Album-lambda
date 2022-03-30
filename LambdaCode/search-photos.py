import json
import boto3
import os
import sys
import uuid
import time
import requests
import inflect

ES_HOST = 'https://search-coms6998hw2-if6wqsl2ycyzxsmj4ujcjvkrem.us-east-1.es.amazonaws.com'
REGION = 'us-east-1'
aws_auth = ('admin', 'Coms6998!')

# 03/29 20:58
# 03/30 10:19
# 03/30 11:35

def return_singular(argument, word):  
	argument = inflect.engine()
	return argument.singular_noun(word)


def singular_test(argument, word):
	argument = inflect.engine()
	if argument.singular_noun(word) == False:
		print(word, "is singular")
		return True
	else:
		print(word, "is plural")
		return False


def get_url(es_index, es_type, keyword):
	# url = ES_HOST + '/' + es_index + '/' + es_type + '/_search?q=' + keyword.lower()
	url = ES_HOST + '/' + es_index + '/_search?q=' + keyword.lower()
	return url


def lambda_handler(event, context):
	# recieve from API Gateway
	print('event: ', event)
	print("EVENT --- {}".format(json.dumps(event)))

	headers = {"Content-Type": "application/json"}
	lex = boto3.client('lex-runtime', 'us-east-1')

	query = event["queryStringParameters"]["q"]
	print('query is: ', query)

	lex_response = lex.post_text(
		botName='photoLex',
		botAlias='photoBot',
		userId='string',
		inputText=query
	)

	print("LEX RESPONSE --- {}".format(json.dumps(lex_response)))
	if 'slots' not in lex_response:
		return {
			'statusCode': 200,
			'headers': {
				'Access-Control-Allow-Headers': '*',
				'Access-Control-Allow-Origin': '*',
				'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
			},
			'body': json.dumps("No such photos.")
		}

	slots = lex_response['slots']
	print('slots are: ', slots)
	img_list_1 = []
	img_list_2 = []
	print('img_list_1 is: ', img_list_1)
	print('img_list_2 is: ', img_list_2)
	flag1 = None
	flag2 = None
	if slots['slotOne']:
		tag = slots['slotOne']
		print('Orign tag is', tag)

		flag1 = singular_test(inflect, tag)  # Ture 为 单数 False为复数
		if flag1 == False:
			tag = return_singular(inflect, tag)
			print('After tag is ', tag)
		url = get_url('photos', 'Photo', tag)
		print("ES URL --- {}".format(url))
		es_response = requests.get(url, auth=aws_auth, headers=headers).json()
		print("ES RESPONSE --- {}".format(json.dumps(es_response)))

		es_src = es_response['hits']['hits']
		print("ES HITS --- {}".format(json.dumps(es_src)))

		for photo in es_src:
			labels = [word.lower() for word in photo['_source']['labels']]
			if tag in labels:
				objectKey = photo['_source']['objectKey']
				print('objectKey: ', objectKey)
				img_url = 'https://s3.amazonaws.com/coms6998hw2b2/' + objectKey
				img_list_1.append(img_url)

	if slots['slotTwo']:
		tag = slots['slotTwo']
		print('Orign tag is', tag)

		flag2 = singular_test(inflect, tag)  # Ture 为 单数 False为复数
		print('Flag is: ', flag2)
		if flag2 == False:
			tag = return_singular(inflect, tag)
			print('After tag is ', tag)

		url = get_url('photos', 'Photo', tag)
		print("ES URL --- {}".format(url))
		es_response = requests.get(url, auth=aws_auth, headers=headers).json()
		print("ES RESPONSE --- {}".format(json.dumps(es_response)))

		es_src = es_response['hits']['hits']
		print("ES HITS --- {}".format(json.dumps(es_src)))

		for photo in es_src:
			labels = [word.lower() for word in photo['_source']['labels']]
			if tag in labels:
				objectKey = photo['_source']['objectKey']
				print('objectKey: ', objectKey)
				img_url = 'https://s3.amazonaws.com/coms6998hw2b2/' + objectKey
				img_list_2.append(img_url)

	img_list = []
	print('img_list_1 is: ', img_list_1)
	print('img_list_2 is: ', img_list_2)

	if img_list_1 == [] and img_list_2 != []:
		img_list_buffer = img_list_2
	elif img_list_1 != [] and img_list_2 == []:
		img_list_buffer = img_list_1
	else:
		img_list_buffer = list(set(img_list_1).intersection(set(img_list_2)))
	print('img_list_buffer is ', img_list_buffer)

	if (flag1 == False and flag2 == False) or (flag1 == False and flag2 == None):  # 全复数是复
		img_list = img_list_buffer
	elif (flag1 == False or flag2 == False) and img_list_buffer != []:  # 有一个是复数就单数
		img_list = [img_list_buffer[0]]
	elif flag1 == True and img_list_buffer != []:
		img_list = [img_list_buffer[0]]

	if img_list:
		print('img_list is ', img_list)
		return {
			'statusCode': 200,
			'headers': {
				'Access-Control-Allow-Headers': '*',
				'Access-Control-Allow-Origin': '*',
				'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
			},
			'body': json.dumps(img_list)
		}
	else:
		return {
			'statusCode': 200,
			'headers': {
				'Access-Control-Allow-Headers': '*',
				'Access-Control-Allow-Origin': '*',
				'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
			},
			'body': json.dumps("No such photos.")
		}