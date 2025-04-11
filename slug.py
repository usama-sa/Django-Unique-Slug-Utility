"""
This module provides a utility function to generate unique slugs for Django model instances.
It handles both regular fields and nested fields (using double underscore notation) and ensures
that the generated slug is unique within the specified model.

IMPORTANT:
    - The slug is generated from the specified field (which can be nested using the double underscore
      notation, e.g. 'table__name').
    - If the generated slug (i.e., the base slug) is already in use by another instance,
      extra digits (a random string) are appended to the slug until a unique slug is obtained.
    - If the base slug is unique, it is returned as-is, without any extra text or digits.

Example Usage of `generate_unique_slug`:

1. For a regular field (e.g., 'title'):
----------------------------------------------------
from your_app.utils.slug import generate_unique_slug

# Inside your model or signal
instance.slug = generate_unique_slug(instance, field_name='title')


2. For a nested field (e.g., ForeignKey field like 'table__name'):
----------------------------------------------------
# This works when you want to base the slug off a foreign key's field,
# i.e., instance.table.name ➝ field_name='table__name'
instance.slug = generate_unique_slug(instance, field_name='table__name')


3. Example inside a Django pre-save signal:
----------------------------------------------------
from django.db.models.signals import pre_save
from django.dispatch import receiver
from your_app.models import YourModel
from your_app.utils.slug import generate_unique_slug

@receiver(pre_save, sender=YourModel)
def yourmodel_pre_save_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance, field_name='title')  # or 'table__name'
"""

import random
import string
from django.utils.text import slugify
from django.db.models import Model


def random_string_generator(size=6, chars=string.ascii_lowercase + string.digits):
    """
    Generates a random string of the specified size using the given charset.
    Default charset is alphanumeric lowercase.
    """
    return ''.join(random.choice(chars) for _ in range(size))


def resolve_field_value(instance: Model, field_name: str) -> str:
    """
    Resolves nested field values using double underscore notation.
    For example, "table__name" will fetch `instance.table.name`.
    
    Args:
        instance (Model): The model instance.
        field_name (str): The field name or nested field path.
    
    Returns:
        str: The value of the specified field as a string.
    
    Raises:
        ValueError: If the field path cannot be resolved.
    """
    attrs = field_name.split("__")
    value = instance
    for attr in attrs:
        try:
            value = getattr(value, attr)
        except AttributeError:
            raise ValueError(
                f"Attribute path '{field_name}' could not be resolved on instance of {instance.__class__.__name__}"
            )
    return str(value)


def generate_unique_slug(
    instance: Model,
    field_name: str,
    slug_field: str = "slug",
    filter_kwargs: dict = None,
    random_digits_size: int = 4,
    charset=string.ascii_lowercase + string.digits
) -> str:
    """
    Generates a unique slug for a Django model instance based on the specified field.
    
    Args:
        instance (Model): The model instance for which to generate the slug.
        field_name (str): Field path (can be nested like "table__name") to base the slug on.
        slug_field (str): The field name on the model where the slug will be stored.
        filter_kwargs (dict): Optional additional filters (e.g., for multi-tenancy).
        random_digits_size (int): The length of the random string to be appended if necessary.
        charset (str): The characters used for generating the random string.

    Returns:
        str: A unique slug string. The slug will be the slugified version of the field data if it 
             is unique. Otherwise, extra digits (a random string) will be appended until a unique slug is found.
    """
    # Get the base value from the field (supports nested fields using double underscores)
    base_value = resolve_field_value(instance, field_name)
    base_slug = slugify(base_value)
    Klass = instance.__class__
    filter_kwargs = filter_kwargs or {}
    
    # Use the base slug initially.
    slug = base_slug

    # Check for uniqueness. If the slug already exists, append a random string until we find a unique one.
    # The random string is only added if needed.
    while Klass.objects.filter(**{slug_field: slug}, **filter_kwargs).exclude(pk=instance.pk).exists():
        randstr = random_string_generator(size=random_digits_size, chars=charset)
        slug = f"{base_slug}-{randstr}"
    
    return slug


