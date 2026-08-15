<h2 id="slide-{{ loop.index }}-heading">{{ rendered_title | safe }}</h2>
<div class="slide-content-area">
{% if rendered_description %}<div class="hero-description">{{ rendered_description | safe }}</div>
{% elif slide.description %}<p class="hero-description">{{ slide.description | e }}</p>{% endif %}
{% if rendered_body %}<div class="hero-body">{{ rendered_body | safe }}</div>{% elif slide.body %}<div class="hero-body">{{ slide.body | e }}</div>{% endif %}
</div>
{% if slide.notes %}<aside class="slide-notes" hidden aria-hidden="true">{{ slide.notes | e }}</aside>{% endif %}
