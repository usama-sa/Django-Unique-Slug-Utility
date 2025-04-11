# Django Unique Slug Generator 🔗

A reusable Django utility for generating **unique slugs** from any model field — including nested or related fields via `ForeignKey`, `OneToOneField`, etc. Handles slug conflicts gracefully by appending random characters **only when needed**, making your URLs clean, consistent, and human-readable.

---

## 🚀 Features

- ✅ Supports both regular and nested field names (e.g., `title`, `category__name`, etc.)
- ✅ Ensures uniqueness of slugs across the model
- ✅ Adds random string suffix **only when needed**
- ✅ Optional support for scoping uniqueness (e.g., per tenant, per organization)
- ✅ Easy to integrate with `pre_save` signals or model save overrides
- ✅ Fully documented and customizable

---

## 📦 Installation

No PyPI package yet. Just copy the utility module into your Django project:

