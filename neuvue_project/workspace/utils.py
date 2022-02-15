from zipfile import ZipFile
from django.core.validators import URLValidator
import json
from pytz import timezone
import pytz

def is_url(value):
    validate = URLValidator()
    try:
        validate(value)
        return True
    except:
        return False

def is_json(value):
    try:
        json.loads(value)
        return True
    except:
        return False

def utc_to_eastern(time_value):
    """Converts a pandas datetime object to a US/Easten datetime.

    Args:
        time_value (pd.DateTime): the timevalue you wish to convert

    Returns:
        DateTime: Datetime object
    """
    try:
        utc = pytz.UTC
        eastern = timezone('US/Eastern')
        date_time = time_value.to_pydatetime()
        date_time = utc.localize(time_value)
        return date_time.astimezone(eastern)
    except:
        return time_value
import os
from django.http import HttpResponse
from typing import Optional
import glob
def download_single_file_response(content_type:str, filename:str, dir:str='/tmp', download_filename:Optional[str]=None):
    """Returns a httpReponse to download a single file

    Args:
        filename (str): The filename to download
    """
    download_filename = download_filename or filename
    # TODO: filter on binary MIME types
    rwmode = 'r' if content_type != 'application/zip' else 'rb'
    try:
        with open(os.path.join(dir,filename),rwmode) as fp:
            response = HttpResponse(fp.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(download_filename)
    finally:
        clean_tmp_files(filename, dir)
        
    return response
def download_multiple_file_zip_response(dir:str,download_filename, globspec="*"):
    # Downloads all files in dir in the form of a zip
    # Do zipping
    
    # throw nice error here if directory already exists for some reason
    
    assert dir!='/tmp'
    zip_filename = os.path.join(dir,'tmp.zip')
    files_to_zip = [fn for fn in glob.glob(os.path.join(dir,globspec))]
    with ZipFile(zip_filename,'w') as zipped:
        for fn in files_to_zip:
            zipped.write(fn,arcname=os.path.basename(fn))
    

        
    try:
        return download_single_file_response(content_type='application/zip',filename=zip_filename, dir=dir, download_filename=download_filename)
    finally:
        clean_tmp_files("*.zip",dir=dir)
        clean_tmp_files(globspec,dir=dir)
        os.rmdir(dir)
        
       
def clean_tmp_files(globspec,dir:str='/tmp'):
    for fn in glob.glob(os.path.join(dir, globspec)):
        os.remove(fn)