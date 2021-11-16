from django.db import models

# Create your models here.
class Namespace(models.Model):
    namespace = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    ng_link_type = models.CharField(max_length=50)
    
    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.namespace
