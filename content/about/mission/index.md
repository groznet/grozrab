---
title: "Наша миссия и цели"
description: "Основные направления деятельности и журналистские стандарты."
draft: false
---

The most important concept to understand before creating a template is context, the data passed into each template. The data may be a simple value, or more commonly objects and associated methods.

For example, a page template receives a Page object, and the Page object provides methods to return values or perform actions.

Current context
Within a template, the dot (.) represents the current context.

In the example above the dot represents the Page object, and we call its Title method to return the title as defined in front matter.

The current context may change within a template. For example, at the top of a template the context might be a Page object, but we rebind the context to another value or object within range or with blocks.