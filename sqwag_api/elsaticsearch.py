import jsonpickle
from httplib2 import Http

def CreateDocument(userdata,id,url):
    data = jsonpickle.encode(userdata, unpicklable=True)
    url = url + str(id)
    h = Http()
    h.request(url,"POST",data)
    
def GetDocument(query=None,url=None,fields=None,filter=None,sort=None):
    data = {}
    flag = 0
    if fields is not None:
        data['fields'] = fields
        flag =1
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
        if flag == 0:
            content = jsonpickle.decode(content)
            result = []
            for res in content['hits']['hits']:
                result.append(res['_source'])
            return result
        else:
            return content
    else:
        return resp

def DeleteDocument(url,id):
    h = Http()
    url = url + str(id)
    h.request(url,"DELETE")