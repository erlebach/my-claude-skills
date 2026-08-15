<h2 id="{{ slide_id }}-heading">{{ rendered_title | safe }}</h2>
<div class="slide-content-area">
{% set body_html = rendered_body if rendered_body else (slide.body | e if slide.body else '') %}
{% set left_has_content = slide.left is not none %}
{% set right_has_content = slide.right is not none %}
{% set both_have_content = left_has_content and right_has_content %}
{% set body_in_column = body_html and (left_has_content != right_has_content) %}
{% if body_html and not body_in_column %}<div class="slide-body two-col-caption-above">{{ body_html | safe }}</div>{% endif %}
<div class="two-col two-col-{{ slide.proportion | replace('/', '-') }}{% if both_have_content %} two-col-both{% endif %}">
  <div class="col-left">
    {% if rendered_left_col %}
      {{ rendered_left_col | safe }}
    {% elif body_in_column %}
      <div class="slide-body">{{ body_html | safe }}</div>
    {% endif %}
  </div>
  <div class="col-right">
    {% if rendered_right_col %}
      {{ rendered_right_col | safe }}
    {% elif body_in_column %}
      <div class="slide-body">{{ body_html | safe }}</div>
    {% endif %}
  </div>
</div>
</div>
{% if slide.notes %}<aside class="slide-notes" hidden aria-hidden="true">{{ slide.notes | e }}</aside>{% endif %}
