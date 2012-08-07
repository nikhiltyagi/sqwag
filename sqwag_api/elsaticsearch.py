import jsonpickle
from httplib2 import Http

def CreateDocument(userdata,id,url):
    data = jsonpickle.encode(userdata, unpicklable=True)
    url = url + str(id)
    h = Http()
    h.request(url,"POST",data)
    
def GetDocument(query=None,url=None,fields=None,filter=None,sort=None):
    data = {}
    if fields is not None:
        data['fields'] = fields
    if query is not None:
        data['query'] = query
    if filter is not None:
        data['filter'] = filter
    if sort is not None:
        data['sort'] = sort
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

def DeleteDocument(url,id):
    h = Http()
    url = url + str(id)
    h.request(url,"DELETE")