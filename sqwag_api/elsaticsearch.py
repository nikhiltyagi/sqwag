import jsonpickle
from httplib2 import Http

def CreateDocument(userdata,id,url):
    data = jsonpickle.encode(userdata, unpicklable=True)
    url = url + str(id)
    h = Http()
    h.request(url,"POST",data)
    
def GetDocument(query,url,fields=None,sort=None):
    data = {}
    if fields is not None:
        data['fields'] = fields
    data['query'] = query
    h = Http()
    data = jsonpickle.encode(data,unpicklable=True)
    print data
    resp,content = h.request(url,"GET",data)
    print content
    print resp
    if resp.status == 200:
        return content
    else:
        return resp