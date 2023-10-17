import csv
import cloudinary
import cloudinary.uploader
import logging
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
import sys, traceback

logging.basicConfig(level=logging.DEBUG,
format='%(levelname)s,%(message)s',
filename='log.csv',
filemode='w')
# turn off warnings from urllib3 library
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("cloudinary").setLevel(logging.ERROR)

def migrate_resources(row):
    # check if the id is in the list      
    try:    
    
        url = row[5]        
        public_id = row[3]                
        asset_folder = row[8].strip()
        display_name = row[9]
        metadata = f'artist={row[2]}|department=["music"]|asset_type=headshot|onyx_id={row[4]}|contentful_image_url={url}|contentful_entryid={row[1]}|contentful_id={row[0]}'        
        
        resource_type = 'image'
            
        resp = cloudinary.uploader.upload(
            'https:' + url,
            public_id=public_id,
            display_name= display_name,
            asset_folder=asset_folder,
            type='upload',
            resource_type=resource_type,
            metadata=metadata,            
            overwrite=True,
            unique_filename=False                    
        )   
        # append the extra columns before making the call
        row.append(public_id)
        row.append(resp['secure_url'])   
        data = '","'.join(row)                         
        logging.info(f'"{data}"')
    except Exception as e:
        row.append(public_id)
        row.append('')                
        row.append(f'{e}')
        logging.error(row)  
        #traceback.print_exc(file=sys.stdout)
        return


def execute_migration():        
    with open('images.csv','rt') as f:
    #with open('demo.csv','rt') as f:
        rows = csv.reader(f)    
        with PoolExecutor(max_workers=40) as executor:
            # migrate images
                for _ in executor.map(migrate_resources, rows):
                    pass        

execute_migration()
