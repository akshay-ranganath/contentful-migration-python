#!/usr/bin/env python
# coding: utf-8

import contentful_management
import json
import csv
import cloudinary.uploader
import re
import requests


# all the setup information
# change the Contentful IDs here

SPACE_ID = '<<space id>>'
API_KEY = '<<api key>>'
ENVIRONMENT_ID = 'master'
CLD_TYPE = 'upload'
ELEMENT_NAME = 'image'
DOMAIN_NAME='res.cloudinary.com'
CLOUD_NAME='<< cloudinary sub-account name>>'
CONTENT_TYPE="musician"
ROOT_FOLDER="Talent Headshots-Approved"
DEPARTMENT="Music"
SUFFIX="-headshot"
assets = {}


# get details of all entries, based on pagination
def get_entries(limit, skip):
    url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/environments/master/entries?access_token={API_KEY}&limit={limit}&skip={skip}"
    response = requests.request("GET", url)
    return response.json()

# get details of a single entry
def get_single_entry(entry_id):
    url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/environments/master/entries/{entry_id}?access_token={API_KEY}"
    #print(url)
    response = requests.get("GET", url)
    return response.json()

# get the embedded image details
def get_image(image_id):
    url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/environments/master/assets/{image_id}?access_token={API_KEY}"
    response = requests.request("GET", url)
    return response.json()

# find the embedded image references within each entry
def get_image_references():    
    total = get_entries(1,skip=0)['total']
    print(f"Checking a total of {total} entries")
    #total = 10
    images = {}
    steps = 100
    unpublished_entry = 0
    published_entry = 0
    for processed in range(0,total,steps):    
        published = False
        entries = get_entries(steps, processed)
        #print(f"{entries['total']},{entries['skip']},{entries['limit']}")
        #print(json.dumps(entries, indent=2))
        current_images = set()
        for entry in entries['items']:  
            fields = entry['fields']
            #print(json.dumps(fields, indent=2))
            if fields.get('image'):                
                image_id = fields['image']['sys']['id']
                #print(image_id)
                current_images.add(image_id)
                #print(fields)
                if image_id in images:
                    print(f'Duplicate detected for the image: {image_id}. It is used on assets with ids {images[image_id]}')
                else:
                    images[image_id] = {
                        'entryId': entry['sys']['id'], 
                        'name': fields['name'],
                        'slug': fields.get('slug') or 'MISSING',
                        'mongoId': fields.get('masterDB') or '-1'
                    }
    #print(f"Published images = {published_entry}\nunpublished images = {unpublished_entry}")
    return images


# extract and save the embedded image information
def get_image_details(images):
    for img_id in images:
        resp = get_image(img_id)
        try:
            if resp.get('sys').get('type') and resp['sys']['type']=="Error":
                print(f'{images[img_id]["entryId"]},{img_id},not found')
            else:

                    fields = resp['fields']['file']
                    images[img_id]['url'] = fields['url']
                    images[img_id]['fileName'] = fields['fileName']
                    images[img_id]['contentType'] = fields['contentType']
        except Exception as e:
                print(resp)
    return images
        

# helper function to build Cloudinary friendly names
def sanitize_image_details(image):
    for field in ['name','slug']:
        image[field] = image[field].replace('+', 'plus')
        image[field] = image[field].replace('&', 'and')
        image[field] = image[field].replace('$', 'and')
        image[field] = image[field].replace('!', '')
    return image

# translate Contentful details to Cloudinary specific format
def get_generate_cloudinary_info(image):
    # for now, it can either be jpeg or png. 
    extension = "jpg"
    if image.get('contentType') and image['contentType'] != "image/jpeg":
            extension = image['contentType'].split('/')[1]
                
    image['assetFolder'] = ROOT_FOLDER + '/' + DEPARTMENT + '/' + image['name'] 
    image['displayName'] = image['slug'] + SUFFIX + '.' + extension
    return image


# dump the details to a manifest file
def write_manifest(images):
    with open('images.csv', 'w') as w:
        writer = csv.writer(w)
        for img_id in images:
            image = images[img_id] 
            image = sanitize_image_details(image)
            image = get_generate_cloudinary_info(image)
            writer.writerow([
                img_id,
                image['entryId'],
                image['name'],
                image['slug'],
                image['mongoId'],
                image.get('url') or '',
                image.get('fileName') or '',
                image.get('contentType') or '',
                image['assetFolder'],
                image['displayName']
            ])


print("Finding image ids referenced in assets")
images = get_image_references()
print("Image references found. Now fetching image details")
images = get_image_details(images)
print("Image information now available. Writing to manifest file")
write_manifest(images)
print("Manifest file created successfully")