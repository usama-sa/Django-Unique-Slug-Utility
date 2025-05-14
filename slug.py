"""
This module provides a utility function to generate unique slugs for Django model instances.
It handles both regular fields and nested fields (using double underscore notation) and ensures
that the generated slug is unique within the specified model while adhering to a maximum length.

IMPORTANT:
    - The slug is generated from the specified field (which can be nested using the double underscore
        notation, e.g. 'table__name').
    - The resulting slug will **never exceed 75 characters**.
    - If the generated slug (i.e., the base slug) is already in use by another instance,
        a random suffix will be appended to the slug, while keeping the entire string within the max length.
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


MAX_SLUG_LENGTH = 75


def random_string_generator(size=6, chars=string.ascii_lowercase + string.digits):
    """
    Generates a random string of the specified size using the given charset.
    Default charset is alphanumeric lowercase.
    
    Args:
        size (int): Length of the random string to generate.
        chars (str): Characters to choose from.
    
    Returns:
        str: Randomly generated string.
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
    charset=string.ascii_lowercase + string.digits,
    max_length: int = MAX_SLUG_LENGTH
) -> str:
    """
    Generates a unique slug for a Django model instance based on the specified field.
    Ensures that the slug does not exceed the max_length and handles uniqueness by
    appending a random suffix if necessary.

    Args:
        instance (Model): The model instance for which to generate the slug.
        field_name (str): Field path (can be nested like "table__name") to base the slug on.
        slug_field (str): The field name on the model where the slug will be stored.
        filter_kwargs (dict): Optional additional filters (e.g., for multi-tenancy).
        random_digits_size (int): The length of the random string to be appended if necessary.
        charset (str): The characters used for generating the random string.
        max_length (int): Maximum allowed length for the final slug.

    Returns:
        str: A unique slug string. The slug will be the slugified version of the field data if it 
            is unique and under the limit. Otherwise, a suffix will be added while keeping the 
            final slug within the length constraint.
    """
    # Step 1: Resolve field value (supports nested fields using double underscores)
    base_value = resolve_field_value(instance, field_name)
    
    # Step 2: Slugify the raw value
    raw_slug = slugify(base_value)

    # Step 3: Trim the slug to the maximum allowed length
    base_slug = raw_slug[:max_length]

    # Step 4: Prepare initial slug and model query
    slug = base_slug
    Klass = instance.__class__
    filter_kwargs = filter_kwargs or {}

    # Step 5: Fetch all existing slugs that start with the base_slug
    existing_slugs = Klass.objects.filter(
        **{f"{slug_field}__startswith": base_slug},
        **filter_kwargs
    ).exclude(pk=instance.pk).values_list(slug_field, flat=True)

    existing_slugs = set(existing_slugs)

    # Step 6: If base slug is unique, return it
    if slug not in existing_slugs:
        return slug

    # Step 7: Try appending suffixes until a unique slug is found
    while True:
        # Create a suffix of fixed size (e.g., "-a1b2")
        suffix = '-' + random_string_generator(size=random_digits_size, chars=charset)

        # Truncate base slug to make room for suffix within max_length
        allowed_base_length = max_length - len(suffix)
        trimmed_base = base_slug[:allowed_base_length]

        # Combine base and suffix
        new_slug = f"{trimmed_base}{suffix}"

        # If the new slug is unique, return it
        if new_slug not in existing_slugs:
            return new_slug
