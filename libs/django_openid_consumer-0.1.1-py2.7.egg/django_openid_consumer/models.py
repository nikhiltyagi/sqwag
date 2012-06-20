from django.db import models

class Nonce(models.Model):
    server_url = models.URLField(db_index=True)
    timestamp  = models.IntegerField(db_index=True)
    salt       = models.CharField( max_length=50 )

    def __unicode__(self):
        return "Nonce: %i @ %s" % (self.timestamp, self.server_url)

class Association(models.Model):
    server_url = models.TextField(max_length=2047, db_index=True)
    handle = models.CharField(max_length=255, db_index=True)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)

    def __unicode__(self):
        return "Association: %s, %s" % (self.server_url, self.handle)
