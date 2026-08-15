<h2 id="{{ slide_id }}-heading">{{ rendered_title | safe }}</h2>
<div class="slide-content-area">
<div class="figure-container">
  <figure>
    {% if rendered_mermaid %}
      <div class="diagram-container">{{ rendered_mermaid | safe }}</div>
    {% elif rendered_svg %}
      <div class="diagram-container" role="img" aria-label="{{ slide.alt_text | e }}">{{ rendered_svg | safe }}</div>
    {% elif rendered_image %}
      {{ rendered_image | safe }}
    {% else %}
      <img src="{{ slide.src | e }}" alt="{{ slide.alt_text | e }}">
    {% endif %}
    {% if slide.caption %}<figcaption id="{{ slide_id }}-caption">{{ slide.caption | e }}</figcaption>{% endif %}
  </figure>
</div>
{% if slide.body %}<div class="slide-body">{{ rendered_body | safe }}</div>{% endif %}
</div>
{% if slide.notes %}<aside class="slide-notes" hidden aria-hidden="true">{{ slide.notes | e }}</aside>{% endif %}
