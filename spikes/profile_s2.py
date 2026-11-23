import time, os
os.environ["AWS_NO_SIGN_REQUEST"]="YES"
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
from pystac_client import Client

bbox=(15.23,-12.97,15.32,-12.88)
cat=Client.open("https://earth-search.aws.element84.com/v1")
t=time.time()
items=list(cat.search(collections=["sentinel-2-l2a"],bbox=bbox,datetime="2025-06-01/2025-09-30",query={"eo:cloud_cover":{"lt":10}}).items())
print("search",round(time.time()-t,1),len(items))
it=items[0]
print({k:v.href[-60:] for k,v in it.assets.items() if k in("red","scl","swir16")})
for env in [{}, {"GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR","CPL_VSIL_CURL_ALLOWED_EXTENSIONS":".tif","GDAL_HTTP_MULTIPLEX":"YES","GDAL_HTTP_VERSION":"2","VSI_CACHE":"TRUE"}]:
  with rasterio.Env(AWS_NO_SIGN_REQUEST="YES",**env):
    for band in ["red","swir16"]:
        t=time.time()
        with rasterio.open(it.assets[band].href) as ds:
            t_open=time.time()-t
            tr=Transformer.from_crs(4326,ds.crs,always_xy=True)
            x0,y0=tr.transform(bbox[0],bbox[1]); x1,y1=tr.transform(bbox[2],bbox[3])
            w=from_bounds(x0,y0,x1,y1,ds.transform)
            a=ds.read(1,window=w)
        print(bool(env),band,"open",round(t_open,2),"total",round(time.time()-t,2),a.shape)
